"""Command-line interface for VSI to WireMock converter."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from vsi2wm import __version__


class CLIError(Exception):
    """Custom exception for CLI errors."""
    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def setup_logging(level: str) -> None:
    """Set up logging configuration."""
    log_level = getattr(logging, level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert VSI files to WireMock stub mappings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vsi2wm convert --in service.vsi --out output
  vsi2wm convert --in service.vsi --out output --latency uniform --soap-match both --log-level debug
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert a VSI file to WireMock mappings"
    )
    convert_parser.add_argument(
        "--in",
        dest="input_file",
        type=Path,
        required=True,
        help="Input VSI file path",
    )
    convert_parser.add_argument(
        "--out",
        dest="output_dir",
        type=Path,
        required=True,
        help="Output directory for WireMock mappings",
    )
    convert_parser.add_argument(
        "--latency",
        choices=["uniform", "fixed"],
        default="uniform",
        help="Latency strategy: uniform (default) or fixed",
    )
    convert_parser.add_argument(
        "--soap-match",
        choices=["soapAction", "xpath", "both"],
        default="both",
        help="SOAP matching strategy (default: both)",
    )
    convert_parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warn", "error"],
        default="info",
        help="Logging level (default: info)",
    )
    convert_parser.add_argument(
        "--max-file-size",
        type=int,
        default=1024 * 1024,  # 1MB
        help="Maximum file size before splitting to __files (default: 1048576 bytes)",
    )

    # Version command
    parser.add_argument(
        "--version",
        action="version",
        version=f"vsi2wm {__version__}",
    )

    return parser.parse_args(args)


def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if args.command == "convert":
        # Validate input file
        if not args.input_file.exists():
            raise CLIError(f"Input file not found: {args.input_file}", exit_code=2)

        if not args.input_file.is_file():
            raise CLIError(f"Input path is not a file: {args.input_file}", exit_code=2)

        if not args.input_file.suffix.lower() == ".vsi":
            raise CLIError(
                f"Input file must have .vsi extension: {args.input_file}", 
                exit_code=2
            )

        # Validate output directory
        if args.output_dir.exists() and not args.output_dir.is_dir():
            raise CLIError(
                f"Output path exists but is not a directory: {args.output_dir}", 
                exit_code=2
            )

        # Validate max file size
        if args.max_file_size <= 0:
            raise CLIError(
                f"Max file size must be positive: {args.max_file_size}", 
                exit_code=2
            )

        # Create output directory if it doesn't exist
        try:
            args.output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise CLIError(
                f"Permission denied creating output directory: {args.output_dir}", 
                exit_code=3
            )


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point for the CLI."""
    try:
        parsed_args = parse_args(args)

        if not parsed_args.command:
            # No command specified, show help
            parse_args(["--help"])
            return 1

        # Set up logging
        setup_logging(parsed_args.log_level)
        logger = logging.getLogger(__name__)

        # Validate arguments
        validate_args(parsed_args)

        if parsed_args.command == "convert":
            logger.info(f"Starting VSI to WireMock conversion")
            logger.info(f"Input: {parsed_args.input_file}")
            logger.info(f"Output: {parsed_args.output_dir}")
            logger.info(f"Latency strategy: {parsed_args.latency}")
            logger.info(f"SOAP match strategy: {parsed_args.soap_match}")
            logger.info(f"Max file size: {parsed_args.max_file_size} bytes")

            # Import and run converter
            from vsi2wm.core import VSIConverter

            converter = VSIConverter(
                input_file=parsed_args.input_file,
                output_dir=parsed_args.output_dir,
                latency_strategy=parsed_args.latency,
                soap_match_strategy=parsed_args.soap_match,
                max_file_size=parsed_args.max_file_size,
            )

            exit_code = converter.convert()
            
            if exit_code == 0:
                logger.info("Conversion completed successfully")
            else:
                logger.error("Conversion failed")
            
            return exit_code

        return 0

    except CLIError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        return e.exit_code
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
