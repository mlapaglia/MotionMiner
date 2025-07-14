#!/usr/bin/env python3
"""
MotionMiner - Extract videos from Google Motion Photos with ease!

A powerful Python tool that extracts embedded MP4 videos from Google Motion Photos (JPG files) 
and converts them to various formats including MP4 and GIF animations.
"""

from ._version import __version__
__author__ = "MotionMiner Team"
__email__ = "contact@motionminer.dev"
__description__ = "Extract videos from Google Motion Photos with ease!"
__url__ = "https://github.com/yourusername/motionminer"

# Main imports for the package
from .extractor import MotionPhotoExtractor
from .converter import VideoConverter
from .analyzer import FileAnalyzer
from .config import ExtractionConfig, GIF_QUALITY_PRESETS
from .cli import CLI

# Main entry point class
from .main import MotionPhotoProcessor

__all__ = [
    'MotionPhotoExtractor',
    'VideoConverter', 
    'FileAnalyzer',
    'ExtractionConfig',
    'GIF_QUALITY_PRESETS',
    'CLI',
    'MotionPhotoProcessor'
] 