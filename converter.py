#!/usr/bin/env python3
"""
Video conversion logic for MP4 to GIF conversion
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from config import GIF_QUALITY_PRESETS, DEFAULT_GIF_WIDTH

class VideoConverter:
    """Handles video format conversions"""
    
    def __init__(self):
        self.temp_files = []
    
    def get_video_fps(self, video_path: Path) -> float:
        """
        Get the frame rate of a video file using ffprobe
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                fps_str = result.stdout.strip()
                # Handle fractional frame rates (e.g., "30000/1001" for 29.97 fps)
                if '/' in fps_str:
                    numerator, denominator = fps_str.split('/')
                    fps = float(numerator) / float(denominator)
                else:
                    fps = float(fps_str)
                
                return round(fps, 2)
            else:
                print(f"Warning: Could not detect FPS, using default 30 FPS")
                return 30.0
                
        except Exception as e:
            print(f"Warning: Error detecting FPS ({e}), using default 30 FPS")
            return 30.0
    
    def convert_mp4_to_gif(self, mp4_path: Path, gif_path: Path, 
                          fps: Optional[float] = None, 
                          width: int = DEFAULT_GIF_WIDTH, 
                          quality: str = 'medium') -> bool:
        """
        Convert MP4 video to GIF using ffmpeg with optimization
        """
        try:
            if fps is None:
                fps = self.get_video_fps(mp4_path)
            
            if quality not in GIF_QUALITY_PRESETS:
                print(f"Warning: Unknown quality '{quality}', using 'medium'")
                quality = 'medium'
            
            settings = GIF_QUALITY_PRESETS[quality]
            
            print(f"Creating GIF at {fps} FPS with {quality} quality...")
            print(f"Settings: {settings.colors} colors, {settings.description}")
            
            final_fps = fps * settings.fps_multiplier
            
            # Step 1: Generate optimized palette
            palette_path = Path('palette.png')
            self.temp_files.append(palette_path)
            
            palette_cmd = [
                'ffmpeg', '-i', str(mp4_path),
                '-vf', f'fps={final_fps},scale={width}:-1:flags=lanczos,palettegen=max_colors={settings.colors}',
                '-y', str(palette_path)
            ]
            
            print("Generating optimized palette...")
            result = subprocess.run(palette_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Palette generation failed: {result.stderr}")
                return False
            
            # Step 2: Create GIF with optimized palette
            gif_cmd = [
                'ffmpeg', '-i', str(mp4_path), '-i', str(palette_path),
                '-filter_complex', f'fps={final_fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither={settings.dither}',
                '-y', str(gif_path)
            ]
            
            print("Creating optimized GIF...")
            result = subprocess.run(gif_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"GIF creation failed: {result.stderr}")
                return False
            
            if not gif_path.exists():
                print("✗ GIF file was not created")
                return False
            
            file_size = os.path.getsize(gif_path)
            size_mb = file_size / (1024 * 1024)
            print(f"✓ Created GIF: {gif_path} (at {final_fps:.1f} FPS, {size_mb:.1f}MB)")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating GIF: {e}")
            return False
        finally:
            self.cleanup_temp_files()
    
    def convert_with_fallback(self, mp4_path: Path, gif_path: Path, 
                             fps: Optional[float] = None, 
                             width: int = DEFAULT_GIF_WIDTH, 
                             quality: str = 'medium') -> bool:
        """
        Convert MP4 to GIF with fallback to simple conversion if optimized fails
        """
        if self.convert_mp4_to_gif(mp4_path, gif_path, fps, width, quality):
            return True
        
        print("Optimized conversion failed, trying simple conversion...")
        
        try:
            if fps is None:
                fps = self.get_video_fps(mp4_path)
            
            cmd = [
                'ffmpeg', '-i', str(mp4_path),
                '-vf', f'fps={fps},scale={width}:-1:flags=lanczos',
                '-y', str(gif_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Simple conversion also failed: {result.stderr}")
                return False
            
            if gif_path.exists():
                file_size = os.path.getsize(gif_path)
                size_mb = file_size / (1024 * 1024)
                print(f"✓ Created GIF (simple): {gif_path} (at {fps:.1f} FPS, {size_mb:.1f}MB)")
                return True
            
            return False
            
        except Exception as e:
            print(f"✗ Simple conversion failed: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            if temp_file.exists():
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Warning: Could not remove temp file {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup_temp_files()