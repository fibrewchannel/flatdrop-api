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

---

## 🌐 REST API Endpoints (`routes.py`)

### `GET /status`
- **Purpose:** Simple health check for the Flatdrop API.
- **Returns:** `{ "status": "ok" }`
- **Usage:** Used by automation or UIs to verify service availability.

---

### `POST /ingest`
- **Purpose:** Ingest and analyze a **single** Markdown file for Tesseract coordinates.
- **Input:** JSON payload with one of the following:
  - `url` — GitHub or raw URL to fetch
  - `path` — Local file path
- **Behavior:** Fetches file, runs OpenAI classification, stores:
  - `<filename>_coords.json`
  - `<filename>_with_coords.md` in `_processed/`
- **Returns:** Status, coordinates, and file path references.

---

### `POST /batch-ingest`
- **Purpose:** Ingest **multiple** files from an index or vault directory.
- **Input (optional):**
  - Path to `_codex_index.json`
  - Filter rules for filename matching
- **Behavior:** Loops through each file, applies the same ingest logic as `/ingest`.
- **Returns:** Summary of processed files and skipped items.

---

### `POST /query/coords`
- **Purpose:** Query processed documents by Tesseract metadata.
- **Input:** JSON with any combination of:
  - `structure`
  - `transmission`
  - `purpose`
  - `terrain`
- **Returns:** List of files matching coordinate filter, with summaries.

---

---

## 🌐 REST API Endpoints (`routes.py`)

### ✅ Core Endpoints

#### `GET /status`
- **Purpose:** Health check for the API.
- **Example:**
  ```bash
  curl http://localhost:8000/status
  ```

#### `POST /ingest`
- **Purpose:** Ingest a single Markdown file.
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d '{"path": "_inload/The Spark.md"}'
  ```

#### `POST /batch-ingest`
- **Purpose:** Process a batch of files using a codex index or wildcard.
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/batch-ingest -H "Content-Type: application/json" -d '{}'
  ```

#### `POST /query/coords`
- **Purpose:** Query documents by Tesseract coordinates.
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/query/coords -H "Content-Type: application/json" -d '{"structure": "summoning", "terrain": "chaotic"}'
  ```

---

### 🧪 Testing / Preview Endpoints

#### `POST /test`
- **Purpose:** Ping OpenAI to validate model access.
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/test -H "Content-Type: application/json" -d '{"prompt": "Say hi."}'
  ```

#### `POST /extract-coords`
- **Purpose:** Extract Tesseract coordinates from a Markdown snippet (no save).
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/extract-coords -H "Content-Type: application/json" -d '{"content": "# My Journal\nToday was hard."}'
  ```

---

### 🧰 Maintenance & Utilities

#### `GET /files`
- **Purpose:** List files in `_inload/` or target path.
- **Example:**
  ```bash
  curl "http://localhost:8000/files?ext=.md"
  ```

#### `POST /reprocess`
- **Purpose:** Re-analyze an already-processed `.md` file.
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/reprocess -H "Content-Type: application/json" -d '{"filename": "_processed/The Spark_with_coords.md"}'
  ```

#### `POST /regenerate-md`
- **Purpose:** Sync `.md` frontmatter with saved `_coords.json`.
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/regenerate-md -H "Content-Type: application/json" -d '{"filename": "_processed/The Spark.md"}'
  ```

#### `POST /tag-review`
- **Purpose:** Mark a file for review, priority, discard, etc.
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/tag-review -H "Content-Type: application/json" -d '{"filename": "_processed/The Spark.md", "priority": "high", "status": "review_pending"}'
  ```

---

### 📦 Output & Draft Assembly

#### `POST /bundle`
- **Purpose:** Export selected files as a zipped memoir draft bundle.
- **Example:**
  ```bash
  curl -X POST http://localhost:8000/bundle -H "Content-Type: application/json" -d '{"coords": {"purpose": "tell-story", "terrain": "chaotic"}}'
  ```

---

