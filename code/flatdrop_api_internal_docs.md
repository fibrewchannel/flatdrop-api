# 🧠 Flatdrop API + Codex Processor — Internal Script Reference

This is a high-level documentation index for key scripts used in Flatdrop's processing architecture.

---

## 🔧 Core Configuration

### `config.py`
Defines constants, directory paths, API keys, and other environment parameters shared across modules.

### `tesseract_config.py`
Schema definitions and utilities for assigning and validating Tesseract coordinates:
- `structure`, `transmission`, `purpose`, `terrain`
- Used by classifier modules

---

## 🛠 Processing & Ingestion

### `run_full_processing.sh`
Bash orchestrator that triggers a full multi-stage ingestion + processing pipeline:
- Includes GitHub pull, batch YAML injection, coordinate extraction, and draft staging.

### `incremental_processor.py`
Processes only new or changed files from `_inload/`.
- Hash-check or mtime based diff
- Supports dry-run mode
   
### `single_file_tester.py`
Run the coordinate pipeline on one `.md` file.
- CLI usage: `python single_file_tester.py /path/to/file.md`

---

## 🧩 Coordinate Handling & Analysis

### `coordinate_distribution_analyzer.py`
Analyzes frequency of coordinate tags across Codex corpus.
- Output: pie/bar charts, JSON summaries

### `parent_piece_clustering.py`
Groups entries with similar coordinate metadata or overlapping topics.
- Used to auto-suggest memoir chapters or narrative groupings

### `training_nibbler.py`
Early-stage module for building fine-tuned classification models or tagging heuristics.
- Extracts semantic features, token patterns

---

## 🧳 Production Utilities

### `production_relocation_nibbler.py`
Moves or renames files based on tag metadata or status.
- E.g., move reviewed files into `_memoir_drafts/`, archive trash, etc.

---

## 🌐 REST API

### `routes.py`
Defines `flatdrop-api` routes including:
- `POST /ingest` — Single file ingest
- `POST /batch-ingest` — Trigger batch mode
- `POST /query/coords` — Query by Tesseract filters
- `GET /status` — Basic health check / status

---

To extend this doc:
- Document function headers with docstrings
- Add CLI usage examples per script
- Cross-link YAML schema references

