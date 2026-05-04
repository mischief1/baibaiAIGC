from __future__ import annotations

from typing import Any


REFERENCE_STAGES = {
    "uploaded",
    "analyzed",
    "configured",
    "english_searched",
    "cn_waiting_login",
    "cn_candidates_confirmed",
    "bindings_generated",
    "applied",
    "exported",
}


def apply_reference_stage(job_payload: dict[str, Any], stage: str) -> dict[str, Any]:
    if stage not in REFERENCE_STAGES:
        raise ValueError(f"Unknown reference stage: {stage}")
    updated = dict(job_payload)
    updated["status"] = stage
    return updated
