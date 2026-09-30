"""Snapshot safety checks used before generated data is committed."""

from __future__ import annotations

from typing import Any


def leaf_paths(value: Any, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        paths: set[str] = set()
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            paths.update(leaf_paths(child, child_prefix))
        return paths
    if isinstance(value, list):
        paths: set[str] = set()
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            paths.update(leaf_paths(child, child_prefix))
        return paths
    return {prefix or "$"}


def validate_snapshot(previous: Any, current: Any, max_removal_ratio: float = 0.10) -> None:
    """Reject a snapshot when too much previously observed structure disappears."""
    old_paths = leaf_paths(previous)
    new_paths = leaf_paths(current)

    if not old_paths:
        return

    removed = old_paths - new_paths
    ratio = len(removed) / len(old_paths)

    if ratio > max_removal_ratio:
        raise ValueError(
            f"snapshot safety guard triggered: {len(removed)}/{len(old_paths)} "
            f"leaf paths disappeared ({ratio:.1%})"
        )
