#!/usr/bin/env python3
"""
Unit tests for cli.py module
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from motionminer.cli import CLI
from motionminer.config import ExtractionConfig, GIF_QUALITY_PRESETS

class TestCLI:
    """Test CLI class functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.cli = CLI()
    
    def test_cli_initialization(self):
        """Test CLI initialization"""
        assert self.cli.parser is not None
        assert hasattr(self.cli, 'parser')
    
    def test_parse_args_minimal(self):
        """Test parsing minimal arguments"""
        args = ['test.jpg']
        config = self.cli.parse_args(args)
        
        assert isinstance(config, ExtractionConfig)
        assert config.input_path == 'test.jpg'
        assert config.output_path is None
        assert config.output_format == 'mp4'
        assert config.gif_quality == 'medium'
        assert config.gif_width == 480
        assert config.analyze_only is False
        assert config.batch_mode is False
        assert config.batch_output_dir is None
    
    def test_parse_args_with_output(self):
        """Test parsing arguments with output path"""
        args = ['test.jpg', '-o', 'output.mp4']
        config = self.cli.parse_args(args)
        
        assert config.input_path == 'test.jpg'
        assert config.output_path == 'output.mp4'
        assert config.output_format == 'mp4'  # Should remain mp4

    def test_parse_args_photo_without_path(self):
        """Test --photo flag without optional PATH argument"""
        for args in (
            ['test.jpg', '--photo'],
            ['test.jpg', '-p'],
        ):
            config = self.cli.parse_args(args)

            assert config.output_photo is True
            assert config.output_photo_path is None

    def test_parse_args_photo_with_path(self):
        """Test --photo flag with optional PATH argument"""
        for args in (
            ['test.jpg', '--photo', 'output.jpg'],
            ['test.jpg', '-p', 'output.jpg'],
        ):
            config = self.cli.parse_args(args)

            assert config.output_photo is True
            assert config.output_photo_path == 'output.jpg'
    
    def test_parse_args_gif_output_format_detection(self):
        """Test automatic GIF format detection from output extension"""
        args = ['test.jpg', '-o', 'output.gif']
        config = self.cli.parse_args(args)
        
        assert config.output_format == 'gif'
    
    def test_parse_args_gif_flag(self):
        """Test --gif flag"""
        args = ['test.jpg', '--gif']
        config = self.cli.parse_args(args)
        
        assert config.output_format == 'gif'
    
    def test_parse_args_both_flag(self):
        """Test --both flag"""
        args = ['test.jpg', '--both']
        config = self.cli.parse_args(args)
        
        assert config.output_format == 'both'
    
    def test_parse_args_gif_quality_flags(self):
        """Test GIF quality flags"""
        quality_flags = [
            ('--gif-tiny', 'tiny'),
            ('--gif-low', 'low'),
            ('--gif-medium', 'medium'),
            ('--gif-high', 'high')
        ]
        
        for flag, expected_quality in quality_flags:
            args = ['test.jpg', flag]
            config = self.cli.parse_args(args)
            
            assert config.output_format == 'gif'
            assert config.gif_quality == expected_quality
    
    def test_parse_args_gif_width(self):
        """Test --gif-width argument"""
        args = ['test.jpg', '--gif-width', '640']
        config = self.cli.parse_args(args)
        
        assert config.gif_width == 640
    
    def test_parse_args_gif_loop_default(self):
        """Test default GIF loop behavior (should loop infinitely)"""
        args = ['test.jpg', '--gif']
        config = self.cli.parse_args(args)
        
        assert config.gif_loop is True
    
    def test_parse_args_gif_no_loop_flag(self):
        """Test --gif-no-loop flag"""
        args = ['test.jpg', '--gif', '--gif-no-loop']
        config = self.cli.parse_args(args)
        
        assert config.gif_loop is False
    
    def test_parse_args_gif_no_loop_with_quality(self):
        """Test --gif-no-loop with quality flags"""
        args = ['test.jpg', '--gif-high', '--gif-no-loop']
        config = self.cli.parse_args(args)
        
        assert config.gif_loop is False
        assert config.gif_quality == 'high'
        assert config.output_format == 'gif'
    
    def test_parse_args_batch_mode(self):
        """Test --batch flag"""
        args = ['photos/', '--batch']
        config = self.cli.parse_args(args)
        
        assert config.batch_mode is True
        assert config.input_path == 'photos/'
    
    def test_parse_args_batch_output(self):
        """Test --batch-output argument"""
        args = ['photos/', '--batch', '--batch-output', 'output_dir']
        config = self.cli.parse_args(args)
        
        assert config.batch_mode is True
        assert config.batch_output_dir == 'output_dir'
    
    def test_parse_args_analyze_flag(self):
        """Test --analyze flag"""
        args = ['test.jpg', '--analyze']
        config = self.cli.parse_args(args)
        
        assert config.analyze_only is True
    
    def test_parse_args_mutually_exclusive_format_flags(self):
        """Test that format flags are mutually exclusive"""
        # These should raise SystemExit due to argument conflicts
        with pytest.raises(SystemExit):
            self.cli.parse_args(['test.jpg', '--gif', '--mp4'])
        
        with pytest.raises(SystemExit):
            self.cli.parse_args(['test.jpg', '--gif', '--both'])
    
    def test_parse_args_mutually_exclusive_quality_flags(self):
        """Test that quality flags are mutually exclusive"""
        with pytest.raises(SystemExit):
            self.cli.parse_args(['test.jpg', '--gif-tiny', '--gif-high'])
    
    def test_parse_args_invalid_gif_width(self):
        """Test invalid GIF width (non-integer)"""
        with pytest.raises(SystemExit):
            self.cli.parse_args(['test.jpg', '--gif-width', 'invalid'])
    
    def test_parse_args_help_flag(self):
        """Test --help flag"""
        with pytest.raises(SystemExit):
            self.cli.parse_args(['--help'])
    
    def test_print_help(self):
        """Test print_help method"""
        with patch('sys.stdout.write') as mock_write:
            self.cli.print_help()
            mock_write.assert_called()
    
    def test_print_quality_info(self):
        """Test print_quality_info method"""
        with patch('builtins.print') as mock_print:
            self.cli.print_quality_info()
            mock_print.assert_called()
            
            # Check that quality information is printed
            call_args = [call[0][0] if call[0] else '' for call in mock_print.call_args_list]
            printed_text = ' '.join(call_args)
            
            assert 'GIF Quality Presets' in printed_text
            for quality in GIF_QUALITY_PRESETS.keys():
                assert quality.upper() in printed_text

class TestCLIValidation:
    """Test CLI validation functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.cli = CLI()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / 'test.jpg'
        self.temp_file.touch()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_config_valid_file(self):
        """Test validation with valid file"""
        config = ExtractionConfig(input_path=str(self.temp_file))
        
        assert self.cli.validate_config(config) is True
    
    def test_validate_config_nonexistent_file(self):
        """Test validation with nonexistent file"""
        config = ExtractionConfig(input_path='nonexistent.jpg')
        
        with patch('builtins.print') as mock_print:
            assert self.cli.validate_config(config) is False
            mock_print.assert_called()
    
    def test_validate_config_batch_mode_with_file(self):
        """Test validation of batch mode with file instead of directory"""
        config = ExtractionConfig(
            input_path=str(self.temp_file),
            batch_mode=True
        )
        
        with patch('builtins.print') as mock_print:
            assert self.cli.validate_config(config) is False
            mock_print.assert_called()
    
    def test_validate_config_batch_mode_with_directory(self):
        """Test validation of batch mode with directory"""
        config = ExtractionConfig(
            input_path=str(self.temp_dir),
            batch_mode=True
        )
        
        assert self.cli.validate_config(config) is True
    
    def test_validate_config_single_mode_with_directory(self):
        """Test validation of single mode with directory"""
        config = ExtractionConfig(
            input_path=str(self.temp_dir),
            batch_mode=False
        )
        
        with patch('builtins.print') as mock_print:
            assert self.cli.validate_config(config) is False
            mock_print.assert_called()
    
    def test_validate_config_invalid_gif_quality(self):
        """Test validation with invalid GIF quality"""
        config = ExtractionConfig(
            input_path=str(self.temp_file),
            gif_quality='invalid'
        )
        
        with patch('builtins.print') as mock_print:
            assert self.cli.validate_config(config) is False
            mock_print.assert_called()
    
    def test_validate_config_invalid_gif_width(self):
        """Test validation with invalid GIF width"""
        config = ExtractionConfig(
            input_path=str(self.temp_file),
            gif_width=0
        )
        
        with patch('builtins.print') as mock_print:
            assert self.cli.validate_config(config) is False
            mock_print.assert_called()
        
        config = ExtractionConfig(
            input_path=str(self.temp_file),
            gif_width=-100
        )
        
        with patch('builtins.print') as mock_print:
            assert self.cli.validate_config(config) is False
            mock_print.assert_called()

class TestCLIExamples:
    """Test CLI with real-world example arguments"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.cli = CLI()
    
    def test_example_basic_extraction(self):
        """Test: python main.py photo.jpg"""
        args = ['photo.jpg']
        config = self.cli.parse_args(args)
        
        assert config.input_path == 'photo.jpg'
        assert config.output_format == 'mp4'
    
    def test_example_gif_extraction(self):
        """Test: python main.py photo.jpg --gif"""
        args = ['photo.jpg', '--gif']
        config = self.cli.parse_args(args)
        
        assert config.output_format == 'gif'
    
    def test_example_both_extraction(self):
        """Test: python main.py photo.jpg --both"""
        args = ['photo.jpg', '--both']
        config = self.cli.parse_args(args)
        
        assert config.output_format == 'both'
    
    def test_example_custom_output(self):
        """Test: python main.py photo.jpg -o my_video.mp4"""
        args = ['photo.jpg', '-o', 'my_video.mp4']
        config = self.cli.parse_args(args)
        
        assert config.output_path == 'my_video.mp4'
    
    def test_example_batch_processing(self):
        """Test: python main.py photos/ --batch"""
        args = ['photos/', '--batch']
        config = self.cli.parse_args(args)
        
        assert config.batch_mode is True
        assert config.input_path == 'photos/'
    
    def test_example_analyze_mode(self):
        """Test: python main.py photo.jpg --analyze"""
        args = ['photo.jpg', '--analyze']
        config = self.cli.parse_args(args)
        
        assert config.analyze_only is True
    
    def test_example_quality_presets(self):
        """Test various quality preset examples"""
        quality_examples = [
            (['photo.jpg', '--gif-tiny'], 'tiny'),
            (['photo.jpg', '--gif-low'], 'low'),
            (['photo.jpg', '--gif-medium'], 'medium'),
            (['photo.jpg', '--gif-high'], 'high'),
        ]
        
        for args, expected_quality in quality_examples:
            config = self.cli.parse_args(args)
            assert config.gif_quality == expected_quality
            assert config.output_format == 'gif' 