import os
from pathlib import Path

# --- Local Mac path (your actual Obsidian vault on disk) ---
LOCAL_VAULT_PATH = Path("/Users/rickshangle/Vaults/flatline-codex")

# --- Docker/Fly path (where the vault will be copied inside the container) ---
DOCKER_VAULT_PATH = Path("/app/flatline-codex")

# --- Auto-switching vault path ---
# Priority:
# 1. FLATDROP_VAULT_PATH (manual override)
# 2. If running on Fly (FLY_APP_NAME is set) -> use Docker path
# 3. Otherwise -> use local laptop path
VAULT_PATH = Path(
    os.getenv("FLATDROP_VAULT_PATH")
    or (DOCKER_VAULT_PATH if os.getenv("FLY_APP_NAME") else LOCAL_VAULT_PATH)
)

# Dependent paths
INLOAD_DOCS_PATH = VAULT_PATH / "_inload/docs"

# Backwards compat for older code that expects VAULT_BASE_PATH
VAULT_BASE_PATH = VAULT_PATH
