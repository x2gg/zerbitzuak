"""Lightweight i18n manager for Gradio frontend.

- Loads all JSON files from `locales/` (e.g., en.json, es.json, eus.json)
- Maintains a current language
- Provides t(key) for nested keys with dot-notation and optional format kwargs
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any
import os

# Locate locales directory relative to this file
_LOCALES_DIR = Path(__file__).parent / "locales"

# Load all translations on import
_TRANSLATIONS: Dict[str, Dict[str, Any]] = {}
for json_file in _LOCALES_DIR.glob("*.json"):
    try:
        lang = json_file.stem
        with open(json_file, "r", encoding="utf-8") as f:
            _TRANSLATIONS[lang] = json.load(f)
    except Exception:
        # Skip malformed files silently to avoid crashing UI
        pass

# Determine default language
_DEFAULT_LANG = os.environ.get("WEB_DEFAULT_LANG", "en")
if _DEFAULT_LANG not in _TRANSLATIONS:
    # Fallback to any available language or en
    _DEFAULT_LANG = "en" if "en" in _TRANSLATIONS else (next(iter(_TRANSLATIONS.keys()), "en"))

_CURRENT_LANGUAGE: str = _DEFAULT_LANG


def get_available_languages() -> list[str]:
    return sorted(_TRANSLATIONS.keys())


def get_current_language() -> str:
    return _CURRENT_LANGUAGE


def set_language(language: str) -> None:
    global _CURRENT_LANGUAGE
    if language in _TRANSLATIONS:
        _CURRENT_LANGUAGE = language


def _get_from(obj: Dict[str, Any], key: str) -> Any:
    cur: Any = obj
    for part in key.split('.'):
        if not isinstance(cur, dict):
            return key
        cur = cur.get(part)
        if cur is None:
            return key
    return cur


def t(key: str, **kwargs) -> str:
    lang_map = _TRANSLATIONS.get(_CURRENT_LANGUAGE) or {}
    value = _get_from(lang_map, key)
    if isinstance(value, str):
        try:
            return value.format(**kwargs) if kwargs else value
        except Exception:
            return value
    return key
