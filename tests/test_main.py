#!/usr/bin/env python3
"""
Unit tests for main.py module
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from motionminer.main import MotionPhotoProcessor, main
from motionminer.config import ExtractionConfig, SUPPORTED_IMAGE_EXTENSIONS

class TestMotionPhotoProcessor:
    """Test MotionPhotoProcessor class functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.processor = MotionPhotoProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_processor_initialization(self):
        """Test processor initialization"""
        assert hasattr(self.processor, 'cli')
        assert hasattr(self.processor, 'extractor')
        assert hasattr(self.processor, 'converter')
        assert hasattr(self.processor, 'analyzer')
    
    def test_run_with_invalid_config(self):
        """Test run with invalid configuration"""
        with patch.object(self.processor.cli, 'parse_args') as mock_parse:
            with patch.object(self.processor.cli, 'validate_config', return_value=False):
                mock_parse.return_value = ExtractionConfig(input_path='nonexistent.jpg')
                
                result = self.processor.run(['nonexistent.jpg'])
                assert result == 1
    
    def test_run_analyze_only_mode(self):
        """Test run in analyze-only mode"""
        config = ExtractionConfig(input_path='test.jpg', analyze_only=True)
        
        with patch.object(self.processor.cli, 'parse_args', return_value=config):
            with patch.object(self.processor.cli, 'validate_config', return_value=True):
                with patch.object(self.processor, '_analyze_file', return_value=0) as mock_analyze:
                    result = self.processor.run(['test.jpg', '--analyze'])
                    
                    assert result == 0
                    mock_analyze.assert_called_once_with(config)
    
    def test_run_batch_mode(self):
        """Test run in batch mode"""
        config = ExtractionConfig(input_path='photos/', batch_mode=True)
        
        with patch.object(self.processor.cli, 'parse_args', return_value=config):
            with patch.object(self.processor.cli, 'validate_config', return_value=True):
                with patch.object(self.processor, '_process_batch', return_value=0) as mock_batch:
                    result = self.processor.run(['photos/', '--batch'])
                    
                    assert result == 0
                    mock_batch.assert_called_once_with(config)
    
    def test_run_single_file_mode(self):
        """Test run in single file mode"""
        config = ExtractionConfig(input_path='test.jpg')
        
        with patch.object(self.processor.cli, 'parse_args', return_value=config):
            with patch.object(self.processor.cli, 'validate_config', return_value=True):
                with patch.object(self.processor, '_process_single_file', return_value=0) as mock_single:
                    result = self.processor.run(['test.jpg'])
                    
                    assert result == 0
                    mock_single.assert_called_once_with(config)
    
    def test_run_keyboard_interrupt(self):
        """Test run with keyboard interrupt"""
        config = ExtractionConfig(input_path='test.jpg')
        
        with patch.object(self.processor.cli, 'parse_args', return_value=config):
            with patch.object(self.processor.cli, 'validate_config', return_value=True):
                with patch.object(self.processor, '_process_single_file', side_effect=KeyboardInterrupt):
                    with patch('builtins.print') as mock_print:
                        result = self.processor.run(['test.jpg'])
                        
                        assert result == 130
                        mock_print.assert_called()
    
    def test_run_unexpected_exception(self):
        """Test run with unexpected exception"""
        config = ExtractionConfig(input_path='test.jpg')
        
        with patch.object(self.processor.cli, 'parse_args', return_value=config):
            with patch.object(self.processor.cli, 'validate_config', return_value=True):
                with patch.object(self.processor, '_process_single_file', side_effect=Exception("Test error")):
                    with patch('builtins.print') as mock_print:
                        result = self.processor.run(['test.jpg'])
                        
                        assert result == 1
                        mock_print.assert_called()
    
    def test_run_cleanup_called(self):
        """Test that cleanup is called even on exception"""
        config = ExtractionConfig(input_path='test.jpg')
        
        with patch.object(self.processor.cli, 'parse_args', return_value=config):
            with patch.object(self.processor.cli, 'validate_config', return_value=True):
                with patch.object(self.processor, '_process_single_file', side_effect=Exception("Test error")):
                    with patch.object(self.processor, '_cleanup') as mock_cleanup:
                        with patch('builtins.print'):
                            self.processor.run(['test.jpg'])
                            
                            mock_cleanup.assert_called_once()
    
    def test_analyze_file(self):
        """Test _analyze_file method"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        jpg_path.touch()
        
        config = ExtractionConfig(input_path=str(jpg_path))
        
        analysis_result = {'file_path': str(jpg_path), 'file_size': 1024}
        
        with patch.object(self.processor.analyzer, 'analyze_jpg_structure', return_value=analysis_result) as mock_analyze:
            with patch.object(self.processor.analyzer, 'print_summary') as mock_print:
                with patch('builtins.print'):
                    result = self.processor._analyze_file(config)
                    
                    assert result == 0
                    mock_analyze.assert_called_once_with(jpg_path)
                    mock_print.assert_called_once_with(analysis_result)
    
    def test_process_single_file_invalid_input(self):
        """Test _process_single_file with invalid input"""
        config = ExtractionConfig(input_path='invalid.jpg')
        
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=False):
            result = self.processor._process_single_file(config)
            assert result == 1
    
    def test_process_single_file_no_mp4_found(self):
        """Test _process_single_file when no MP4 is found"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        jpg_path.touch()
        
        config = ExtractionConfig(input_path=str(jpg_path))
        
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(None, None)):
                with patch('builtins.print') as mock_print:
                    result = self.processor._process_single_file(config)
                    
                    assert result == 1
                    mock_print.assert_called()
    
    def test_process_single_file_extraction_error(self):
        """Test _process_single_file with extraction error"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        jpg_path.touch()
        
        config = ExtractionConfig(input_path=str(jpg_path))
        
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(1000, 5000)):
                with patch.object(self.processor.extractor, 'extract_mp4_data', side_effect=Exception("Extraction failed")):
                    with patch('builtins.print') as mock_print:
                        result = self.processor._process_single_file(config)
                        
                        assert result == 1
                        mock_print.assert_called()
    
    def test_process_single_file_mp4_output_success(self):
        """Test _process_single_file with successful MP4 output"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        temp_mp4_path = Path(self.temp_dir) / 'temp.mp4'
        jpg_path.touch()
        temp_mp4_path.touch()
        
        config = ExtractionConfig(input_path=str(jpg_path), output_format='mp4')
        
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(1000, 5000)):
                with patch.object(self.processor.extractor, 'extract_mp4_data', return_value=temp_mp4_path):
                    with patch.object(self.processor.extractor, 'save_mp4_final', return_value=True):
                        with patch('builtins.print'):
                            result = self.processor._process_single_file(config)
                            
                            assert result == 0
    
    def test_process_single_file_gif_output_success(self):
        """Test _process_single_file with successful GIF output"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        temp_mp4_path = Path(self.temp_dir) / 'temp.mp4'
        jpg_path.touch()
        temp_mp4_path.touch()
        
        config = ExtractionConfig(input_path=str(jpg_path), output_format='gif')
        
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(1000, 5000)):
                with patch.object(self.processor.extractor, 'extract_mp4_data', return_value=temp_mp4_path):
                    with patch.object(self.processor.converter, 'convert_with_fallback', return_value=True):
                        with patch('builtins.print'):
                            result = self.processor._process_single_file(config)
                            
                            assert result == 0
    
    def test_process_single_file_both_output_success(self):
        """Test _process_single_file with both MP4 and GIF output"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        temp_mp4_path = Path(self.temp_dir) / 'temp.mp4'
        jpg_path.touch()
        temp_mp4_path.touch()
        
        config = ExtractionConfig(input_path=str(jpg_path), output_format='both')
        
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(1000, 5000)):
                with patch.object(self.processor.extractor, 'extract_mp4_data', return_value=temp_mp4_path):
                    with patch.object(self.processor.extractor, 'save_mp4_final', return_value=True):
                        with patch.object(self.processor.converter, 'convert_with_fallback', return_value=True):
                            with patch('builtins.print'):
                                result = self.processor._process_single_file(config)
                                
                                assert result == 0
    
    def test_process_single_file_mp4_save_failure(self):
        """Test _process_single_file with MP4 save failure"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        temp_mp4_path = Path(self.temp_dir) / 'temp.mp4'
        jpg_path.touch()
        temp_mp4_path.touch()
        
        config = ExtractionConfig(input_path=str(jpg_path), output_format='mp4')
        
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(1000, 5000)):
                with patch.object(self.processor.extractor, 'extract_mp4_data', return_value=temp_mp4_path):
                    with patch.object(self.processor.extractor, 'save_mp4_final', return_value=False):
                        with patch('builtins.print'):
                            result = self.processor._process_single_file(config)
                            
                            assert result == 1
    
    def test_process_single_file_gif_conversion_failure(self):
        """Test _process_single_file with GIF conversion failure"""
        jpg_path = Path(self.temp_dir) / 'test.jpg'
        temp_mp4_path = Path(self.temp_dir) / 'temp.mp4'
        jpg_path.touch()
        temp_mp4_path.touch()
        
        config = ExtractionConfig(input_path=str(jpg_path), output_format='gif')
        
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(1000, 5000)):
                with patch.object(self.processor.extractor, 'extract_mp4_data', return_value=temp_mp4_path):
                    with patch.object(self.processor.converter, 'convert_with_fallback', return_value=False):
                        with patch('builtins.print'):
                            result = self.processor._process_single_file(config)
                            
                            assert result == 1
    
    def test_process_batch_no_files(self):
        """Test _process_batch with no files found"""
        batch_dir = Path(self.temp_dir) / 'batch'
        batch_dir.mkdir()
        
        config = ExtractionConfig(input_path=str(batch_dir), batch_mode=True)
        
        with patch('builtins.print') as mock_print:
            result = self.processor._process_batch(config)
            
            assert result == 1
            mock_print.assert_called()
    
    def test_process_batch_with_files(self):
        """Test _process_batch with files found"""
        batch_dir = Path(self.temp_dir) / 'batch'
        batch_dir.mkdir()
        
        # Create test files
        for i in range(3):
            jpg_file = batch_dir / f'test_{i}.jpg'
            jpg_file.touch()
        
        config = ExtractionConfig(input_path=str(batch_dir), batch_mode=True)
        
        with patch.object(self.processor, '_process_single_file', return_value=0) as mock_single:
            with patch('builtins.print'):
                result = self.processor._process_batch(config)
                
                assert result == 0
                assert mock_single.call_count == 3
    
    def test_process_batch_with_output_directory(self):
        """Test _process_batch with custom output directory"""
        batch_dir = Path(self.temp_dir) / 'batch'
        output_dir = Path(self.temp_dir) / 'output'
        batch_dir.mkdir()
        
        jpg_file = batch_dir / 'test.jpg'
        jpg_file.touch()
        
        config = ExtractionConfig(
            input_path=str(batch_dir), 
            batch_mode=True,
            batch_output_dir=str(output_dir)
        )
        
        with patch.object(self.processor, '_process_single_file', return_value=0) as mock_single:
            with patch('builtins.print'):
                result = self.processor._process_batch(config)
                
                assert result == 0
                assert output_dir.exists()
                mock_single.assert_called_once()
    
    def test_process_batch_mixed_results(self):
        """Test _process_batch with mixed success/failure results"""
        batch_dir = Path(self.temp_dir) / 'batch'
        batch_dir.mkdir()
        
        # Create test files
        for i in range(3):
            jpg_file = batch_dir / f'test_{i}.jpg'
            jpg_file.touch()
        
        config = ExtractionConfig(input_path=str(batch_dir), batch_mode=True)
        
        # Mock mixed results (1 success, 2 failures) - need 6 values due to duplicate file detection
        with patch.object(self.processor, '_process_single_file', side_effect=[0, 1, 1, 0, 1, 1]) as mock_single:
            with patch('builtins.print') as mock_print:
                result = self.processor._process_batch(config)
                
                assert result == 0  # Should return 0 if any files succeeded
                assert mock_single.call_count == 3
                mock_print.assert_called()
    
    def test_process_batch_all_failures(self):
        """Test _process_batch with all files failing"""
        batch_dir = Path(self.temp_dir) / 'batch'
        batch_dir.mkdir()
        
        # Create test files
        for i in range(2):
            jpg_file = batch_dir / f'test_{i}.jpg'
            jpg_file.touch()
        
        config = ExtractionConfig(input_path=str(batch_dir), batch_mode=True)
        
        with patch.object(self.processor, '_process_single_file', return_value=1) as mock_single:
            with patch('builtins.print') as mock_print:
                result = self.processor._process_batch(config)
                
                assert result == 1  # Should return 1 if no files succeeded
                assert mock_single.call_count == 2
                mock_print.assert_called()
    
    def test_get_output_path_with_provided_path(self):
        """Test _get_output_path with provided output path"""
        input_path = Path('test.jpg')
        output_path = 'custom_output.mp4'
        
        result = self.processor._get_output_path(input_path, output_path, '.mp4')
        
        assert result == Path(output_path)
    
    def test_get_output_path_auto_generated(self):
        """Test _get_output_path with auto-generated path"""
        input_path = Path('test.jpg')
        
        result = self.processor._get_output_path(input_path, None, '.mp4')
        
        assert result == Path('test.mp4')
    
    def test_cleanup(self):
        """Test _cleanup method"""
        with patch.object(self.processor.extractor, 'cleanup_temp_files') as mock_extractor:
            with patch.object(self.processor.converter, 'cleanup_temp_files') as mock_converter:
                self.processor._cleanup()
                
                mock_extractor.assert_called_once()
                mock_converter.assert_called_once()

class TestMainFunction:
    """Test main function"""
    
    def test_main_function_calls_processor(self):
        """Test that main function creates processor and calls run"""
        with patch('motionminer.main.MotionPhotoProcessor') as mock_processor_class:
            with patch('sys.exit') as mock_exit:
                mock_processor = MagicMock()
                mock_processor.run.return_value = 0
                mock_processor_class.return_value = mock_processor
                
                main()
                
                mock_processor_class.assert_called_once()
                mock_processor.run.assert_called_once()
                mock_exit.assert_called_once_with(0)
    
    def test_main_function_with_exit_code(self):
        """Test main function with non-zero exit code"""
        with patch('motionminer.main.MotionPhotoProcessor') as mock_processor_class:
            with patch('sys.exit') as mock_exit:
                mock_processor = MagicMock()
                mock_processor.run.return_value = 1
                mock_processor_class.return_value = mock_processor
                
                main()
                
                mock_exit.assert_called_once_with(1)

class TestProcessorIntegration:
    """Integration tests for processor functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.processor = MotionPhotoProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_workflow_mp4(self):
        """Test complete end-to-end workflow for MP4 extraction"""
        # Create test motion photo
        jpg_path = Path(self.temp_dir) / 'motion_photo.jpg'
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        mp4_data = b'\x00\x00\x00\x20ftyp' + b'fake mp4 data' * 100
        
        with open(jpg_path, 'wb') as f:
            f.write(jpeg_data + mp4_data)
        
        args = [str(jpg_path), '--mp4']
        
        # Mock the components to simulate successful workflow
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(len(jpeg_data), len(mp4_data))):
                with patch.object(self.processor.extractor, 'extract_mp4_data', return_value=Path(self.temp_dir) / 'temp.mp4'):
                    with patch.object(self.processor.extractor, 'save_mp4_final', return_value=True):
                        with patch('builtins.print'):
                            result = self.processor.run(args)
                            
                            assert result == 0
    
    def test_end_to_end_workflow_gif(self):
        """Test complete end-to-end workflow for GIF conversion"""
        # Create test motion photo
        jpg_path = Path(self.temp_dir) / 'motion_photo.jpg'
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        mp4_data = b'\x00\x00\x00\x20ftyp' + b'fake mp4 data' * 100
        
        with open(jpg_path, 'wb') as f:
            f.write(jpeg_data + mp4_data)
        
        args = [str(jpg_path), '--gif']
        
        # Mock the components to simulate successful workflow
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(len(jpeg_data), len(mp4_data))):
                with patch.object(self.processor.extractor, 'extract_mp4_data', return_value=Path(self.temp_dir) / 'temp.mp4'):
                    with patch.object(self.processor.converter, 'convert_with_fallback', return_value=True):
                        with patch('builtins.print'):
                            result = self.processor.run(args)
                            
                            assert result == 0
    
    def test_end_to_end_workflow_analyze(self):
        """Test complete end-to-end workflow for analysis"""
        # Create test motion photo
        jpg_path = Path(self.temp_dir) / 'motion_photo.jpg'
        jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
        
        with open(jpg_path, 'wb') as f:
            f.write(jpeg_data)
        
        args = [str(jpg_path), '--analyze']
        
        analysis_result = {
            'file_path': str(jpg_path),
            'file_size': len(jpeg_data),
            'has_motion_photo_markers': False,
            'mp4_signatures': [],
            'markers_found': {'JPEG Start': [0], 'JPEG End': [len(jpeg_data) - 2]}
        }
        
        with patch.object(self.processor.analyzer, 'analyze_jpg_structure', return_value=analysis_result):
            with patch.object(self.processor.analyzer, 'print_summary'):
                with patch('builtins.print'):
                    result = self.processor.run(args)
                    
                    assert result == 0
    
    def test_end_to_end_workflow_batch(self):
        """Test complete end-to-end workflow for batch processing"""
        # Create test directory with multiple files
        batch_dir = Path(self.temp_dir) / 'batch'
        batch_dir.mkdir()
        
        for i in range(2):
            jpg_path = batch_dir / f'motion_photo_{i}.jpg'
            jpeg_data = b'\xff\xd8' + b'fake jpeg data' + b'\xff\xd9'
            mp4_data = b'\x00\x00\x00\x20ftyp' + b'fake mp4 data' * 100
            
            with open(jpg_path, 'wb') as f:
                f.write(jpeg_data + mp4_data)
        
        args = [str(batch_dir), '--batch', '--mp4']
        
        # Mock the components to simulate successful workflow
        with patch.object(self.processor.extractor, 'validate_input_file', return_value=True):
            with patch.object(self.processor.extractor, 'find_mp4_in_jpg', return_value=(len(jpeg_data), len(mp4_data))):
                with patch.object(self.processor.extractor, 'extract_mp4_data', return_value=Path(self.temp_dir) / 'temp.mp4'):
                    with patch.object(self.processor.extractor, 'save_mp4_final', return_value=True):
                        with patch('builtins.print'):
                            result = self.processor.run(args)
                            
                            assert result == 0 