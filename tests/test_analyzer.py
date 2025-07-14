#!/usr/bin/env python3
"""
Unit tests for analyzer.py module
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from motionminer.analyzer import FileAnalyzer
from motionminer.config import MOTION_PHOTO_MARKERS, JPEG_END_MARKER, MP4_FTYP_MARKER

class TestFileAnalyzer:
    """Test FileAnalyzer class functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.analyzer = FileAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        assert isinstance(self.analyzer, FileAnalyzer)
    
    def test_find_all_occurrences_single_match(self):
        """Test _find_all_occurrences with single match"""
        data = b'hello world test hello'
        pattern = b'hello'
        
        result = self.analyzer._find_all_occurrences(data, pattern)
        assert result == [0, 17]
    
    def test_find_all_occurrences_no_match(self):
        """Test _find_all_occurrences with no matches"""
        data = b'hello world test'
        pattern = b'xyz'
        
        result = self.analyzer._find_all_occurrences(data, pattern)
        assert result == []
    
    def test_find_all_occurrences_overlapping(self):
        """Test _find_all_occurrences with overlapping patterns"""
        data = b'aaaa'
        pattern = b'aa'
        
        result = self.analyzer._find_all_occurrences(data, pattern)
        assert result == [0, 1, 2]  # Should find all overlapping occurrences
    
    def test_find_all_occurrences_empty_data(self):
        """Test _find_all_occurrences with empty data"""
        data = b''
        pattern = b'test'
        
        result = self.analyzer._find_all_occurrences(data, pattern)
        assert result == []
    
    def test_find_all_occurrences_empty_pattern(self):
        """Test _find_all_occurrences with empty pattern"""
        data = b'hello world'
        pattern = b''
        
        result = self.analyzer._find_all_occurrences(data, pattern)
        # Empty pattern should match at every position
        assert len(result) == len(data) + 1
    
    def test_analyze_jpg_structure_nonexistent_file(self):
        """Test analyze_jpg_structure with nonexistent file"""
        jpg_path = Path(self.temp_dir) / 'nonexistent.jpg'
        
        with patch('builtins.print') as mock_print:
            result = self.analyzer.analyze_jpg_structure(jpg_path)
            
            assert 'error' in result
            assert result['file_path'] == str(jpg_path)
            assert result['file_size'] == 0
            mock_print.assert_called()
    
    def test_analyze_jpg_structure_empty_file(self):
        """Test analyze_jpg_structure with empty file"""
        jpg_path = Path(self.temp_dir) / 'empty.jpg'
        jpg_path.touch()
        
        with patch('builtins.print') as mock_print:
            result = self.analyzer.analyze_jpg_structure(jpg_path)
            
            assert result['file_path'] == str(jpg_path)
            assert result['file_size'] == 0
            assert result['markers_found'] == {}
            assert result['mp4_signatures'] == []
            assert result['has_motion_photo_markers'] is False
    
    def test_analyze_jpg_structure_basic_jpeg(self):
        """Test analyze_jpg_structure with basic JPEG file"""
        jpg_path = Path(self.temp_dir) / 'basic.jpg'
        
        # Create basic JPEG structure
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        
        with open(jpg_path, 'wb') as f:
            f.write(jpeg_data)
        
        with patch('builtins.print') as mock_print:
            result = self.analyzer.analyze_jpg_structure(jpg_path)
            
            assert result['file_path'] == str(jpg_path)
            assert result['file_size'] == len(jpeg_data)
            assert 'JPEG Start' in result['markers_found']
            assert 'JPEG End' in result['markers_found']
            assert result['markers_found']['JPEG Start'] == [0]
            assert result['markers_found']['JPEG End'] == [len(jpeg_data) - 2]
            assert result['has_motion_photo_markers'] is False
    
    def test_analyze_jpg_structure_with_motion_photo_markers(self):
        """Test analyze_jpg_structure with motion photo markers"""
        jpg_path = Path(self.temp_dir) / 'motion_photo.jpg'
        
        # Create JPEG with motion photo markers
        jpeg_data = (b'\xff\xd8' + b'fake jpeg data' + 
                    b'GCamera' + b'more data' + 
                    b'Google' + b'even more data' + 
                    b'\xff\xd9')
        
        with open(jpg_path, 'wb') as f:
            f.write(jpeg_data)
        
        with patch('builtins.print') as mock_print:
            result = self.analyzer.analyze_jpg_structure(jpg_path)
            
            assert result['has_motion_photo_markers'] is True
            assert 'GCamera' in result['markers_found']
            assert 'Google' in result['markers_found']
    
    def test_analyze_jpg_structure_with_mp4_data(self):
        """Test analyze_jpg_structure with MP4 data"""
        jpg_path = Path(self.temp_dir) / 'with_mp4.jpg'
        
        # Create JPEG with MP4 data
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        mp4_data = b'\x00\x00\x00\x18ftypmp4' + b'fake mp4 data'
        
        full_data = jpeg_data + mp4_data
        
        with open(jpg_path, 'wb') as f:
            f.write(full_data)
        
        with patch('builtins.print') as mock_print:
            result = self.analyzer.analyze_jpg_structure(jpg_path)
            
            assert 'MP4 ftyp' in result['markers_found']
            assert len(result['mp4_signatures']) > 0
            assert result['mp4_signatures'][0]['signature'] == '00000018667479706d7034'
    
    def test_analyze_jpg_structure_multiple_mp4_signatures(self):
        """Test analyze_jpg_structure with multiple MP4 signatures"""
        jpg_path = Path(self.temp_dir) / 'multiple_mp4.jpg'
        
        # Create JPEG with multiple MP4 signatures
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        mp4_data = (b'\x00\x00\x00\x18ftypmp4' + b'data1' + 
                   b'\x00\x00\x00\x1cftypmp4' + b'data2')
        
        full_data = jpeg_data + mp4_data
        
        with open(jpg_path, 'wb') as f:
            f.write(full_data)
        
        with patch('builtins.print') as mock_print:
            result = self.analyzer.analyze_jpg_structure(jpg_path)
            
            assert len(result['mp4_signatures']) == 2
            assert result['mp4_signatures'][0]['signature'] == '00000018667479706d7034'
            assert result['mp4_signatures'][1]['signature'] == '0000001c667479706d7034'
    
    def test_analyze_file_sections_with_mp4(self):
        """Test _analyze_file_sections with MP4 data"""
        jpg_path = Path(self.temp_dir) / 'with_sections.jpg'
        
        # Create structured data
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        mp4_data = b'some padding' + b'ftyp' + b'mp4 data'
        
        full_data = jpeg_data + mp4_data
        
        with open(jpg_path, 'wb') as f:
            f.write(full_data)
        
        analysis = {'file_path': str(jpg_path), 'file_size': len(full_data)}
        
        with patch('builtins.print') as mock_print:
            self.analyzer._analyze_file_sections(full_data, analysis)
            
            # Should print section information
            mock_print.assert_called()
            
            # Check that it identified sections correctly
            call_args = [call[0][0] for call in mock_print.call_args_list]
            printed_text = ' '.join(call_args)
            assert 'JPEG section' in printed_text
            assert 'Data after JPEG' in printed_text
    
    def test_analyze_file_sections_jpeg_only(self):
        """Test _analyze_file_sections with JPEG only"""
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        analysis = {'file_path': 'test.jpg', 'file_size': len(jpeg_data)}
        
        with patch('builtins.print') as mock_print:
            self.analyzer._analyze_file_sections(jpeg_data, analysis)
            
            # Should print JPEG section info
            mock_print.assert_called()
            
            call_args = [call[0][0] for call in mock_print.call_args_list]
            printed_text = ' '.join(call_args)
            assert 'JPEG section' in printed_text
    
    def test_analyze_file_sections_no_jpeg_markers(self):
        """Test _analyze_file_sections with no JPEG markers"""
        data = b'not a jpeg file'
        analysis = {'file_path': 'test.jpg', 'file_size': len(data)}
        
        with patch('builtins.print') as mock_print:
            self.analyzer._analyze_file_sections(data, analysis)
            
            # Should handle gracefully
            mock_print.assert_called()
    
    def test_print_summary_basic_file(self):
        """Test print_summary with basic file analysis"""
        analysis = {
            'file_path': 'test.jpg',
            'file_size': 1024000,
            'has_motion_photo_markers': False,
            'mp4_signatures': [],
            'markers_found': {
                'JPEG End': [500000]
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.analyzer.print_summary(analysis)
            
            mock_print.assert_called()
            
            # Check printed content
            call_args = [call[0][0] for call in mock_print.call_args_list]
            printed_text = ' '.join(call_args)
            
            assert 'test.jpg' in printed_text
            assert '1,024,000' in printed_text
            assert 'No Motion Photo markers found' in printed_text
            assert 'No MP4 signatures found' in printed_text
    
    def test_print_summary_motion_photo(self):
        """Test print_summary with motion photo analysis"""
        analysis = {
            'file_path': 'motion_photo.jpg',
            'file_size': 2048000,
            'has_motion_photo_markers': True,
            'mp4_signatures': [
                {'signature': '00000018667479706d7034', 'positions': [1000000]}
            ],
            'markers_found': {
                'JPEG End': [800000]
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.analyzer.print_summary(analysis)
            
            mock_print.assert_called()
            
            # Check printed content
            call_args = [call[0][0] for call in mock_print.call_args_list]
            printed_text = ' '.join(call_args)
            
            assert 'motion_photo.jpg' in printed_text
            assert '2,048,000' in printed_text
            assert 'Motion Photo markers detected' in printed_text
            assert '1 MP4 signature(s) found' in printed_text
            assert 'Data after JPEG: 1,248,000' in printed_text
            assert 'Significant data after JPEG' in printed_text
    
    def test_print_summary_minimal_data_after_jpeg(self):
        """Test print_summary with minimal data after JPEG"""
        analysis = {
            'file_path': 'small.jpg',
            'file_size': 50000,
            'has_motion_photo_markers': False,
            'mp4_signatures': [],
            'markers_found': {
                'JPEG End': [49000]
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.analyzer.print_summary(analysis)
            
            mock_print.assert_called()
            
            # Check printed content
            call_args = [call[0][0] for call in mock_print.call_args_list]
            printed_text = ' '.join(call_args)
            
            assert 'Data after JPEG: 998' in printed_text
            assert 'Minimal data after JPEG' in printed_text
    
    def test_print_summary_no_jpeg_end(self):
        """Test print_summary with no JPEG end marker"""
        analysis = {
            'file_path': 'invalid.jpg',
            'file_size': 50000,
            'has_motion_photo_markers': False,
            'mp4_signatures': [],
            'markers_found': {}
        }
        
        with patch('builtins.print') as mock_print:
            self.analyzer.print_summary(analysis)
            
            mock_print.assert_called()
            
            # Should handle gracefully without JPEG End marker
            call_args = [call[0][0] for call in mock_print.call_args_list]
            printed_text = ' '.join(call_args)
            
            assert 'invalid.jpg' in printed_text
            assert 'No Motion Photo markers found' in printed_text

class TestAnalyzerIntegration:
    """Integration tests for analyzer functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.analyzer = FileAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_analysis_workflow(self):
        """Test complete analysis workflow"""
        jpg_path = Path(self.temp_dir) / 'complete_test.jpg'
        
        # Create comprehensive test file
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'GCamera' + b'Google'
        jpeg_end = b'\xff\xd9'
        mp4_data = b'\x00\x00\x00\x18ftypmp4' + b'fake mp4 video data' * 100
        
        full_data = jpeg_data + jpeg_end + mp4_data
        
        with open(jpg_path, 'wb') as f:
            f.write(full_data)
        
        # Run full analysis
        with patch('builtins.print') as mock_print:
            analysis = self.analyzer.analyze_jpg_structure(jpg_path)
            
            # Verify comprehensive analysis
            assert analysis['file_path'] == str(jpg_path)
            assert analysis['file_size'] == len(full_data)
            assert analysis['has_motion_photo_markers'] is True
            assert len(analysis['mp4_signatures']) == 1
            assert 'JPEG Start' in analysis['markers_found']
            assert 'JPEG End' in analysis['markers_found']
            assert 'GCamera' in analysis['markers_found']
            assert 'Google' in analysis['markers_found']
            assert 'MP4 ftyp' in analysis['markers_found']
            
            # Print summary
            self.analyzer.print_summary(analysis)
            
            # Verify all components were tested
            mock_print.assert_called()
    
    def test_real_world_jpeg_analysis(self):
        """Test analysis with realistic JPEG structure"""
        jpg_path = Path(self.temp_dir) / 'realistic.jpg'
        
        # Create more realistic JPEG structure
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_data = b'x' * 500000  # 500KB of image data
        jpeg_end = b'\xff\xd9'
        
        # Motion photo metadata
        metadata = b'GCamera:MicroVideo' + b'x' * 100
        
        # MP4 video data
        mp4_header = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom'
        mp4_data = b'x' * 1000000  # 1MB of video data
        
        full_data = jpeg_header + jpeg_data + jpeg_end + metadata + mp4_header + mp4_data
        
        with open(jpg_path, 'wb') as f:
            f.write(full_data)
        
        # Analyze
        with patch('builtins.print'):
            analysis = self.analyzer.analyze_jpg_structure(jpg_path)
            
            # Should detect all components
            assert analysis['file_size'] > 1500000  # > 1.5MB
            assert analysis['has_motion_photo_markers'] is True
            assert len(analysis['mp4_signatures']) >= 1
            
            # Print summary and verify output
            self.analyzer.print_summary(analysis)
            
            # Should indicate significant embedded data
            assert 'JPEG End' in analysis['markers_found']
            jpeg_end_pos = analysis['markers_found']['JPEG End'][0]
            remaining_data = analysis['file_size'] - jpeg_end_pos - 2
            assert remaining_data > 100000  # Significant data after JPEG 