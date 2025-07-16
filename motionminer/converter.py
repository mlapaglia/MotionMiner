#!/usr/bin/env python3
"""
Video conversion logic for MP4 to GIF conversion
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from .config import GIF_QUALITY_PRESETS, DEFAULT_GIF_WIDTH

class VideoConverter:
    """Handles video format conversions"""
    
    def __init__(self) -> None:
        self.temp_files: List[Path] = []
    
    def get_video_fps(self, video_path: Path) -> float:
        """
        Get the frame rate of a video file using ffprobe
        """
        try:
            # Try avg_frame_rate first as it's more accurate for motion photos
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'stream=avg_frame_rate', '-of', 'csv=p=0',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                fps_str = result.stdout.strip().rstrip(',').strip()
                
                if fps_str and fps_str != '0/0':
                    # Handle fractional frame rates (e.g., "4140000/141763" for 29.2 fps)
                    if '/' in fps_str:
                        numerator, denominator = fps_str.split('/')
                        if float(denominator) != 0:
                            fps = float(numerator) / float(denominator)
                            if fps > 0:
                                return round(fps, 2)
                    else:
                        fps = float(fps_str)
                        if fps > 0:
                            return round(fps, 2)
            
            # Fallback to r_frame_rate if avg_frame_rate doesn't work
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                fps_str = result.stdout.strip().rstrip(',').strip()
                
                if fps_str and fps_str != '0/0':
                    # Handle fractional frame rates (e.g., "30000/1001" for 29.97 fps)
                    if '/' in fps_str:
                        numerator, denominator = fps_str.split('/')
                        if float(denominator) != 0:
                            fps = float(numerator) / float(denominator)
                            # Cap very high frame rates as they're likely incorrect for motion photos
                            if fps > 60:
                                print(f"Warning: Very high frame rate detected ({fps:.1f} FPS), using 30 FPS instead")
                                return 30.0
                            if fps > 0:
                                return round(fps, 2)
                    else:
                        fps = float(fps_str)
                        if fps > 60:
                            print(f"Warning: Very high frame rate detected ({fps:.1f} FPS), using 30 FPS instead")
                            return 30.0
                        if fps > 0:
                            return round(fps, 2)
            
            print(f"Warning: Could not detect valid FPS, using default 30 FPS")
            return 30.0
                
        except Exception as e:
            print(f"Warning: Error detecting FPS ({e}), using default 30 FPS")
            return 30.0
    
    def convert_mp4_to_gif(self, mp4_path: Path, gif_path: Path, 
                          fps: Optional[float] = None, 
                          width: int = DEFAULT_GIF_WIDTH, 
                          quality: str = 'medium',
                          gif_loop: bool = True) -> bool:
        """
        Convert MP4 video to GIF using ffmpeg with optimization
        Args:
            gif_loop: If True, GIF will loop infinitely. If False, GIF will play once.
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
            
            # Step 1: Generate optimized palette - explicitly select the first video stream
            palette_path = Path('palette.png')
            self.temp_files.append(palette_path)
            
            palette_cmd = [
                'ffmpeg', '-i', str(mp4_path),
                '-vf', f'fps={final_fps},scale={width}:-1:flags=lanczos,palettegen=max_colors={settings.colors}',
                '-map', '0:v:0',  # Explicitly select the first video stream
                '-y', str(palette_path)
            ]
            
            print("Generating optimized palette...")
            result = subprocess.run(palette_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Palette generation failed: {result.stderr}")
                return False
            
            # Step 2: Create GIF with optimized palette
            loop_value = 0 if gif_loop else 1  # 0 = infinite loop, 1 = play once
            gif_cmd = [
                'ffmpeg', '-i', str(mp4_path), '-i', str(palette_path),
                '-filter_complex', f'[0:v:0]fps={final_fps},scale={width}:-1:flags=lanczos[v];[v][1:v]paletteuse=dither={settings.dither}[out]',
                '-map', '[out]',  # Use the filtered output stream
                '-loop', str(loop_value),  # Control GIF looping
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
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            if temp_file.exists():
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Warning: Could not remove temp file {temp_file}: {e}")
        
        self.temp_files.clear()
        
        # Also clean up any remaining palette files
        palette_path = Path('palette.png')
        if palette_path.exists():
            try:
                os.remove(palette_path)
            except Exception as e:
                print(f"Warning: Could not remove palette file: {e}")
    
    def _cleanup_empty_file(self, file_path: Path) -> None:
        """Remove file if it exists and is empty"""
        if file_path.exists():
            try:
                if os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                    print(f"Removed empty file: {file_path}")
            except Exception as e:
                print(f"Warning: Could not check/remove empty file {file_path}: {e}")
    
    def convert_with_fallback(self, mp4_path: Path, gif_path: Path, 
                             fps: Optional[float] = None, 
                             width: int = DEFAULT_GIF_WIDTH, 
                             quality: str = 'medium',
                             gif_loop: bool = True) -> bool:
        """
        Convert MP4 to GIF with fallback to simple conversion if optimized fails
        """
        # Clean up any existing empty GIF file
        self._cleanup_empty_file(gif_path)
        
        if self.convert_mp4_to_gif(mp4_path, gif_path, fps, width, quality, gif_loop):
            return True
        
        print("Optimized conversion failed, trying simple conversion...")
        
        try:
            if fps is None:
                fps = self.get_video_fps(mp4_path)
            
            # Simple conversion with explicit stream selection
            loop_value = 0 if gif_loop else 1  # 0 = infinite loop, 1 = play once
            cmd = [
                'ffmpeg', '-i', str(mp4_path),
                '-vf', f'fps={fps},scale={width}:-1:flags=lanczos',
                '-map', '0:v:0',  # Explicitly select the first video stream
                '-loop', str(loop_value),  # Control GIF looping
                '-y', str(gif_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Simple conversion also failed: {result.stderr}")
                # Clean up any failed GIF file
                self._cleanup_empty_file(gif_path)
                return False
            
            if gif_path.exists() and os.path.getsize(gif_path) > 0:
                file_size = os.path.getsize(gif_path)
                size_mb = file_size / (1024 * 1024)
                print(f"✓ Created GIF (simple): {gif_path} (at {fps:.1f} FPS, {size_mb:.1f}MB)")
                return True
            else:
                print("✗ GIF file was not created or is empty")
                self._cleanup_empty_file(gif_path)
                return False
            
        except Exception as e:
            print(f"✗ Simple conversion failed: {e}")
            self._cleanup_empty_file(gif_path)
            return False
    
    def __del__(self) -> None:
        """Cleanup on destruction"""
        self.cleanup_temp_files()