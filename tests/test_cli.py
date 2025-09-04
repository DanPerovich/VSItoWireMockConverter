"""Tests for CLI module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from vsi2wm.cli import parse_args, validate_args


class TestCLI:
    """Test CLI argument parsing and validation."""
    
    def test_parse_args_convert(self):
        """Test parsing convert command arguments."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--latency", "uniform",
            "--soap-match", "both",
            "--log-level", "debug"
        ]
        
        parsed = parse_args(args)
        
        assert parsed.command == "convert"
        assert parsed.input_file == Path("test.vsi")
        assert parsed.output_dir == Path("output")
        assert parsed.latency == "uniform"
        assert parsed.soap_match == "both"
        assert parsed.log_level == "debug"
    
    def test_parse_args_defaults(self):
        """Test default argument values."""
        args = ["convert", "--in", "test.vsi", "--out", "output"]
        
        parsed = parse_args(args)
        
        assert parsed.latency == "uniform"
        assert parsed.soap_match == "both"
        assert parsed.log_level == "info"
    
    def test_parse_args_version(self):
        """Test version argument."""
        with pytest.raises(SystemExit):
            parse_args(["--version"])
    
    def test_validate_args_file_not_found(self):
        """Test validation with non-existent file."""
        args = parse_args(["convert", "--in", "nonexistent.vsi", "--out", "output"])
        
        with pytest.raises(FileNotFoundError):
            validate_args(args)
    
    def test_validate_args_wrong_extension(self):
        """Test validation with wrong file extension."""
        # Create a temporary file with wrong extension
        temp_file = Path("temp.txt")
        temp_file.write_text("test")
        
        try:
            args = parse_args(["convert", "--in", "temp.txt", "--out", "output"])
            
            with pytest.raises(ValueError, match="must have .vsi extension"):
                validate_args(args)
        finally:
            temp_file.unlink()
