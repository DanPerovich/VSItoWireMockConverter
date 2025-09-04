"""VSI file parser for detecting layout and extracting metadata."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree.ElementTree import Element, iterparse

logger = logging.getLogger(__name__)


class VSILayout:
    """Enumeration of VSI layout types."""

    MODEL_BASED = "model_based"  # Uses <bd> elements
    RR_PAIRS = "rr_pairs"  # Uses <reqData>/<rspData> elements
    UNKNOWN = "unknown"


class VSIParser:
    """Parser for VSI files with layout detection and metadata extraction."""

    def __init__(self, vsi_file_path: Path):
        self.vsi_file_path = vsi_file_path
        self.layout: str = VSILayout.UNKNOWN
        self.source_version: Optional[str] = None
        self.build_number: Optional[str] = None
        self.protocol: Optional[str] = None
        self.transactions_count = 0
        self.warnings: List[str] = []

    def detect_layout(self) -> str:
        """Detect the VSI layout by examining the XML structure."""
        logger.info(f"Detecting layout for {self.vsi_file_path}")

        try:
            # Use iterparse for memory-efficient parsing
            context = iterparse(self.vsi_file_path, events=("start", "end"))

            for event, elem in context:
                if event == "start":
                    # Check for model-based layout indicators
                    if elem.tag == "bd":
                        self.layout = VSILayout.MODEL_BASED
                        logger.info("Detected model-based layout (uses <bd> elements)")
                        break

                    # Check for RR-pairs layout indicators
                    elif elem.tag in ["reqData", "rspData"]:
                        self.layout = VSILayout.RR_PAIRS
                        logger.info(
                            "Detected RR-pairs layout (uses <reqData>/<rspData> elements)"
                        )
                        break

                    # Check for transaction elements to count
                    elif elem.tag == "t":
                        self.transactions_count += 1

                # Clear element to free memory
                elem.clear()

        except Exception as e:
            logger.error(f"Error detecting layout: {e}")
            self.warnings.append(f"Layout detection failed: {e}")
            self.layout = VSILayout.UNKNOWN

        if self.layout == VSILayout.UNKNOWN:
            logger.warning("Could not determine VSI layout - assuming model-based")
            self.layout = VSILayout.MODEL_BASED

        return self.layout

    def extract_metadata(self) -> Dict[str, Optional[str]]:
        """Extract metadata from the VSI file."""
        logger.info("Extracting metadata from VSI file")

        try:
            context = iterparse(self.vsi_file_path, events=("start",))

            for event, elem in context:
                if elem.tag == "serviceImage":
                    # Extract version and build number from serviceImage attributes
                    self.source_version = elem.get("version")
                    self.build_number = elem.get("buildNumber")

                    logger.info(f"Extracted version: {self.source_version}")
                    logger.info(f"Extracted build number: {self.build_number}")
                    break

                elem.clear()

        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            self.warnings.append(f"Metadata extraction failed: {e}")

        return {
            "source_version": self.source_version,
            "build_number": self.build_number,
        }

    def detect_protocol(self) -> Optional[str]:
        """Detect the protocol used in the VSI file."""
        logger.info("Detecting protocol from VSI file")

        try:
            context = iterparse(self.vsi_file_path, events=("start",))

            for event, elem in context:
                if elem.tag == "protocol":
                    self.protocol = elem.text
                    logger.info(f"Detected protocol: {self.protocol}")
                    break
                elif elem.tag == "p" and elem.get("n") == "protocol":
                    # Check for protocol in properties
                    self.protocol = elem.text
                    logger.info(f"Detected protocol from properties: {self.protocol}")
                    break

                elem.clear()

        except Exception as e:
            logger.error(f"Error detecting protocol: {e}")
            self.warnings.append(f"Protocol detection failed: {e}")

        return self.protocol

    def is_http_protocol(self) -> bool:
        """Check if the VSI file contains HTTP/S protocol."""
        protocol = self.detect_protocol()
        if protocol is None:
            # If no protocol detected, assume HTTP (common case)
            logger.info("No protocol detected - assuming HTTP")
            return True

        # Normalize protocol string
        protocol_lower = protocol.lower()
        is_http = protocol_lower in ["http", "https", "http/s"]

        if not is_http:
            logger.warning(f"Non-HTTP protocol detected: {protocol}")
            self.warnings.append(f"Skipping non-HTTP protocol: {protocol}")

        return is_http

    def parse(self) -> Dict[str, Any]:
        """Main parsing method that performs all detection and extraction."""
        logger.info(f"Starting VSI parsing: {self.vsi_file_path}")

        # Detect layout
        layout = self.detect_layout()

        # Extract metadata
        metadata = self.extract_metadata()

        # Detect protocol
        protocol = self.detect_protocol()
        is_http = self.is_http_protocol()

        result = {
            "layout": layout,
            "metadata": metadata,
            "protocol": protocol,
            "is_http": is_http,
            "transactions_count": self.transactions_count,
            "warnings": self.warnings,
        }

        logger.info(f"Parsing completed: {result}")
        return result


def parse_vsi_file(vsi_file_path: Path) -> Dict[str, Any]:
    """Convenience function to parse a VSI file."""
    parser = VSIParser(vsi_file_path)
    return parser.parse()
