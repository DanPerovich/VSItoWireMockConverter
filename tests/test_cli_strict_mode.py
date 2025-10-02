"""
Integration tests for CLI strict mode functionality.
"""

import pytest
import tempfile
import subprocess
import sys
from pathlib import Path


class TestCLIStrictMode:
    """Test CLI strict mode functionality."""
    
    def test_cli_strict_mode_with_unsupported_helpers(self):
        """Test CLI strict mode fails when unsupported helpers are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a VSI file with unsupported helpers
            vsi_content = '''<?xml version="1.0" encoding="UTF-8"?>
            <serviceImage>
                <t id="1">
                    <rq>
                        <method>GET</method>
                        <url>/test</url>
                    </rq>
                    <rs>
                        <rp id="1">
                            <status>200</status>
                            <bd>{"message": "{{=doRandomString(10)}}"}</bd>
                        </rp>
                    </rs>
                </t>
            </serviceImage>'''
            
            vsi_file = temp_path / "test.vsi"
            vsi_file.write_text(vsi_content)
            
            # Run CLI with strict mode
            result = subprocess.run([
                sys.executable, "-m", "vsi2wm.cli", "convert",
                "--in", str(vsi_file),
                "--out", str(temp_path / "output"),
                "--strict-mode"
            ], capture_output=True, text=True)
            
            # Should fail with exit code 1
            assert result.returncode == 1
            
            # Should contain error message about unsupported helpers
            assert "Strict mode enabled: Found unsupported CA LISA helpers" in result.stderr
            assert "Unsupported CA LISA helper" in result.stderr
    
    def test_cli_strict_mode_without_unsupported_helpers(self):
        """Test CLI strict mode succeeds when no unsupported helpers are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a VSI file without unsupported helpers
            vsi_content = '''<?xml version="1.0" encoding="UTF-8"?>
            <serviceImage>
                <t id="1">
                    <rq>
                        <method>GET</method>
                        <url>/test</url>
                    </rq>
                    <rs>
                        <rp id="1">
                            <status>200</status>
                            <bd>{"message": "Hello World"}</bd>
                        </rp>
                    </rs>
                </t>
            </serviceImage>'''
            
            vsi_file = temp_path / "test.vsi"
            vsi_file.write_text(vsi_content)
            
            # Run CLI with strict mode
            result = subprocess.run([
                sys.executable, "-m", "vsi2wm.cli", "convert",
                "--in", str(vsi_file),
                "--out", str(temp_path / "output"),
                "--strict-mode"
            ], capture_output=True, text=True)
            
            # Should succeed with exit code 0
            assert result.returncode == 0
    
    def test_cli_normal_mode_with_unsupported_helpers(self):
        """Test CLI normal mode succeeds with warnings when unsupported helpers are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a VSI file with unsupported helpers
            vsi_content = '''<?xml version="1.0" encoding="UTF-8"?>
            <serviceImage>
                <t id="1">
                    <rq>
                        <method>GET</method>
                        <url>/test</url>
                    </rq>
                    <rs>
                        <rp id="1">
                            <status>200</status>
                            <bd>{"message": "{{=doRandomString(10)}}"}</bd>
                        </rp>
                    </rs>
                </t>
            </serviceImage>'''
            
            vsi_file = temp_path / "test.vsi"
            vsi_file.write_text(vsi_content)
            
            # Run CLI without strict mode (normal mode)
            result = subprocess.run([
                sys.executable, "-m", "vsi2wm.cli", "convert",
                "--in", str(vsi_file),
                "--out", str(temp_path / "output")
            ], capture_output=True, text=True)
            
            # Should succeed with exit code 0
            assert result.returncode == 0
            
            # Should contain warning about unsupported helpers
            assert "Unsupported CA LISA helper" in result.stderr
    
    def test_cli_help_includes_strict_mode(self):
        """Test that CLI help includes the --strict-mode flag."""
        result = subprocess.run([
            sys.executable, "-m", "vsi2wm.cli", "convert", "--help"
        ], capture_output=True, text=True)
        
        # Should include the strict-mode flag in help
        assert "--strict-mode" in result.stdout
        assert "unsupported CA LISA helpers" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__])
