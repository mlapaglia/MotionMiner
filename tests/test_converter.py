#!/usr/bin/env python3
"""
Unit tests for converter.py module
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import subprocess

from motionminer.converter import VideoConverter
from motionminer.config import GIF_QUALITY_PRESETS, DEFAULT_GIF_WIDTH

class TestVideoConverter:
    """Test VideoConverter class functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.converter = VideoConverter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.converter.cleanup_temp_files()
    
    def test_converter_initialization(self):
        """Test converter initialization"""
        assert isinstance(self.converter.temp_files, list)
        assert len(self.converter.temp_files) == 0
    
    def test_get_video_fps_success(self):
        """Test successful FPS detection"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        # Mock successful ffprobe output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "30/1"
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            fps = self.converter.get_video_fps(video_path)
            
            assert fps == 30.0
            mock_run.assert_called_once()
            
            # Check ffprobe command
            call_args = mock_run.call_args[0][0]
            assert 'ffprobe' in call_args
            assert str(video_path) in call_args
    
    def test_get_video_fps_fractional(self):
        """Test FPS detection with fractional frame rate"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        # Mock fractional FPS (29.97)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "30000/1001"
        
        with patch('subprocess.run', return_value=mock_result):
            fps = self.converter.get_video_fps(video_path)
            
            assert abs(fps - 29.97) < 0.01  # Should be approximately 29.97
    
    def test_get_video_fps_simple_float(self):
        """Test FPS detection with simple float value"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "25.0"
        
        with patch('subprocess.run', return_value=mock_result):
            fps = self.converter.get_video_fps(video_path)
            
            assert fps == 25.0
    
    def test_get_video_fps_high_framerate_warning(self):
        """Test FPS detection with high frame rate warning (>60 FPS)"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        # Mock avg_frame_rate failing, r_frame_rate returning high FPS
        mock_results = [
            MagicMock(returncode=0, stdout="0/0"),  # avg_frame_rate returns 0/0
            MagicMock(returncode=0, stdout="120.0")  # r_frame_rate returns 120 FPS
        ]
        
        with patch('subprocess.run', side_effect=mock_results):
            with patch('builtins.print') as mock_print:
                fps = self.converter.get_video_fps(video_path)
                
                assert fps == 30.0  # Should be capped at 30 FPS
                mock_print.assert_called_with("Warning: Very high frame rate detected (120.0 FPS), using 30 FPS instead")
    
    def test_get_video_fps_high_framerate_fractional_warning(self):
        """Test FPS detection with high fractional frame rate warning (>60 FPS)"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        # Mock avg_frame_rate failing, r_frame_rate returning high fractional FPS
        mock_results = [
            MagicMock(returncode=0, stdout=""),  # avg_frame_rate empty
            MagicMock(returncode=0, stdout="7200/100")  # r_frame_rate returns 72 FPS
        ]
        
        with patch('subprocess.run', side_effect=mock_results):
            with patch('builtins.print') as mock_print:
                fps = self.converter.get_video_fps(video_path)
                
                assert fps == 30.0  # Should be capped at 30 FPS
                mock_print.assert_called_with("Warning: Very high frame rate detected (72.0 FPS), using 30 FPS instead")
    
    def test_get_video_fps_fallback_to_r_frame_rate(self):
        """Test FPS detection fallback to r_frame_rate when avg_frame_rate fails"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        # Mock avg_frame_rate failing, r_frame_rate succeeding
        mock_results = [
            MagicMock(returncode=0, stdout="0/0"),  # avg_frame_rate returns 0/0
            MagicMock(returncode=0, stdout="24/1")  # r_frame_rate returns 24 FPS
        ]
        
        with patch('subprocess.run', side_effect=mock_results):
            fps = self.converter.get_video_fps(video_path)
            
            assert fps == 24.0
    
    def test_get_video_fps_fallback_r_frame_rate_high_fps(self):
        """Test FPS detection fallback with high r_frame_rate"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        # Mock avg_frame_rate failing, r_frame_rate returning high FPS
        mock_results = [
            MagicMock(returncode=0, stdout=""),  # avg_frame_rate empty
            MagicMock(returncode=0, stdout="9000/100")  # r_frame_rate returns 90 FPS
        ]
        
        with patch('subprocess.run', side_effect=mock_results):
            with patch('builtins.print') as mock_print:
                fps = self.converter.get_video_fps(video_path)
                
                assert fps == 30.0  # Should be capped at 30 FPS
                mock_print.assert_called_with("Warning: Very high frame rate detected (90.0 FPS), using 30 FPS instead")
    
    def test_get_video_fps_fallback_both_fail(self):
        """Test FPS detection when both avg_frame_rate and r_frame_rate fail"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        # Mock both failing
        mock_results = [
            MagicMock(returncode=0, stdout="0/0"),  # avg_frame_rate returns 0/0
            MagicMock(returncode=0, stdout="0/0")   # r_frame_rate also returns 0/0
        ]
        
        with patch('subprocess.run', side_effect=mock_results):
            with patch('builtins.print') as mock_print:
                fps = self.converter.get_video_fps(video_path)
                
                assert fps == 30.0  # Should default to 30 FPS
                mock_print.assert_called_with("Warning: Could not detect valid FPS, using default 30 FPS")
    
    def test_get_video_fps_zero_denominator(self):
        """Test FPS detection with zero denominator in fraction"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "30/0"  # Zero denominator
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('builtins.print') as mock_print:
                fps = self.converter.get_video_fps(video_path)
                
                assert fps == 30.0  # Should default to 30 FPS
    
    def test_get_video_fps_ffprobe_error(self):
        """Test FPS detection with ffprobe error"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('builtins.print') as mock_print:
                fps = self.converter.get_video_fps(video_path)
                
                assert fps == 30.0  # Should default to 30 FPS
                mock_print.assert_called()
    
    def test_get_video_fps_exception(self):
        """Test FPS detection with exception"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        with patch('subprocess.run', side_effect=Exception("Command failed")):
            with patch('builtins.print') as mock_print:
                fps = self.converter.get_video_fps(video_path)
                
                assert fps == 30.0  # Should default to 30 FPS
                mock_print.assert_called()
    
    def test_get_video_fps_empty_output(self):
        """Test FPS detection with empty output"""
        video_path = Path(self.temp_dir) / 'test.mp4'
        video_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('builtins.print') as mock_print:
                fps = self.converter.get_video_fps(video_path)
                
                assert fps == 30.0  # Should default to 30 FPS
                mock_print.assert_called()
    
    def test_cleanup_empty_file_removes_empty_file(self):
        """Test _cleanup_empty_file removes empty files"""
        empty_file = Path(self.temp_dir) / 'empty.gif'
        empty_file.touch()  # Create empty file
        
        with patch('builtins.print') as mock_print:
            self.converter._cleanup_empty_file(empty_file)
            
            assert not empty_file.exists()
            mock_print.assert_called_with(f"Removed empty file: {empty_file}")
    
    def test_cleanup_empty_file_keeps_nonempty_file(self):
        """Test _cleanup_empty_file keeps non-empty files"""
        nonempty_file = Path(self.temp_dir) / 'nonempty.gif'
        nonempty_file.write_bytes(b'GIF89a content')
        
        self.converter._cleanup_empty_file(nonempty_file)
        
        assert nonempty_file.exists()
        assert nonempty_file.stat().st_size > 0
    
    def test_cleanup_empty_file_nonexistent(self):
        """Test _cleanup_empty_file with nonexistent file"""
        nonexistent_file = Path(self.temp_dir) / 'nonexistent.gif'
        
        # Should not raise error
        self.converter._cleanup_empty_file(nonexistent_file)
    
    def test_cleanup_empty_file_exception(self):
        """Test _cleanup_empty_file with exception during size check"""
        test_file = Path(self.temp_dir) / 'test.gif'
        test_file.touch()
        
        with patch('os.path.getsize', side_effect=OSError("Access denied")):
            with patch('builtins.print') as mock_print:
                self.converter._cleanup_empty_file(test_file)
                
                mock_print.assert_called()
                assert "Warning: Could not check/remove empty file" in str(mock_print.call_args)
    
    def test_convert_mp4_to_gif_success(self):
        """Test successful MP4 to GIF conversion"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        # Mock successful ffmpeg calls
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            with patch('builtins.print') as mock_print:
                with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                    # Create the output GIF file to simulate successful conversion
                    gif_path.write_bytes(b'GIF89a fake gif content')
                    
                    result = self.converter.convert_mp4_to_gif(mp4_path, gif_path)
                    
                    assert result is True
                    assert gif_path.exists()
                    
                    # Should have called ffmpeg twice (palette generation + GIF creation)
                    assert mock_run.call_count == 2
                    
                    # Check palette generation call
                    first_call = mock_run.call_args_list[0][0][0]
                    assert 'ffmpeg' in first_call
                    assert 'palettegen' in ' '.join(first_call)
                    
                    # Check GIF creation call
                    second_call = mock_run.call_args_list[1][0][0]
                    assert 'ffmpeg' in second_call
                    assert 'paletteuse' in ' '.join(second_call)
    
    def test_convert_mp4_to_gif_custom_settings(self):
        """Test GIF conversion with custom settings"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            with patch('builtins.print'):
                with patch.object(self.converter, 'get_video_fps', return_value=24.0):
                    gif_path.write_bytes(b'GIF89a fake gif content')
                    
                    result = self.converter.convert_mp4_to_gif(
                        mp4_path, gif_path, 
                        fps=24.0, 
                        width=640, 
                        quality='high'
                    )
                    
                    assert result is True
                    
                    # Check that settings were applied
                    second_call = mock_run.call_args_list[1][0][0]
                    command_str = ' '.join(second_call)
                    assert 'scale=640:-1' in command_str
                    assert 'fps=24' in command_str
    
    def test_convert_mp4_to_gif_invalid_quality(self):
        """Test GIF conversion with invalid quality"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('builtins.print') as mock_print:
                with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                    gif_path.write_bytes(b'GIF89a fake gif content')
                    
                    result = self.converter.convert_mp4_to_gif(
                        mp4_path, gif_path, 
                        quality='invalid'
                    )
                    
                    assert result is True
                    # Should print warning about invalid quality
                    mock_print.assert_called()
    
    def test_convert_mp4_to_gif_palette_generation_fails(self):
        """Test GIF conversion when palette generation fails"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        # Mock palette generation failure
        mock_result_fail = MagicMock()
        mock_result_fail.returncode = 1
        mock_result_fail.stderr = "Palette generation failed"
        
        with patch('subprocess.run', return_value=mock_result_fail):
            with patch('builtins.print') as mock_print:
                with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                    result = self.converter.convert_mp4_to_gif(mp4_path, gif_path)
                    
                    assert result is False
                    mock_print.assert_called()
    
    def test_convert_mp4_to_gif_creation_fails(self):
        """Test GIF conversion when GIF creation fails"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        # Mock successful palette generation, failed GIF creation
        mock_results = [
            MagicMock(returncode=0),  # Palette generation success
            MagicMock(returncode=1, stderr="GIF creation failed")  # GIF creation failure
        ]
        
        with patch('subprocess.run', side_effect=mock_results):
            with patch('builtins.print') as mock_print:
                with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                    result = self.converter.convert_mp4_to_gif(mp4_path, gif_path)
                    
                    assert result is False
                    mock_print.assert_called()
    
    def test_convert_mp4_to_gif_no_output_file(self):
        """Test GIF conversion when output file is not created"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('builtins.print') as mock_print:
                with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                    # Don't create output file
                    result = self.converter.convert_mp4_to_gif(mp4_path, gif_path)
                    
                    assert result is False
                    mock_print.assert_called()
    
    def test_convert_mp4_to_gif_exception(self):
        """Test GIF conversion with exception"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        with patch('subprocess.run', side_effect=Exception("Command failed")):
            with patch('builtins.print') as mock_print:
                with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                    result = self.converter.convert_mp4_to_gif(mp4_path, gif_path)
                    
                    assert result is False
                    mock_print.assert_called()
    
    def test_convert_with_fallback_success_first_attempt(self):
        """Test convert_with_fallback succeeds on first attempt"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        with patch.object(self.converter, 'convert_mp4_to_gif', return_value=True):
            with patch.object(self.converter, '_cleanup_empty_file') as mock_cleanup:
                result = self.converter.convert_with_fallback(mp4_path, gif_path)
                
                assert result is True
                mock_cleanup.assert_called_once_with(gif_path)
    
    def test_convert_with_fallback_success_second_attempt(self):
        """Test convert_with_fallback succeeds on fallback attempt"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        # Mock first attempt failure, second attempt success
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch.object(self.converter, 'convert_mp4_to_gif', return_value=False):
            with patch('subprocess.run', return_value=mock_result):
                with patch('builtins.print') as mock_print:
                    with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                        # Create output file with content to simulate success
                        gif_path.write_bytes(b'GIF89a fake gif content')
                        
                        result = self.converter.convert_with_fallback(mp4_path, gif_path)
                        
                        assert result is True
                        mock_print.assert_called()
    
    def test_convert_with_fallback_simple_conversion_empty_file(self):
        """Test convert_with_fallback when simple conversion creates empty file"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch.object(self.converter, 'convert_mp4_to_gif', return_value=False):
            with patch('subprocess.run', return_value=mock_result):
                with patch('builtins.print') as mock_print:
                    with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                        with patch.object(self.converter, '_cleanup_empty_file') as mock_cleanup:
                            # Create empty output file
                            gif_path.touch()
                            
                            result = self.converter.convert_with_fallback(mp4_path, gif_path)
                            
                            assert result is False
                            mock_print.assert_called()
                            mock_cleanup.assert_called()
    
    def test_convert_with_fallback_both_attempts_fail(self):
        """Test convert_with_fallback when both attempts fail"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        # Mock both attempts failing
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Command failed"
        
        with patch.object(self.converter, 'convert_mp4_to_gif', return_value=False):
            with patch('subprocess.run', return_value=mock_result):
                with patch('builtins.print') as mock_print:
                    with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                        with patch.object(self.converter, '_cleanup_empty_file') as mock_cleanup:
                            result = self.converter.convert_with_fallback(mp4_path, gif_path)
                            
                            assert result is False
                            mock_print.assert_called()
                            mock_cleanup.assert_called()
    
    def test_convert_with_fallback_exception(self):
        """Test convert_with_fallback with exception in fallback"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        with patch.object(self.converter, 'convert_mp4_to_gif', return_value=False):
            with patch('subprocess.run', side_effect=Exception("Command failed")):
                with patch('builtins.print') as mock_print:
                    with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                        with patch.object(self.converter, '_cleanup_empty_file') as mock_cleanup:
                            result = self.converter.convert_with_fallback(mp4_path, gif_path)
                            
                            assert result is False
                            mock_print.assert_called()
                            mock_cleanup.assert_called()
    
    def test_cleanup_temp_files_success(self):
        """Test successful cleanup of temporary files"""
        temp_files = []
        for i in range(3):
            temp_file = Path(self.temp_dir) / f'temp_{i}.png'
            temp_file.touch()
            temp_files.append(temp_file)
            self.converter.temp_files.append(temp_file)
        
        self.converter.cleanup_temp_files()
        
        # All temp files should be removed
        for temp_file in temp_files:
            assert not temp_file.exists()
        
        # Temp files list should be empty
        assert len(self.converter.temp_files) == 0
    
    def test_cleanup_temp_files_with_errors(self):
        """Test cleanup with file removal errors"""
        temp_file = Path(self.temp_dir) / 'temp.png'
        temp_file.touch()
        self.converter.temp_files.append(temp_file)
        
        with patch('os.remove', side_effect=OSError("Remove error")):
            with patch('builtins.print') as mock_print:
                self.converter.cleanup_temp_files()
                
                # Should handle error gracefully
                assert len(self.converter.temp_files) == 0
                mock_print.assert_called()
    
    def test_cleanup_temp_files_palette_cleanup(self):
        """Test cleanup of palette.png file"""
        palette_file = Path('palette.png')
        palette_file.touch()
        
        try:
            self.converter.cleanup_temp_files()
            
            # Palette file should be removed
            assert not palette_file.exists()
        finally:
            # Cleanup in case test fails
            if palette_file.exists():
                palette_file.unlink()
    
    def test_cleanup_temp_files_palette_error(self):
        """Test cleanup with palette file removal error"""
        palette_file = Path('palette.png')
        palette_file.touch()
        
        try:
            with patch('os.remove', side_effect=OSError("Remove error")) as mock_remove:
                with patch('builtins.print') as mock_print:
                    self.converter.cleanup_temp_files()
                    
                    # Should handle error gracefully
                    mock_print.assert_called()
        finally:
            # Cleanup in case test fails
            if palette_file.exists():
                palette_file.unlink()
    
    def test_cleanup_temp_files_nonexistent(self):
        """Test cleanup with nonexistent temp files"""
        temp_file = Path(self.temp_dir) / 'nonexistent.png'
        self.converter.temp_files.append(temp_file)
        
        # Should not raise error for nonexistent files
        self.converter.cleanup_temp_files()
        assert len(self.converter.temp_files) == 0
    
    def test_destructor_cleanup(self):
        """Test that destructor calls cleanup"""
        temp_file = Path(self.temp_dir) / 'temp.png'
        temp_file.touch()
        
        converter = VideoConverter()
        converter.temp_files.append(temp_file)
        
        # Simulate destructor call
        converter.__del__()
        
        # File should be cleaned up
        assert not temp_file.exists()

class TestVideoConverterQualitySettings:
    """Test video converter with different quality settings"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.converter = VideoConverter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.converter.cleanup_temp_files()
    
    def test_all_quality_presets(self):
        """Test conversion with all quality presets"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        mp4_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        for quality in GIF_QUALITY_PRESETS.keys():
            gif_path = Path(self.temp_dir) / f'output_{quality}.gif'
            
            with patch('subprocess.run', return_value=mock_result) as mock_run:
                with patch('builtins.print'):
                    with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                        gif_path.write_bytes(b'GIF89a fake gif content')
                        
                        result = self.converter.convert_mp4_to_gif(
                            mp4_path, gif_path, 
                            quality=quality
                        )
                        
                        assert result is True
                        
                        # Check that quality settings were applied
                        palette_call = mock_run.call_args_list[0][0][0]
                        gif_call = mock_run.call_args_list[1][0][0]
                        
                        settings = GIF_QUALITY_PRESETS[quality]
                        
                        palette_str = ' '.join(palette_call)
                        gif_str = ' '.join(gif_call)
                        
                        assert f'max_colors={settings.colors}' in palette_str
                        assert f'dither={settings.dither}' in gif_str
                        
                        # Check FPS multiplier
                        expected_fps = 30.0 * settings.fps_multiplier
                        assert f'fps={expected_fps}' in gif_str
    
    def test_gif_width_parameter(self):
        """Test GIF width parameter"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        widths = [320, 480, 640, 1280]
        
        for width in widths:
            with patch('subprocess.run', return_value=mock_result) as mock_run:
                with patch('builtins.print'):
                    with patch.object(self.converter, 'get_video_fps', return_value=30.0):
                        gif_path.write_bytes(b'GIF89a fake gif content')
                        
                        result = self.converter.convert_mp4_to_gif(
                            mp4_path, gif_path, 
                            width=width
                        )
                        
                        assert result is True
                        
                        # Check that width was applied
                        gif_call = mock_run.call_args_list[1][0][0]
                        gif_str = ' '.join(gif_call)
                        
                        assert f'scale={width}:-1' in gif_str
    
    def test_fps_parameter(self):
        """Test FPS parameter"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        fps_values = [15.0, 24.0, 30.0, 60.0]
        
        for fps in fps_values:
            with patch('subprocess.run', return_value=mock_result) as mock_run:
                with patch('builtins.print'):
                    gif_path.write_bytes(b'GIF89a fake gif content')
                    
                    result = self.converter.convert_mp4_to_gif(
                        mp4_path, gif_path, 
                        fps=fps
                    )
                    
                    assert result is True
                    
                    # Check that FPS was applied
                    gif_call = mock_run.call_args_list[1][0][0]
                    gif_str = ' '.join(gif_call)
                    
                    assert f'fps={fps}' in gif_str

class TestVideoConverterIntegration:
    """Integration tests for video converter"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.converter = VideoConverter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.converter.cleanup_temp_files()
    
    def test_full_conversion_workflow(self):
        """Test complete conversion workflow"""
        mp4_path = Path(self.temp_dir) / 'input.mp4'
        gif_path = Path(self.temp_dir) / 'output.gif'
        mp4_path.touch()
        
        # Mock all subprocess calls
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "30/1"
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            with patch('builtins.print'):
                # Create output file with content to simulate successful conversion
                gif_path.write_bytes(b'GIF89a fake gif content')
                
                result = self.converter.convert_with_fallback(
                    mp4_path, gif_path,
                    width=640,
                    quality='high'
                )
                
                assert result is True
                assert gif_path.exists()
                
                # Should have made calls for FPS detection and conversion
                assert mock_run.call_count >= 2
                
                # First call should be FPS detection
                fps_call = mock_run.call_args_list[0][0][0]
                assert 'ffprobe' in fps_call
                
                # Subsequent calls should be conversion
                conversion_calls = mock_run.call_args_list[1:]
                assert len(conversion_calls) >= 2  # Palette + GIF creation 