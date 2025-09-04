"""Tests for CLI functionality."""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from vsi2wm.cli import CLIError, main, parse_args, setup_logging, validate_args


class TestCLI:
    """Test CLI functionality."""

    def test_parse_args_convert(self):
        """Test parsing convert command arguments."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--latency", "uniform",
            "--soap-match", "both",
            "--log-level", "debug",
            "--max-file-size", "2048576"
        ]
        
        parsed = parse_args(args)
        
        assert parsed.command == "convert"
        assert parsed.input_file == Path("test.vsi")
        assert parsed.output_dir == Path("output")
        assert parsed.latency == "uniform"
        assert parsed.soap_match == "both"
        assert parsed.log_level == "debug"
        assert parsed.max_file_size == 2048576

    def test_parse_args_defaults(self):
        """Test parsing with default values."""
        args = ["convert", "--in", "test.vsi", "--out", "output"]
        
        parsed = parse_args(args)
        
        assert parsed.latency == "uniform"
        assert parsed.soap_match == "both"
        assert parsed.log_level == "info"
        assert parsed.max_file_size == 1024 * 1024  # 1MB

    def test_parse_args_version(self):
        """Test version argument."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--version"])
        
        assert exc_info.value.code == 0

    def test_validate_args_file_not_found(self):
        """Test validation with non-existent file."""
        args = Mock()
        args.command = "convert"
        args.input_file = Path("nonexistent.vsi")
        args.output_dir = Path("output")
        args.max_file_size = 1024 * 1024
        
        with pytest.raises(CLIError) as exc_info:
            validate_args(args)
        
        assert "Input file not found" in str(exc_info.value)
        assert exc_info.value.exit_code == 2

    def test_validate_args_wrong_extension(self):
        """Test validation with wrong file extension."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            args = Mock()
            args.command = "convert"
            args.input_file = Path(tmp.name)
            args.output_dir = Path("output")
            args.max_file_size = 1024 * 1024
            
            with pytest.raises(CLIError) as exc_info:
                validate_args(args)
            
            assert "must have .vsi extension" in str(exc_info.value)
            assert exc_info.value.exit_code == 2

    def test_validate_args_not_a_file(self):
        """Test validation when input is not a file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = Mock()
            args.command = "convert"
            args.input_file = Path(tmp_dir)  # Directory, not file
            args.output_dir = Path("output")
            args.max_file_size = 1024 * 1024
            
            with pytest.raises(CLIError) as exc_info:
                validate_args(args)
            
            assert "not a file" in str(exc_info.value)
            assert exc_info.value.exit_code == 2



    def test_validate_args_success(self):
        """Test successful validation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a test VSI file
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = Mock()
            args.command = "convert"
            args.input_file = vsi_file
            args.output_dir = Path(tmp_dir) / "output"
            args.max_file_size = 1024 * 1024
            
            # Should not raise any exception
            validate_args(args)
            
            # Check that output directory was created
            assert args.output_dir.exists()

    def test_setup_logging(self):
        """Test logging setup."""
        # Should not raise any exception
        setup_logging("info")
        setup_logging("debug")
        setup_logging("warn")
        setup_logging("error")

    def test_cli_error(self):
        """Test CLIError exception."""
        error = CLIError("Test error", exit_code=5)
        assert error.message == "Test error"
        assert error.exit_code == 5
        assert str(error) == "Test error"

    @patch('vsi2wm.core.VSIConverter')
    def test_main_success(self, mock_converter):
        """Test successful main execution."""
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 0
        mock_converter.return_value = mock_converter_instance
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a test VSI file
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output")
            ]
            
            exit_code = main(args)
            assert exit_code == 0

    @patch('vsi2wm.core.VSIConverter')
    def test_main_conversion_failure(self, mock_converter):
        """Test main execution with conversion failure."""
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 1
        mock_converter.return_value = mock_converter_instance
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a test VSI file
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output")
            ]
            
            exit_code = main(args)
            assert exit_code == 1

    def test_main_no_command(self):
        """Test main execution with no command."""
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 0  # Help shows with exit code 0

    def test_main_file_not_found(self):
        """Test main execution with file not found."""
        args = ["convert", "--in", "nonexistent.vsi", "--out", "output"]
        exit_code = main(args)
        assert exit_code == 2

    def test_main_keyboard_interrupt(self):
        """Test main execution with keyboard interrupt."""
        with patch('vsi2wm.cli.parse_args', side_effect=KeyboardInterrupt):
            exit_code = main()
            assert exit_code == 130

    def test_main_unexpected_error(self):
        """Test main execution with unexpected error."""
        with patch('vsi2wm.cli.parse_args', side_effect=Exception("Unexpected")):
            exit_code = main()
            assert exit_code == 1
