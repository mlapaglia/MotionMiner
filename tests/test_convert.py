#!/usr/bin/env python3
"""
Tests for motionminer.convert module
"""

import os
import sys
import struct
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch, mock_open
from pathlib import Path
import subprocess

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motionminer.convert import (
    find_mp4_in_jpg,
    get_video_fps,
    convert_mp4_to_gif,
    extract_mp4_from_jpg,
    analyze_jpg_structure,
    batch_extract,
    main
)


class TestFindMp4InJpg(unittest.TestCase):
    """Test the find_mp4_in_jpg function"""
    
    def test_find_mp4_in_jpg_success(self):
        """Test successful MP4 extraction from JPG"""
        # Create fake JPG data with embedded MP4
        jpeg_data = b'\xff\xd8' + b'fake_jpeg_data' + b'\xff\xd9'  # JPEG markers
        mp4_box_size = struct.pack('>I', 100)  # 4 bytes box size
        mp4_data = mp4_box_size + b'ftyp' + b'mp4\x00' + b'fake_mp4_data' * 20
        fake_file_data = jpeg_data + mp4_data
        
        with patch('builtins.open', mock_open(read_data=fake_file_data)):
            with patch('builtins.print'):
                start, size = find_mp4_in_jpg('fake.jpg')
                
                self.assertIsNotNone(start)
                self.assertIsNotNone(size)
                self.assertEqual(start, len(jpeg_data))
                self.assertEqual(size, len(mp4_data))
    
    def test_find_mp4_in_jpg_no_jpeg_end(self):
        """Test when JPEG end marker is not found"""
        fake_file_data = b'\xff\xd8' + b'fake_jpeg_data_no_end'
        
        with patch('builtins.open', mock_open(read_data=fake_file_data)):
            with patch('builtins.print'):
                start, size = find_mp4_in_jpg('fake.jpg')
                
                self.assertIsNone(start)
                self.assertIsNone(size)
    
    def test_find_mp4_in_jpg_no_ftyp(self):
        """Test when ftyp box is not found"""
        fake_file_data = b'\xff\xd8' + b'fake_jpeg_data' + b'\xff\xd9' + b'no_mp4_here'
        
        with patch('builtins.open', mock_open(read_data=fake_file_data)):
            with patch('builtins.print'):
                start, size = find_mp4_in_jpg('fake.jpg')
                
                self.assertIsNone(start)
                self.assertIsNone(size)
    
    def test_find_mp4_in_jpg_file_error(self):
        """Test file read error handling"""
        with patch('builtins.open', side_effect=IOError("File not found")):
            with patch('builtins.print'):
                start, size = find_mp4_in_jpg('nonexistent.jpg')
                
                self.assertIsNone(start)
                self.assertIsNone(size)
    
    def test_find_mp4_in_jpg_invalid_mp4_start(self):
        """Test invalid MP4 start position"""
        # Create data where ftyp is too close to beginning
        fake_file_data = b'\xff\xd8\xff\xd9' + b'ftyp'
        
        with patch('builtins.open', mock_open(read_data=fake_file_data)):
            with patch('builtins.print'):
                start, size = find_mp4_in_jpg('fake.jpg')
                
                self.assertIsNone(start)
                self.assertIsNone(size)


class TestGetVideoFps(unittest.TestCase):
    """Test the get_video_fps function"""
    
    @patch('subprocess.run')
    def test_get_video_fps_success(self, mock_run):
        """Test successful FPS detection"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '30.0'
        
        with patch('builtins.print'):
            fps = get_video_fps('test.mp4')
            
            self.assertEqual(fps, 30.0)
            mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_get_video_fps_fractional(self, mock_run):
        """Test fractional FPS handling"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '30000/1001'
        
        with patch('builtins.print'):
            fps = get_video_fps('test.mp4')
            
            self.assertAlmostEqual(fps, 29.97, places=2)
    
    @patch('subprocess.run')
    def test_get_video_fps_failure(self, mock_run):
        """Test FPS detection failure"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ''
        
        with patch('builtins.print'):
            fps = get_video_fps('test.mp4')
            
            self.assertEqual(fps, 30.0)  # Default fallback
    
    @patch('subprocess.run')
    def test_get_video_fps_exception(self, mock_run):
        """Test exception handling"""
        mock_run.side_effect = Exception("Command failed")
        
        with patch('builtins.print'):
            fps = get_video_fps('test.mp4')
            
            self.assertEqual(fps, 30.0)  # Default fallback


class TestConvertMp4ToGif(unittest.TestCase):
    """Test the convert_mp4_to_gif function"""
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.remove')
    @patch('os.path.getsize')
    def test_convert_mp4_to_gif_success_with_optimization(self, mock_getsize, mock_remove, mock_exists, mock_run):
        """Test successful MP4 to GIF conversion with optimization"""
        mock_run.return_value.returncode = 0
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 * 1024  # 1MB
        
        with patch('builtins.print'):
            with patch('motionminer.convert.get_video_fps', return_value=30.0):
                result = convert_mp4_to_gif('test.mp4', 'test.gif', optimize=True)
                
                self.assertTrue(result)
                self.assertEqual(mock_run.call_count, 2)  # Palette + GIF creation
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_convert_mp4_to_gif_success_no_optimization(self, mock_getsize, mock_exists, mock_run):
        """Test successful MP4 to GIF conversion without optimization"""
        mock_run.return_value.returncode = 0
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 * 1024  # 1MB
        
        with patch('builtins.print'):
            with patch('motionminer.convert.get_video_fps', return_value=30.0):
                result = convert_mp4_to_gif('test.mp4', 'test.gif', optimize=False)
                
                self.assertTrue(result)
                self.assertEqual(mock_run.call_count, 1)  # Only GIF creation
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_convert_mp4_to_gif_palette_failure(self, mock_exists, mock_run):
        """Test palette generation failure"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Palette generation failed"
        
        with patch('builtins.print'):
            with patch('motionminer.convert.get_video_fps', return_value=30.0):
                result = convert_mp4_to_gif('test.mp4', 'test.gif', optimize=True)
                
                self.assertFalse(result)
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_convert_mp4_to_gif_different_qualities(self, mock_remove, mock_exists, mock_run):
        """Test different quality settings"""
        mock_run.return_value.returncode = 0
        mock_exists.return_value = True
        
        qualities = ['tiny', 'low', 'medium', 'high']
        
        with patch('builtins.print'):
            with patch('motionminer.convert.get_video_fps', return_value=30.0):
                with patch('os.path.getsize', return_value=1024):
                    for quality in qualities:
                        result = convert_mp4_to_gif('test.mp4', 'test.gif', quality=quality)
                        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_convert_mp4_to_gif_subprocess_error(self, mock_run):
        """Test subprocess error handling"""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ffmpeg')
        
        with patch('builtins.print'):
            with patch('motionminer.convert.get_video_fps', return_value=30.0):
                result = convert_mp4_to_gif('test.mp4', 'test.gif')
                
                self.assertFalse(result)


class TestExtractMp4FromJpg(unittest.TestCase):
    """Test the extract_mp4_from_jpg function"""
    
    @patch('pathlib.Path.exists')
    @patch('motionminer.convert.find_mp4_in_jpg')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.rename')
    def test_extract_mp4_from_jpg_success(self, mock_rename, mock_open_file, mock_find_mp4, mock_exists):
        """Test successful MP4 extraction"""
        mock_exists.return_value = True
        mock_find_mp4.return_value = (100, 1000)
        mock_open_file.return_value.read.return_value = b'fake_mp4_data'
        
        with patch('builtins.print'):
            result = extract_mp4_from_jpg('test.jpg', output_format='mp4')
            
            self.assertTrue(result)
            mock_find_mp4.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_extract_mp4_from_jpg_file_not_found(self, mock_exists):
        """Test file not found error"""
        mock_exists.return_value = False
        
        with patch('builtins.print'):
            result = extract_mp4_from_jpg('nonexistent.jpg')
            
            self.assertFalse(result)
    
    @patch('pathlib.Path.exists')
    def test_extract_mp4_from_jpg_not_jpg_file(self, mock_exists):
        """Test non-JPG file error"""
        mock_exists.return_value = True
        
        with patch('builtins.print'):
            result = extract_mp4_from_jpg('test.txt')
            
            self.assertFalse(result)
    
    @patch('pathlib.Path.exists')
    @patch('motionminer.convert.find_mp4_in_jpg')
    def test_extract_mp4_from_jpg_no_mp4_found(self, mock_find_mp4, mock_exists):
        """Test no MP4 found in JPG"""
        mock_exists.return_value = True
        mock_find_mp4.return_value = (None, None)
        
        with patch('builtins.print'):
            result = extract_mp4_from_jpg('test.jpg')
            
            self.assertFalse(result)
    
    @patch('pathlib.Path.exists')
    @patch('motionminer.convert.find_mp4_in_jpg')
    @patch('builtins.open', new_callable=mock_open)
    @patch('motionminer.convert.convert_mp4_to_gif')
    def test_extract_mp4_from_jpg_gif_format(self, mock_convert, mock_open_file, mock_find_mp4, mock_exists):
        """Test GIF format extraction"""
        mock_exists.return_value = True
        mock_find_mp4.return_value = (100, 1000)
        mock_open_file.return_value.read.return_value = b'fake_mp4_data'
        mock_convert.return_value = True
        
        with patch('builtins.print'):
            with patch('os.remove'):
                result = extract_mp4_from_jpg('test.jpg', output_format='gif')
                
                self.assertTrue(result)
                mock_convert.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('motionminer.convert.find_mp4_in_jpg')
    @patch('builtins.open', new_callable=mock_open)
    @patch('motionminer.convert.convert_mp4_to_gif')
    @patch('os.rename')
    @patch('os.remove')
    def test_extract_mp4_from_jpg_both_formats(self, mock_remove, mock_rename, mock_convert, mock_open_file, mock_find_mp4, mock_exists):
        """Test both MP4 and GIF format extraction"""
        mock_exists.return_value = True
        mock_find_mp4.return_value = (100, 1000)
        mock_open_file.return_value.read.return_value = b'fake_mp4_data'
        mock_convert.return_value = True
        
        with patch('builtins.print'):
            result = extract_mp4_from_jpg('test.jpg', output_format='both')
            
            self.assertTrue(result)
            mock_convert.assert_called_once()
            mock_rename.assert_called_once()


class TestAnalyzeJpgStructure(unittest.TestCase):
    """Test the analyze_jpg_structure function"""
    
    @patch('builtins.open', new_callable=mock_open)
    def test_analyze_jpg_structure_success(self, mock_open_file):
        """Test successful JPG structure analysis"""
        fake_data = b'\xff\xd8' + b'fake_jpeg_data' + b'\xff\xd9' + b'ftyp' + b'moov' + b'mdat'
        mock_open_file.return_value.read.return_value = fake_data
        
        with patch('builtins.print') as mock_print:
            analyze_jpg_structure('test.jpg')
            
            mock_print.assert_called()
            # Check that various structure elements were found
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any('JPEG Start' in call for call in print_calls))
            self.assertTrue(any('JPEG End' in call for call in print_calls))
    
    @patch('builtins.open', side_effect=IOError("File not found"))
    def test_analyze_jpg_structure_file_error(self, mock_open_file):
        """Test file read error handling"""
        with patch('builtins.print') as mock_print:
            analyze_jpg_structure('nonexistent.jpg')
            
            mock_print.assert_called_with("Error analyzing file: File not found")


class TestBatchExtract(unittest.TestCase):
    """Test the batch_extract function"""
    
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.mkdir')
    @patch('motionminer.convert.extract_mp4_from_jpg')
    def test_batch_extract_success(self, mock_extract, mock_mkdir, mock_glob):
        """Test successful batch extraction"""
        # Mock glob to return different results for .jpg and .jpeg
        mock_glob.side_effect = [
            [Path('test1.jpg')],  # First call for *.jpg
            [Path('test2.jpeg')]  # Second call for *.jpeg
        ]
        mock_extract.return_value = True
        
        with patch('builtins.print'):
            batch_extract('input_dir', 'output_dir', 'mp4')
            
            self.assertEqual(mock_extract.call_count, 2)
            mock_mkdir.assert_called_once()
    
    @patch('pathlib.Path.glob')
    def test_batch_extract_no_files(self, mock_glob):
        """Test batch extraction with no JPG files"""
        mock_glob.return_value = []  # Both calls return empty lists
        
        with patch('builtins.print') as mock_print:
            batch_extract('input_dir')
            
            mock_print.assert_called_with("No JPG files found in input_dir")
    
    @patch('pathlib.Path.glob')
    @patch('motionminer.convert.extract_mp4_from_jpg')
    def test_batch_extract_no_output_dir(self, mock_extract, mock_glob):
        """Test batch extraction without output directory"""
        # Mock glob to return one file on first call, empty on second
        mock_glob.side_effect = [
            [Path('test1.jpg')],  # First call for *.jpg
            []  # Second call for *.jpeg
        ]
        mock_extract.return_value = True
        
        with patch('builtins.print'):
            batch_extract('input_dir', output_format='gif')
            
            mock_extract.assert_called_with(Path('test1.jpg'), None, 'gif')


class TestMain(unittest.TestCase):
    """Test the main function"""
    
    @patch('sys.argv', ['script.py'])
    def test_main_no_args(self):
        """Test main function with no arguments"""
        with patch('builtins.print') as mock_print:
            main()
            
            # Check that usage information was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any('Usage:' in call for call in print_calls))
    
    @patch('sys.argv', ['script.py', 'test.jpg', '--analyze'])
    @patch('motionminer.convert.analyze_jpg_structure')
    def test_main_analyze_mode(self, mock_analyze):
        """Test main function in analyze mode"""
        main()
        
        mock_analyze.assert_called_once_with('test.jpg')
    
    @patch('sys.argv', ['script.py', 'input_dir', '--batch'])
    @patch('motionminer.convert.batch_extract')
    def test_main_batch_mode(self, mock_batch):
        """Test main function in batch mode"""
        main()
        
        mock_batch.assert_called_once_with('input_dir', None, 'mp4')
    
    @patch('sys.argv', ['script.py', 'input_dir', '--batch', 'output_dir', '--gif'])
    @patch('motionminer.convert.batch_extract')
    def test_main_batch_mode_with_output_and_gif(self, mock_batch):
        """Test main function in batch mode with output dir and GIF format"""
        main()
        
        mock_batch.assert_called_once_with('input_dir', 'output_dir', 'gif')
    
    @patch('sys.argv', ['script.py', 'test.jpg', '--gif'])
    @patch('motionminer.convert.extract_mp4_from_jpg')
    def test_main_gif_mode(self, mock_extract):
        """Test main function in GIF mode"""
        main()
        
        mock_extract.assert_called_once_with('test.jpg', None, 'gif', 'medium')
    
    @patch('sys.argv', ['script.py', 'test.jpg', '--gif-tiny'])
    @patch('motionminer.convert.extract_mp4_from_jpg')
    def test_main_gif_tiny_mode(self, mock_extract):
        """Test main function in GIF tiny mode"""
        main()
        
        mock_extract.assert_called_once_with('test.jpg', None, 'gif', 'tiny')
    
    @patch('sys.argv', ['script.py', 'test.jpg', '--both'])
    @patch('motionminer.convert.extract_mp4_from_jpg')
    def test_main_both_mode(self, mock_extract):
        """Test main function in both formats mode"""
        main()
        
        mock_extract.assert_called_once_with('test.jpg', None, 'both', 'medium')
    
    @patch('sys.argv', ['script.py', 'test.jpg', 'output.mp4'])
    @patch('motionminer.convert.extract_mp4_from_jpg')
    def test_main_custom_output(self, mock_extract):
        """Test main function with custom output filename"""
        main()
        
        mock_extract.assert_called_once_with('test.jpg', 'output.mp4', 'mp4', 'medium')
    
    @patch('sys.argv', ['script.py', 'test.jpg', 'output.gif'])
    @patch('motionminer.convert.extract_mp4_from_jpg')
    def test_main_custom_gif_output(self, mock_extract):
        """Test main function with custom GIF output filename"""
        main()
        
        mock_extract.assert_called_once_with('test.jpg', 'output.gif', 'gif', 'medium')


if __name__ == '__main__':
    unittest.main() 