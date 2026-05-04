# 参考文献功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为项目新增独立的“添加参考文献”工作台，支持长文分析、真实中英文文献检索、知网 Browser MCP 辅助流程、句级 `[x]` 插入和文末参考文献导出。

**Architecture:** 保持现有 Flask + React + `python-docx` 结构，不复用降 AI 的 round/chunk 状态机，新增一条独立 `reference` 流水线。后端拆成文档解析、全文分析、英文检索、中文候选接收、句级绑定、导出、记录与服务编排模块；前端新增独立参考文献工作台页面和状态树。

**Tech Stack:** Python, Flask, React, TypeScript, `python-docx`, OpenAlex API, Crossref API, Browser MCP, pytest

**Current status (2026-05-02):** Task 1-10 implemented, backend test suite passed, frontend build passed. Task 11 Browser MCP guardrail contract and Task 12 manual acceptance / commit steps remain open.

---

## File Map

### Backend new files

- Create: `scripts/reference_models.py`
- Create: `scripts/reference_document.py`
- Create: `scripts/reference_analysis.py`
- Create: `scripts/reference_search_english.py`
- Create: `scripts/reference_search_cn.py`
- Create: `scripts/reference_binding.py`
- Create: `scripts/reference_export.py`
- Create: `scripts/reference_records.py`
- Create: `scripts/reference_service.py`
- Create: `scripts/reference_pipeline.py`

### Backend modified files

- Modify: `scripts/web_app.py`
- Modify: `scripts/app_service.py` or keep unchanged if reference service stays isolated
- Modify: `requirements.txt` only if a new dependency is strictly necessary

### Frontend new files

- Create: `app/src/components/reference/ReferenceWorkspace.tsx`
- Create: `app/src/components/reference/ReferenceAnalysisCard.tsx`
- Create: `app/src/components/reference/ReferenceEnglishCandidatesCard.tsx`
- Create: `app/src/components/reference/ReferenceCnBrowserCard.tsx`
- Create: `app/src/components/reference/ReferenceBindingPreviewCard.tsx`
- Create: `app/src/components/reference/ReferenceExportCard.tsx`
- Create: `app/src/hooks/useReferenceState.ts`
- Create: `app/src/lib/referenceWebService.ts`

### Frontend modified files

- Modify: `app/src/App.tsx`
- Modify: `app/src/lib/appService.ts`
- Modify: `app/src/lib/webService.ts`
- Modify: `app/src/types/app.ts`
- Modify: `app/src/styles/global.css`

### Tests

- Create: `tests/test_reference_document.py`
- Create: `tests/test_reference_analysis.py`
- Create: `tests/test_reference_search_english.py`
- Create: `tests/test_reference_binding.py`
- Create: `tests/test_reference_export.py`
- Create: `tests/test_reference_service.py`

## Task 1: Define reference-domain models and records

**Files:**
- Create: `scripts/reference_models.py`
- Create: `scripts/reference_records.py`
- Test: `tests/test_reference_service.py`

- [x] **Step 1: Write failing tests for record and model serialization**

Write tests covering:
- a `ReferenceJob` can be created with default stage statuses
- a `ReferenceCandidate` round-trips to dict
- history records persist Chinese and English candidate metadata separately

Suggested test targets:
- `test_reference_job_defaults`
- `test_reference_candidate_to_dict_roundtrip`
- `test_reference_records_persist_job_payload`

- [x] **Step 2: Run tests to verify failures**

Run:

```powershell
pytest tests/test_reference_service.py -v
```

Expected:
- import errors for missing `reference_models` / `reference_records`

- [x] **Step 3: Implement minimal domain models**

In `scripts/reference_models.py`, add dataclasses for:
- `ReferenceJob`
- `ReferenceDocument`
- `SentenceNode`
- `SentenceCandidate`
- `TopicCluster`
- `ReferenceCandidate`
- `CitationBinding`
- `ReferencePreview`
- `ReferenceApplyResult`

Requirements:
- each model exposes `to_dict()`
- list fields default safely
- status fields are strings, not enums, to match current Flask JSON style

- [x] **Step 4: Implement record persistence**

In `scripts/reference_records.py`, add helpers to:
- resolve a record file under `finish/reference/records.json`
- load empty defaults when file missing
- create/update job records
- persist:
  - source path
  - analysis summary
  - candidate lists
  - bindings
  - export paths

- [x] **Step 5: Re-run focused tests**

Run:

```powershell
pytest tests/test_reference_service.py -v
```

Expected:
- PASS for model/record tests

- [ ] **Step 6: Commit**

```powershell
git add scripts/reference_models.py scripts/reference_records.py tests/test_reference_service.py
git commit -m "feat: add reference job models and records"
```

## Task 2: Build document parsing and sentence extraction

**Files:**
- Create: `scripts/reference_document.py`
- Test: `tests/test_reference_document.py`
- Reference: `scripts/docx_pipeline.py`

- [x] **Step 1: Write failing tests for text/docx parsing**

Cover:
- parsing txt into paragraphs and sentence nodes
- parsing docx using existing `docx_pipeline` helpers
- detecting and excluding an existing “参考文献” section
- preserving stable sentence ids

- [x] **Step 2: Run tests to verify failures**

Run:

```powershell
pytest tests/test_reference_document.py -v
```

Expected:
- FAIL because parser module does not exist

- [x] **Step 3: Implement paragraph and sentence parsing**

In `scripts/reference_document.py`, add functions to:
- read `txt` and `docx`
- normalize line breaks
- split into paragraphs
- split paragraphs into sentence nodes using Chinese and English punctuation

Reuse:
- `scripts/docx_pipeline.py` for docx text loading

- [x] **Step 4: Implement section detection and reference-section exclusion**

Add logic to:
- identify headings heuristically
- detect “参考文献”, “References”, “参考文献列表” style markers
- stop正文 extraction once an existing reference section begins

- [x] **Step 5: Re-run tests**

Run:

```powershell
pytest tests/test_reference_document.py -v
```

Expected:
- PASS

- [ ] **Step 6: Commit**

```powershell
git add scripts/reference_document.py tests/test_reference_document.py
git commit -m "feat: add reference document parser"
```

## Task 3: Implement full-text analysis and recommendation engine

**Files:**
- Create: `scripts/reference_analysis.py`
- Test: `tests/test_reference_analysis.py`

- [x] **Step 1: Write failing tests for analysis output**

Cover:
- citation-need scoring ranks literature-review style sentences above neutral narration
- topic clustering reduces multiple similar sentences into fewer clusters
- recommendation engine suggests Chinese/English counts based on document size and cluster count

- [x] **Step 2: Run tests to verify failures**

Run:

```powershell
pytest tests/test_reference_analysis.py -v
```

Expected:
- FAIL for missing module/functions

- [x] **Step 3: Implement citation-need scoring**

In `scripts/reference_analysis.py`, add:
- section-aware score boosts
- phrase-based heuristics
- filters to skip already cited or low-value sentences

Output:
- a bounded list of `SentenceCandidate`

- [x] **Step 4: Implement topic clustering**

Add a lightweight clustering strategy that:
- groups by normalized keywords
- caps total clusters
- tracks `sentenceIds` per cluster

Keep first version simple and deterministic; do not add vector dependencies unless strictly needed.

- [x] **Step 5: Implement count recommendation**

Return:
- recommended total count
- recommended Chinese count
- recommended English count
- recommended citation positions count

- [x] **Step 6: Re-run tests**

Run:

```powershell
pytest tests/test_reference_analysis.py -v
```

Expected:
- PASS

- [ ] **Step 7: Commit**

```powershell
git add scripts/reference_analysis.py tests/test_reference_analysis.py
git commit -m "feat: add reference analysis heuristics"
```

## Task 4: Implement English reference search and verification

**Files:**
- Create: `scripts/reference_search_english.py`
- Test: `tests/test_reference_search_english.py`

- [x] **Step 1: Write failing tests with mocked API responses**

Cover:
- parsing OpenAlex results into normalized candidates
- merging Crossref verification fields
- removing duplicate candidates by DOI/title
- marking low-quality incomplete candidates as unverified

- [x] **Step 2: Run tests to verify failures**

Run:

```powershell
pytest tests/test_reference_search_english.py -v
```

Expected:
- FAIL because module missing

- [x] **Step 3: Implement OpenAlex query client**

In `scripts/reference_search_english.py`, add a small HTTP client abstraction that:
- accepts query terms from topic clusters
- fetches a small bounded candidate set
- normalizes title, author, year, source, DOI, URL

- [x] **Step 4: Implement Crossref verification**

Add a verifier that:
- enriches DOI/source metadata
- marks candidate `verified=True` when required fields present
- merges duplicates safely

- [x] **Step 5: Re-run tests**

Run:

```powershell
pytest tests/test_reference_search_english.py -v
```

Expected:
- PASS

- [ ] **Step 6: Commit**

```powershell
git add scripts/reference_search_english.py tests/test_reference_search_english.py
git commit -m "feat: add english reference search"
```

## Task 5: Implement Chinese candidate intake and CNKI session boundaries

**Files:**
- Create: `scripts/reference_search_cn.py`
- Test: `tests/test_reference_service.py`

- [x] **Step 1: Write failing tests for candidate submission and safety rules**

Cover:
- accepting user-confirmed Chinese candidates
- rejecting payloads missing title/authors/year/source
- enforcing per-cluster and per-job limits

- [x] **Step 2: Run tests to verify failures**

Run:

```powershell
pytest tests/test_reference_service.py -v
```

Expected:
- FAIL for missing Chinese candidate intake functions

- [x] **Step 3: Implement normalized Chinese candidate intake**

In `scripts/reference_search_cn.py`, add helpers to:
- validate candidate payloads
- normalize author lists and year
- persist `userConfirmed=True`

- [x] **Step 4: Encode CNKI safety boundaries in service-friendly helpers**

Add constants/helpers for:
- max Chinese topic clusters
- max candidates per cluster
- required user-confirmation gate
- stop conditions for captcha/risk page flags

- [x] **Step 5: Re-run tests**

Run:

```powershell
pytest tests/test_reference_service.py -v
```

Expected:
- PASS for Chinese candidate intake tests

- [ ] **Step 6: Commit**

```powershell
git add scripts/reference_search_cn.py tests/test_reference_service.py
git commit -m "feat: add chinese reference candidate intake"
```

## Task 6: Implement binding engine and numbering

**Files:**
- Create: `scripts/reference_binding.py`
- Test: `tests/test_reference_binding.py`

- [x] **Step 1: Write failing tests for sentence-level bindings**

Cover:
- a verified reference can bind to multiple related sentences
- dense consecutive bindings in one paragraph are reduced
- numbering follows first appearance order in正文
- only actually bound references appear in final ordered list

- [x] **Step 2: Run tests to verify failures**

Run:

```powershell
pytest tests/test_reference_binding.py -v
```

Expected:
- FAIL because binding module missing

- [x] **Step 3: Implement candidate-to-sentence matching**

In `scripts/reference_binding.py`, add logic that:
- scores topic-cluster overlap
- prefers verified and user-confirmed candidates
- supports one reference bound to multiple nearby sentences

- [x] **Step 4: Implement density control and numbering**

Add rules to:
- avoid over-citing adjacent sentences in the same paragraph
- keep one to three references per sentence maximum
- assign `[1]...[N]` based on first applied occurrence

- [x] **Step 5: Re-run tests**

Run:

```powershell
pytest tests/test_reference_binding.py -v
```

Expected:
- PASS

- [ ] **Step 6: Commit**

```powershell
git add scripts/reference_binding.py tests/test_reference_binding.py
git commit -m "feat: add reference binding engine"
```

## Task 7: Implement preview/export pipeline

**Files:**
- Create: `scripts/reference_export.py`
- Test: `tests/test_reference_export.py`
- Reference: `scripts/docx_pipeline.py`

- [x] **Step 1: Write failing tests for preview and export**

Cover:
- sentence-level insertion of `[x]` markers
- generation of final reference section containing only used references
- txt export output
- docx export output with reference section appended

- [x] **Step 2: Run tests to verify failures**

Run:

```powershell
pytest tests/test_reference_export.py -v
```

Expected:
- FAIL because export module missing

- [x] **Step 3: Implement text preview generation**

In `scripts/reference_export.py`, add:
- a function to rebuild paragraphs with sentence-level citation markers
- a function to render the final “参考文献” section

- [x] **Step 4: Implement txt/docx export**

Reuse:
- `scripts/docx_pipeline.py`

Behavior:
- text export writes combined正文 + references
- docx export writes paragraph blocks in final order

- [x] **Step 5: Re-run tests**

Run:

```powershell
pytest tests/test_reference_export.py -v
```

Expected:
- PASS

- [ ] **Step 6: Commit**

```powershell
git add scripts/reference_export.py tests/test_reference_export.py
git commit -m "feat: add reference preview and export"
```

## Task 8: Implement reference service and Flask API

**Files:**
- Create: `scripts/reference_service.py`
- Create: `scripts/reference_pipeline.py`
- Modify: `scripts/web_app.py`
- Test: `tests/test_reference_service.py`

- [x] **Step 1: Write failing service/API tests**

Cover:
- upload creates a reference job
- analyze returns counts/clusters/recommendations
- configure saves user target counts
- English search stores candidates
- Chinese candidate submission updates job
- binding generation produces preview
- export returns a managed file path

- [x] **Step 2: Run tests to verify failures**

Run:

```powershell
pytest tests/test_reference_service.py -v
```

Expected:
- FAIL because service and routes missing

- [x] **Step 3: Implement service orchestration**

In `scripts/reference_service.py`, wire together:
- parser
- analysis
- English search
- Chinese intake
- binding
- export
- record persistence

- [x] **Step 4: Implement pipeline status transitions**

In `scripts/reference_pipeline.py`, add job stage transitions:
- `uploaded`
- `analyzed`
- `configured`
- `english_searched`
- `cn_waiting_login`
- `cn_candidates_confirmed`
- `bindings_generated`
- `applied`
- `exported`

- [x] **Step 5: Add Flask routes**

In `scripts/web_app.py`, add:
- `POST /api/reference/upload-document`
- `GET /api/reference/status`
- `GET /api/reference/history`
- `POST /api/reference/analyze`
- `POST /api/reference/configure`
- `POST /api/reference/search-english`
- `POST /api/reference/start-cn-browser-session`
- `POST /api/reference/submit-cn-candidates`
- `POST /api/reference/generate-bindings`
- `GET /api/reference/preview`
- `POST /api/reference/apply`
- `GET /api/reference/export`

- [x] **Step 6: Re-run tests**

Run:

```powershell
pytest tests/test_reference_service.py -v
```

Expected:
- PASS

- [ ] **Step 7: Commit**

```powershell
git add scripts/reference_service.py scripts/reference_pipeline.py scripts/web_app.py tests/test_reference_service.py
git commit -m "feat: add reference service and api"
```

## Task 9: Extend TypeScript types and service layer

**Files:**
- Modify: `app/src/types/app.ts`
- Modify: `app/src/lib/appService.ts`
- Modify: `app/src/lib/webService.ts`
- Create: `app/src/lib/referenceWebService.ts`

- [x] **Step 1: Add failing type-level and integration assumptions**

Before editing, map required client-side types:
- `ReferenceJobStatus`
- `ReferenceAnalysisResult`
- `ReferenceCandidate`
- `ReferenceBindingPreview`
- `ReferenceExportResult`

- [x] **Step 2: Implement frontend types**

Add to `app/src/types/app.ts`:
- reference job/stage types
- analysis payload types
- English and Chinese candidate types
- binding preview and export result types

- [x] **Step 3: Implement service methods**

Expose calls for:
- upload reference document
- analyze
- configure counts
- search English
- start CN session
- submit CN candidates
- generate bindings
- preview
- export

- [x] **Step 4: Validate build**

Run:

```powershell
cd app
npm run build
```

Expected:
- successful TypeScript build

- [ ] **Step 5: Commit**

```powershell
git add app/src/types/app.ts app/src/lib/appService.ts app/src/lib/webService.ts app/src/lib/referenceWebService.ts
git commit -m "feat: add reference client service types"
```

## Task 10: Build reference workspace UI

**Files:**
- Create: `app/src/hooks/useReferenceState.ts`
- Create: `app/src/components/reference/ReferenceWorkspace.tsx`
- Create: `app/src/components/reference/ReferenceAnalysisCard.tsx`
- Create: `app/src/components/reference/ReferenceEnglishCandidatesCard.tsx`
- Create: `app/src/components/reference/ReferenceCnBrowserCard.tsx`
- Create: `app/src/components/reference/ReferenceBindingPreviewCard.tsx`
- Create: `app/src/components/reference/ReferenceExportCard.tsx`
- Modify: `app/src/App.tsx`
- Modify: `app/src/styles/global.css`

- [x] **Step 1: Build state hook**

Implement `useReferenceState.ts` to track:
- uploaded doc
- analysis payload
- chosen Chinese/English counts
- English candidates
- CN candidates
- binding preview
- export result
- busy/error/notice state

- [x] **Step 2: Add workspace shell**

Create `ReferenceWorkspace.tsx` that:
- uploads document
- triggers analyze
- configures counts
- controls stage progression

- [x] **Step 3: Add analysis and candidate cards**

Create cards to display:
- analysis summary
- recommended counts
- English verified candidates
- CNKI guidance and confirmed candidates

- [x] **Step 4: Add binding preview and export cards**

Show:
- highlighted sentence-level citation preview
- final reference list
- export actions

- [x] **Step 5: Integrate into main app**

Modify `app/src/App.tsx` to add a dedicated reference page/tab without disturbing the existing降AI workflow.

- [x] **Step 6: Validate build**

Run:

```powershell
cd app
npm run build
```

Expected:
- successful production build

- [ ] **Step 7: Commit**

```powershell
git add app/src/hooks/useReferenceState.ts app/src/components/reference app/src/App.tsx app/src/styles/global.css
git commit -m "feat: add reference workspace ui"
```

## Task 11: Integrate Browser MCP workflow contract

**Files:**
- Modify: `dev-doc/2026-05-02-reference-citation-dev-doc.md` if contract details change
- Modify: `app/src/components/reference/ReferenceCnBrowserCard.tsx`
- Modify: `scripts/reference_service.py`
- Test: `tests/test_reference_service.py`

- [ ] **Step 1: Define browser-session payload contract**

Document and implement fields for:
- current topic cluster
- recommended query terms
- per-cluster search limit flags
- stop reason values like captcha/risk/login-expired

- [ ] **Step 2: Add server-side guardrails**

Ensure `reference_service.py` enforces:
- max Chinese cluster count
- no candidate ingestion without explicit confirmation
- stop-state persistence when CN session reports captcha/risk/login expired

- [ ] **Step 3: Add UI guidance and stop-state handling**

In `ReferenceCnBrowserCard.tsx`, show:
- login reminder
- legal-use reminder
- stop/captcha messages
- per-cluster progress

- [ ] **Step 4: Re-run tests and build**

Run:

```powershell
pytest tests/test_reference_service.py -v
cd app
npm run build
```

Expected:
- tests pass
- frontend build succeeds

- [ ] **Step 5: Commit**

```powershell
git add scripts/reference_service.py app/src/components/reference/ReferenceCnBrowserCard.tsx tests/test_reference_service.py dev-doc/2026-05-02-reference-citation-dev-doc.md
git commit -m "feat: add cnki browser session guardrails"
```

## Task 12: Verification and end-to-end acceptance

**Files:**
- Test: `tests/test_reference_document.py`
- Test: `tests/test_reference_analysis.py`
- Test: `tests/test_reference_search_english.py`
- Test: `tests/test_reference_binding.py`
- Test: `tests/test_reference_export.py`
- Test: `tests/test_reference_service.py`

- [x] **Step 1: Run backend test suite**

Run:

```powershell
pytest tests/test_reference_document.py tests/test_reference_analysis.py tests/test_reference_search_english.py tests/test_reference_binding.py tests/test_reference_export.py tests/test_reference_service.py -v
```

Expected:
- all tests pass

- [x] **Step 2: Run frontend build**

Run:

```powershell
cd app
npm run build
```

Expected:
- build succeeds

- [ ] **Step 3: Manual acceptance pass**

Validate:
- upload docx/txt works
- analysis gives count recommendations
- English candidates show verified metadata
- CN browser stage clearly requires user login
- Chinese candidates cannot proceed without confirmation
- preview shows sentence-level `[x]`
- exported docx includes only actually used references

- [ ] **Step 4: Commit**

```powershell
git add .
git commit -m "test: verify reference citation workflow"
```

## Self-Review

### Spec coverage

This plan covers:
- independent reference workflow
- count recommendation for long papers
- sentence-level citation insertion
- English real-source search
- CNKI Browser MCP inclusion before launch
- user-login and candidate-confirmation boundaries
- preview/export and docx output
- safety and stop conditions

### Placeholder scan

No `TODO` / `TBD` placeholders are intentionally left in implementation steps. Each task names exact files, commands, and expected outputs.

### Type consistency

The plan consistently uses:
- `ReferenceJob`
- `SentenceCandidate`
- `TopicCluster`
- `ReferenceCandidate`
- `CitationBinding`

These names should be kept stable through implementation.

---

Plan complete and saved to [2026-05-02-reference-citation-implementation-plan.md](D:/code/new/baibaiAIGC/dev-doc/2026-05-02-reference-citation-implementation-plan.md).

Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
