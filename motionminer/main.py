#!/usr/bin/env python3
"""
Google Motion Photo Extractor - Main Application
"""

import sys
from pathlib import Path
from typing import List, Optional

from .config import ExtractionConfig, SUPPORTED_IMAGE_EXTENSIONS
from .cli import CLI
from .extractor import MotionPhotoExtractor
from .converter import VideoConverter
from .analyzer import FileAnalyzer

class MotionPhotoProcessor:    
    def __init__(self) -> None:
        self.cli = CLI()
        self.extractor = MotionPhotoExtractor()
        self.converter = VideoConverter()
        self.analyzer = FileAnalyzer()
    
    def run(self, args: Optional[List[str]] = None) -> int:
        try:
            config = self.cli.parse_args(args)
            
            if not self.cli.validate_config(config):
                return 1

            if config.analyze_only:
                return self._analyze_file(config)

            if config.batch_mode:
                return self._process_batch(config)

            return self._process_single_file(config)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
        finally:
            self._cleanup()
    
    def _analyze_file(self, config: ExtractionConfig) -> int:
        input_path = Path(config.input_path)
        
        print(f"Analyzing: {input_path}")
        analysis = self.analyzer.analyze_jpg_structure(input_path)
        self.analyzer.print_summary(analysis)
        
        return 0
    
    def _process_single_file(self, config: ExtractionConfig) -> int:
        input_path = Path(config.input_path)
        
        print(f"Processing: {input_path}")
        
        if not self.extractor.validate_input_file(input_path):
            return 1
        
        mp4_start, mp4_size = self.extractor.find_mp4_in_jpg(input_path)
        if mp4_start is None or mp4_size is None:
            print("✗ No embedded MP4 video found in this JPG")
            print("  This might not be a Google Motion Photo, or the format is different")
            return 1
        
        try:
            temp_mp4_path = self.extractor.extract_mp4_data(input_path, mp4_start, mp4_size)
        except Exception as e:
            print(f"✗ Failed to extract MP4 data: {e}")
            return 1
        
        success = True
        
        if config.output_format in ['mp4', 'both']:
            mp4_output = self._get_output_path(input_path, config.output_path, '.mp4')
            if not self.extractor.save_mp4_final(temp_mp4_path, mp4_output):
                success = False
        
        if config.output_format in ['gif', 'both']:
            gif_output = self._get_output_path(input_path, config.output_path, '.gif')
            
            # Use temp MP4 for conversion (or final MP4 if it was saved)
            mp4_source = temp_mp4_path
            if config.output_format == 'both':
                mp4_source = self._get_output_path(input_path, config.output_path, '.mp4')
            
            if not self.converter.convert_with_fallback(
                mp4_source, gif_output, 
                width=config.gif_width, 
                quality=config.gif_quality,
                gif_loop=config.gif_loop
            ):
                success = False
        
        return 0 if success else 1
    
    def _process_batch(self, config: ExtractionConfig) -> int:
        """Process multiple files in batch mode"""
        input_dir = Path(config.input_path)
        
        jpg_files: List[Path] = []
        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            jpg_files.extend(input_dir.glob(f'*{ext}'))
            jpg_files.extend(input_dir.glob(f'*{ext.upper()}'))
        
        # Remove duplicates that can occur on case-insensitive filesystems
        jpg_files = list(set(jpg_files))
        
        if not jpg_files:
            print(f"No JPG files found in {input_dir}")
            return 1
        
        output_dir = None
        if config.batch_output_dir:
            output_dir = Path(config.batch_output_dir)
            output_dir.mkdir(exist_ok=True)
        
        print(f"Found {len(jpg_files)} JPG files to process")
        
        success_count = 0
        for i, jpg_file in enumerate(jpg_files, 1):
            print(f"\n[{i}/{len(jpg_files)}] Processing: {jpg_file.name}")
            
            file_config = ExtractionConfig(
                input_path=str(jpg_file),
                output_path=None,  # Will be auto-generated
                output_format=config.output_format,
                gif_quality=config.gif_quality,
                gif_width=config.gif_width,
                batch_mode=False,  # Process as single file
                batch_output_dir=str(output_dir) if output_dir else None
            )
            
            if output_dir:
                if config.output_format == 'gif':
                    file_config.output_path = str(output_dir / jpg_file.with_suffix('.gif').name)
                else:
                    file_config.output_path = str(output_dir / jpg_file.with_suffix('.mp4').name)
            
            if self._process_single_file(file_config) == 0:
                success_count += 1
        
        print(f"\nBatch processing complete: {success_count}/{len(jpg_files)} files processed successfully")
        return 0 if success_count > 0 else 1
    
    def _get_output_path(self, input_path: Path, output_path: Optional[str], default_ext: str) -> Path:
        """Get the output path for a file"""
        if output_path:
            return Path(output_path)
        
        return input_path.with_suffix(default_ext)
    
    def _cleanup(self) -> None:
        """Clean up temporary files"""
        self.extractor.cleanup_temp_files()
        self.converter.cleanup_temp_files()

def main() -> None:
    """Main entry point"""
    processor = MotionPhotoProcessor()
    exit_code = processor.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()