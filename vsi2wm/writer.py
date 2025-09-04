"""Writer module for saving WireMock stubs and reports with advanced features."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WireMockWriter:
    """Handles writing WireMock stubs and reports with advanced features."""

    def __init__(self, output_dir: Path, max_file_size: int = 1024 * 1024):  # 1MB default
        self.output_dir = output_dir
        self.mappings_dir = output_dir / "mappings"
        self.files_dir = output_dir / "__files"
        self.max_file_size = max_file_size
        self.large_files_count = 0
        self.total_large_file_size = 0
        
        # Create directories
        self.mappings_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def write_stubs(self, stubs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Write WireMock stubs with advanced features."""
        logger.info(f"Writing {len(stubs)} stubs to {self.mappings_dir}")
        
        stats = {
            "total_stubs": len(stubs),
            "files_written": 0,
            "large_files_split": 0,
            "errors": []
        }
        
        for i, stub in enumerate(stubs):
            try:
                self._write_stub(stub, i, stats)
            except Exception as e:
                error_msg = f"Failed to write stub {i}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        logger.info(f"Stub writing completed: {stats['files_written']} files written")
        if stats["large_files_split"] > 0:
            logger.info(f"Large files split: {stats['large_files_split']}")
        
        return stats

    def _write_stub(self, stub: Dict[str, Any], index: int, stats: Dict[str, Any]) -> None:
        """Write a single stub with large file handling."""
        # Generate filename
        transaction_id = stub.get("metadata", {}).get("devtest_transaction_id", f"stub_{index}")
        safe_transaction_id = self._sanitize_filename(transaction_id)
        filename = f"{safe_transaction_id}_{index}.json"
        file_path = self.mappings_dir / filename
        
        # Check if response body is large
        response = stub.get("response", {})
        body_content = self._extract_body_content(response)
        
        if body_content and len(body_content) > self.max_file_size:
            # Split large body to __files directory
            body_file_path = self._write_large_body(body_content, safe_transaction_id, index)
            stub = self._update_stub_with_file_reference(stub, body_file_path)
            stats["large_files_split"] += 1
        
        # Write stub with pretty formatting
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stub, f, indent=2, ensure_ascii=False)
        
        stats["files_written"] += 1
        logger.debug(f"Written stub to {file_path}")

    def _extract_body_content(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract body content from response."""
        if "jsonBody" in response:
            return json.dumps(response["jsonBody"], ensure_ascii=False)
        elif "body" in response:
            return response["body"]
        return None

    def _write_large_body(self, body_content: str, transaction_id: str, index: int) -> str:
        """Write large body content to __files directory with enhanced features."""
        # Determine file extension and content type based on content
        content_type, extension = self._detect_content_type(body_content)
        
        # Create sanitized filename
        sanitized_id = self._sanitize_filename(transaction_id)
        filename = f"{sanitized_id}_{index}_body.{extension}"
        file_path = self.files_dir / filename
        
        # Write content with proper encoding
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(body_content)
        
        # Log file size for monitoring and track statistics
        file_size = file_path.stat().st_size
        self.large_files_count += 1
        self.total_large_file_size += file_size
        logger.debug(f"Written large body to {file_path} ({file_size} bytes)")
        
        return f"__files/{filename}"
    
    def _detect_content_type(self, content: str) -> tuple[str, str]:
        """Detect content type and appropriate file extension."""
        content = content.strip()
        
        # JSON detection
        if content.startswith("{") or content.startswith("["):
            return "application/json", "json"
        
        # XML detection
        if content.startswith("<"):
            return "application/xml", "xml"
        
        # HTML detection
        if content.startswith("<!DOCTYPE") or content.startswith("<html"):
            return "text/html", "html"
        
        # Plain text detection
        if content.startswith("text/") or "Content-Type: text/" in content:
            return "text/plain", "txt"
        
        # Binary content detection (base64)
        if self._is_base64_content(content):
            return "application/octet-stream", "bin"
        
        # Default to text
        return "text/plain", "txt"
    
    def _is_base64_content(self, content: str) -> bool:
        """Check if content appears to be base64 encoded."""
        import base64
        import re
        
        # Remove whitespace and check if it looks like base64
        clean_content = re.sub(r'\s+', '', content)
        
        # Base64 should only contain A-Z, a-z, 0-9, +, /, and = for padding
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', clean_content):
            return False
        
        # Check if length is reasonable for base64
        if len(clean_content) % 4 != 0:
            return False
        
        try:
            # Try to decode a small portion
            base64.b64decode(clean_content[:100])
            return True
        except Exception:
            return False

    def _update_stub_with_file_reference(self, stub: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Update stub to reference external file instead of inline body."""
        response = stub.get("response", {})
        
        # Remove inline body and add file reference
        if "jsonBody" in response:
            del response["jsonBody"]
            response["bodyFileName"] = file_path
        elif "body" in response:
            del response["body"]
            response["bodyFileName"] = file_path
        
        stub["response"] = response
        return stub

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Replace invalid characters
        invalid_chars = ['#', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename

    def write_report(self, report_data: Dict[str, Any]) -> None:
        """Write conversion report with enhanced formatting."""
        report_file = self.output_dir / "report.json"
        
        # Add writer metadata
        enhanced_report = {
            **report_data,
            "writer_info": {
                "max_file_size": self.max_file_size,
                "output_format": "wiremock",
                "version": "1.0",
                "files_written": len(list(self.files_dir.glob("*"))) if self.files_dir.exists() else 0,
                "large_files_split": self.large_files_count if hasattr(self, 'large_files_count') else 0,
                "total_large_file_size": self.total_large_file_size if hasattr(self, 'total_large_file_size') else 0,
            }
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(enhanced_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report written to {report_file}")

    def write_index_file(self, stubs: List[Dict[str, Any]]) -> None:
        """Write an index file listing all generated stubs."""
        index_data = {
            "total_stubs": len(stubs),
            "stubs": []
        }
        
        for i, stub in enumerate(stubs):
            stub_info = {
                "index": i,
                "transaction_id": stub.get("metadata", {}).get("devtest_transaction_id", f"stub_{i}"),
                "method": stub.get("request", {}).get("method", "UNKNOWN"),
                "url": stub.get("request", {}).get("urlPath") or stub.get("request", {}).get("urlPathPattern", "UNKNOWN"),
                "status": stub.get("response", {}).get("status", 0),
                "priority": stub.get("priority", 0),
                "filename": f"{self._sanitize_filename(stub.get('metadata', {}).get('devtest_transaction_id', f'stub_{i}'))}_{i}.json"
            }
            index_data["stubs"].append(stub_info)
        
        index_file = self.output_dir / "stubs_index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Index file written to {index_file}")

    def write_summary(self, stats: Dict[str, Any]) -> None:
        """Write a human-readable summary file."""
        summary_file = self.output_dir / "summary.txt"
        
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("VSI to WireMock Conversion Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total stubs generated: {stats['total_stubs']}\n")
            f.write(f"Files written: {stats['files_written']}\n")
            f.write(f"Large files split: {stats['large_files_split']}\n")
            
            if stats["errors"]:
                f.write(f"\nErrors encountered: {len(stats['errors'])}\n")
                for error in stats["errors"]:
                    f.write(f"  - {error}\n")
            else:
                f.write("\nNo errors encountered.\n")
            
            f.write(f"\nOutput directory: {self.output_dir}\n")
            f.write(f"Mappings directory: {self.mappings_dir}\n")
            f.write(f"Files directory: {self.files_dir}\n")
        
        logger.info(f"Summary written to {summary_file}")


def write_wiremock_output(
    stubs: List[Dict[str, Any]],
    report_data: Dict[str, Any],
    output_dir: Path,
    max_file_size: int = 1024 * 1024,
) -> Dict[str, Any]:
    """Convenience function to write complete WireMock output."""
    writer = WireMockWriter(output_dir, max_file_size)
    
    # Write stubs
    stats = writer.write_stubs(stubs)
    
    # Write report
    writer.write_report(report_data)
    
    # Write index file
    writer.write_index_file(stubs)
    
    # Write summary
    writer.write_summary(stats)
    
    return stats
