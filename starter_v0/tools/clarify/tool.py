from __future__ import annotations

from typing import Any, List, Optional


def ask_user(
    question: str = "",
    response_type: str = "text",
    options: Optional[List[str]] = None,
) -> dict[str, Any]:
    """Tạm dừng và trả về câu hỏi làm rõ cho người dùng.
    
    response_type có thể là 'text', 'yes_no', hoặc lựa chọn từ 'options'.
    """
    return {
        "tool": "ask_user",
        "question": question,
        "response_type": response_type,
        "options": options or [],
        "awaiting_user": True,
    }