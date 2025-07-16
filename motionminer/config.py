#!/usr/bin/env python3
"""
Configuration and settings for Google Motion Photo Extractor
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class GifQualitySettings:
    """Settings for different GIF quality levels"""
    colors: int
    dither: str
    fps_multiplier: float
    description: str
    estimated_size: str

# GIF Quality presets
GIF_QUALITY_PRESETS = {
    'tiny': GifQualitySettings(
        colors=64,
        dither='bayer:bayer_scale=2',
        fps_multiplier=0.8,
        description='Maximum compression',
        estimated_size='~1-2MB'
    ),
    'low': GifQualitySettings(
        colors=128,
        dither='bayer:bayer_scale=1',
        fps_multiplier=0.9,
        description='Heavy compression but decent quality',
        estimated_size='~2-3MB'
    ),
    'medium': GifQualitySettings(
        colors=192,
        dither='floyd_steinberg',
        fps_multiplier=1.0,
        description='Balanced quality and size',
        estimated_size='~3-4MB'
    ),
    'high': GifQualitySettings(
        colors=256,
        dither='floyd_steinberg',
        fps_multiplier=1.0,
        description='Best quality',
        estimated_size='~5-7MB'
    )
}

@dataclass
class ExtractionConfig:
    """Configuration for extraction process"""
    input_path: str
    output_path: Optional[str] = None
    output_format: str = 'mp4'
    gif_quality: str = 'medium'
    gif_width: int = 480
    gif_loop: bool = True
    analyze_only: bool = False
    batch_mode: bool = False
    batch_output_dir: Optional[str] = None

# Default settings
DEFAULT_GIF_WIDTH = 480
DEFAULT_GIF_QUALITY = 'medium'
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg']
SUPPORTED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']

# File signatures for motion photo detection
JPEG_END_MARKER = b'\xff\xd9'
MP4_FTYP_MARKER = b'ftyp'
MOTION_PHOTO_MARKERS = [b'GCamera', b'MotionPhoto', b'Google']