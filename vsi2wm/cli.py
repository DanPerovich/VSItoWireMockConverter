"""Command-line interface for VSI to WireMock converter."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from vsi2wm import __version__
from vsi2wm.config import load_config, merge_config_with_args, create_default_config
from vsi2wm.exceptions import CLIError


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
        "--config",
        type=Path,
        help="Configuration file (YAML)",
    )
    convert_parser.add_argument(
        "--latency",
        choices=["uniform", "fixed"],
        help="Latency strategy: uniform (default) or fixed (overrides config)",
    )
    convert_parser.add_argument(
        "--soap-match",
        choices=["soapAction", "xpath", "both"],
        help="SOAP matching strategy (overrides config)",
    )
    convert_parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warn", "error"],
        help="Logging level (overrides config)",
    )
    convert_parser.add_argument(
        "--max-file-size",
        type=int,
        help="Maximum file size before splitting to __files (overrides config)",
    )
    convert_parser.add_argument(
        "--wiremock-cloud",
        action="store_true",
        help="Create WireMock Cloud export format",
    )
    convert_parser.add_argument(
        "--upload-to-cloud",
        action="store_true",
        help="Upload stubs directly to WireMock Cloud",
    )
    convert_parser.add_argument(
        "--test-cloud-connection",
        action="store_true",
        help="Test WireMock Cloud connection",
    )
    convert_parser.add_argument(
        "--analyze-scenario",
        action="store_true",
        help="Analyze VSI scenario for patterns and complexity",
    )
    convert_parser.add_argument(
        "--optimize-scenario",
        action="store_true",
        help="Optimize scenario for better WireMock performance",
    )

    # Config command
    config_parser = subparsers.add_parser(
        "config", help="Configuration management"
    )
    config_parser.add_argument(
        "action",
        choices=["create", "show"],
        help="Action to perform",
    )
    config_parser.add_argument(
        "--file",
        type=Path,
        default=Path("vsi2wm.yaml"),
        help="Configuration file path (default: vsi2wm.yaml)",
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

        # Validate max file size (only if provided via command line)
        if hasattr(args, 'max_file_size') and args.max_file_size is not None:
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
            return 0

        # Handle config command
        if parsed_args.command == "config":
            if parsed_args.action == "create":
                create_default_config(parsed_args.file)
                print(f"Created default configuration file: {parsed_args.file}")
                return 0
            elif parsed_args.action == "show":
                if parsed_args.file.exists():
                    with open(parsed_args.file, "r") as f:
                        print(f.read())
                else:
                    print(f"Configuration file not found: {parsed_args.file}")
                return 0

        # Load configuration
        config = load_config(parsed_args.config if hasattr(parsed_args, 'config') else None)
        
        # Merge with command line arguments
        if parsed_args.command == "convert":
            config = merge_config_with_args(
                config,
                latency_strategy=getattr(parsed_args, 'latency', None),
                soap_match_strategy=getattr(parsed_args, 'soap_match', None),
                log_level=getattr(parsed_args, 'log_level', None),
                max_file_size=getattr(parsed_args, 'max_file_size', None),
            )

        # Set up logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)

        # Validate arguments
        validate_args(parsed_args)

        if parsed_args.command == "convert":
            logger.info(f"Starting VSI to WireMock conversion")
            logger.info(f"Input: {parsed_args.input_file}")
            logger.info(f"Output: {parsed_args.output_dir}")
            logger.info(f"Latency strategy: {config.latency_strategy}")
            logger.info(f"SOAP match strategy: {config.soap_match_strategy}")
            logger.info(f"Max file size: {config.max_file_size} bytes")

            # Import and run converter
            from vsi2wm.core import VSIConverter

            converter = VSIConverter(
                input_file=parsed_args.input_file,
                output_dir=parsed_args.output_dir,
                latency_strategy=config.latency_strategy,
                soap_match_strategy=config.soap_match_strategy,
                max_file_size=config.max_file_size,
            )

            exit_code = converter.convert()
            
            if exit_code == 0:
                logger.info("Conversion completed successfully")
                
                # Handle WireMock Cloud features
                if parsed_args.wiremock_cloud or parsed_args.upload_to_cloud or parsed_args.test_cloud_connection or parsed_args.analyze_scenario or parsed_args.optimize_scenario:
                    from vsi2wm.wiremock_cloud import (
                        create_wiremock_cloud_export,
                        upload_to_wiremock_cloud,
                        test_wiremock_cloud_connection,
                    )
                    
                    # Load stubs for WireMock Cloud operations
                    stubs = []
                    mappings_dir = parsed_args.output_dir / "mappings"
                    for stub_file in mappings_dir.glob("*.json"):
                        with open(stub_file, "r") as f:
                            stubs.append(json.load(f))
                    
                    # Test connection if requested
                    if parsed_args.test_cloud_connection:
                        if config.wiremock_cloud:
                            logger.info("Testing WireMock Cloud connection...")
                            result = test_wiremock_cloud_connection(config.wiremock_cloud)
                            logger.info(f"Connection test result: {result}")
                        else:
                            logger.warning("No WireMock Cloud configuration found for connection test")
                    
                    # Create WireMock Cloud export
                    if parsed_args.wiremock_cloud:
                        logger.info("Creating WireMock Cloud export...")
                        result = create_wiremock_cloud_export(stubs, parsed_args.output_dir, config.wiremock_cloud)
                        logger.info(f"WireMock Cloud export created: {result}")
                    
                    # Upload to WireMock Cloud
                    if parsed_args.upload_to_cloud:
                        if config.wiremock_cloud:
                            logger.info("Uploading to WireMock Cloud...")
                            result = upload_to_wiremock_cloud(stubs, config.wiremock_cloud)
                            logger.info(f"Upload result: {result}")
                        else:
                            logger.error("No WireMock Cloud configuration found for upload")
                            return 1
                    
                    # Handle scenario analysis
                    if parsed_args.analyze_scenario or parsed_args.optimize_scenario:
                        from vsi2wm.scenario_helpers import create_scenario_report
                        from vsi2wm.ir_builder import build_ir_from_vsi
                        
                        # Build IR for analysis
                        logger.info("Building IR for scenario analysis...")
                        ir = build_ir_from_vsi(parsed_args.input_file)
                        
                        # Create scenario report
                        logger.info("Creating scenario report...")
                        report = create_scenario_report(
                            ir.transactions,
                            parsed_args.output_dir,
                            analysis=None if parsed_args.analyze_scenario else None,
                            optimization=None if parsed_args.optimize_scenario else None
                        )
                        
                        logger.info(f"Scenario analysis completed: {report['summary']}")
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
