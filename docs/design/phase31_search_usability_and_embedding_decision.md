# Phase 3.1b Search Usability and Embedding Decision

Checkpoint baseline: `v0.2.0-rc8`

Library benchmarked:

```text
C:\Users\hcai\OneDrive - The Estee Lauder Companies Inc\Desktop\Symex_CML125_library_full
```

## Scope

This review evaluates the current SQLite/FTS search path after Phase 3.1a:

- FTS search
- token fallback for zero-hit multi-term queries
- ranking adjustments for locators and evidence types
- facets
- optional related/context chunks

No vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or SQLite/FTS replacement is included.

## Benchmark Summary

| Query | Category | Mode | Hits | Locator | Usefulness | Note |
| --- | --- | ---: | ---: | ---: | --- | --- |
| SY909735 | exact | fts | 104 | yes | yes | Top result is HMI translation table; project documentation follows. |
| CML125 | exact | fts | 35 | yes | yes | Equipment list and project report are visible. |
| 1V2005 | exact | fts | 5 | yes | yes | HMI group and equipment list both appear. |
| 2M2001 | exact | fts | 2 | yes | yes | HMI row directly identifies Homogenizer 2M2001. |
| S7-300 | exact | fts | 62 | yes | yes | Datasheet/manual pages appear. |
| 1THLS200 | exact | none | 0 | no | no | No indexed coverage found for this identifier. |
| homogenizer cooling | phrase | token_fallback | 18 | yes | yes | HMI cooling water and homogenizer contexts appear. |
| alarm history | phrase | token_fallback | 17 | yes | yes | HMI alarm/fault groups and fault catalog appear. |
| temperature probe | phrase | fts | 20 | yes | yes | HMI probe calibration and temperature probe datasheets appear. |
| seal liquid | phrase | token_fallback | 19 | yes | yes | Sealing liquid pump and sealing liquid temperature contexts appear. |
| CIP sequence | phrase | token_fallback | 20 | yes | partial | CIP HMI rows appear, but "sequence" is weakly represented. |
| operation manual | phrase | fts | 7 | yes | yes | Manual pages appear. |
| maintenance plan | phrase | fts | 17 | yes | yes | Maintenance plan pages appear. |
| cooling circuit issue | conceptual | token_fallback | 30 | yes | partial | Cooling/wiring/manual issue contexts appear; query is broad. |
| agitator temperature problem | conceptual | token_fallback | 30 | yes | partial | Agitator and temperature contexts appear separately. |
| vacuum pump fault | conceptual | token_fallback | 26 | yes | partial | Pump contexts appear, but vacuum/fault combination is weak. |
| water flow control | conceptual | token_fallback | 29 | yes | yes | Water dosing, flow, and control mode contexts appear. |
| user password | conceptual | token_fallback | 14 | yes | partial | Password result appears, but not at rank 1. |
| calibration sensor | conceptual | token_fallback | 20 | yes | yes | Probe calibration and sensor contexts appear. |
| pump maintenance | conceptual | token_fallback | 20 | yes | partial | Pump and maintenance contexts appear, but ranking is broad. |
| Chinese: homogenizer | bilingual | fts | 7 | yes | yes | Chinese HMI rows for homogenizer are found. |
| Chinese: cooling water | bilingual | none | 0 | no | no | Missing bilingual alias/token behavior. |
| Chinese: alarm history | bilingual | none | 0 | no | no | Missing bilingual alias/token behavior. |
| Chinese: sealing liquid | bilingual | none | 0 | no | no | Missing bilingual alias/token behavior. |
| Chinese: operation manual | bilingual | none | 0 | no | no | Missing bilingual alias/token behavior. |

## Strong Queries

The current search path is strong for:

- exact project, equipment, and part identifiers
- HMI translation rows and groups
- manual/datasheet lookup
- operational phrases that include indexed English terms
- queries where token fallback can combine useful nearby results
- locator-based retrieval

Examples: `SY909735`, `1V2005`, `2M2001`, `homogenizer cooling`, `alarm history`, `temperature probe`, `seal liquid`, `maintenance plan`.

## Weak Queries

| Query | Cause | Notes |
| --- | --- | --- |
| 1THLS200 | no document coverage or token mismatch | Exact identifier is not found. This should be investigated as coverage/normalization before embeddings. |
| CIP sequence | phrase too narrow | CIP exists, but "sequence" is not strongly represented. Alias/query expansion may help. |
| cooling circuit issue | token fallback too broad | Results are useful but mixed; "issue" is too generic. |
| agitator temperature problem | token fallback too broad | Agitator and temperature results are not necessarily the same issue. |
| vacuum pump fault | missing alias/synonym | Needs better relation between vacuum pump and fault catalog/HMI alarm terms. |
| user password | ranking issue | A password result exists but is not first. |
| pump maintenance | token fallback too broad | Pump and maintenance terms appear separately. |
| Chinese cooling water/alarm history/sealing liquid/operation manual | bilingual mismatch | Requires bilingual aliases or better Chinese token handling. |

## Feature Checks

`--facets` works on representative queries and does not affect default search. It reports document kind, evidence type, source file, output dir, has-locator, and entity counts.

`--context 2` works on representative queries and returns nearby chunks from the same document/HMI group/page.

`--output-dir` works with known output directory names, for example `copy-of-sy909735-translation-chinese-ver-1`.

Repeatable `--entity` works with known entities such as `HMI`.

Default search still works without optional flags.

## Embedding Decision

Current FTS + token fallback + facets + context are good enough for practical CML125 knowledge retrieval today.

Optional offline embeddings are not justified as the next implementation step yet. The remaining weak cases mostly fall into categories that can be improved without embeddings:

- identifier normalization and coverage checks
- small bilingual alias mapping
- query expansion for common operational terms
- ranking improvements for generic terms such as `issue`, `problem`, and `fault`
- better grouping of token fallback hits by same document/page/HMI group
- stronger snippets for HMI translation groups

Semantic/vector retrieval may become useful later for:

- broad conceptual troubleshooting queries
- queries where the document uses different wording than the user
- natural-language symptom descriptions
- cross-document similarity discovery

But adding embeddings now would introduce dependency, model, storage, build-time, and validation risk before the cheaper FTS improvements are exhausted.

## Recommended Next Step

Do not implement embeddings yet.

Recommended Phase 3.1c should be further FTS polish:

1. Add a small local alias table for low-risk bilingual and technical terms.
2. Normalize common identifier variants and punctuation.
3. Improve token fallback ranking by boosting chunks that match multiple tokens in the same text, same page, or same HMI group.
4. Add optional query diagnostics so weak searches show matched tokens and missing tokens.
5. Investigate `1THLS200` coverage before treating it as a semantic search problem.

## Strict Out Of Scope

- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- SQLite/FTS replacement
- legacy `.doc` conversion
- answer generation/chatbot behavior
