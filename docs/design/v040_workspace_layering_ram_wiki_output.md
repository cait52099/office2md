# v0.4.0 Workspace Layering: RAM / Wiki / Output / Version Control

Status: design only.

## Purpose

office2md already converts local documents into structured Knowledge Packs and searchable libraries. As the product grows from a conversion utility into a local document knowledge workspace, it needs clearer boundaries between source facts, human understanding, generated products, and traceability metadata.

A layered workspace architecture is needed to:

- protect raw source facts from accidental rewriting;
- allow humans to maintain editable understanding without mutating evidence;
- generate reports and exports that remain traceable to their inputs;
- support future AI assistance safely, with AI able to help interpret facts without being allowed to silently rewrite facts.

The main product rule is:

> RAM preserves what the sources said. Wiki records what people understand. Outputs present what the workspace produced. Version control explains how each layer changed.

## Layer Definitions

### 1. RAM / Raw Material Layer

The RAM layer contains source-grounded material:

- original source files;
- conversion Knowledge Packs;
- `library.db`;
- `source_map.json`;
- `chunks.jsonl`;
- `manifest.json`;
- rendered or extracted assets.

Rules:

- AI access is read-only.
- Source checksums are preserved.
- Source locators are preserved.
- Content is appended, regenerated, or rebuilt only through controlled conversion/library workflows.
- Manual editing is not expected.
- The RAM layer remains the evidence base when higher layers disagree.

The RAM layer is not a place for interpretation, cleanup by hand, or AI-authored replacement text. If a source is wrong, the correction belongs in Wiki with a link back to the source evidence.

### 2. Wiki / Understanding Layer

The Wiki layer contains editable workspace understanding:

- human-readable notes;
- concept notes;
- corrections;
- glossary entries;
- AI-drafted suggestions awaiting review.

Rules:

- Humans can edit, refine, and correct Wiki notes.
- AI may draft suggestions for review.
- AI suggestions should not be auto-promoted into accepted Wiki content without human review.
- Wiki notes should link back to RAM evidence such as `chunk_id`, locator, and source checksum.
- Human corrections should be additive and explicit rather than silently changing RAM facts.

The Wiki layer answers questions such as:

- What does this project mean?
- Which concepts matter?
- Which source claims have been corrected or clarified?
- Which interpretations have been reviewed by a human?

### 3. Output Layer

The Output layer contains generated products:

- reports;
- Obsidian exports;
- future HTML, DOCX, and PDF exports;
- evidence packages.

Rules:

- Outputs are generated products, not source-of-truth inputs.
- Outputs should include source traceability.
- Output manifests should record:
  - `library_version`;
  - `wiki_version`;
  - source chunks used;
  - `generated_at`;
  - tool version.
- Outputs may be regenerated when RAM, Wiki, or templates change.
- Outputs should not be treated as a substitute for the RAM or Wiki layers.

### 4. Version / Traceability Layer

The Version / Traceability layer records workspace state and lineage:

- `source_manifest.json`;
- `workspace_manifest.json`;
- `library_versions.json`;
- `wiki_versions.json`;
- `output_manifest.json`.

Rules:

- Track source file checksum and modified time.
- Track office2md version.
- Track conversion time, library build time, export time, and output generation time.
- Enable comparison and rollback across workspace states.
- Do not rely only on Git for large generated data, binary assets, or generated library artifacts.

Git may still be useful for code, templates, and selected Wiki content, but office2md should maintain explicit workspace-native manifests for data lineage.

## Proposed Workspace Structure

```text
project.office2md/
  source_manifest.json
  conversion/
  library/
  wiki/
    Concepts/
    Notes/
    Corrections/
    _suggestions/
  outputs/
    obsidian/
    reports/
    html/
    _manifests/
  logs/
  versions/
```

Suggested responsibilities:

- `conversion/`: per-document Knowledge Packs and RAM artifacts.
- `library/`: current built library, search index, graph exports, and library metadata.
- `wiki/`: editable understanding, reviewed notes, and pending suggestions.
- `outputs/`: generated deliverables and their manifests.
- `logs/`: operational logs from conversion/build/export workflows.
- `versions/`: snapshots, version indexes, comparisons, and rollback metadata.

## AI Permission Model

Future AI features should follow explicit permissions:

- AI can read RAM.
- AI can draft Wiki suggestions.
- AI can generate Outputs.
- AI cannot directly modify RAM.
- AI should not silently overwrite human Wiki edits.
- AI-generated outputs must include provenance.

Operationally:

- AI writes to `_suggestions/` before any accepted Wiki location.
- Promotion from suggestion to Wiki should be reviewable and attributable.
- If AI uses Wiki content and RAM evidence together, the output should preserve both levels of provenance.
- AI should never be allowed to “fix” a source by replacing its RAM representation.

## Obsidian Relationship

Obsidian can participate in two different ways:

### Obsidian Export as Output Layer

The current v0.3.2 export is an Output-layer product:

- generated from the built library;
- safe to regenerate;
- useful for browsing;
- not the canonical editable understanding layer.

This mode matches the current `export-obsidian` MVP.

### Obsidian-Compatible Wiki as Wiki Layer

A future Obsidian-compatible Wiki layer would be different:

- notes are part of the editable workspace state;
- humans review and maintain them;
- they may contain corrections, glossary entries, or reviewed concepts;
- they link back to RAM evidence and participate in Wiki versioning.

The difference is simple:

- Output Obsidian vault: generated view.
- Wiki Obsidian notes: maintained understanding.

Keeping those modes separate avoids confusing “exported snapshot” with “reviewed knowledge.”

## Traceability Model

The target traceability chain is:

```text
Output paragraph
  -> Wiki note / concept
  -> chunk_id
  -> source_map locator
  -> source file checksum
```

This chain should let a reviewer answer:

1. Which output text am I reading?
2. Which accepted understanding or concept supported it?
3. Which exact source chunk supports that understanding?
4. Where is that chunk located in the original source?
5. Which source file version was used?

When an output is generated directly from RAM without Wiki mediation, the chain may shorten to:

```text
Output paragraph
  -> chunk_id
  -> source_map locator
  -> source file checksum
```

## Versioning Model

### Source Version

Represents the source corpus state:

- source file path;
- checksum;
- modified time;
- added/removed/changed status.

### Conversion / Library Version

Represents the processed evidence state:

- office2md version;
- conversion configuration;
- library build time;
- source manifest version used;
- counts and warnings.

### Wiki Version

Represents the editable understanding state:

- accepted notes;
- corrections;
- glossary;
- reviewed suggestions;
- human or tool attribution;
- change summary.

### Output Version

Represents each generated deliverable state:

- output type;
- generating tool/version;
- library version;
- wiki version;
- chunk references used;
- generated time;
- output checksum.

These four versions should be independently visible so that a changed report can be explained as a source update, a library rebuild, a Wiki correction, a template change, or a different output generation run.

## Future CLI / GUI Ideas

Possible future CLI commands:

```text
office2md workspace init
office2md workspace scan
office2md wiki generate-suggestions
office2md output build
office2md trace OUTPUT_FILE
```

Possible GUI areas:

- Create Workspace;
- RAM status;
- Wiki review;
- Output exports;
- Traceability panel.

These ideas are directional only. They do not replace the current CLI or GUI workflows in this design phase.

## Non-Goals For This v0.4.0 Design

- No default AI writeback.
- No cloud dependency.
- No automatic deletion.
- No replacement of the current library workflow.
- No mandatory Git requirement.
- No Marker integration in this document.

## Migration From Current v0.3.x

The current v0.3.x workspace pattern is already close to the proposed future model:

```text
workspace/
  conversion/
  library/
  logs/
```

It can evolve incrementally into:

```text
workspace/
  conversion/
  library/
  wiki/
  outputs/
  logs/
  versions/
```

Migration principles:

- Keep `conversion/`, `library/`, and `logs/` intact as the initial RAM/runtime foundation.
- Add `wiki/` without changing conversion outputs.
- Add `outputs/` for generated deliverables such as Obsidian exports and reports.
- Add `versions/` plus top-level manifests to record workspace-native lineage.
- Preserve compatibility with existing `build-library`, search, export, and GUI workflows while the new layers are introduced.

This lets office2md grow toward a layered workspace without forcing current users to abandon the stable v0.3.x operating model.
