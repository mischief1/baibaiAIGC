from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reference_models import CitationBinding, ReferenceCandidate, ReferenceJob


def resolve_reference_records_path(root_dir: Path | None = None) -> Path:
    workspace_root = Path(root_dir) if root_dir is not None else Path(__file__).resolve().parents[1]
    return workspace_root / "finish" / "reference" / "records.json"


def _ensure_reference_record_dir(root_dir: Path | None = None) -> Path:
    path = resolve_reference_records_path(root_dir=root_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_reference_records(root_dir: Path | None = None) -> dict[str, Any]:
    path = resolve_reference_records_path(root_dir=root_dir)
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def save_reference_records(records: dict[str, Any], root_dir: Path | None = None) -> Path:
    path = _ensure_reference_record_dir(root_dir=root_dir)
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return path


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_job_entry(records: dict[str, Any], job_id: str) -> dict[str, Any]:
    entry = records.get(job_id)
    if isinstance(entry, dict):
        return entry
    new_entry: dict[str, Any] = {
        "jobId": job_id,
        "sourcePath": "",
        "status": "created",
        "analysisStatus": "pending",
        "englishSearchStatus": "pending",
        "chineseSearchStatus": "pending",
        "bindingStatus": "pending",
        "exportStatus": "pending",
        "analysisSummary": {},
        "englishCandidates": [],
        "chineseCandidates": [],
        "bindings": [],
        "exportPaths": {},
        "metadata": {},
    }
    records[job_id] = new_entry
    return new_entry


def create_or_update_job_record(job: ReferenceJob, root_dir: Path | None = None) -> dict[str, Any]:
    records = load_reference_records(root_dir=root_dir)
    payload = job.to_dict()
    job_id = str(payload["jobId"])
    entry = _ensure_job_entry(records, job_id)
    created_at = str(entry.get("createdAt", "") or payload.get("createdAt", "") or _iso_now())
    entry.update(payload)
    entry["createdAt"] = created_at
    entry["updatedAt"] = _iso_now()
    records[job_id] = entry
    save_reference_records(records, root_dir=root_dir)
    return entry


def update_job_candidates(
    job_id: str,
    *,
    english_candidates: list[ReferenceCandidate] | None = None,
    chinese_candidates: list[ReferenceCandidate] | None = None,
    root_dir: Path | None = None,
) -> dict[str, Any]:
    records = load_reference_records(root_dir=root_dir)
    entry = _ensure_job_entry(records, job_id)
    if english_candidates is not None:
        entry["englishCandidates"] = [candidate.to_dict() for candidate in english_candidates]
    if chinese_candidates is not None:
        entry["chineseCandidates"] = [candidate.to_dict() for candidate in chinese_candidates]
    entry["updatedAt"] = _iso_now()
    records[job_id] = entry
    save_reference_records(records, root_dir=root_dir)
    return entry


def update_job_analysis_summary(
    job_id: str,
    analysis_summary: dict[str, Any],
    *,
    root_dir: Path | None = None,
) -> dict[str, Any]:
    records = load_reference_records(root_dir=root_dir)
    entry = _ensure_job_entry(records, job_id)
    entry["analysisSummary"] = dict(analysis_summary or {})
    entry["updatedAt"] = _iso_now()
    records[job_id] = entry
    save_reference_records(records, root_dir=root_dir)
    return entry


def update_job_bindings(
    job_id: str,
    bindings: list[CitationBinding],
    *,
    root_dir: Path | None = None,
) -> dict[str, Any]:
    records = load_reference_records(root_dir=root_dir)
    entry = _ensure_job_entry(records, job_id)
    entry["bindings"] = [binding.to_dict() for binding in bindings]
    entry["updatedAt"] = _iso_now()
    records[job_id] = entry
    save_reference_records(records, root_dir=root_dir)
    return entry


def update_job_export_paths(
    job_id: str,
    export_paths: dict[str, Any],
    *,
    root_dir: Path | None = None,
) -> dict[str, Any]:
    records = load_reference_records(root_dir=root_dir)
    entry = _ensure_job_entry(records, job_id)
    entry["exportPaths"] = dict(export_paths or {})
    entry["updatedAt"] = _iso_now()
    records[job_id] = entry
    save_reference_records(records, root_dir=root_dir)
    return entry
