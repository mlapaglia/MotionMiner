#!/usr/bin/env python3
"""
Unit tests for extractor.py module
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import struct

from motionminer.extractor import MotionPhotoExtractor
from motionminer.config import JPEG_END_MARKER, MP4_FTYP_MARKER, SUPPORTED_IMAGE_EXTENSIONS

class TestMotionPhotoExtractor:
    """Test MotionPhotoExtractor class functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.extractor = MotionPhotoExtractor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.extractor.cleanup_temp_files()
    
    def test_extractor_initialization(self):
        """Test extractor initialization"""
        assert isinstance(self.extractor.temp_files, list)
        assert len(self.extractor.temp_files) == 0
    
    def test_validate_input_file_valid(self):
        """Test validate_input_file with valid JPG file"""
        jpg_file = Path(self.temp_dir) / 'test.jpg'
        jpg_file.touch()
        
        result = self.extractor.validate_input_file(jpg_file)
        assert result is True
    
    def test_validate_input_file_nonexistent(self):
        """Test validate_input_file with nonexistent file"""
        jpg_file = Path(self.temp_dir) / 'nonexistent.jpg'
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.validate_input_file(jpg_file)
            assert result is False
            mock_print.assert_called()
    
    def test_validate_input_file_invalid_extension(self):
        """Test validate_input_file with invalid file extension"""
        txt_file = Path(self.temp_dir) / 'test.txt'
        txt_file.touch()
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.validate_input_file(txt_file)
            assert result is False
            mock_print.assert_called()
    
    def test_validate_input_file_supported_extensions(self):
        """Test validate_input_file with all supported extensions"""
        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            jpg_file = Path(self.temp_dir) / f'test{ext}'
            jpg_file.touch()
            
            result = self.extractor.validate_input_file(jpg_file)
            assert result is True
            
            jpg_file.unlink()  # Clean up
    
    def test_find_mp4_in_jpg_no_jpeg_end(self):
        """Test find_mp4_in_jpg when JPEG end marker is not found"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        test_data = b'some invalid jpeg data'
        
        with open(jpg_path, 'wb') as f:
            f.write(test_data)
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.find_mp4_in_jpg(jpg_path)
            assert result == (None, None)
            mock_print.assert_called()
    
    def test_find_mp4_in_jpg_no_mp4_ftyp(self):
        """Test find_mp4_in_jpg when MP4 ftyp marker is not found"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        test_data = b'some jpeg data' + JPEG_END_MARKER + b'some other data'
        
        with open(jpg_path, 'wb') as f:
            f.write(test_data)
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.find_mp4_in_jpg(jpg_path)
            assert result == (None, None)
            mock_print.assert_called()
    
    def test_find_mp4_in_jpg_valid_motion_photo(self):
        """Test find_mp4_in_jpg with valid motion photo structure"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        
        # Create a mock motion photo with JPEG end marker followed by MP4 data
        jpeg_data = b'fake jpeg data'
        mp4_box_size = struct.pack('>I', 32)  # 32 bytes box size
        mp4_data = mp4_box_size + MP4_FTYP_MARKER + b'mp42' + b'additional_mp4_data'
        
        full_data = jpeg_data + JPEG_END_MARKER + mp4_data
        
        with open(jpg_path, 'wb') as f:
            f.write(full_data)
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.find_mp4_in_jpg(jpg_path)
            
            mp4_start, mp4_size = result
            assert mp4_start is not None
            assert mp4_size is not None
            assert mp4_start > 0
            assert mp4_size > 0
            
            # MP4 should start 4 bytes before the ftyp marker
            expected_start = len(jpeg_data) + len(JPEG_END_MARKER)
            assert mp4_start == expected_start
            
            # MP4 size should be from start to end of file
            expected_size = len(mp4_data)
            assert mp4_size == expected_size
    
    def test_find_mp4_in_jpg_invalid_mp4_position(self):
        """Test find_mp4_in_jpg with invalid MP4 position"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        
        # Create data where ftyp appears too early (invalid position)
        test_data = MP4_FTYP_MARKER + JPEG_END_MARKER + b'some data'
        
        with open(jpg_path, 'wb') as f:
            f.write(test_data)
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.find_mp4_in_jpg(jpg_path)
            assert result == (None, None)
            mock_print.assert_called()
    
    def test_find_mp4_in_jpg_file_read_error(self):
        """Test find_mp4_in_jpg with file read error"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        
        # Create a file that will cause read error
        with patch('builtins.open', side_effect=IOError("File read error")):
            with patch('builtins.print') as mock_print:
                result = self.extractor.find_mp4_in_jpg(jpg_path)
                assert result == (None, None)
                mock_print.assert_called()
    
    def test_extract_mp4_data_success(self):
        """Test successful MP4 data extraction"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        
        # Create test data
        jpeg_data = b'fake jpeg data'
        mp4_data = b'fake mp4 data with sufficient length'
        full_data = jpeg_data + mp4_data
        
        with open(jpg_path, 'wb') as f:
            f.write(full_data)
        
        mp4_start = len(jpeg_data)
        mp4_size = len(mp4_data)
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.extract_mp4_data(jpg_path, mp4_start, mp4_size)
            
            assert isinstance(result, Path)
            assert result.exists()
            assert result.suffix == '.mp4'
            assert result in self.extractor.temp_files
            
            # Verify extracted data
            with open(result, 'rb') as f:
                extracted_data = f.read()
            assert extracted_data == mp4_data
    
    def test_extract_mp4_data_file_error(self):
        """Test MP4 data extraction with file error"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        
        with patch('builtins.open', side_effect=IOError("File error")):
            with patch('builtins.print') as mock_print:
                with pytest.raises(IOError):
                    self.extractor.extract_mp4_data(jpg_path, 0, 100)
                mock_print.assert_called()
    
    def test_save_mp4_final_success(self):
        """Test successful MP4 file saving"""
        temp_mp4 = Path(self.temp_dir) / 'temp.mp4'
        final_mp4 = Path(self.temp_dir) / 'final.mp4'
        
        # Create temp file
        with open(temp_mp4, 'wb') as f:
            f.write(b'test mp4 data')
        
        self.extractor.temp_files.append(temp_mp4)
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.save_mp4_final(temp_mp4, final_mp4)
            
            assert result is True
            assert final_mp4.exists()
            assert not temp_mp4.exists()  # Should be moved
            assert temp_mp4 not in self.extractor.temp_files
            mock_print.assert_called()
    
    def test_save_mp4_final_same_path(self):
        """Test saving MP4 with same temp and final paths"""
        mp4_path = Path(self.temp_dir) / 'same.mp4'
        
        with open(mp4_path, 'wb') as f:
            f.write(b'test mp4 data')
        
        with patch('builtins.print') as mock_print:
            result = self.extractor.save_mp4_final(mp4_path, mp4_path)
            
            assert result is True
            assert mp4_path.exists()
            mock_print.assert_called()
    
    def test_save_mp4_final_error(self):
        """Test MP4 saving with file error"""
        temp_mp4 = Path(self.temp_dir) / 'temp.mp4'
        final_mp4 = Path(self.temp_dir) / 'final.mp4'
        
        with open(temp_mp4, 'wb') as f:
            f.write(b'test mp4 data')
        
        with patch('os.rename', side_effect=OSError("File error")):
            with patch('builtins.print') as mock_print:
                result = self.extractor.save_mp4_final(temp_mp4, final_mp4)
                
                assert result is False
                mock_print.assert_called()
    
    def test_cleanup_temp_files_success(self):
        """Test successful cleanup of temporary files"""
        temp_files = []
        for i in range(3):
            temp_file = Path(self.temp_dir) / f'temp_{i}.mp4'
            with open(temp_file, 'wb') as f:
                f.write(b'test data')
            temp_files.append(temp_file)
            self.extractor.temp_files.append(temp_file)
        
        self.extractor.cleanup_temp_files()
        
        # All temp files should be removed
        for temp_file in temp_files:
            assert not temp_file.exists()
        
        # Temp files list should be empty
        assert len(self.extractor.temp_files) == 0
    
    def test_cleanup_temp_files_with_errors(self):
        """Test cleanup with file removal errors"""
        temp_file = Path(self.temp_dir) / 'temp.mp4'
        self.extractor.temp_files.append(temp_file)
        
        with patch('os.remove', side_effect=OSError("Remove error")):
            with patch('builtins.print') as mock_print:
                self.extractor.cleanup_temp_files()
                
                # Should handle error gracefully
                assert len(self.extractor.temp_files) == 0
                # mock_print.assert_called()
    
    def test_cleanup_temp_files_nonexistent(self):
        """Test cleanup with nonexistent temp files"""
        temp_file = Path(self.temp_dir) / 'nonexistent.mp4'
        self.extractor.temp_files.append(temp_file)
        
        # Should not raise error for nonexistent files
        self.extractor.cleanup_temp_files()
        assert len(self.extractor.temp_files) == 0
    
    def test_destructor_cleanup(self):
        """Test that destructor calls cleanup"""
        temp_file = Path(self.temp_dir) / 'temp.mp4'
        with open(temp_file, 'wb') as f:
            f.write(b'test data')
        
        extractor = MotionPhotoExtractor()
        extractor.temp_files.append(temp_file)
        
        # Simulate destructor call
        extractor.__del__()
        
        # File should be cleaned up
        assert not temp_file.exists()

class TestExtractorIntegration:
    """Integration tests for extractor functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.extractor = MotionPhotoExtractor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.extractor.cleanup_temp_files()
    
    def test_full_extraction_workflow(self):
        """Test complete extraction workflow"""
        jpg_path = Path(self.temp_dir) / 'motion_photo.jpg'
        
        # Create a realistic motion photo structure
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' * 100  # JPEG start + data
        mp4_box_size = struct.pack('>I', 48)  # 48 bytes box size
        mp4_data = mp4_box_size + MP4_FTYP_MARKER + b'mp42' + b'fake mp4 video data' * 50
        
        full_data = jpeg_data + JPEG_END_MARKER + mp4_data
        
        with open(jpg_path, 'wb') as f:
            f.write(full_data)
        
        # Test the full workflow
        assert self.extractor.validate_input_file(jpg_path) is True
        
        mp4_start, mp4_size = self.extractor.find_mp4_in_jpg(jpg_path)
        assert mp4_start is not None
        assert mp4_size is not None
        
        temp_mp4_path = self.extractor.extract_mp4_data(jpg_path, mp4_start, mp4_size)
        assert temp_mp4_path.exists()
        assert temp_mp4_path in self.extractor.temp_files
        
        final_mp4_path = Path(self.temp_dir) / 'final.mp4'
        assert self.extractor.save_mp4_final(temp_mp4_path, final_mp4_path) is True
        assert final_mp4_path.exists()
        assert not temp_mp4_path.exists()
        
        # Verify final file contains correct data
        with open(final_mp4_path, 'rb') as f:
            final_data = f.read()
        assert final_data == mp4_data 