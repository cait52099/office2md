# office2md v0.2.0-rc10 Release Notes

Release candidate focused on Phase 3.1c: conservative FTS query polish after the Phase 3.1b embedding decision gate.

v0.2.0-rc10 keeps SQLite/FTS as the search engine. It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or a SQLite/FTS replacement.

## Query Alias and Normalization

Added a small local query expansion layer for `search-library`.

The behavior is intentionally conservative:

- the original query is always tried first
- aliases and normalization run only after the original query returns 0 hits
- aliases are deterministic and local
- CLI output reports alias or normalization use
- exact lookups such as `SY909735`, `1V2005`, `2M2001`, and `S7-300` remain unchanged when the original query hits

Covered aliases include:

- `冷却水` -> `cooling water`
- `报警历史` -> `alarm history` / `alarm`
- `密封液` -> `sealing liquid`
- `操作手册` -> `operation manual`
- `均质器` -> `homogenizer`
- `CIP sequence` -> `CIP`
- `cooling circuit` -> `cooling water`
- `user password` -> `password`

Identifier-like no-hit queries can use a controlled prefix fallback. This improves `1THLS200` by finding related indexed `1THLS...` HMI temperature context without changing exact part-number searches that already hit.

## Validation

```bash
python -m pytest
63 passed

python -m ruff check .
All checks passed!
```

Smoke checks against the existing CML125 full-directory library passed for:

- `SY909735`
- `1V2005`
- `2M2001`
- `S7-300`
- `1THLS200`
- `冷却水`
- `报警历史`
- `密封液`
- `操作手册`
- `CIP sequence`
- `cooling circuit issue`
- `user password`
- `homogenizer cooling`
- `alarm history`

Known remaining partial queries:

- `vacuum pump fault`: still broad; library results mostly surface pump/CIP contexts rather than a clean vacuum-pump fault record.
- `agitator temperature problem`: still partial; agitator and temperature are found but are not strongly tied as one issue.

## Explicit Non-Goals

v0.2.0-rc10 does not add:

- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud or network dependency
- Office image export
- SQLite/FTS replacement
- aggressive synonym expansion
