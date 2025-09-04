"""Command-line interface for VSI to WireMock converter."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from vsi2wm import __version__


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
        help="Latency strategy: uniform (default) or fixed:<ms>",
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
        if not args.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {args.input_file}")

        if not args.input_file.suffix.lower() == ".vsi":
            raise ValueError(f"Input file must have .vsi extension: {args.input_file}")

        # Create output directory if it doesn't exist
        args.output_dir.mkdir(parents=True, exist_ok=True)


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

            # Import and run converter
            from vsi2wm.core import VSIConverter

            converter = VSIConverter(
                input_file=parsed_args.input_file,
                output_dir=parsed_args.output_dir,
                latency_strategy=parsed_args.latency,
                soap_match_strategy=parsed_args.soap_match,
            )

            return converter.convert()

        return 0

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
