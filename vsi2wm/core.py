"""Core conversion logic for VSI to WireMock converter."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversionReport:
    """Tracks conversion progress and issues."""

    def __init__(self, source_file: Path):
        self.source_file = source_file
        self.source_version: Optional[str] = None
        self.build_number: Optional[str] = None
        self.transactions_count = 0
        self.variants_count = 0
        self.stubs_generated = 0
        self.warnings: List[str] = []
        self.notes: List[str] = []

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(message)

    def add_note(self, message: str) -> None:
        """Add an informational note."""
        self.notes.append(message)
        logger.info(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "source_file": str(self.source_file),
            "source_version": self.source_version,
            "build_number": self.build_number,
            "counts": {
                "transactions": self.transactions_count,
                "variants": self.variants_count,
                "stubs_generated": self.stubs_generated,
            },
            "warnings": self.warnings,
            "notes": self.notes,
        }

    def save(self, output_dir: Path) -> None:
        """Save report to JSON file."""
        report_file = output_dir / "report.json"
        with open(report_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Conversion report saved to {report_file}")


class VSIConverter:
    """Main converter class for VSI to WireMock mappings."""

    def __init__(
        self,
        input_file: Path,
        output_dir: Path,
        latency_strategy: str = "uniform",
        soap_match_strategy: str = "both",
    ):
        self.input_file = input_file
        self.output_dir = output_dir
        self.latency_strategy = latency_strategy
        self.soap_match_strategy = soap_match_strategy
        self.report = ConversionReport(input_file)

        # Create output directories
        self.mappings_dir = output_dir / "mappings"
        self.files_dir = output_dir / "__files"
        self.mappings_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def convert(self) -> int:
        """Main conversion method."""
        try:
            logger.info(f"Starting conversion of {self.input_file}")

            # 1. Parse VSI file
            from vsi2wm.parser import parse_vsi_file

            parse_result = parse_vsi_file(self.input_file)

            # Update report with parsing results
            metadata = parse_result["metadata"]
            self.report.source_version = metadata["source_version"]
            self.report.build_number = metadata["build_number"]
            self.report.transactions_count = parse_result["transactions_count"]

            # Add warnings from parser
            warnings = parse_result["warnings"]
            for warning in warnings:
                self.report.add_warning(warning)

            # Check if this is an HTTP protocol
            if not parse_result["is_http"]:
                self.report.add_warning(
                    f"Non-HTTP protocol detected: {parse_result['protocol']}"
                )
                logger.warning("Skipping non-HTTP VSI file")
                self.report.save(self.output_dir)
                return 0  # Not an error, just skipped

            # Add parsing notes
            self.report.add_note(f"Detected layout: {parse_result['layout']}")
            self.report.add_note(
                f"Protocol: {parse_result['protocol'] or 'HTTP (assumed)'}"
            )
            self.report.add_note(
                f"Transactions found: {parse_result['transactions_count']}"
            )

            # 2. Build Intermediate Representation
            from vsi2wm.ir_builder import build_ir_from_vsi

            ir = build_ir_from_vsi(self.input_file)

            # Update report with IR results
            self.report.variants_count = sum(
                len(t.response_variants) for t in ir.transactions
            )

            # Add IR notes
            self.report.add_note(f"Built IR with {len(ir.transactions)} transactions")
            self.report.add_note(f"Total response variants: {self.report.variants_count}")

            # 3. Generate WireMock mappings
            from vsi2wm.mapper import map_ir_to_wiremock

            stubs = map_ir_to_wiremock(
                ir,
                latency_strategy=self.latency_strategy,
                soap_match_strategy=self.soap_match_strategy,
            )

            # Update report with mapping results
            self.report.stubs_generated = len(stubs)
            self.report.add_note(f"Generated {len(stubs)} WireMock stubs")

            # 4. Save mappings and report using enhanced writer
            from vsi2wm.writer import write_wiremock_output

            writer_stats = write_wiremock_output(
                stubs,
                self.report.to_dict(),
                self.output_dir,
                max_file_size=1024 * 1024  # 1MB
            )

            # Update report with writer stats
            if writer_stats["large_files_split"] > 0:
                self.report.add_note(f"Large files split: {writer_stats['large_files_split']}")
            if writer_stats["errors"]:
                for error in writer_stats["errors"]:
                    self.report.add_warning(error)

            logger.info(f"Conversion completed successfully: {len(stubs)} stubs generated")
            self.report.add_note("WireMock mapping completed successfully")

            return 0

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            self.report.add_warning(f"Conversion failed: {e}")
            self.report.save(self.output_dir)
            return 1


