from __future__ import annotations

from typing import Protocol

from foresight.schemas import SceneGraph


class PerceptionProvider(Protocol):
    def get_scene(self) -> SceneGraph:
        """Return the latest scene graph or raise a provider-specific exception."""
