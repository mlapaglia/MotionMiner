#!/usr/bin/env python3
"""
Core extraction logic for Google Motion Photos
"""

import os
import struct
from pathlib import Path
from typing import List, Tuple, Optional

from .config import JPEG_END_MARKER, MP4_FTYP_MARKER, SUPPORTED_IMAGE_EXTENSIONS

class MotionPhotoExtractor:
    """Handles extraction of MP4 video from Google Motion Photos"""
    
    def __init__(self) -> None:
        self.temp_files: List[Path] = []
    
    def find_mp4_in_jpg(self, jpg_path: Path) -> Tuple[Optional[int], Optional[int]]:
        """
        Find MP4 video embedded in Google Motion Photo JPG file
        Returns tuple of (mp4_start_offset, mp4_size) or (None, None) if not found
        """
        try:
            with open(jpg_path, 'rb') as f:
                data = f.read()
            
            jpeg_end = data.find(JPEG_END_MARKER)
            if jpeg_end == -1:
                print("Could not find JPEG end marker")
                return None, None
            
            search_start = jpeg_end + 2  # Start after JPEG end marker
            
            ftyp_pos = data.find(MP4_FTYP_MARKER, search_start)
            if ftyp_pos == -1:
                print("Could not find MP4 ftyp box")
                return None, None
            
            # The MP4 starts 4 bytes before 'ftyp' (the size field)
            mp4_start = ftyp_pos - 4
            
            if mp4_start < 0 or mp4_start >= len(data) - 8:
                print("Invalid MP4 start position")
                return None, None
            
            box_size = struct.unpack('>I', data[mp4_start:mp4_start+4])[0]
            
            mp4_size = len(data) - mp4_start
            
            print(f"Found MP4 at byte {mp4_start}, size: {mp4_size:,} bytes")
            print(f"First MP4 box size: {box_size} bytes")
            
            return mp4_start, mp4_size
            
        except Exception as e:
            print(f"Error reading file: {e}")
            return None, None
    
    def validate_input_file(self, jpg_path: Path) -> bool:
        """Validate that the input file exists and is a JPG"""
        if not jpg_path.exists():
            print(f"✗ File not found: {jpg_path}")
            return False
        
        if jpg_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            print(f"✗ Not a supported image file: {jpg_path}")
            print(f"  Supported extensions: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}")
            return False
        
        return True
    
    def extract_mp4_data(self, jpg_path: Path, mp4_start: int, mp4_size: int) -> Path:
        """
        Extract MP4 data from JPG file and save to temporary file
        Returns path to temporary MP4 file
        """
        temp_mp4_path = jpg_path.with_suffix('.temp.mp4')
        self.temp_files.append(temp_mp4_path)
        
        try:
            with open(jpg_path, 'rb') as f:
                f.seek(mp4_start)
                mp4_data = f.read(mp4_size)
            
            with open(temp_mp4_path, 'wb') as f:
                f.write(mp4_data)
            
            print(f"✓ Extracted MP4 video data: {mp4_size:,} bytes")
            return temp_mp4_path
            
        except Exception as e:
            print(f"✗ Error extracting MP4 data: {e}")
            raise
    
    def save_mp4_final(self, temp_mp4_path: Path, final_mp4_path: Path) -> bool:
        """Move temporary MP4 to final location"""
        try:
            if temp_mp4_path != final_mp4_path:
                os.rename(temp_mp4_path, final_mp4_path)
                # Remove from temp files list since it's now permanent
                if temp_mp4_path in self.temp_files:
                    self.temp_files.remove(temp_mp4_path)
            
            print(f"✓ Saved MP4: {final_mp4_path}")
            return True
            
        except Exception as e:
            print(f"✗ Error saving MP4: {e}")
            return False
    
    def cleanup_temp_files(self) -> None:
        """Clean up any temporary files"""
        for temp_file in self.temp_files:
            if temp_file.exists():
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Warning: Could not remove temp file {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def __del__(self) -> None:
        """Cleanup on destruction"""
        self.cleanup_temp_files()