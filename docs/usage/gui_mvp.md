# office2md GUI MVP

The v0.3.0 GUI MVP is a local Streamlit workflow shell around existing stable office2md library functionality.

It is optional. Normal CLI installation and usage do not require Streamlit.

## Install Optional GUI Dependency

```powershell
cd C:\Users\hcai\Downloads\office2md
.\.venv\Scripts\Activate.ps1
pip install -e ".[gui]"
```

## Launch

```powershell
python -m streamlit run office2md/gui/app.py
```

## Expected First Screen

The app opens with:

```text
office2md GUI MVP
```

Use the sidebar to enter a Knowledge Library folder path or a `library.db` path. The Library Overview page loads existing `library_report()` data and shows:

- `documents_count`
- `chunks_count`
- `entities_count`
- `noisy_chunks_count`
- `chunks_without_locator`
- `page_level_pdf_documents`

If the library path is missing or invalid, the app shows a warning instead of running any workflow.

## Current Pages

- Library Overview: implemented.
- Search: placeholder for v0.3.0 P2.
- Locate Document: placeholder for v0.3.0 P3.
- Evidence Package: placeholder for v0.3.0 P4.
- Runner Dry-run: placeholder for v0.3.0 P5.

## Current Limitations

- The GUI does not run conversion.
- The GUI does not change search ranking, aliases, token fallback, or diagnostics behavior.
- The GUI does not change library-report metrics or scoring.
- The GUI does not change runner process-control behavior.
- Search, locate-document, evidence-package generation, and runner dry-run controls are placeholders in this first skeleton.

## Explicit Non-Goals

The GUI MVP does not add AI/MiniMax, OCR, embeddings/vector search, cloud/network dependency, Office image export, legacy `.doc` conversion, or Office provenance redesign.
