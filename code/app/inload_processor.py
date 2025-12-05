#!/usr/bin/env python3
"""
inload_processor.py

Spec-aligned inload runner built on top of:
- IncrementalProcessor (new/unprocessed detection, archiving)
- ProductionRelocationNibbler (chunk extraction, relocation, YAML creation)

Responsibilities in this first pass:
- Wire paths from config.VAULT_BASE_PATH (no hardcoded absolute paths)
- Process only *new* files from _inload (md/txt/rtf)
- Archive processed sources into _archive/processed-sources
- Maintain a human-readable TSV log at _inload/inload_log.tsv with per-file/per-chunk entries

This is intentionally thin: orchestration + logging.
Deeper things (chunking, coordinate assignment, YAML) remain in the Nibbler.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import VAULT_BASE_PATH
from incremental_processor import IncrementalProcessor


INLOAD_SUBDIR = "_inload"
BACKUP_SUBDIR = "_backups"
RELOCATION_LOG_DIR = "_relocation_logs"
PROCESSED_SOURCES_LOG = "processed_sources.json"
INLOAD_TSV_LOG = "inload_log.tsv"


@dataclass
class InloadLogEntry:
    """Single row for _inload/inload_log.tsv"""
    timestamp: str
    source_path: str
    dest_path: str
    status: str          # moved | analyzed | error | skipped
    notes: str           # free-form summary (disposition, quality, theme, error, etc.)

    def to_row(self) -> Dict[str, str]:
        return {
            "timestamp": self.timestamp,
            "source_path": self.source_path,
            "dest_path": self.dest_path,
            "status": self.status,
            "notes": self.notes,
        }


class InloadProcessor(IncrementalProcessor):
    """
    High-level inload processor.

    Extends IncrementalProcessor to:
    - Use dynamic paths from config.VAULT_BASE_PATH
    - Emit _inload/inload_log.tsv rows as it processes files
    """

    def __init__(
        self,
        vault_base: Optional[Path] = None,
        dry_run: bool = False,
    ) -> None:
        self.vault_base = Path(vault_base or VAULT_BASE_PATH)

        source_dir = self.vault_base / INLOAD_SUBDIR
        output_base = self.vault_base
        backup_dir = self.vault_base / BACKUP_SUBDIR
        processed_log = (
            self.vault_base / RELOCATION_LOG_DIR / PROCESSED_SOURCES_LOG
        )

        # Initialize parent (IncrementalProcessor)
        super().__init__(
            source_dir=str(source_dir),
            output_base=str(output_base),
            backup_dir=str(backup_dir),
            log_file=str(processed_log),
        )

        # TSV inload log
        self.inload_log_path = source_dir / INLOAD_TSV_LOG
        self.dry_run = dry_run

    # ---------- TSV logging ----------

    @property
    def _tsv_fieldnames(self) -> List[str]:
        return ["timestamp", "source_path", "dest_path", "status", "notes"]

    def append_log_entries(self, entries: List[InloadLogEntry]) -> None:
        """
        Append one or more rows to _inload/inload_log.tsv.
        Creates the file and header if it doesn't exist.
        """
        if not entries:
            return

        log_file = self.inload_log_path
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_exists = log_file.exists()

        with log_file.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self._tsv_fieldnames,
                delimiter="\t",
                extrasaction="ignore",
            )
            if not file_exists:
                writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_row())

    # ---------- Main processing entrypoint ----------

    def process_new_files_with_log(self, dry_run: Optional[bool] = None) -> Dict[str, Any]:
        """
        Spec-aligned wrapper around IncrementalProcessor.process_new_files
        that:
        - Uses the same detection, backup, archiving logic
        - Adds TSV logging for each processed file/chunk

        Returns a high-level summary similar to IncrementalProcessor.
        """
        if dry_run is None:
            dry_run = self.dry_run

        print("\n=== InloadProcessor: scanning _inload for new files ===")
        now_iso = datetime.now().isoformat()

        # Reuse the internal helpers from IncrementalProcessor
        new_files, already_processed = self.scan_for_new_files()

        new_by_type = {
            ".md": len([f for f in new_files if f.suffix == ".md"]),
            ".txt": len([f for f in new_files if f.suffix == ".txt"]),
            ".rtf": len([f for f in new_files if f.suffix == ".rtf"]),
        }

        if already_processed:
            print(f"✓ Found {len(already_processed)} already-processed files")
            if dry_run:
                print("  (These would be archived in a real run)")

        if not new_files:
            print("\n✅ No new files to process!")
            return {
                "new_files": 0,
                "already_processed": len(already_processed),
                "message": "Nothing to do",
            }

        print(f"\n📂 Found {len(new_files)} new files to process")
        print(f"   - .md: {new_by_type['.md']}")
        print(f"   - .txt: {new_by_type['.txt']}")
        print(f"   - .rtf: {new_by_type['.rtf']}")

        if dry_run:
            print("\n🔍 DRY RUN - showing what would be processed:")
            for i, file_path in enumerate(new_files[:10], 1):
                rel = file_path.relative_to(self.source_dir)
                print(f"  {i}. {rel} ({file_path.suffix})")
            if len(new_files) > 10:
                print(f"  ... and {len(new_files) - 10} more")

            # No TSV logging on pure dry-run summary
            return {
                "dry_run": True,
                "new_files": len(new_files),
                "new_by_type": new_by_type,
                "already_processed": len(already_processed),
            }

        # REAL RUN BELOW

        print("\n💾 Creating backup via ProductionRelocationNibbler...")
        backup_path = self.nibbler.create_backup()

        batch_size = 10
        batch_id = 1
        all_results: List[Dict[str, Any]] = []

        for i in range(0, len(new_files), batch_size):
            batch_files = new_files[i : i + batch_size]
            print(f"\n⚙️ Processing Batch {batch_id}: {len(batch_files)} files")

            batch_results: List[Dict[str, Any]] = []
            tsv_entries: List[InloadLogEntry] = []

            for file_path in batch_files:
                rel_source = file_path.relative_to(self.source_dir)
                # Process via Nibbler (chunk extraction + relocation)
                result = self.nibbler.process_single_file(file_path, dry_run=False)
                batch_results.append(result)

                if "error" in result:
                    # Log error row
                    tsv_entries.append(
                        InloadLogEntry(
                            timestamp=now_iso,
                            source_path=str(rel_source),
                            dest_path="",
                            status="error",
                            notes=result.get("error", "unknown error"),
                        )
                    )
                    continue

                # Summarize dispositions for IncrementalProcessor log
                disposition_summary: Dict[str, int] = {}
                for chunk in result.get("chunks", []):
                    dispo = chunk["disposition"]
                    disposition_summary[dispo] = disposition_summary.get(dispo, 0) + 1

                    # TSV row per chunk
                    notes = (
                        f"{dispo}; Q={chunk['quality_score']:.1f}; "
                        f"theme={chunk.get('theme', 'unknown')}"
                    )
                    tsv_entries.append(
                        InloadLogEntry(
                            timestamp=now_iso,
                            source_path=str(rel_source),
                            dest_path=chunk.get("destination", ""),
                            status="moved",
                            notes=notes,
                        )
                    )

                # Mark as processed in JSON log
                processing_info = {
                    "chunks_extracted": result.get("chunks_extracted", 0),
                    "disposition_summary": disposition_summary,
                }
                self.mark_as_processed(file_path, processing_info)

                # Archive the source file
                self.archive_source_file(file_path)

            # Append TSV entries for this batch
            self.append_log_entries(tsv_entries)

            all_results.extend(batch_results)
            batch_id += 1

        # Archive already-processed files (if they weren't already moved)
        if already_processed:
            print(f"\n📦 Archiving {len(already_processed)} already-processed files...")
            for file_path in already_processed:
                if file_path.exists():
                    self.archive_source_file(file_path)

        # Save updated JSON processed_sources log
        self.save_processed_log()

        # Aggregate stats for return value
        total_chunks = sum(r.get("chunks_extracted", 0) for r in all_results)
        total_dispositions = {
            "memoir-grade": 0,
            "promising": 0,
            "borderline": 0,
            "trash": 0,
        }

        for result in all_results:
            for chunk in result.get("chunks", []):
                dispo = chunk["disposition"]
                if dispo not in total_dispositions:
                    total_dispositions[dispo] = 0
                total_dispositions[dispo] += 1

        summary = {
            "new_files_processed": len(new_files),
            "new_files_by_type": new_by_type,
            "already_processed_archived": len(already_processed),
            "total_chunks_extracted": total_chunks,
            "disposition_breakdown": total_dispositions,
            "backup_location": str(backup_path),
            "processing_date": now_iso,
            "tsv_log": str(self.inload_log_path),
        }

        print("\n✅ Inload processing complete.")
        print(f"   New files processed: {summary['new_files_processed']}")
        print(f"   Total chunks: {summary['total_chunks_extracted']}")
        print(f"   TSV log: {summary['tsv_log']}")

        return summary


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flatdrop Inload Processor (spec-aligned orchestrator)"
    )
    parser.add_argument(
        "--vault",
        type=str,
        default=None,
        help="Override vault base path (defaults to config.VAULT_BASE_PATH)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report, but do not backup, relocate, or archive",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vault_base = Path(args.vault) if args.vault else VAULT_BASE_PATH

    processor = InloadProcessor(vault_base=vault_base, dry_run=args.dry_run)

    if args.dry_run:
        summary = processor.process_new_files_with_log(dry_run=True)
    else:
        summary = processor.process_new_files_with_log(dry_run=False)

    # Basic JSON-ish print for shell use
    print("\nSummary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
