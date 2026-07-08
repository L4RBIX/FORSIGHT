from __future__ import annotations

import re

from foresight.schemas import ParsedCommand, ReferenceSelector, SpatialGoal, TargetSelector

COLOR_PATTERNS: list[tuple[str, str]] = [
    (r"\bblue\b|\bsin(?:iy|yaya|yu)?\b|син\w*|көк|\bkok\b", "blue"),
    (r"\bred\b|красн\w*|қызыл|кызыл|\bqyzyl\b", "red"),
    (r"\bgreen\b|зелен\w*|жасыл|\bzhasyl\b", "green"),
    (r"\byellow\b|желт\w*|сары|\bsary\b", "yellow"),
    (r"\bwhite\b|бел\w*|ақ|ак", "white"),
]

OBJECT_PATTERNS: list[tuple[str, str]] = [
    (r"\bbox\b|\bcube\b|\bblock\b|короб\w*|куб\w*|блок\w*|қорап\w*|корап\w*", "box"),
    (r"\bmug\b|\bcup\b|круж\w*|чаш\w*|кесе\w*", "mug"),
    (r"\bbottle\b|бутыл\w*|бөтелке\w*|ботелке\w*", "bottle"),
    (r"\bperson\b|\bhuman\b|человек\w*|адам\w*", "person"),
    (r"\bhand\b|рук\w*|қол\w*|кол\w*", "hand"),
    (r"\bface\b|лиц\w*|бет\w*", "face"),
    (r"\bknife\b|нож\w*|пышақ\w*|пышак\w*", "knife"),
]

DIRECTION_PATTERNS: list[tuple[str, str]] = [
    (r"\bright\b|вправ\w*|оңға|онга", "right"),
    (r"\bleft\b|налев\w*|влев\w*|солға|солга", "left"),
    (r"\bforward\b|\bahead\b|впер[её]д\w*|алға|алга", "forward"),
    (r"\bback\b|\bbackward\b|назад\w*|артқа|артка", "back"),
]

DANGEROUS_WORDS = re.compile(r"\b(person|human|hand|face|knife)\b|человек|рук\w*|лиц\w*|нож\w*|адам|қол|кол|бет|пышақ|пышак", re.I)


def _find_first(patterns: list[tuple[str, str]], text: str) -> str | None:
    for pattern, value in patterns:
        if re.search(pattern, text, re.I):
            return value
    return None


def _find_object_in(text: str) -> str | None:
    return _find_first(OBJECT_PATTERNS, text)


def _find_color_in(text: str) -> str | None:
    return _find_first(COLOR_PATTERNS, text)


def _parse_distance_m(text: str) -> float:
    # Supports "10 cm", "0.1m", "10 сантиметров", "10 см", "10 метр".
    m = re.search(r"(?P<num>\d+(?:[\.,]\d+)?)\s*(?P<unit>cm|сm|см|centimeter(?:s)?|сантиметр\w*)\b", text, re.I)
    if m:
        return min(0.50, max(0.0, float(m.group("num").replace(",", ".")) / 100.0))
    m = re.search(r"(?P<num>\d+(?:[\.,]\d+)?)\s*(?P<unit>m|м|meter(?:s)?|метр\w*)\b", text, re.I)
    if m:
        return min(0.50, max(0.0, float(m.group("num").replace(",", "."))))
    return 0.10


def _split_relation(text: str) -> tuple[str, str | None, str | None]:
    relation_patterns = [
        ("away_from", r"\baway\s+from\b|\bfrom\b|от\s+|шеттен\s+алыс|алыс"),
        ("toward", r"\btoward(?:s)?\b|\bto\b|\bnear\b|\bк\s+|қарай|карай|ға\s+қарай|ге\s+қарай|га\s+карай|ге\s+карай"),
    ]
    for relation, pattern in relation_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            return text[: m.start()], text[m.end() :], relation
    return text, None, None


def parse_command(text: str) -> ParsedCommand:
    raw = text
    t = " ".join(text.strip().lower().split())
    if not t:
        return ParsedCommand(raw_command=raw, action="stop", confidence=0.0, needs_grounding=True)

    if re.search(r"\b(scan|look|detect)\b|скан\w*", t, re.I):
        return ParsedCommand(raw_command=raw, action="scan_scene", confidence=1.0, needs_grounding=False)

    if re.search(r"\b(stop|halt|cancel)\b|стоп\w*|останов\w*|тоқта\w*|токта\w*", t, re.I):
        return ParsedCommand(raw_command=raw, action="stop", confidence=1.0, needs_grounding=False)

    is_push = bool(re.search(r"\b(push|move|slide)\b|толк\w*|подвин\w*|сдвин\w*|итер\w*|жылжыт\w*", t, re.I))
    if not is_push:
        return ParsedCommand(raw_command=raw, action="stop", confidence=0.05, needs_grounding=True)

    confidence = 0.45 if DANGEROUS_WORDS.search(t) else 0.9
    distance_m = _parse_distance_m(t)
    direction = _find_first(DIRECTION_PATTERNS, t)
    before_rel, after_rel, relation = _split_relation(t)

    target_color = _find_color_in(before_rel) or _find_color_in(t)
    target_class = _find_object_in(before_rel) or _find_object_in(t)
    target = TargetSelector(class_name=target_class, color=target_color) if (target_class or target_color) else None

    reference: ReferenceSelector | None = None
    spatial_goal = SpatialGoal(type="none", distance_m=distance_m)

    if relation and after_rel is not None:
        if re.search(r"\bedge\b|кра[йя]\w*|шет\w*", after_rel, re.I):
            reference = ReferenceSelector(relation="edge")
            spatial_goal = SpatialGoal(type="away_from_reference" if relation == "away_from" else "toward_reference", distance_m=distance_m)
        else:
            ref_class = _find_object_in(after_rel)
            # Kazakh/Russian case-suffix forms can place the reference before the
            # relation marker, e.g. "қызыл кубты кружкаға қарай итер". If the
            # text after the marker is only the verb, use the last object mention
            # before the marker as the reference and the first mention as target.
            if not ref_class:
                mentions: list[tuple[int, str]] = []
                for pattern, value in OBJECT_PATTERNS:
                    for match in re.finditer(pattern, before_rel, re.I):
                        mentions.append((match.start(), value))
                mentions.sort(key=lambda item: item[0])
                if len(mentions) >= 2:
                    ref_class = mentions[-1][1]
            reference = ReferenceSelector(class_name=ref_class, relation=relation) if ref_class else ReferenceSelector(relation=relation)
            spatial_goal = SpatialGoal(type="away_from_reference" if relation == "away_from" else "toward_reference", distance_m=distance_m)
    elif direction:
        spatial_goal = SpatialGoal(type="direction", direction=direction, distance_m=distance_m)

    if target is None:
        confidence = min(confidence, 0.3)

    return ParsedCommand(
        raw_command=raw,
        action="push",
        target=target,
        reference=reference,
        spatial_goal=spatial_goal,
        confidence=confidence,
        needs_grounding=True,
    )
