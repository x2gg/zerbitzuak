"""HTML formatting helpers for NLP results."""
from __future__ import annotations
import html
import re
import handlers as h


# def format_lemmatized_result(result: dict) -> str:
#     if "emaitza" not in result:
#         return f"<span style='color:red'>{h.t('messages.formatting.invalid_response')}</span>"

#     return "<br>".join(
#         f"<span style='color:#2b5876'><b>{word}</b> → <span style='color:#4CAF50'>{lemma}</span></span>"
#         for word, lemma in result["emaitza"].items()
#     )

def format_lemmatized_result(result: dict) -> str:
    #if "emaitza" not in result or not isinstance(result["emaitza"], list):
    if "emaitza" not in result:
        return f"<span style='color:red'>{h.t('messages.formatting.invalid_response')}</span>"
    
    return "<br>".join(
        f"<span style='color:#2b5876'><b>{item['word']}</b> → <span style='color:#4CAF50'>{item['lemma']}</span></span>"
        for item in result["emaitza"]
    )


def format_nerc_result(result: dict, original_text: str | None = None) -> str:
    """Format NERC results.

    If ``original_text`` is provided, return the full text with inline-highlighted
    entities. Otherwise, fall back to a compact list of entities.
    """
    if "emaitza" not in result:
        return f"<span style='color:red'>{h.t('messages.formatting.invalid_response')}</span>"

    color_map = {
        "LOC": "#FFB74D",
        "PER": "#4fb054",
        "ORG": "#3ea2f4",
        "MISC": "#b566ff",
    }

    # Inline highlighting when we have the original text (text input case)
    if isinstance(original_text, str) and original_text.strip():
        return _format_nerc_inline(original_text, result["emaitza"], color_map)

    # Fallback: render as a list of entity chips
    formatted = []
    for entity, etype in result["emaitza"].items():
        color = color_map.get(str(etype).upper(), "#E0E0E0")
        formatted.append(
            f"<span style='background:{color}; padding:2px 5px; border-radius:3px; margin:2px; display:inline-block'>"
            f"{html.escape(entity.strip())} <small>({html.escape(str(etype).upper())})</small>"
            "</span>"
        )
    return " ".join(formatted)


def _format_nerc_inline(text: str, entities: dict, color_map: dict[str, str]) -> str:
    """Return HTML with inline highlights for entities within ``text``.

    - Avoid overlapping highlights by preferring longer matches first.
    - Match occurrences case-sensitively using the provided surface forms.
    - Safely escape non-entity text and entity labels.
    """
    # Collect all potential matches (start, end, type, surface)
    candidates: list[tuple[int, int, str, str]] = []
    for surface, etype in entities.items():
        if surface is None:
            continue
        surf = str(surface).strip()
        if not surf:
            continue
        try:
            for m in re.finditer(re.escape(surf), text):
                candidates.append((m.start(), m.end(), str(etype), surf))
        except re.error:
            # If pattern fails for some reason, skip this surface
            continue

    if not candidates:
        # No occurrences found -> just return escaped original text with preserved line breaks
        escaped_text = html.escape(text).replace('\n', '<br>')
        return f'<div style="white-space: pre-line">{escaped_text}</div>'

    # Prefer longer spans first to reduce overlaps, then earlier positions
    candidates.sort(key=lambda x: (-(x[1]-x[0]), x[0]))

    selected: list[tuple[int, int, str, str]] = []
    def overlaps(a, b):
        return not (a[1] <= b[0] or b[1] <= a[0])

    for cand in candidates:
        if any(overlaps(cand, sel) for sel in selected):
            continue
        selected.append(cand)

    # Emit in textual order
    selected.sort(key=lambda x: x[0])

    out_parts: list[str] = []
    cursor = 0
    for start, end, etype, surface in selected:
        # Text before the entity
        if cursor < start:
            # Replace newlines with <br> in the escaped text
            escaped_text = html.escape(text[cursor:start]).replace('\n', '<br>')
            out_parts.append(escaped_text)
        color = color_map.get(str(etype).upper(), "#E0E0E0")
        ent_html = (
            f"<span style='background:{color}; padding:2px 5px; border-radius:3px'>"
            f"{html.escape(text[start:end])}"
            f" <small>({html.escape(str(etype).upper())})</small>"
            f"</span>"
        )
        out_parts.append(ent_html)
        cursor = end

    # Tail after last entity
    if cursor < len(text):
        # Replace newlines with <br> in the escaped text
        escaped_text = html.escape(text[cursor:]).replace('\n', '<br>')
        out_parts.append(escaped_text)

    return f"<div>{''.join(out_parts)}</div>"


# def format_lemmatized_text(result: dict) -> str:
#     """Return plain-text lines in the format "word -> lemma" for lemmatizer results.

#     Expects the same structure used by format_lemmatized_result: {"emaitza": {word: lemma, ...}}.
#     """
#     if "emaitza" not in result or not isinstance(result["emaitza"], dict):
#         return ""
#     lines = []
#     for word, lemma in result["emaitza"].items():
#         lines.append(f"{word} -> {lemma}")
#     return "\n".join(lines)

def format_lemmatized_text(result: dict) -> str:
    """Return plain-text lines in the format "word -> lemma" for lemmatizer results.
    Expects the structure: {"emaitza": [{"word": ..., "lemma": ...}, ...]}.
    """
    if "emaitza" not in result or not isinstance(result["emaitza"], list):
        return ""
    
    lines = []
    for item in result["emaitza"]:
        if isinstance(item, dict) and "word" in item and "lemma" in item:
            lines.append(f"{item['word']} -> {item['lemma']}")
    
    return "\n".join(lines)


def format_nerc_bracketed_text(original_text: str, entities: dict) -> str:
    """Return the original text with bracketed entity tags like Bilbao[LOC].

    - Uses straightforward substring replacement similar to _format_nerc_inline, but emits plain text.
    - Avoid overlapping highlights by preferring longer matches first.
    - If no matches are found, returns the original text.
    """
    import re

    if not isinstance(original_text, str) or not original_text:
        return ""

    # Collect all matches: (start, end, type, surface)
    candidates: list[tuple[int, int, str, str]] = []
    for surface, etype in (entities or {}).items():
        if surface is None:
            continue
        surf = str(surface).strip()
        if not surf:
            continue
        try:
            for m in re.finditer(re.escape(surf), original_text):
                candidates.append((m.start(), m.end(), str(etype), surf))
        except re.error:
            continue

    if not candidates:
        return original_text

    # Prefer longer spans first, then earlier positions
    candidates.sort(key=lambda x: (-(x[1] - x[0]), x[0]))

    selected: list[tuple[int, int, str, str]] = []
    def overlaps(a, b):
        return not (a[1] <= b[0] or b[1] <= a[0])

    for cand in candidates:
        if any(overlaps(cand, sel) for sel in selected):
            continue
        selected.append(cand)

    selected.sort(key=lambda x: x[0])

    out_parts: list[str] = []
    cursor = 0
    for start, end, etype, _surf in selected:
        if cursor < start:
            out_parts.append(original_text[cursor:start])
        out_parts.append(f"{original_text[start:end]}[{str(etype).upper()}]")
        cursor = end
    if cursor < len(original_text):
        out_parts.append(original_text[cursor:])

    return "".join(out_parts)