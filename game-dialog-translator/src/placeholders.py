from __future__ import annotations

import re
from dataclasses import dataclass

RESERVED = {
    "NI", "WO", "CH", "TA", "NTA", "ABC", "ME", "CITY", "ITEM", "PLACE",
    "PLACE1NAME", "PLACE2NAME", "SN1MING", "SN2MING", "SN3MING", "SN1CH", "SN2CH",
    "SN3CH", "AMING", "NMING", "NIMNG", "WOAMING",
}

PATTERNS = [
    r"\b[A-Z]{2,}\b",
    r"\b[A-Z]+\d+[A-Z0-9]*\b",
    r"\{[^{}]+\}",
    r"%[sd]|%\.\d+f|%\d*\.\d*f",
    r"<[^>]+>",
    r"\\[rnt]",
    r"\[(?:[A-Za-z_][^\]]*)\]",
]
COMPILED = [re.compile(p) for p in PATTERNS]


@dataclass
class PlaceholderBundle:
    protected_text: str
    token_to_original: dict[str, str]


def protect_placeholders(text: str) -> PlaceholderBundle:
    candidates: list[tuple[int, int, str]] = []
    for name in RESERVED:
        for m in re.finditer(rf"\b{re.escape(name)}\b", text):
            candidates.append((m.start(), m.end(), m.group(0)))
    for rgx in COMPILED:
        for m in rgx.finditer(text):
            candidates.append((m.start(), m.end(), m.group(0)))
    candidates = sorted(set(candidates), key=lambda x: (x[0], -(x[1]-x[0])))
    merged: list[tuple[int, int, str]] = []
    last_end = -1
    for s, e, v in candidates:
        if s >= last_end:
            merged.append((s, e, v))
            last_end = e

    result = []
    pos = 0
    token_map: dict[str, str] = {}
    counter = 1
    for s, e, v in merged:
        result.append(text[pos:s])
        token = f"__PH_{counter:04d}__"
        token_map[token] = v
        result.append(token)
        pos = e
        counter += 1
    result.append(text[pos:])
    return PlaceholderBundle("".join(result), token_map)


def restore_placeholders(text: str, token_map: dict[str, str]) -> str:
    out = text
    for token, original in token_map.items():
        out = out.replace(token, original)
    return out


def placeholders_preserved(original: str, translated: str) -> bool:
    bundle = protect_placeholders(original)
    originals = set(bundle.token_to_original.values())
    return all(p in translated for p in originals)
