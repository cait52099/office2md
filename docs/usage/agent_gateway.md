# Agent Gateway

The agent gateway provides read-only commands for listing libraries, building evidence context, and reviewing update readiness.

## Typical Agent Workflow

1. **Discover libraries** — `kb-list` to find registered libraries
2. **Query evidence** — `kb-context` with query and library selection
3. **Cite evidence** — use fields: `library_id`, `library_name`, `library_path`, `source_file`, `locator`, `chunk_id`, `document_id`
4. **Check warnings** — if `kb-context` returns stale/unknown library warnings, run `kb-review`

office2md provides evidence and context only. It does not generate final AI answers.

## Evidence Fields

Every evidence item includes per-library provenance:

- `library_id` — Library identifier from catalog
- `library_name` — Human-readable library name
- `library_path` — Absolute path to library folder
- `source_file` — Original source file path
- `locator` — Chunk location within source
- `chunk_id` — Unique chunk identifier
- `document_id` — Parent document identifier
- `document_title` — Document title
- `document_kind` — Document type (e.g., technical_drawing_pdf)
- `evidence_type` — Evidence classification
- `confidence` — Confidence level
- `limitation` — Limitation note if any

## List Libraries

```powershell
python -m office2md.cli kb-list .\libraries.json --json
```

## Build Context

One library:

```powershell
python -m office2md.cli kb-context .\libraries.json "vacuum pump fault" --library cml125
```

Multiple libraries:

```powershell
python -m office2md.cli kb-context .\libraries.json "vacuum pump fault" --libraries cml125,interview
```

Write JSON:

```powershell
python -m office2md.cli kb-context .\libraries.json "vacuum pump fault" --library cml125 --export-json .\agent_context.json
```

The JSON schema is:

```text
office2md.agent_context.v1
```

The context packet includes request metadata, selected libraries, library status, evidence, supporting chunks, warnings, limitations, and next steps.

## Review a Library

```powershell
python -m office2md.cli kb-review .\libraries.json cml125
```

`kb-review` is read-only. It does not execute `update-library`, convert files, rebuild libraries, delete evidence, or modify source files.

## Agent Rules

Agents should:

- use `kb-list` to discover registered libraries;
- use `kb-context` for evidence-first context;
- cite all evidence provenance fields (`library_id`, `library_name`, `library_path`, `source_file`, `locator`, `chunk_id`, `document_id`);
- inspect warnings when a library is stale or unknown;
- run `kb-review` before relying on changed source folders.

office2md provides evidence and context only. It does not generate final AI answers.
