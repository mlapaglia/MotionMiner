#!/usr/bin/env python3
"""
Command line interface for Google Motion Photo Extractor
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

from .config import ExtractionConfig, GIF_QUALITY_PRESETS, DEFAULT_GIF_QUALITY, DEFAULT_GIF_WIDTH

class CLI:
    """Command line interface handler"""
    
    def __init__(self) -> None:
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description="Extract embedded videos from Google Motion Photos",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples_text()
        )
        
        parser.add_argument(
            'input',
            help='Input JPG file or directory containing JPG files'
        )
        
        parser.add_argument(
            '-o', '--output',
            help='Output file path (optional, auto-generated if not provided)'
        )
        
        format_group = parser.add_mutually_exclusive_group()
        format_group.add_argument(
            '--mp4',
            action='store_true',
            help='Extract as MP4 video (default)'
        )
        format_group.add_argument(
            '--gif',
            action='store_true',
            help='Extract as GIF animation'
        )
        format_group.add_argument(
            '--both',
            action='store_true',
            help='Extract both MP4 and GIF'
        )
        
        gif_group = parser.add_mutually_exclusive_group()
        gif_group.add_argument(
            '--gif-tiny',
            action='store_true',
            help='Extract as tiny GIF (64 colors, ~1-2MB)'
        )
        gif_group.add_argument(
            '--gif-low',
            action='store_true',
            help='Extract as low quality GIF (128 colors, ~2-3MB)'
        )
        gif_group.add_argument(
            '--gif-medium',
            action='store_true',
            help='Extract as medium quality GIF (192 colors, ~3-4MB)'
        )
        gif_group.add_argument(
            '--gif-high',
            action='store_true',
            help='Extract as high quality GIF (256 colors, ~5-7MB)'
        )
        
        parser.add_argument(
            '--gif-width',
            type=int,
            default=DEFAULT_GIF_WIDTH,
            help=f'GIF width in pixels (default: {DEFAULT_GIF_WIDTH})'
        )
        
        parser.add_argument(
            '--gif-no-loop',
            action='store_true',
            help='Create GIF that plays once instead of looping infinitely'
        )
        
        parser.add_argument(
            '--batch',
            action='store_true',
            help='Process all JPG files in input directory'
        )
        
        parser.add_argument(
            '--batch-output',
            help='Output directory for batch processing'
        )
        
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze file structure without extracting'
        )
        
        return parser
    
    def _get_examples_text(self) -> str:
        """Get examples text for help"""
        return """
Examples:
  %(prog)s photo.jpg                     # Extract as MP4
  %(prog)s photo.jpg --gif               # Extract as GIF (medium quality)
  %(prog)s photo.jpg --gif-tiny          # Extract as tiny GIF (~1-2MB)
  %(prog)s photo.jpg --gif --gif-no-loop # Extract as GIF that plays once
  %(prog)s photo.jpg --both              # Extract both MP4 and GIF
  %(prog)s photo.jpg -o video.mp4        # Custom output name
  %(prog)s photos/ --batch               # Process all JPGs in directory
  %(prog)s photos/ --batch --gif-low     # Batch convert to low quality GIFs
  %(prog)s photo.jpg --analyze           # Analyze file structure

GIF Quality Options:
  --gif-tiny:   Maximum compression, ~1-2MB, 64 colors, 80%% FPS
  --gif-low:    Heavy compression, ~2-3MB, 128 colors, 90%% FPS  
  --gif-medium: Balanced quality, ~3-4MB, 192 colors, full FPS
  --gif-high:   Best quality, ~5-7MB, 256 colors, full FPS
"""
    
    def parse_args(self, args: Optional[List[str]] = None) -> ExtractionConfig:
        """Parse command line arguments and return configuration"""
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = self.parser.parse_args(args)
        
        output_format = 'mp4'  # default
        gif_quality = DEFAULT_GIF_QUALITY
        
        if parsed_args.gif or parsed_args.gif_tiny or parsed_args.gif_low or parsed_args.gif_medium or parsed_args.gif_high:
            output_format = 'gif'
            
        if parsed_args.both:
            output_format = 'both'
            
        if parsed_args.gif_tiny:
            gif_quality = 'tiny'
        elif parsed_args.gif_low:
            gif_quality = 'low'
        elif parsed_args.gif_medium:
            gif_quality = 'medium'
        elif parsed_args.gif_high:
            gif_quality = 'high'
        
        if parsed_args.output:
            output_ext = Path(parsed_args.output).suffix.lower()
            if output_ext == '.gif':
                output_format = 'gif'
            elif output_ext == '.mp4':
                output_format = 'mp4'
        
        config = ExtractionConfig(
            input_path=parsed_args.input,
            output_path=parsed_args.output,
            output_format=output_format,
            gif_quality=gif_quality,
            gif_width=parsed_args.gif_width,
            gif_loop=not parsed_args.gif_no_loop,  # True if --gif-no-loop is NOT provided
            analyze_only=parsed_args.analyze,
            batch_mode=parsed_args.batch,
            batch_output_dir=parsed_args.batch_output
        )
        
        return config
    
    def print_help(self):
        """Print help message"""
        self.parser.print_help()
    
    def print_quality_info(self):
        """Print information about GIF quality presets"""
        print("GIF Quality Presets:")
        print("=" * 50)
        
        for quality_name, settings in GIF_QUALITY_PRESETS.items():
            print(f"{quality_name.upper()}:")
            print(f"  Colors: {settings.colors}")
            print(f"  FPS Multiplier: {settings.fps_multiplier}")
            print(f"  Description: {settings.description}")
            print(f"  Estimated Size: {settings.estimated_size}")
            print()
    
    def validate_config(self, config: ExtractionConfig) -> bool:
        """Validate the configuration"""
        input_path = Path(config.input_path)
        
        if not input_path.exists():
            print(f"Error: Input path does not exist: {input_path}")
            return False
        
        if config.batch_mode and not input_path.is_dir():
            print(f"Error: Batch mode requires a directory as input: {input_path}")
            return False
        
        if not config.batch_mode and not input_path.is_file():
            print(f"Error: Single file mode requires a file as input: {input_path}")
            return False
        
        if config.gif_quality not in GIF_QUALITY_PRESETS:
            print(f"Error: Invalid GIF quality: {config.gif_quality}")
            print(f"Valid options: {', '.join(GIF_QUALITY_PRESETS.keys())}")
            return False
        
        if config.gif_width <= 0:
            print(f"Error: GIF width must be positive: {config.gif_width}")
            return False
        
        return True