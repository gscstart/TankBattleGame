"""B6 国际化 (F15 i18n) - 简化实现.

- 单一全局语言 LANG, 默认 'zh'
- 加载 i18n/{lang}.json 字典
- t(key, **kwargs) 查表 + format 占位符 (如 {level})
- 不存在的 key fallback 返回 key 本身 (防崩溃)
- set_lang(lang) 切换语言

不做的 (按 karpathy Simplicity):
- 嵌套命名空间 (用扁平 key 如 'menu.title')
- 自动检测系统语言 (用固定默认 zh)
- 字符串拼接 (用 format 表达式)
"""
import os
import json
import locale

# 默认语言 (从系统 locale 检测, 失败 fallback zh)
def _detect_default_lang() -> str:
    try:
        # Python 3.11+: locale.getlocale() 不被 deprecate
        lang, _ = locale.getlocale()
        if lang and lang.lower().startswith("en"):
            return "en"
    except Exception:
        pass
    return "zh"


LANG: str = _detect_default_lang()
I18N_DIR: str = os.path.join(os.path.dirname(__file__), "..", "i18n")
_STRINGS: dict = {}  # 当前语言的字符串表


def _load_lang(lang: str):
    """加载 i18n/{lang}.json 到 _STRINGS."""
    global _STRINGS
    path = os.path.join(I18N_DIR, f"{lang}.json")
    if not os.path.exists(path):
        # fallback: 不清空, 保留上一语言
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            _STRINGS = json.load(f)
    except (json.JSONDecodeError, OSError):
        _STRINGS = {}


# 启动时加载默认语言
_load_lang(LANG)


def set_lang(lang: str) -> bool:
    """切换语言. 返回是否成功 (有对应 json 文件)."""
    global LANG
    path = os.path.join(I18N_DIR, f"{lang}.json")
    if not os.path.exists(path):
        return False
    LANG = lang
    _load_lang(lang)
    return True


def get_lang() -> str:
    """当前语言代码 (zh/en)."""
    return LANG


def t(key: str, **kwargs) -> str:
    """查表 + format 占位符.

    不存在 key: 返回 key 本身 (不抛异常, 防止 1 个缺 key 整个 UI 崩).
    """
    s = _STRINGS.get(key)
    if s is None:
        return key
    try:
        return s.format(**kwargs) if kwargs else s
    except (KeyError, IndexError):
        return s  # 占位符未填, 返回原模板 (不抛)


def reload():
    """重载当前语言 json (开发/测试用)."""
    _load_lang(LANG)


def available_langs() -> list:
    """列出 i18n/ 目录下所有 .json 语言代码 (不含扩展名)."""
    if not os.path.isdir(I18N_DIR):
        return []
    return [os.path.splitext(f)[0] for f in os.listdir(I18N_DIR)
            if f.endswith(".json")]
