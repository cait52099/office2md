# Library Catalog

The library catalog is an additive routing file for agent workflows. It does not modify libraries and does not merge search indexes.

## Add a Library

```powershell
python -m office2md.cli library-catalog .\libraries.json --add-library .\library-a --library-id lib-a --library-name "Library A" --source-root .\source-a
```

## List Libraries

```powershell
python -m office2md.cli library-catalog .\libraries.json
python -m office2md.cli library-catalog .\libraries.json --json
```

The catalog uses schema:

```text
office2md.library_catalog.v1
```

Each record includes:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_root`;
- `registered_at`.

## Agent Guidance

Agents should decide whether to answer from library A, library B, or both before searching. Evidence from any library must preserve:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_file`;
- `locator`;
- `chunk_id`;
- `document_id`.

Existing single-library commands remain the source of evidence:

```powershell
python -m office2md.cli search-library .\library-a\library.db "query"
python -m office2md.cli open-chunk .\library-a CHUNK_ID --export-json .\chunk.json
python -m office2md.cli build-report-context .\library-a "query" --export-json .\context.json
```

For cross-library reports today, run those commands against each selected library and keep library provenance in the downstream notes.

## Future Work

Future versions may add multi-library search and report context commands. Future MCP tools should wrap the same read-only contracts and must not expose unrestricted SQL, shell execution, or write-back.
