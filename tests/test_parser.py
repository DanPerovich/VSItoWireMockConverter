"""Tests for VSI parser module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vsi2wm.parser import VSILayout, VSIParser, parse_vsi_file


class TestVSILayout:
    """Test VSILayout enumeration."""

    def test_layout_values(self):
        """Test that layout values are correctly defined."""
        assert VSILayout.MODEL_BASED == "model_based"
        assert VSILayout.RR_PAIRS == "rr_pairs"
        assert VSILayout.UNKNOWN == "unknown"


class TestVSIParser:
    """Test VSIParser class."""

    def test_init(self):
        """Test parser initialization."""
        vsi_file = Path("test.vsi")
        parser = VSIParser(vsi_file)

        assert parser.vsi_file_path == vsi_file
        assert parser.layout == VSILayout.UNKNOWN
        assert parser.source_version is None
        assert parser.build_number is None
        assert parser.protocol is None
        assert parser.transactions_count == 0
        assert parser.warnings == []

    def test_detect_layout_model_based(self):
        """Test detection of model-based layout."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <rq><bd>request data</bd></rq>
      <rs><rp><bd>response data</bd></rp></rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            layout = parser.detect_layout()

            assert layout == VSILayout.MODEL_BASED
            assert parser.transactions_count == 1

            # Cleanup
            Path(f.name).unlink()

    def test_detect_layout_rr_pairs(self):
        """Test detection of RR-pairs layout."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <reqData>request data</reqData>
      <rspData>response data</rspData>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            layout = parser.detect_layout()

            assert layout == VSILayout.RR_PAIRS
            assert parser.transactions_count == 1

            # Cleanup
            Path(f.name).unlink()

    def test_detect_layout_unknown_falls_back(self):
        """Test that unknown layout falls back to model-based."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <someOtherTag>data</someOtherTag>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            layout = parser.detect_layout()

            assert layout == VSILayout.MODEL_BASED  # Falls back to model-based
            assert parser.transactions_count == 1

            # Cleanup
            Path(f.name).unlink()

    def test_extract_metadata(self):
        """Test metadata extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="10.5.0" buildNumber="510">
  <transactions>
    <t></t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            metadata = parser.extract_metadata()

            assert metadata["source_version"] == "10.5.0"
            assert metadata["build_number"] == "510"

            # Cleanup
            Path(f.name).unlink()

    def test_extract_metadata_missing_attributes(self):
        """Test metadata extraction when attributes are missing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t></t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            metadata = parser.extract_metadata()

            assert metadata["source_version"] is None
            assert metadata["build_number"] is None

            # Cleanup
            Path(f.name).unlink()

    def test_detect_protocol_from_element(self):
        """Test protocol detection from protocol element."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <rq>
        <m>
          <protocol>http</protocol>
        </m>
      </rq>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            protocol = parser.detect_protocol()

            assert protocol == "http"

            # Cleanup
            Path(f.name).unlink()

    def test_detect_protocol_from_properties(self):
        """Test protocol detection from properties."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <rq>
        <ag>
          <p n="protocol">https</p>
        </ag>
      </rq>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            protocol = parser.detect_protocol()

            assert protocol == "https"

            # Cleanup
            Path(f.name).unlink()

    def test_is_http_protocol_http(self):
        """Test HTTP protocol detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <rq>
        <m>
          <protocol>http</protocol>
        </m>
      </rq>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            is_http = parser.is_http_protocol()

            assert is_http is True

            # Cleanup
            Path(f.name).unlink()

    def test_is_http_protocol_https(self):
        """Test HTTPS protocol detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <rq>
        <m>
          <protocol>https</protocol>
        </m>
      </rq>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            is_http = parser.is_http_protocol()

            assert is_http is True

            # Cleanup
            Path(f.name).unlink()

    def test_is_http_protocol_non_http(self):
        """Test non-HTTP protocol detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <rq>
        <m>
          <protocol>mq</protocol>
        </m>
      </rq>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            is_http = parser.is_http_protocol()

            assert is_http is False
            assert "Skipping non-HTTP protocol: mq" in parser.warnings

            # Cleanup
            Path(f.name).unlink()

    def test_is_http_protocol_no_protocol_assumes_http(self):
        """Test that missing protocol assumes HTTP."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage>
  <transactions>
    <t>
      <rq>
        <m>
          <method>GET</method>
        </m>
      </rq>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            is_http = parser.is_http_protocol()

            assert is_http is True

            # Cleanup
            Path(f.name).unlink()

    def test_parse_complete(self):
        """Test complete parsing workflow."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="10.5.0" buildNumber="510">
  <transactions>
    <t>
      <rq>
        <m>
          <protocol>https</protocol>
          <method>GET</method>
        </m>
        <bd>request data</bd>
      </rq>
      <rs>
        <rp>
          <bd>response data</bd>
        </rp>
      </rs>
    </t>
    <t>
      <rq>
        <m>
          <method>POST</method>
        </m>
        <bd>another request</bd>
      </rq>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            parser = VSIParser(Path(f.name))
            result = parser.parse()

            assert result["layout"] == VSILayout.MODEL_BASED
            assert result["metadata"]["source_version"] == "10.5.0"
            assert result["metadata"]["build_number"] == "510"
            assert result["protocol"] == "https"
            assert result["is_http"] is True
            assert (
                result["transactions_count"] == 1
            )  # Only counts during layout detection
            assert result["warnings"] == []

            # Cleanup
            Path(f.name).unlink()


class TestParseVSIFile:
    """Test parse_vsi_file convenience function."""

    def test_parse_vsi_file(self):
        """Test the convenience function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t>
      <rq><bd>data</bd></rq>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

            result = parse_vsi_file(Path(f.name))

            assert result["layout"] == VSILayout.MODEL_BASED
            assert result["metadata"]["source_version"] == "1.0"
            assert result["is_http"] is True

            # Cleanup
            Path(f.name).unlink()
