# office2md

> **Convert Office, PDF, and text documents into structured, knowledge-base-ready Markdown**

[![PyPI version](https://img.shields.io/pypi/v/office2md.svg)](https://pypi.org/project/office2md/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

**office2md** transforms Office documents (Word, Excel, PowerPoint), PDFs, and text files into clean Markdown with structured metadata, entities, and searchable knowledge libraries — entirely local, no AI required by default.

## Key Features

- **Multi-format conversion** — PDF, DOCX, XLSX, PPTX, HTML, TXT, CSV, JSON, MD
- **Rich Knowledge Pack output** — chunks, entities, source maps, provenance metadata
- **Knowledge Library Builder** — SQLite FTS5 search, document graph, interop exports (LlamaIndex, Haystack, txtai, GraphRAG)
- **Visual PDF rendering** — page snapshots for technical drawings and diagrams
- **HMI/PLC translation support** — structured extraction for Chinese/English field device tables
- **Optional AI enrichment** — opt-in framework for CLI-based AI adapters
- **Fully local** — no external APIs, no cloud dependencies, no vector DB required

## Quick Start

### Installation

```bash
pip install office2md
```

Or for development with all features:

```bash
git clone https://github.com/cait52099/office2md.git
cd office2md
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Initialize a local workspace foundation
office2md workspace-init ./project.office2md

# Register source files and checksums without converting them
office2md workspace-scan ./project.office2md ./input

# Register a built library as a workspace version
office2md workspace-register-library ./project.office2md ./library

# Register a generated output as a workspace version
office2md workspace-register-output ./project.office2md ./obsidian-vault

# Review read-only traceability status
office2md workspace-status ./project.office2md

# Convert a folder of documents
office2md convert ./input ./output --recursive

# Convert a single file
office2md convert-file document.pdf ./output

# Build a searchable knowledge library
office2md build-library ./output ./library

# Search the library
office2md search-library ./library/library.db "PLC wiring diagram"
```

### Output Profiles

| Profile | Image Links | Use Case |
|---------|-------------|----------|
| `kb` (default) | `![Page 1](assets/page_001.png)` | Knowledge bases, RAG |
| `rag` | `![Page 1](assets/page_001.png)` | RAG pipelines |
| `memory` | `![Page 1](assets/page_001.png)` | Memory systems |
| `obsidian` | `![[assets/page_001.png]]` | Obsidian vault |

## Supported Formats

| Format | Extensions | Engine |
|--------|------------|--------|
| PDF | `.pdf` | Docling → MarkItDown fallback |
| Modern Office | `.docx`, `.xlsx`, `.pptx` | MarkItDown |
| Legacy Office | `.doc`, `.xls`, `.ppt` | LibreOffice → MarkItDown |
| Web | `.html`, `.htm` | MarkItDown |
| Text | `.txt`, `.csv`, `.json`, `.md` | Direct copy |

## Project Architecture

```
Input Files → office2md convert → Knowledge Pack per document
                                       ↓
                    office2md build-library → Knowledge Library
                                               ↓
                    ┌─────────────────────────┼─────────────────────────┐
                    ↓                         ↓                         ↓
              library.db              library_graph.json         _library.md
           (SQLite FTS5)            (document relationships)   (Markdown portal)
                    ↓                         ↓                         ↓
        search-library CLI          graph analysis              human browsing
```

## Knowledge Pack Output

Each converted document produces:

```
output/
  source-file-slug/
    document.md          # Markdown with YAML frontmatter
    document.raw.md      # Raw conversion output
    document.json        # Full document metadata
    chunks.jsonl         # Structured content chunks
    manifest.json        # Conversion record & warnings
    knowledge.json       # Title, summary, tags, document kind
    entities.json        # Extracted entities (project, equipment, etc.)
    source_map.json      # Chunk → source location mapping
    assets/              # Rendered PDF pages (if enabled)
```

## Knowledge Library Outputs

`build-library` creates a complete knowledge library:

- `library.db` — SQLite database with FTS5 full-text search
- `library_manifest.json` — Build statistics and configuration
- `library_index.json` — All documents and chunks indexed
- `library_graph.json` — Document relationship graph
- `_library.md` — Human-readable library overview
- `_documents.md`, `_entities.md`, `_topics.md` — Structured indexes
- `exports/` — Interop exports (LlamaIndex, Haystack, txtai, GraphRAG)

## Advanced Usage

### PDF Visual Rendering

```bash
# Render first 5 pages of technical drawings
office2md convert-file diagram.pdf ./output \
  --render-pdf-pages --max-render-pages 5
```

### Search with Filters

```bash
# Search with document kind filter
office2md search-library ./library/library.db "CIP" \
  --kind technical_drawing_pdf --limit 20

# Search with evidence type
office2md search-library ./library/library.db "pump fault" \
  --evidence drawing_index --limit 10

# Faceted search
office2md search-library ./library/library.db "valve" --facets --limit 20
```

### Obsidian Export

Export a built Knowledge Library to an Obsidian-friendly local vault folder:

```bash
office2md export-obsidian ./library ./obsidian-vault
```

The export creates `00_Index.md`, `00_Library_Report.md`, `Documents/`, `Concepts/`, and `_office2md/export_manifest.json`. It uses library-native concepts from the existing indexed content and does not require Obsidian to be installed. Use `--dry-run` to preview counts and `--overwrite` to replace a non-empty output folder.

### Workspace Foundation

Create a conservative local workspace skeleton for future RAM / Wiki / Output / Version workflows:

```bash
office2md workspace-init ./project.office2md
```

The command creates workspace folders plus manifest/version files without converting documents or requiring Git. Use `--dry-run` to preview changes. Existing source/version manifests are preserved unless `--overwrite-manifests` is explicitly provided.

`workspace-scan` then registers supported source files and SHA-256 checksums in `source_manifest.json`. It is a traceability step only: it does not convert files or build a library.

`workspace-register-library` appends a built library version to `versions/library_versions.json`, linking library metrics and file hashes back to the current `source_manifest.json`. It does not build or modify the library.

`workspace-register-output` appends a generated output version to `versions/output_versions.json`, linking file or folder hashes back to a library version and its source manifest. It does not generate or modify exports.

`workspace-status` shows a read-only source/library/output traceability summary, including the latest `source_manifest_hash -> library_version_id -> output_version_id` chain. Use `--json` for machine-readable output, `--show-history` for recent versions, and `--strict` when missing manifests or broken linkage should fail the command.

The optional Streamlit GUI also includes a read-only Workspace Status page for the same status summary and JSON download. Its Workspace Root Path must be a folder created by `workspace-init`, separate from the Library path used by Library/Search/Knowledge Graph. It does not scan, convert, build, export, or modify workspace files.

### OfficeCLI Benchmark

`officecli-benchmark` is an optional, read-only benchmark command for evaluating OfficeCLI against DOCX/XLSX/PPTX files. It verifies source checksums before and after OfficeCLI commands and writes artifacts only to the requested output folder. It does not change the default conversion pipeline or require OfficeCLI as a dependency.

### Agent-Ready CLI JSON

office2md is preparing stable, read-only CLI JSON contracts for future AI-agent workflows. The planned interface is evidence-first: search a built Knowledge Library, open selected chunks by `chunk_id`, and cite `source_file`, `locator`, and `document_id` in downstream answers or report drafts. See `docs/usage/agent_ready_cli.md` and `docs/design/v044_agent_ready_json_contract.md`.

### Incremental Status Foundation

`library-status` and `scan-changes` provide a read-only foundation for checking whether a built Knowledge Library may be stale relative to source files:

```bash
office2md library-status ./library
office2md scan-changes ./source ./library --dry-run
office2md scan-changes ./source ./library --export-json ./change_plan.json
```

These commands do not run conversion, rebuild the library, update SQLite rows, delete evidence, or watch folders in the background. Agents must not assume new raw files are searchable until an explicit scan/update workflow has been run. See `docs/usage/incremental_update.md` and `docs/design/v045_incremental_update_workflow.md`.

`source-registry` can explicitly save or export `source_registry.json`, and `library-status --write-state` can write a `library_state.json` snapshot. These files are status artifacts only; they do not update the library.

`update-library` is the explicit update path. Preview first, then run it with the source folder, conversion output folder, and library folder:

```bash
office2md update-library ./source ./conversion-output ./library --dry-run
office2md update-library ./source ./conversion-output ./library
```

It converts only new/modified files, reuses unchanged valid Knowledge Packs, records deleted/missing and stale sources without deleting evidence, rebuilds the library through the existing build path, and writes `update_result.json`.

`library-catalog` records multiple local libraries for agent routing:

```bash
office2md library-catalog ./libraries.json --add-library ./library-a --library-id lib-a --library-name "Library A"
office2md library-catalog ./libraries.json --json
```

Catalog records carry `library_id`, `library_name`, `library_path`, and optional `source_root`. Multi-library search execution is future work; existing single-library commands remain compatible.

### AI Enrichment (Optional)

AI enrichment is opt-in. AI is disabled by default, and the MiniMax CLI is not required for normal conversion, library building, search, reports, or the GUI workflow.

```bash
# Requires --use-ai flag and CLI adapter
office2md convert-file input.pdf ./output \
  --use-ai --ai-backend cli --ai-command "minimax-cli --prompt"
```

### Doctor & Diagnostics

```bash
# Check system readiness
office2md doctor

# Docling-specific diagnostics
office2md doctor-docling

# Warm up Docling models before batch processing
office2md warmup-docling
```

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `--engine` | Conversion engine (`auto`, `docling`, `markitdown`) | `auto` |
| `--profile` | Output profile (`kb`, `rag`, `memory`, `obsidian`) | `kb` |
| `--recursive` | Process subdirectories | `false` |
| `--max-files` | Cap files per run (safety) | unlimited |
| `--dry-run` | Preview files without converting | `false` |
| `--skip-existing` | Skip already-converted files | `false` |
| `--use-ai` | Enable AI enrichment | `false` |
| `--render-pdf-pages` | Render PDF pages to images | `false` |
| `--max-render-pages` | Max pages to render | `3` |

## Comparison

| Feature | office2md | Marker | Docling |
|---------|-----------|--------|---------|
| Local-only | ✓ | partial | partial |
| Office-first | ✓ | ✗ | ✗ |
| Knowledge Library | ✓ | ✗ | ✗ |
| SQLite FTS | ✓ | ✗ | ✗ |
| Graph export | ✓ | ✗ | ✗ |
| HMI translation | ✓ | ✗ | ✗ |

## Upstream Engines

office2md delegates conversion to proven open-source parsers:

- [Docling](https://github.com/docling-project/docling) — PDF conversion with layout analysis
- [MarkItDown](https://github.com/microsoft/markitdown) — Microsoft Office and other formats

## License

MIT License — see [LICENSE](LICENSE) for details.

## Links

- [Documentation](docs/)
- [Release Notes](RELEASE_NOTES_v0.4.0.md)
- [Issue Tracker](https://github.com/cait52099/office2md/issues)
