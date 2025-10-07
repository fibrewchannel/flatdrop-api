#!/bin/bash
# Full idempotent processing and clustering pipeline
# Run from: /Users/rickshangle/flatdrop-api/code/app

set -e  # Exit on any error

echo "============================================================"
echo "FLATLINE CODEX PROCESSING PIPELINE"
echo "============================================================"
echo ""
echo "Step 1: Incremental processing (new files only)"
echo "Step 2: Parent piece clustering analysis"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

# Step 1: Process new files
echo ""
echo "============================================================"
echo "STEP 1: INCREMENTAL PROCESSING"
echo "============================================================"
python3 incremental_processor.py <<EOF
2
yes
EOF

# Step 2: Run clustering analysis
echo ""
echo "============================================================"
echo "STEP 2: CLUSTERING ANALYSIS"
echo "============================================================"
python3 parent_piece_clustering.py

echo ""
echo "============================================================"
echo "PIPELINE COMPLETE"
echo "============================================================"
echo ""
echo "Review outputs:"
echo "  - _relocation_logs/incremental_*.json (processing results)"
echo "  - _relocation_logs/chapter_suggestions.md (clustering results)"
echo "  - _archive/processed-sources/ (archived source files)"
echo ""
echo "_inload/ should now be empty"
