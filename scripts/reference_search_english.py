from __future__ import annotations

import json
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from reference_models import ReferenceCandidate, TopicCluster


HttpGetter = Callable[[str], dict[str, Any]]


def _default_http_get(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=15) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def _normalize_doi(value: str) -> str:
    stripped = str(value or "").strip()
    if stripped.startswith("https://doi.org/"):
        return stripped.replace("https://doi.org/", "", 1)
    if stripped.startswith("http://doi.org/"):
        return stripped.replace("http://doi.org/", "", 1)
    return stripped


def _build_openalex_url(query: str, *, per_page: int) -> str:
    return f"https://api.openalex.org/works?search={quote(query)}&per-page={per_page}"


def _parse_openalex_candidate(item: dict[str, Any], cluster: TopicCluster) -> ReferenceCandidate:
    title = str(item.get("title", "") or "").strip()
    authorships = item.get("authorships") if isinstance(item.get("authorships"), list) else []
    authors = [
        str(authorship.get("author", {}).get("display_name", "")).strip()
        for authorship in authorships
        if isinstance(authorship, dict) and str(authorship.get("author", {}).get("display_name", "")).strip()
    ]
    primary_location = item.get("primary_location") if isinstance(item.get("primary_location"), dict) else {}
    source = primary_location.get("source") if isinstance(primary_location.get("source"), dict) else {}
    doi = _normalize_doi(str(item.get("doi", "") or ""))
    work_id = str(item.get("id", "") or "")

    return ReferenceCandidate(
        candidate_id=work_id or f"openalex:{title}",
        title=title,
        authors=authors,
        year=str(item.get("publication_year", "") or ""),
        source=str(source.get("display_name", "") or ""),
        language="en",
        doi=doi,
        url=str(primary_location.get("landing_page_url", "") or ""),
        journal=str(source.get("display_name", "") or ""),
        query=cluster.query,
        relevance_score=0.75 if doi else 0.55,
        matched_topic_ids=[cluster.topic_id],
        verified=bool(doi and title),
        metadata={"provider": "openalex", "openalexId": work_id},
    )


def search_openalex_candidates(
    clusters: list[TopicCluster],
    *,
    http_get: HttpGetter | None = None,
    per_query: int = 5,
) -> list[ReferenceCandidate]:
    getter = http_get or _default_http_get
    candidates: list[ReferenceCandidate] = []

    for cluster in clusters:
        query = cluster.query.strip() or cluster.label.strip()
        if not query:
            continue
        payload = getter(_build_openalex_url(query, per_page=per_query))
        results = payload.get("results") if isinstance(payload.get("results"), list) else []
        for item in results[:per_query]:
            if not isinstance(item, dict):
                continue
            candidates.append(_parse_openalex_candidate(item, cluster))
    return candidates


def _build_crossref_url(doi: str) -> str:
    return f"https://api.crossref.org/works/{quote(doi)}"


def _merge_crossref_message(candidate: ReferenceCandidate, message: dict[str, Any]) -> ReferenceCandidate:
    title_values = message.get("title") if isinstance(message.get("title"), list) else []
    container_titles = message.get("container-title") if isinstance(message.get("container-title"), list) else []
    author_values = message.get("author") if isinstance(message.get("author"), list) else []
    published_print = message.get("published-print") if isinstance(message.get("published-print"), dict) else {}
    date_parts = published_print.get("date-parts") if isinstance(published_print.get("date-parts"), list) else []

    if title_values and not candidate.title:
        candidate.title = str(title_values[0] or "")
    if container_titles and not candidate.source:
        candidate.source = str(container_titles[0] or "")
    if container_titles and not candidate.journal:
        candidate.journal = str(container_titles[0] or "")
    if date_parts and isinstance(date_parts[0], list) and date_parts[0]:
        candidate.year = candidate.year or str(date_parts[0][0])
    if author_values and not candidate.authors:
        candidate.authors = [
            " ".join(
                part for part in [
                    str(author.get("given", "") or "").strip(),
                    str(author.get("family", "") or "").strip(),
                ]
                if part
            )
            for author in author_values
            if isinstance(author, dict)
        ]
    if not candidate.url:
        candidate.url = str(message.get("URL", "") or "")
    candidate.doi = candidate.doi or _normalize_doi(str(message.get("DOI", "") or ""))

    required = bool(candidate.title and candidate.authors and candidate.year and candidate.source)
    candidate.verified = required
    candidate.metadata["verificationStatus"] = "verified" if required else "unverified"
    candidate.metadata["verifiedBy"] = "crossref"
    return candidate


def verify_candidates_with_crossref(
    candidates: list[ReferenceCandidate],
    *,
    http_get: HttpGetter | None = None,
) -> list[ReferenceCandidate]:
    getter = http_get or _default_http_get
    verified_candidates: list[ReferenceCandidate] = []

    for candidate in candidates:
        payload: dict[str, Any] = {}
        if candidate.doi:
            try:
                payload = getter(_build_crossref_url(candidate.doi))
            except HTTPError as exc:
                if exc.code not in {404, 410}:
                    raise
                candidate.verified = False
                candidate.metadata["verificationStatus"] = "crossref_not_found"
                candidate.metadata["verifiedBy"] = "crossref"
                verified_candidates.append(candidate)
                continue
        message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
        merged = _merge_crossref_message(candidate, message)
        if "verificationStatus" not in merged.metadata:
            merged.metadata["verificationStatus"] = "verified" if merged.verified else "unverified"
        verified_candidates.append(merged)
    return verified_candidates


def _candidate_key(candidate: ReferenceCandidate) -> str:
    if candidate.doi:
        return f"doi:{candidate.doi.lower()}"
    return f"title:{candidate.title.strip().lower()}"


def _candidate_quality(candidate: ReferenceCandidate) -> tuple[int, float]:
    completeness = sum(
        1 for value in [candidate.title, candidate.authors, candidate.year, candidate.source, candidate.doi] if value
    )
    return (1 if candidate.verified else 0, candidate.relevance_score + completeness)


def dedupe_reference_candidates(candidates: list[ReferenceCandidate]) -> list[ReferenceCandidate]:
    merged: dict[str, ReferenceCandidate] = {}

    for candidate in candidates:
        key = _candidate_key(candidate)
        current = merged.get(key)
        if current is None or _candidate_quality(candidate) > _candidate_quality(current):
            merged[key] = candidate

    return sorted(merged.values(), key=lambda item: (-item.verified, -item.relevance_score, item.title.lower()))
