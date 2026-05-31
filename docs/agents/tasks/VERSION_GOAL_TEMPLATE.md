# Version Goal — <version>

## Version

<version>

## Goal

Describe the small version goal in 2–5 lines.

## Why This Matters

Explain the user value and risk reduction.

## Scope

Allowed changes:
- 

Expected files or areas:
- 

## Non-goals

Do not:
- push
- tag
- change conversion behavior unless explicitly scoped
- change build-library behavior unless explicitly scoped
- change search/ranking/aliases/token fallback unless explicitly scoped
- add AI/OCR/embedding/vector/cloud features
- modify source files or Knowledge Packs

## Commit Policy

- final local commit only
- no checkpoint commits
- no tag
- no push

Commit message:

```text
Release <version>
```

## Validation

Required:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall office2md/gui
.venv/bin/python -m office2md.cli --help
```

Task-specific:
- 

## Smoke Tests

- 

## Final Report Path

```text
/Volumes/seagate 2t/offic2md/office2md-vault/50_Releases/<date> <version> Local Commit.md
```
