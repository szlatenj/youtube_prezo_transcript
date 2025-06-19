"""
Configuration settings for YouTube Presentation Extractor
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configuration class for the YouTube presentation extractor."""
    
    # Scene detection settings
    scene_change_threshold: float = 0.3  # SSIM threshold for scene changes
    min_time_between_captures: float = 2.0  # Minimum seconds between screenshots
    histogram_threshold: float = 0.15  # Histogram comparison threshold
    
    # Video processing settings
    target_resolution: Optional[tuple] = None  # (width, height) or None for original
    video_quality: str = "720p"  # Video quality to download: 144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p
    frame_rate: int = 1  # Frames per second to process
    skip_intro_outro: bool = True
    intro_outro_duration: float = 30.0  # Seconds to skip from start/end
    
    # Screenshot settings
    screenshot_format: str = "PNG"
    screenshot_quality: int = 95  # For JPEG format
    screenshot_resolution: Optional[tuple] = None  # (width, height) for screenshot resizing
    output_directory: str = "output"
    
    # Document generation settings
    output_format: str = "HTML"  # HTML, MARKDOWN, or PDF
    template_name: str = "presentation.html"
    include_timestamps: bool = True
    include_navigation: bool = True
    
    # LLM Enhancement settings
    enable_llm_enhancement: bool = False  # Enable/disable LLM enhancement
    enhancement_level: str = "detailed"  # basic, detailed, academic
    anthropic_model: str = "claude-3-7-sonnet-20250219"  # Claude model to use
    max_tokens_per_request: int = 4000  # Max tokens per API request (increased for larger context)
    max_cost_per_video: float = 5.0  # Maximum cost per video in USD
    cache_enhanced_results: bool = True  # Cache enhancement results
    cache_file: str = "enhancement_cache.json"  # Cache file path
    
    # LLM Batching settings
    batch_target_tokens: int = 1500  # Target tokens per batch (will result in ~700-1000 tokens of actual text)
    enable_batching: bool = True  # Enable batching for transcript enhancement
    batch_overlap_tolerance: float = 0.2  # Allow 20% overlap in batch sizes
    
    # LLM Prompt customization
    custom_prompt_template: Optional[str] = None  # Custom prompt template (optional)
    prompt_style: str = "clear"  # clear, academic, conversational, technical
    
    # Error handling
    max_retries: int = 3
    timeout: int = 30
    
    # Performance settings
    chunk_size: int = 100  # Frames to process in chunks
    memory_limit_mb: int = 512  # Memory limit for processing
    
    def __post_init__(self):
        """Ensure output directory exists and set default resolutions."""
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Set default screenshot resolution if not specified
        if self.screenshot_resolution is None:
            if self.target_resolution:
                self.screenshot_resolution = self.target_resolution
            else:
                # Default to 1280x720 for screenshots
                self.screenshot_resolution = (1280, 720)

# Default configuration
DEFAULT_CONFIG = Config()

def load_config_from_file(config_path: str) -> Config:
    """Load configuration from a JSON file."""
    import json
    
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG
    
    try:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # Convert tuple strings back to tuples
        if 'target_resolution' in config_dict and config_dict['target_resolution']:
            config_dict['target_resolution'] = tuple(config_dict['target_resolution'])
        
        if 'screenshot_resolution' in config_dict and config_dict['screenshot_resolution']:
            config_dict['screenshot_resolution'] = tuple(config_dict['screenshot_resolution'])
        
        return Config(**config_dict)
    except Exception as e:
        print(f"Warning: Could not load config from {config_path}: {e}")
        return DEFAULT_CONFIG

def save_config_to_file(config: Config, config_path: str):
    """Save configuration to a JSON file."""
    import json
    
    config_dict = {
        'scene_change_threshold': config.scene_change_threshold,
        'min_time_between_captures': config.min_time_between_captures,
        'histogram_threshold': config.histogram_threshold,
        'target_resolution': config.target_resolution,
        'video_quality': config.video_quality,
        'frame_rate': config.frame_rate,
        'skip_intro_outro': config.skip_intro_outro,
        'intro_outro_duration': config.intro_outro_duration,
        'screenshot_format': config.screenshot_format,
        'screenshot_quality': config.screenshot_quality,
        'screenshot_resolution': config.screenshot_resolution,
        'output_directory': config.output_directory,
        'output_format': config.output_format,
        'template_name': config.template_name,
        'include_timestamps': config.include_timestamps,
        'include_navigation': config.include_navigation,
        'enable_llm_enhancement': config.enable_llm_enhancement,
        'enhancement_level': config.enhancement_level,
        'anthropic_model': config.anthropic_model,
        'max_tokens_per_request': config.max_tokens_per_request,
        'max_cost_per_video': config.max_cost_per_video,
        'cache_enhanced_results': config.cache_enhanced_results,
        'cache_file': config.cache_file,
        'batch_target_tokens': config.batch_target_tokens,
        'enable_batching': config.enable_batching,
        'batch_overlap_tolerance': config.batch_overlap_tolerance,
        'custom_prompt_template': config.custom_prompt_template,
        'prompt_style': config.prompt_style,
        'max_retries': config.max_retries,
        'timeout': config.timeout,
        'chunk_size': config.chunk_size,
        'memory_limit_mb': config.memory_limit_mb
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save config to {config_path}: {e}")

def get_resolution_presets():
    """Get common resolution presets."""
    return {
        '144p': (256, 144),
        '240p': (426, 240),
        '360p': (640, 360),
        '480p': (854, 480),
        '720p': (1280, 720),
        '1080p': (1920, 1080),
        '1440p': (2560, 1440),
        '2160p': (3840, 2160),
        '4k': (3840, 2160),
        'hd': (1280, 720),
        'fullhd': (1920, 1080),
        'qhd': (2560, 1440),
        'uhd': (3840, 2160)
    } 