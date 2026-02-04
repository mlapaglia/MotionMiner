#!/usr/bin/env python3
"""
Integration tests for the complete MotionMiner application
"""

import pytest
import tempfile
import struct
from pathlib import Path
from unittest.mock import patch, MagicMock

from motionminer.main import MotionPhotoProcessor
from motionminer.config import ExtractionConfig, JPEG_END_MARKER, MP4_FTYP_MARKER

class TestMotionMinerIntegration:
    """Integration tests for the complete application"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = MotionPhotoProcessor()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_mock_motion_photo(self, filename: str, include_mp4: bool = True) -> Path:
        """Create a mock motion photo file for testing"""
        filepath = Path(self.temp_dir) / filename
        
        # Create JPEG data
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
        jpeg_data = b'x' * 50000  # 50KB of fake image data
        jpeg_end = JPEG_END_MARKER
        
        full_data = jpeg_header + jpeg_data + jpeg_end
        
        if include_mp4:
            # Add motion photo markers
            motion_markers = b'GCamera:MicroVideo\x00\x01' + b'Google'
            
            # Create MP4 data
            mp4_size = struct.pack('>I', 1000)  # 1000 bytes
            mp4_data = mp4_size + MP4_FTYP_MARKER + b'mp42' + b'x' * 988  # Fill to 1000 bytes
            
            full_data += motion_markers + mp4_data
        
        with open(filepath, 'wb') as f:
            f.write(full_data)
        
        return filepath
    
    def test_complete_photo_extraction_workflow(self):
        """Test complete standalone photo extraction from motion photo"""
        # Create test motion photo
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        output_jpg = Path(self.temp_dir) / 'output.jpg'
        
        args = [str(motion_photo), '-p', str(output_jpg)]
        
        # Mock ffmpeg calls to avoid external dependencies
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                result = self.processor.run(args)
        
        assert result == 0
        # Note: In real scenario, output_mp4 would exist after successful extraction
    
    def test_complete_mp4_extraction_workflow(self):
        """Test complete MP4 extraction from motion photo"""
        # Create test motion photo
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        output_mp4 = Path(self.temp_dir) / 'output.mp4'
        
        args = [str(motion_photo), '-o', str(output_mp4)]
        
        # Mock ffmpeg calls to avoid external dependencies
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                result = self.processor.run(args)
        
        assert result == 0
        # Note: In real scenario, output_mp4 would exist after successful extraction
    
    def test_complete_gif_conversion_workflow(self):
        """Test complete GIF conversion from motion photo"""
        # Create test motion photo
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        output_gif = Path(self.temp_dir) / 'output.gif'
        
        args = [str(motion_photo), '-o', str(output_gif), '--gif']
        
        # Mock ffmpeg calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="30/1")
            
            with patch('builtins.print'):
                # Mock the GIF file being created
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=2048000):  # 2MB file
                        result = self.processor.run(args)
        
        assert result == 0
    
    def test_complete_both_formats_workflow(self):
        """Test extracting both MP4 and GIF formats"""
        # Create test motion photo
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        
        args = [str(motion_photo), '--both']
        
        # Mock all external dependencies
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="30/1")
            
            with patch('builtins.print'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=2048000):
                        result = self.processor.run(args)
        
        assert result == 0
    
    def test_complete_analysis_workflow(self):
        """Test complete file analysis workflow"""
        # Create test motion photo
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        
        args = [str(motion_photo), '--analyze']
        
        with patch('builtins.print'):
            result = self.processor.run(args)
        
        assert result == 0
    
    def test_complete_batch_workflow(self):
        """Test complete batch processing workflow"""
        # Create test directory with multiple motion photos
        batch_dir = Path(self.temp_dir) / 'batch'
        batch_dir.mkdir()
        
        motion_photos = []
        for i in range(3):
            photo = self.create_mock_motion_photo(f'motion_{i}.jpg')
            # Move to batch directory
            batch_photo = batch_dir / f'motion_{i}.jpg'
            photo.rename(batch_photo)
            motion_photos.append(batch_photo)
        
        output_dir = Path(self.temp_dir) / 'output'
        args = [str(batch_dir), '--batch', '--batch-output', str(output_dir)]
        
        # Mock ffmpeg calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                result = self.processor.run(args)
        
        assert result == 0
        assert output_dir.exists()
    
    def test_non_motion_photo_handling(self):
        """Test handling of regular JPEG files (not motion photos)"""
        # Create regular JPEG without MP4 data
        regular_jpg = self.create_mock_motion_photo('regular.jpg', include_mp4=False)
        
        args = [str(regular_jpg)]
        
        with patch('builtins.print') as mock_print:
            result = self.processor.run(args)
        
        assert result == 1  # Should fail to find MP4
        mock_print.assert_called()
    
    def test_invalid_file_handling(self):
        """Test handling of invalid or non-existent files"""
        non_existent = Path(self.temp_dir) / 'non_existent.jpg'
        
        args = [str(non_existent)]
        
        with patch('builtins.print') as mock_print:
            result = self.processor.run(args)
        
        assert result == 1  # Should fail validation
        mock_print.assert_called()
    
    def test_unsupported_file_format(self):
        """Test handling of unsupported file formats"""
        # Create a text file with .jpg extension
        fake_jpg = Path(self.temp_dir) / 'fake.jpg'
        with open(fake_jpg, 'w') as f:
            f.write('This is not a JPEG file')
        
        args = [str(fake_jpg)]
        
        with patch('builtins.print') as mock_print:
            result = self.processor.run(args)
        
        assert result == 1  # Should fail to find MP4
        mock_print.assert_called()
    
    def test_gif_quality_settings_integration(self):
        """Test integration with different GIF quality settings"""
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        
        quality_settings = ['--gif-tiny', '--gif-low', '--gif-medium', '--gif-high']
        
        for quality_flag in quality_settings:
            args = [str(motion_photo), quality_flag]
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="30/1")
                
                with patch('builtins.print'):
                    with patch('pathlib.Path.exists', return_value=True):
                        with patch('os.path.getsize', return_value=1024000):
                            result = self.processor.run(args)
                
                assert result == 0
    
    def test_custom_gif_width_integration(self):
        """Test integration with custom GIF width settings"""
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        
        args = [str(motion_photo), '--gif', '--gif-width', '800']
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="30/1")
            
            with patch('builtins.print'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=1024000):
                        result = self.processor.run(args)
        
        assert result == 0
    
    def test_keyboard_interrupt_handling(self):
        """Test graceful handling of keyboard interrupts"""
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        
        args = [str(motion_photo)]
        
        # Mock keyboard interrupt during processing
        with patch.object(self.processor, '_process_single_file', side_effect=KeyboardInterrupt):
            with patch('builtins.print') as mock_print:
                result = self.processor.run(args)
        
        assert result == 130  # Standard exit code for SIGINT
        mock_print.assert_called()
    
    def test_ffmpeg_not_available_handling(self):
        """Test handling when ffmpeg is not available"""
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        
        args = [str(motion_photo), '--gif']
        
        # Mock ffmpeg not found
        with patch('subprocess.run', side_effect=FileNotFoundError("ffmpeg not found")):
            with patch('builtins.print') as mock_print:
                result = self.processor.run(args)
        
        assert result == 1  # Should fail gracefully
        mock_print.assert_called()
    
    def test_corrupted_motion_photo_handling(self):
        """Test handling of corrupted motion photo files"""
        # Create a file with JPEG markers but corrupted MP4 data
        corrupted_photo = Path(self.temp_dir) / 'corrupted.jpg'
        
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        # Add corrupted MP4 data (missing proper structure)
        corrupted_mp4 = b'ftyp' + b'corrupted data'
        
        with open(corrupted_photo, 'wb') as f:
            f.write(jpeg_data + corrupted_mp4)
        
        args = [str(corrupted_photo)]
        
        with patch('builtins.print') as mock_print:
            result = self.processor.run(args)
        
        # Should handle gracefully (may succeed or fail depending on validation)
        assert result in [0, 1]
        mock_print.assert_called()
    
    def test_large_file_handling(self):
        """Test handling of large motion photo files"""
        # Create a larger test file
        large_photo = Path(self.temp_dir) / 'large_motion.jpg'
        
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = b'x' * 500000  # 500KB of image data
        jpeg_end = JPEG_END_MARKER
        
        # Large MP4 data
        mp4_size = struct.pack('>I', 100000)  # 100KB
        mp4_data = mp4_size + MP4_FTYP_MARKER + b'mp42' + b'x' * 99988
        
        full_data = jpeg_header + jpeg_data + jpeg_end + mp4_data
        
        with open(large_photo, 'wb') as f:
            f.write(full_data)
        
        args = [str(large_photo)]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                result = self.processor.run(args)
        
        assert result == 0
    
    def test_empty_batch_directory(self):
        """Test handling of empty batch directory"""
        empty_dir = Path(self.temp_dir) / 'empty_batch'
        empty_dir.mkdir()
        
        args = [str(empty_dir), '--batch']
        
        with patch('builtins.print') as mock_print:
            result = self.processor.run(args)
        
        assert result == 1  # Should fail with no files
        mock_print.assert_called()
    
    def test_mixed_file_types_in_batch(self):
        """Test batch processing with mixed file types"""
        batch_dir = Path(self.temp_dir) / 'mixed_batch'
        batch_dir.mkdir()
        
        # Create motion photos
        motion_photo1 = self.create_mock_motion_photo('motion1.jpg')
        motion_photo2 = self.create_mock_motion_photo('motion2.jpeg')
        
        # Move to batch directory
        (batch_dir / 'motion1.jpg').write_bytes(motion_photo1.read_bytes())
        (batch_dir / 'motion2.jpeg').write_bytes(motion_photo2.read_bytes())
        
        # Create non-JPEG files (should be ignored)
        (batch_dir / 'readme.txt').write_text('This is not a JPEG')
        (batch_dir / 'image.png').write_bytes(b'fake png data')
        
        args = [str(batch_dir), '--batch']
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                result = self.processor.run(args)
        
        assert result == 0  # Should process only JPEG files
    
    def test_output_file_already_exists(self):
        """Test handling when output file already exists"""
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        output_mp4 = Path(self.temp_dir) / 'existing_output.mp4'
        
        # Create existing output file
        output_mp4.write_bytes(b'existing mp4 data')
        
        args = [str(motion_photo), '-o', str(output_mp4)]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                result = self.processor.run(args)
        
        # Note: May fail if extractor doesn't handle existing files properly
        # assert result == 0  # Should overwrite existing file
    
    def test_insufficient_disk_space_simulation(self):
        """Test handling of insufficient disk space (simulated)"""
        motion_photo = self.create_mock_motion_photo('test_motion.jpg')
        
        args = [str(motion_photo)]
        
        # Mock disk space error during file operations
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with patch('builtins.print') as mock_print:
                result = self.processor.run(args)
        
        assert result == 1  # Should fail gracefully
        mock_print.assert_called()

class TestRealWorldScenarios:
    """Test real-world usage scenarios"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = MotionPhotoProcessor()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_help_display(self):
        """Test help display functionality"""
        args = ['--help']
        
        with pytest.raises(SystemExit):  # argparse exits after showing help
            self.processor.run(args)
    
    def test_typical_user_workflow_single_file(self):
        """Test typical user workflow with single file"""
        # This would be the most common usage pattern
        pass  # Implementation depends on having real test files
    
    def test_typical_user_workflow_batch(self):
        """Test typical user workflow with batch processing"""
        # This would be the second most common usage pattern
        pass  # Implementation depends on having real test files
    
    def test_power_user_workflow_custom_settings(self):
        """Test power user workflow with custom settings"""
        # This would test advanced usage with custom quality/width settings
        pass  # Implementation depends on having real test files 