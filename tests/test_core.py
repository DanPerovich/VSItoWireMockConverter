"""Tests for core module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from vsi2wm.core import ConversionReport, VSIConverter


class TestConversionReport:
    """Test ConversionReport class."""

    def test_init(self):
        """Test report initialization."""
        source_file = Path("test.vsi")
        report = ConversionReport(source_file)

        assert report.source_file == source_file
        assert report.source_version is None
        assert report.build_number is None
        assert report.transactions_count == 0
        assert report.variants_count == 0
        assert report.stubs_generated == 0
        assert report.warnings == []
        assert report.notes == []

    def test_add_warning(self):
        """Test adding warnings."""
        report = ConversionReport(Path("test.vsi"))
        report.add_warning("Test warning")

        assert "Test warning" in report.warnings
        assert len(report.warnings) == 1

    def test_add_note(self):
        """Test adding notes."""
        report = ConversionReport(Path("test.vsi"))
        report.add_note("Test note")

        assert "Test note" in report.notes
        assert len(report.notes) == 1

    def test_to_dict(self):
        """Test converting report to dictionary."""
        report = ConversionReport(Path("test.vsi"))
        report.source_version = "10.5.0"
        report.build_number = "510"
        report.transactions_count = 5
        report.variants_count = 10
        report.stubs_generated = 8
        report.add_warning("Test warning")
        report.add_note("Test note")

        result = report.to_dict()

        assert result["source_file"] == "test.vsi"
        assert result["source_version"] == "10.5.0"
        assert result["build_number"] == "510"
        assert result["counts"]["transactions"] == 5
        assert result["counts"]["variants"] == 10
        assert result["counts"]["stubs_generated"] == 8
        assert result["warnings"] == ["Test warning"]
        assert result["notes"] == ["Test note"]

    def test_save(self, tmp_path):
        """Test saving report to file."""
        report = ConversionReport(Path("test.vsi"))
        report.add_note("Test note")

        report.save(tmp_path)

        report_file = tmp_path / "report.json"
        assert report_file.exists()

        with open(report_file) as f:
            data = json.load(f)

        assert data["source_file"] == "test.vsi"
        assert data["notes"] == ["Test note"]


class TestVSIConverter:
    """Test VSIConverter class."""

    def test_init(self, tmp_path):
        """Test converter initialization."""
        input_file = Path("test.vsi")
        output_dir = tmp_path / "output"

        converter = VSIConverter(
            input_file=input_file,
            output_dir=output_dir,
            latency_strategy="uniform",
            soap_match_strategy="both",
        )

        assert converter.input_file == input_file
        assert converter.output_dir == output_dir
        assert converter.latency_strategy == "uniform"
        assert converter.soap_match_strategy == "both"
        assert converter.report.source_file == input_file

        # Check that directories were created
        assert (output_dir / "mappings").exists()
        assert (output_dir / "__files").exists()

    def test_convert_placeholder(self, tmp_path):
        """Test placeholder conversion logic."""
        input_file = Path("test.vsi")
        output_dir = tmp_path / "output"

        converter = VSIConverter(input_file, output_dir)

        # Should return 0 (success) even with placeholder logic
        result = converter.convert()
        assert result == 0

        # Should create report file
        report_file = output_dir / "report.json"
        assert report_file.exists()
