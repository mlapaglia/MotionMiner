#!/usr/bin/env python3
"""
Unit tests for config.py module
"""

import pytest
from motionminer.config import (
    GifQualitySettings, 
    ExtractionConfig, 
    GIF_QUALITY_PRESETS,
    DEFAULT_GIF_WIDTH,
    DEFAULT_GIF_QUALITY,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    JPEG_END_MARKER,
    MP4_FTYP_MARKER,
    MOTION_PHOTO_MARKERS
)

class TestGifQualitySettings:
    """Test GifQualitySettings dataclass"""
    
    def test_gif_quality_settings_creation(self):
        """Test creating GifQualitySettings instance"""
        settings = GifQualitySettings(
            colors=128,
            dither='floyd_steinberg',
            fps_multiplier=1.0,
            description='Test quality',
            estimated_size='~2MB'
        )
        
        assert settings.colors == 128
        assert settings.dither == 'floyd_steinberg'
        assert settings.fps_multiplier == 1.0
        assert settings.description == 'Test quality'
        assert settings.estimated_size == '~2MB'
    
    def test_gif_quality_presets_exist(self):
        """Test that all expected quality presets exist"""
        expected_presets = ['tiny', 'low', 'medium', 'high']
        
        for preset in expected_presets:
            assert preset in GIF_QUALITY_PRESETS
            assert isinstance(GIF_QUALITY_PRESETS[preset], GifQualitySettings)
    
    def test_quality_presets_have_valid_values(self):
        """Test that quality presets have valid values"""
        for preset_name, preset in GIF_QUALITY_PRESETS.items():
            assert preset.colors > 0
            assert preset.colors <= 256
            assert preset.fps_multiplier > 0
            assert preset.fps_multiplier <= 1.0
            assert isinstance(preset.description, str)
            assert isinstance(preset.estimated_size, str)
            assert preset.dither in ['floyd_steinberg', 'bayer:bayer_scale=1', 'bayer:bayer_scale=2']
    
    def test_quality_presets_ordering(self):
        """Test that quality presets are ordered correctly by colors"""
        presets = ['tiny', 'low', 'medium', 'high']
        colors = [GIF_QUALITY_PRESETS[p].colors for p in presets]
        
        assert colors == sorted(colors)  # Should be in ascending order

class TestExtractionConfig:
    """Test ExtractionConfig dataclass"""
    
    def test_extraction_config_creation_minimal(self):
        """Test creating ExtractionConfig with minimal parameters"""
        config = ExtractionConfig(input_path='test.jpg')
        
        assert config.input_path == 'test.jpg'
        assert config.output_path is None
        assert config.output_format == 'mp4'
        assert config.gif_quality == 'medium'
        assert config.gif_width == 480
        assert config.analyze_only is False
        assert config.batch_mode is False
        assert config.batch_output_dir is None
    
    def test_extraction_config_creation_full(self):
        """Test creating ExtractionConfig with all parameters"""
        config = ExtractionConfig(
            input_path='input.jpg',
            output_path='output.mp4',
            output_format='gif',
            gif_quality='high',
            gif_width=640,
            analyze_only=True,
            batch_mode=True,
            batch_output_dir='output_dir'
        )
        
        assert config.input_path == 'input.jpg'
        assert config.output_path == 'output.mp4'
        assert config.output_format == 'gif'
        assert config.gif_quality == 'high'
        assert config.gif_width == 640
        assert config.analyze_only is True
        assert config.batch_mode is True
        assert config.batch_output_dir == 'output_dir'

class TestConstants:
    """Test module constants"""
    
    def test_default_values(self):
        """Test default configuration values"""
        assert DEFAULT_GIF_WIDTH == 480
        assert DEFAULT_GIF_QUALITY == 'medium'
        assert DEFAULT_GIF_QUALITY in GIF_QUALITY_PRESETS
    
    def test_supported_extensions(self):
        """Test supported file extensions"""
        assert '.jpg' in SUPPORTED_IMAGE_EXTENSIONS
        assert '.jpeg' in SUPPORTED_IMAGE_EXTENSIONS
        assert len(SUPPORTED_IMAGE_EXTENSIONS) >= 2
        
        assert '.mp4' in SUPPORTED_VIDEO_EXTENSIONS
        assert len(SUPPORTED_VIDEO_EXTENSIONS) >= 1
    
    def test_file_markers(self):
        """Test file format markers"""
        assert JPEG_END_MARKER == b'\xff\xd9'
        assert MP4_FTYP_MARKER == b'ftyp'
        assert isinstance(MOTION_PHOTO_MARKERS, list)
        assert len(MOTION_PHOTO_MARKERS) >= 1
        
        # Check that motion photo markers are bytes
        for marker in MOTION_PHOTO_MARKERS:
            assert isinstance(marker, bytes)

class TestConfigValidation:
    """Test configuration validation logic"""
    
    def test_valid_output_formats(self):
        """Test valid output formats"""
        valid_formats = ['mp4', 'gif', 'both']
        
        for fmt in valid_formats:
            config = ExtractionConfig(input_path='test.jpg', output_format=fmt)
            assert config.output_format == fmt
    
    def test_valid_gif_qualities(self):
        """Test valid GIF qualities"""
        for quality in GIF_QUALITY_PRESETS.keys():
            config = ExtractionConfig(input_path='test.jpg', gif_quality=quality)
            assert config.gif_quality == quality
    
    def test_gif_width_bounds(self):
        """Test GIF width boundary values"""
        # Test minimum reasonable width
        config = ExtractionConfig(input_path='test.jpg', gif_width=100)
        assert config.gif_width == 100
        
        # Test maximum reasonable width
        config = ExtractionConfig(input_path='test.jpg', gif_width=1920)
        assert config.gif_width == 1920 