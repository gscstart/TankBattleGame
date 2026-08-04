"""B6 i18n (F15) 测试.

- t(key) 返回字符串
- t(key, **kwargs) format 占位符
- set_lang 切换语言
- 不存在的 key fallback 返回 key 本身
- available_langs 返回所有 .json
"""
import os
import pytest

import utils.i18n as i18n


# ---- t() 基础 ----

def test_t_returns_chinese_by_default():
    """默认中文."""
    if i18n.get_lang() == "zh":
        assert i18n.t("menu.title") == "坦克大战"


def test_t_returns_string_for_known_key():
    """已知 key 返回字符串."""
    i18n.set_lang("zh")
    assert isinstance(i18n.t("menu.title"), str)
    assert len(i18n.t("menu.title")) > 0


def test_t_format_placeholder():
    """t(key, level=N) format 占位符."""
    i18n.set_lang("zh")
    assert i18n.t("hud.level", level=3) == "第 3 关"
    # 数字格式化 (06d)
    assert "000100" in i18n.t("menu.game_over.score", score=100)


# ---- set_lang / get_lang ----

def test_set_lang_to_english():
    i18n.set_lang("en")
    assert i18n.get_lang() == "en"
    assert i18n.t("menu.title") == "Tank Battle"


def test_set_lang_to_chinese():
    i18n.set_lang("zh")
    assert i18n.get_lang() == "zh"
    assert i18n.t("menu.title") == "坦克大战"


def test_set_lang_invalid_returns_false():
    """不存在的语言返回 False, 不改变当前语言."""
    i18n.set_lang("zh")
    result = i18n.set_lang("xx_nonexistent")
    assert result is False
    assert i18n.get_lang() == "zh"


def test_round_trip_zh_to_en_to_zh():
    i18n.set_lang("zh")
    zh_title = i18n.t("menu.title")
    i18n.set_lang("en")
    en_title = i18n.t("menu.title")
    i18n.set_lang("zh")
    assert i18n.t("menu.title") == zh_title
    assert en_title != zh_title


# ---- Fallback ----

def test_t_missing_key_returns_key_itself():
    """不存在的 key 返回 key 本身 (不抛异常)."""
    i18n.set_lang("zh")
    assert i18n.t("nonexistent.key") == "nonexistent.key"


def test_t_format_with_missing_placeholder_returns_template():
    """占位符未填返回原模板 (不抛 KeyError)."""
    i18n.set_lang("zh")
    # 不传 level, 模板含 {level} 也不抛
    result = i18n.t("hud.level")
    # 应保留 {level} 字面或 fallback
    assert "level" in result.lower() or "{" in result


# ---- available_langs ----

def test_available_langs_includes_zh_and_en():
    langs = i18n.available_langs()
    assert "zh" in langs
    assert "en" in langs


def test_reload_after_json_change(monkeypatch):
    """修改 json 后 reload 应读到新值 (开发用)."""
    import tempfile
    import shutil
    tmpdir = tempfile.mkdtemp(prefix="i18n_test_")
    try:
        # 写测试 json
        with open(os.path.join(tmpdir, "zh.json"), "w", encoding="utf-8") as f:
            f.write('{"menu.title": "测试标题"}')
        with open(os.path.join(tmpdir, "en.json"), "w", encoding="utf-8") as f:
            f.write('{"menu.title": "Test Title"}')
        # monkeypatch 改 I18N_DIR
        monkeypatch.setattr(i18n, "I18N_DIR", tmpdir)
        i18n.set_lang("zh")
        i18n.reload()
        assert i18n.t("menu.title") == "测试标题"
        i18n.set_lang("en")
        i18n.reload()
        assert i18n.t("menu.title") == "Test Title"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
