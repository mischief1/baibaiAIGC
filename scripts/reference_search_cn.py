from __future__ import annotations

from collections import Counter
from typing import Any

from reference_models import ReferenceCandidate


def _normalize_candidate(payload: dict[str, Any]) -> ReferenceCandidate:
    candidate = ReferenceCandidate.from_dict(payload)
    candidate.language = "zh"
    candidate.user_confirmed = bool(payload.get("userConfirmed"))
    candidate.verified = candidate.user_confirmed
    candidate.metadata["provider"] = "cnki"
    candidate.metadata["confirmationSource"] = "user"
    return candidate


def _validate_candidate(candidate: ReferenceCandidate) -> None:
    missing_fields: list[str] = []
    if not candidate.title.strip():
        missing_fields.append("title")
    if not candidate.authors:
        missing_fields.append("authors")
    if not candidate.year.strip():
        missing_fields.append("year")
    if not candidate.source.strip():
        missing_fields.append("source")
    if not candidate.user_confirmed:
        missing_fields.append("userConfirmed")
    if not candidate.matched_topic_ids:
        missing_fields.append("matchedTopicIds")
    if missing_fields:
        raise ValueError(f"Chinese candidate missing required fields: {', '.join(missing_fields)}")


def submit_confirmed_cn_candidates(
    payloads: list[dict[str, Any]],
    *,
    max_per_cluster: int = 3,
    max_per_job: int = 20,
) -> list[ReferenceCandidate]:
    if len(payloads) > max_per_job:
        raise ValueError("Chinese candidate submission exceeds per-job limit.")

    accepted: list[ReferenceCandidate] = []
    cluster_counter: Counter[str] = Counter()

    for payload in payloads:
        candidate = _normalize_candidate(payload)
        _validate_candidate(candidate)

        for topic_id in candidate.matched_topic_ids:
            cluster_counter[topic_id] += 1
            if cluster_counter[topic_id] > max_per_cluster:
                raise ValueError("Chinese candidate submission exceeds per-cluster limit.")

        accepted.append(candidate)

    if len(accepted) > max_per_job:
        raise ValueError("Chinese candidate submission exceeds per-job limit.")
    return accepted
