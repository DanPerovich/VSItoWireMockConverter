"""Configuration management for VSI to WireMock converter."""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from vsi2wm.exceptions import CLIError


@dataclass
class ConversionConfig:
    """Configuration for VSI to WireMock conversion."""
    
    # Latency strategy
    latency_strategy: str = "uniform"
    
    # SOAP matching strategy
    soap_match_strategy: str = "both"
    
    # File size limits
    max_file_size: int = 1024 * 1024  # 1MB
    
    # Logging
    log_level: str = "info"
    
    # WireMock Cloud settings
    wiremock_cloud: Optional[Dict[str, Any]] = None
    
    # Advanced mapping options
    json_matching: Dict[str, Any] = field(default_factory=lambda: {
        "ignore_array_order": True,
        "ignore_extra_elements": True,
    })
    
    xml_matching: Dict[str, Any] = field(default_factory=lambda: {
        "normalize_whitespace": True,
    })
    
    # Priority assignment
    priority_strategy: str = "weight_descending"  # weight_descending, weight_ascending, order
    
    # Response templates
    enable_response_templates: bool = True
    
    # Metadata preservation
    preserve_devtest_metadata: bool = True
    
    # Output organization
    create_index_files: bool = True
    create_summary_files: bool = True
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConversionConfig":
        """Create config from dictionary."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "latency_strategy": self.latency_strategy,
            "soap_match_strategy": self.soap_match_strategy,
            "max_file_size": self.max_file_size,
            "log_level": self.log_level,
            "wiremock_cloud": self.wiremock_cloud,
            "json_matching": self.json_matching,
            "xml_matching": self.xml_matching,
            "priority_strategy": self.priority_strategy,
            "enable_response_templates": self.enable_response_templates,
            "preserve_devtest_metadata": self.preserve_devtest_metadata,
            "create_index_files": self.create_index_files,
            "create_summary_files": self.create_summary_files,
        }


def load_config(config_file: Optional[Path] = None) -> ConversionConfig:
    """Load configuration from file or return defaults."""
    if config_file is None:
        return ConversionConfig()
    
    if not config_file.exists():
        raise CLIError(f"Config file not found: {config_file}", exit_code=2)
    
    if not config_file.is_file():
        raise CLIError(f"Config path is not a file: {config_file}", exit_code=2)
    
    try:
        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f)
        
        if config_dict is None:
            return ConversionConfig()
        
        return ConversionConfig.from_dict(config_dict)
    
    except yaml.YAMLError as e:
        raise CLIError(f"Invalid YAML in config file: {e}", exit_code=2)
    except Exception as e:
        raise CLIError(f"Error loading config file: {e}", exit_code=2)


def save_config(config: ConversionConfig, config_file: Path) -> None:
    """Save configuration to file."""
    try:
        with open(config_file, "w") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, indent=2)
    except Exception as e:
        raise CLIError(f"Error saving config file: {e}", exit_code=2)


def create_default_config(config_file: Path) -> None:
    """Create a default configuration file."""
    try:
        with open(config_file, "w") as f:
            f.write("""# VSI to WireMock Converter Configuration
# This file contains configuration options for the VSI to WireMock converter

# Latency strategy: uniform (default) or fixed:<ms>
latency_strategy: uniform

# SOAP match strategy: soapAction, xpath, both (default: both)
soap_match_strategy: both

# Maximum file size in bytes before splitting to __files/ (default: 1048576 = 1MB)
max_file_size: 1048576

# Log level: debug, info, warn, error (default: info)
log_level: info

# WireMock Cloud settings (optional)
# wiremock_cloud:
#   api_key: your_api_key_here
#   project_id: your_project_id_here
#   environment: your_environment_here

# JSON matching options
json_matching:
  ignore_array_order: true
  ignore_extra_elements: true

# XML matching options
xml_matching:
  normalize_whitespace: true

# Priority strategy: weight_descending (default), weight_ascending, order
priority_strategy: weight_descending

# Enable response templates (default: true)
enable_response_templates: true

# Preserve DevTest metadata (default: true)
preserve_devtest_metadata: true

# Create index files (default: true)
create_index_files: true

# Create summary files (default: true)
create_summary_files: true
""")
    except Exception as e:
        raise CLIError(f"Error creating config file: {e}", exit_code=2)


def merge_config_with_args(config: ConversionConfig, **kwargs) -> ConversionConfig:
    """Merge command line arguments with config file."""
    merged_config = ConversionConfig.from_dict(config.to_dict())
    
    # Override with command line arguments
    for key, value in kwargs.items():
        if value is not None and hasattr(merged_config, key):
            setattr(merged_config, key, value)
    
    return merged_config
