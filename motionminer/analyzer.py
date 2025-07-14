#!/usr/bin/env python3
"""
File analysis tools for debugging Motion Photo extraction
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

from .config import MOTION_PHOTO_MARKERS

class FileAnalyzer:
    """Analyzes file structure for debugging purposes"""
    
    def analyze_jpg_structure(self, jpg_path: Path) -> Dict[str, Any]:
        """
        Analyze the structure of a JPG file to help debug Motion Photo extraction
        """
        analysis: Dict[str, Any] = {
            'file_path': str(jpg_path),
            'file_size': 0,
            'markers_found': {},
            'mp4_signatures': [],
            'has_motion_photo_markers': False
        }
        
        try:
            with open(jpg_path, 'rb') as f:
                data = f.read()
            
            analysis['file_size'] = len(data)
            
            print(f"\nFile analysis for: {jpg_path}")
            print(f"Total file size: {len(data):,} bytes")
            
            markers = {
                'JPEG Start': b'\xff\xd8',
                'JPEG End': b'\xff\xd9',
                'MP4 ftyp': b'ftyp',
                'MP4 moov': b'moov',
                'MP4 mdat': b'mdat',
                'GCamera': b'GCamera',
                'Motion Photo': b'MotionPhoto',
                'Google': b'Google',
            }
            
            for name, marker in markers.items():
                positions = self._find_all_occurrences(data, marker)
                if positions:
                    analysis['markers_found'][name] = positions
                    print(f"  {name}: found at byte(s) {positions}")
                    
                    pos = positions[0]
                    start = max(0, pos - 10)
                    end = min(len(data), pos + len(marker) + 10)
                    context = data[start:end]
                    print(f"    Context: {context!r}")
                    
                    if marker in MOTION_PHOTO_MARKERS:
                        analysis['has_motion_photo_markers'] = True
            
            mp4_signatures = [
                b'\x00\x00\x00\x18ftypmp4',
                b'\x00\x00\x00\x1cftypmp4',
                b'\x00\x00\x00\x20ftypmp4',
                b'\x00\x00\x00\x24ftypmp4',
            ]
            
            for i, sig in enumerate(mp4_signatures):
                positions = self._find_all_occurrences(data, sig)
                if positions:
                    sig_info = {
                        'signature': sig.hex(),
                        'positions': positions
                    }
                    analysis['mp4_signatures'].append(sig_info)
                    print(f"  MP4 signature {i+1}: found at byte(s) {positions}")
            
            self._analyze_file_sections(data, analysis)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing file: {e}")
            analysis['error'] = str(e)
            return analysis
    
    def _find_all_occurrences(self, data: bytes, pattern: bytes) -> List[int]:
        """Find all occurrences of a pattern in data"""
        positions = []
        start = 0
        while True:
            pos = data.find(pattern, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return positions
    
    def _analyze_file_sections(self, data: bytes, analysis: Dict[str, Any]) -> None:
        """Analyze different sections of the file"""
        jpeg_start = data.find(b'\xff\xd8')
        jpeg_end = data.find(b'\xff\xd9')
        
        if jpeg_start != -1 and jpeg_end != -1:
            jpeg_size = jpeg_end - jpeg_start + 2
            print(f"  JPEG section: {jpeg_start} to {jpeg_end} ({jpeg_size:,} bytes)")
            
            remaining_size = len(data) - (jpeg_end + 2)
            if remaining_size > 0:
                print(f"  Data after JPEG: {remaining_size:,} bytes")
                
                remaining_data = data[jpeg_end + 2:]
                ftyp_pos = remaining_data.find(b'ftyp')
                if ftyp_pos != -1:
                    absolute_pos = jpeg_end + 2 + ftyp_pos
                    print(f"  MP4 ftyp found at absolute position: {absolute_pos}")
                    
                    # 4 bytes before ftyp for size
                    mp4_start = absolute_pos - 4
                    if mp4_start >= 0:
                        mp4_size = len(data) - mp4_start
                        print(f"  Estimated MP4 size: {mp4_size:,} bytes")
    
    def print_summary(self, analysis: Dict[str, Any]) -> None:
        """Print a summary of the analysis"""
        print("\n" + "="*50)
        print("ANALYSIS SUMMARY")
        print("="*50)
        
        print(f"File: {analysis['file_path']}")
        print(f"Size: {analysis['file_size']:,} bytes")
        
        if analysis['has_motion_photo_markers']:
            print("✓ Motion Photo markers detected")
        else:
            print("✗ No Motion Photo markers found")
        
        if analysis['mp4_signatures']:
            print(f"✓ {len(analysis['mp4_signatures'])} MP4 signature(s) found")
        else:
            print("✗ No MP4 signatures found")
        
        if 'JPEG End' in analysis['markers_found']:
            jpeg_end = analysis['markers_found']['JPEG End'][0]
            remaining = analysis['file_size'] - jpeg_end - 2
            print(f"Data after JPEG: {remaining:,} bytes")
            
            if remaining > 100000:  # More than 100KB suggests embedded video
                print("✓ Significant data after JPEG (likely embedded video)")
            else:
                print("✗ Minimal data after JPEG")
        
        print("="*50)