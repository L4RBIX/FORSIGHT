from pydantic import BaseModel


class ParsedAction(BaseModel):
    object_id: str
    action: str
    direction: list[float]
    force_n: float = 4.0
    duration_s: float = 0.5


def parse_action(text: str) -> ParsedAction:
    lowered = text.lower()
    direction = [1.0, 0.0, 0.0]
    if "left" in lowered:
        direction = [-1.0, 0.0, 0.0]
    elif "forward" in lowered:
        direction = [0.0, 1.0, 0.0]
    elif "back" in lowered:
        direction = [0.0, -1.0, 0.0]

    object_id = "box_2" if "box" in lowered else "mug_1"
    return ParsedAction(object_id=object_id, action="push", direction=direction)
