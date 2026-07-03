# agent/prompts/__init__.py
from pathlib import Path

_PROMPT_DIR = Path(__file__).parent

def load_prompt(name: str) -> str:
    """按角色名读取 prompt。name 对应 prompts/<name>.md。"""
    return (_PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")