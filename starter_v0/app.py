from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"

load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent Lab",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root {
        --ink: #0f172a;
        --muted: #64748b;
        --paper: #f6f9ff;
        --card: #ffffff;
        --blue: #2563eb;
        --blue-dark: #1e40af;
        --blue-soft: #dbeafe;
        --border: #e2e8f0;
      }
      .stApp {
        background: radial-gradient(circle at 90% 0%, #dbeafe 0, transparent 26rem),
                    linear-gradient(180deg, #f8fbff 0%, #f1f5f9 100%);
        color: var(--ink);
      }
      .stApp, .stApp p, .stApp label, .stApp li,
      .stApp [data-testid="stMarkdownContainer"] {
        color: var(--ink);
      }
      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2f78, #123d97);
        border-right: 1px solid rgba(255,255,255,.12);
      }
      [data-testid="stSidebar"] h1,
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3,
      [data-testid="stSidebar"] p,
      [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] small,
      [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #f7f4ea !important;
      }
      [data-testid="stSidebar"] .stSelectbox label,
      [data-testid="stSidebar"] .stTextInput label,
      [data-testid="stSidebar"] .stSlider label {
        color: #dce5de !important;
      }
      [data-testid="stSidebar"] input {
        background: #fffdf8 !important;
        color: #17211b !important;
        caret-color: #17211b !important;
      }
      [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #fffdf8 !important;
        color: #17211b !important;
      }
      [data-testid="stSidebar"] [data-baseweb="select"] span {
        color: #17211b !important;
      }
      [data-testid="stSidebar"] code {
        background: #0b245f;
        color: #dbeafe !important;
      }
      .hero {
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 24px 28px;
        margin: 4px 0 22px;
        background: rgba(255,255,255,.92);
        box-shadow: 0 12px 32px rgba(37,99,235,.08);
      }
      .eyebrow {
        color: var(--blue);
        font-size: .76rem;
        font-weight: 800;
        letter-spacing: .14em;
        text-transform: uppercase;
      }
      .hero h1 {
        color: var(--ink);
        font-family: Inter, ui-sans-serif, system-ui, sans-serif;
        font-size: clamp(1.85rem, 3vw, 3rem);
        line-height: 1.08;
        letter-spacing: -.035em;
        margin: 8px 0 12px;
      }
      .hero p { color: var(--muted); max-width: 720px; margin: 0; }
      .artifact-pill {
        display: inline-block;
        margin-top: 14px;
        padding: 6px 10px;
        background: var(--blue-soft);
        color: var(--blue-dark);
        border-radius: 999px;
        font: 700 .75rem ui-monospace, monospace;
      }
      [data-testid="stChatMessage"] {
        background: rgba(255,255,255,.92);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 8px 12px;
        box-shadow: 0 6px 20px rgba(15,23,42,.05);
      }
      [data-testid="stChatMessage"] p,
      [data-testid="stChatMessage"] li {
        color: #17211b !important;
      }
      [data-testid="stMetric"] {
        background: #fff;
        border: 1px solid var(--border);
        padding: 14px 16px;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(15,23,42,.04);
      }
      [data-testid="stMetricLabel"] *,
      [data-testid="stMetricValue"] {
        color: #17211b !important;
      }
      .trace-title {
        color: var(--blue-dark);
        font-weight: 800;
        letter-spacing: .02em;
      }
      .tool-chip {
        display: inline-block;
        padding: 3px 8px;
        margin-right: 5px;
        border-radius: 999px;
        background: var(--blue);
        color: #fff;
        font-size: .75rem;
      }
      .status-ok { color: #267051; font-weight: 800; }
      .status-wait { color: #a4532b; font-weight: 800; }
      .stButton > button {
        border-radius: 10px;
        border: 1px solid #60a5fa;
        background: var(--blue);
        color: white;
        font-weight: 700;
      }
      .stButton > button:hover {
        background: var(--blue-dark);
        color: white;
        border-color: var(--blue-dark);
      }
      [data-testid="stDataFrame"], [data-testid="stExpander"] {
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 14px;
        box-shadow: 0 5px 18px rgba(15,23,42,.04);
      }
      @media (max-width: 768px) {
        .hero { padding: 20px; border-radius: 16px; }
        .hero h1 { font-size: 1.75rem; }
        [data-testid="stHorizontalBlock"] { gap: .65rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def new_transcript(
    version: str,
    provider_name: str,
    model: str | None,
    history_window: int,
    max_tool_rounds: int,
) -> tuple[dict[str, Any], Path]:
    artifact = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join(
        [safe_slug(version), safe_slug(provider_name), stamp]
    )
    path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    write_transcript(path, transcript)
    return transcript, path


def reset_session() -> None:
    for key in ("messages", "turns", "transcript", "transcript_path", "session_config"):
        st.session_state.pop(key, None)


def configured_providers() -> list[str]:
    env_by_provider = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    return [
        provider
        for provider, env_name in env_by_provider.items()
        if os.getenv(env_name, "").strip()
    ]


SENSITIVE_KEYS = re.compile(
    r"(api[_-]?key|authorization|token|secret|password|cookie|credential)",
    re.IGNORECASE,
)
BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
KEY_PATTERN = re.compile(
    r"\b(?:sk|pk|key|token)-[A-Za-z0-9_-]{8,}\b", re.IGNORECASE
)
EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


def redact_sensitive(value: Any) -> Any:
    """Return a display-safe copy without mutating the evidence stored on disk."""
    if isinstance(value, dict):
        return {
            key: ("••••••••" if SENSITIVE_KEYS.search(str(key)) else redact_sensitive(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)
    if isinstance(value, str):
        text = BEARER_PATTERN.sub("Bearer ••••••••", value)
        text = KEY_PATTERN.sub("••••••••", text)
        if st.session_state.get("hide_personal_data", True):
            text = EMAIL_PATTERN.sub("•••@•••", text)
        return text
    return value


def safe_json_bytes(value: Any) -> bytes:
    return json.dumps(
        redact_sensitive(value), ensure_ascii=False, indent=2
    ).encode("utf-8")


def friendly_provider_error(exc: Exception, provider_name: str) -> str:
    message = str(exc)
    if "Missing API key env var" in message:
        return f"{message}. Bổ sung key trong .env rồi khởi động lại UI."
    if "Không kết nối được" in message or type(exc).__name__ in {
        "APIConnectionError",
        "APITimeoutError",
    }:
        return (
            f"{message}\n\n"
            f"Provider đang chọn: `{provider_name}`. "
            "Hãy kiểm tra mạng/firewall và thử lại sau vài giây."
        )
    return f"{type(exc).__name__}: {message}"


def show_trace(turn: dict[str, Any]) -> None:
    rounds = turn.get("rounds", [])
    status = turn.get("status", "unknown")
    label = f"Trace · {len(rounds)} round(s) · {status}"
    with st.expander(label, expanded=status in {"provider_error", "max_tool_rounds"}):
        if turn.get("error"):
            st.error(turn["error"])
        for round_data in rounds:
            st.markdown(
                f'<div class="trace-title">Round {round_data.get("round", "?")}</div>',
                unsafe_allow_html=True,
            )
            calls = round_data.get("tool_calls", [])
            if not calls:
                st.caption("Không gọi tool — agent trả lời trực tiếp.")
            for index, call in enumerate(calls, start=1):
                name = call.get("name", "unknown")
                st.markdown(
                    f'<span class="tool-chip">{index}. {name}</span>',
                    unsafe_allow_html=True,
                )
                left, right = st.columns(2)
                with left:
                    st.caption("Arguments")
                    st.json(redact_sensitive(call.get("args", {})), expanded=True)
                event = next(
                    (
                        item
                        for item in round_data.get("tool_results", [])
                        if item.get("tool") == name
                    ),
                    {},
                )
                with right:
                    st.caption("Result / error")
                    st.json(redact_sensitive(event.get("result", {})), expanded=True)
            if round_data.get("assistant_text"):
                st.caption("Assistant note")
                st.write(round_data["assistant_text"])


with st.sidebar:
    st.markdown("## 🔎 Research Agent")
    st.caption("Trung tâm điều khiển và giám sát")
    page = st.radio(
        "Menu",
        ["💬 Trò chuyện", "📊 Tổng quan", "🧭 Tool traces"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### Bộ lọc & bảo mật")
    status_filter = st.selectbox(
        "Trạng thái trace",
        ["Tất cả", "completed", "provider_error", "max_tool_rounds"],
    )
    st.session_state.hide_personal_data = st.toggle(
        "Ẩn email và dữ liệu cá nhân",
        value=st.session_state.get("hide_personal_data", True),
        help="API key, token, secret và mật khẩu luôn được che.",
    )
    st.caption("🔒 Secrets luôn được ẩn trên giao diện và file tải xuống.")
    st.markdown("---")
    st.markdown("### Cấu hình phiên")
    provider_options = configured_providers()
    if not provider_options:
        st.error("Chưa tìm thấy API key hợp lệ trong .env.")
        provider_options = ["openrouter"]
    provider_name = st.selectbox("Provider", provider_options, index=0)
    st.caption("Chỉ hiển thị provider đã có API key.")
    version = st.text_input("Artifact version", value="v1")
    model_override = st.text_input("Model override", value="", placeholder="Để trống = mặc định")
    history_window = st.slider("History window", 1, 10, 5)
    max_tool_rounds = st.slider("Max tool rounds", 1, 8, 4)

    current_artifact = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    st.markdown("---")
    st.caption("ARTIFACT ID")
    st.code(current_artifact.artifact_version, language=None)
    st.caption(f"Prompt hash · {current_artifact.prompt_hash}")
    st.caption(f"Tools hash · {current_artifact.tools_hash}")

    if st.button("Bắt đầu phiên mới", use_container_width=True):
        reset_session()
        st.rerun()

    if st.session_state.get("transcript_path"):
        path = Path(st.session_state.transcript_path)
        st.markdown("---")
        st.caption("TRANSCRIPT")
        st.code(path.name, language=None)
        if path.exists():
            st.download_button(
                "Tải transcript đã ẩn dữ liệu",
                data=safe_json_bytes(st.session_state.transcript),
                file_name=path.name,
                mime="application/json",
                use_container_width=True,
            )

st.markdown(
    f"""
    <section class="hero">
      <div class="eyebrow">AI Research Workspace</div>
      <h1>Research Agent<br>Control Center</h1>
      <p>Nghiên cứu, theo dõi công cụ và đánh giá hiệu suất trong một
      không gian làm việc bảo mật, rõ ràng và chuyên nghiệp.</p>
      <span class="artifact-pill">{current_artifact.artifact_version}</span>
    </section>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(3)
turns = st.session_state.get("turns", [])
tool_count = sum(len(turn.get("tool_events", [])) for turn in turns)
error_count = sum(1 for turn in turns if turn.get("status") == "provider_error")
metric_cols[0].metric("Turns", len(turns))
metric_cols[1].metric("Tool events", tool_count)
metric_cols[2].metric("Provider errors", error_count)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "turns" not in st.session_state:
    st.session_state.turns = []

if page == "📊 Tổng quan":
    st.subheader("Phân tích hoạt động")
    tool_names = [
        event.get("tool", "unknown")
        for turn in turns
        for event in turn.get("tool_events", [])
    ]
    tool_rows = [
        {"Công cụ": name, "Số lần gọi": count}
        for name, count in Counter(tool_names).most_common()
    ]
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### Lượt gọi theo công cụ")
        if tool_rows:
            st.bar_chart(tool_rows, x="Công cụ", y="Số lần gọi", color="#2563eb")
        else:
            st.info("Chưa có dữ liệu. Hãy bắt đầu một cuộc trò chuyện.")
    with right:
        st.markdown("#### Dữ liệu phiên gần đây")
        summary_rows = [
            {
                "Lượt": turn.get("turn_index"),
                "Trạng thái": turn.get("status"),
                "Rounds": len(turn.get("rounds", [])),
                "Tool events": len(turn.get("tool_events", [])),
            }
            for turn in turns[-10:]
        ]
        if summary_rows:
            st.dataframe(summary_rows, use_container_width=True, hide_index=True)
        else:
            st.info("Bảng sẽ xuất hiện khi có lượt chạy đầu tiên.")
    st.stop()

if page == "🧭 Tool traces":
    st.subheader("Nhật ký công cụ")
    visible_turns = [
        turn
        for turn in reversed(turns)
        if status_filter == "Tất cả" or turn.get("status") == status_filter
    ]
    if not visible_turns:
        st.info("Không có trace phù hợp với bộ lọc.")
    for turn in visible_turns:
        st.markdown(f"#### Lượt {turn.get('turn_index', '?')}")
        show_trace(turn)
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("turn"):
            show_trace(message["turn"])

user_text = st.chat_input("Hỏi về tin tức, web, bài viết hoặc mạng xã hội…")
if user_text:
    config = (
        provider_name,
        version,
        model_override,
        history_window,
        max_tool_rounds,
    )
    if st.session_state.get("session_config") not in (None, config):
        st.warning("Cấu hình đã thay đổi. Hãy bấm “Bắt đầu phiên mới” trước khi gửi.")
        st.stop()

    if "transcript" not in st.session_state:
        try:
            provider = make_provider(provider_name)
            selected_model = model_override or getattr(provider, "default_model", None)
            transcript, path = new_transcript(
                version,
                provider_name,
                selected_model,
                history_window,
                max_tool_rounds,
            )
            st.session_state.transcript = transcript
            st.session_state.transcript_path = str(path)
            st.session_state.session_config = config
        except Exception as exc:
            st.error(f"Không thể khởi tạo phiên: {type(exc).__name__}: {exc}")
            st.stop()

    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    history = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.messages[:-1]
        if item["role"] in {"user", "assistant"}
    ]
    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    declarations = load_tool_declarations(TOOLS_PATH)
    openai_tools = to_openai_tools(declarations)
    turn_record: dict[str, Any] = {
        "turn_index": len(st.session_state.turns) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        with st.spinner("Agent đang nghiên cứu và ghi trace…"):
            try:
                provider = make_provider(provider_name)
                result = run_model_tool_loop(
                    provider=provider,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *trim_history(history, history_window),
                        {"role": "user", "content": user_text},
                    ],
                    tools=openai_tools,
                    model=model_override or None,
                    max_tool_rounds=max_tool_rounds,
                )
                turn_record.update(result)
                assistant_text = result.get("assistant_text") or "Agent không trả về nội dung."
                st.markdown(assistant_text)
            except Exception as exc:
                assistant_text = "Không thể hoàn tất yêu cầu do lỗi provider."
                error_message = friendly_provider_error(exc, provider_name)
                turn_record.update(
                    {
                        "status": "provider_error",
                        "assistant_text": assistant_text,
                        "error": error_message,
                    }
                )
                st.error(error_message)

        turn_record["ended_at"] = now_iso()
        show_trace(turn_record)

    st.session_state.turns.append(turn_record)
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_text, "turn": turn_record}
    )
    transcript = st.session_state.transcript
    transcript["turns"].append(turn_record)
    write_transcript(Path(st.session_state.transcript_path), transcript)
    st.rerun()
