#!/usr/bin/env python3
"""
Google Motion Photo Extractor
Extracts embedded MP4 video from Google Motion Photos (JPG files with embedded video)
"""

import os
import sys
import struct
import subprocess
from pathlib import Path

def find_mp4_in_jpg(jpg_path):
    """
    Find MP4 video embedded in Google Motion Photo JPG file
    Returns tuple of (mp4_start_offset, mp4_size) or (None, None) if not found
    """
    try:
        with open(jpg_path, 'rb') as f:
            data = f.read()
        
        jpeg_end = data.find(b'\xff\xd9')  # JPEG end marker
        if jpeg_end == -1:
            print("Could not find JPEG end marker")
            return None, None
        
        # The ftyp box structure: [4 bytes size][4 bytes 'ftyp'][brand][minor_version][compatible_brands...]
        search_start = jpeg_end + 2  # Start after JPEG end marker
        
        ftyp_pos = data.find(b'ftyp', search_start)
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

def get_video_fps(video_path):
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

def convert_mp4_to_gif(mp4_path, gif_path, fps=None, width=480, optimize=True, quality='high', gif_loop=True):
    """
    Convert MP4 video to GIF using ffmpeg with various optimization levels
    quality: 'high', 'medium', 'low', or 'tiny'
    gif_loop: If True, GIF will loop infinitely. If False, GIF will play once.
    """
    try:
        # Auto-detect FPS if not provided
        if fps is None:
            fps = get_video_fps(mp4_path)
        
        print(f"Creating GIF at {fps} FPS (matching source video) with {quality} quality...")
        
        if quality == 'tiny':
            # Maximum compression - very small file
            colors = 64
            dither = 'bayer:bayer_scale=2'
            fps_multiplier = 0.8  # Slightly reduce FPS
        elif quality == 'low':
            # Heavy compression but still decent
            colors = 128
            dither = 'bayer:bayer_scale=1'
            fps_multiplier = 0.9
        elif quality == 'medium':
            # Balanced compression
            colors = 192
            dither = 'floyd_steinberg'
            fps_multiplier = 1.0
        else:  # high
            # Best quality (current default)
            colors = 256
            dither = 'floyd_steinberg'
            fps_multiplier = 1.0
        
        final_fps = fps * fps_multiplier
        loop_value = 0 if gif_loop else 1

        if optimize:
            # Step 1: Generate optimized palette
            palette_cmd = [
                'ffmpeg', '-i', str(mp4_path),
                '-vf', f'fps={final_fps},scale={width}:-1:flags=lanczos,palettegen=max_colors={colors}',
                '-y', 'palette.png'
            ]
            
            print("Generating optimized palette...")
            result = subprocess.run(palette_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Palette generation failed: {result.stderr}")
                return False
            
            # Step 2: Create GIF with optimized palette
            
            gif_cmd = [
                'ffmpeg', '-i', str(mp4_path), '-i', 'palette.png',
                '-filter_complex', f'fps={final_fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither={dither}',
                '-loop', str(loop_value),
                '-y', str(gif_path)
            ]
            
            print("Creating optimized GIF...")
            result = subprocess.run(gif_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"GIF creation failed: {result.stderr}")
                if os.path.exists('palette.png'):
                    os.remove('palette.png')
                return False
            
            if os.path.exists('palette.png'):
                os.remove('palette.png')
        else:
            cmd = [
                'ffmpeg', '-i', str(mp4_path),
                '-vf', f'fps={final_fps},scale={width}:-1:flags=lanczos',
                '-loop', str(loop_value),
                '-y', str(gif_path)
            ]
            
            print("Creating simple GIF...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Simple GIF creation failed: {result.stderr}")
                return False
        
        if os.path.exists(gif_path):
            file_size = os.path.getsize(gif_path)
            size_mb = file_size / (1024 * 1024)
            print(f"✓ Created GIF: {gif_path} (at {final_fps:.1f} FPS, {size_mb:.1f}MB)")
            return True
        else:
            print("✗ GIF file was not created")
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error creating GIF: {e}")
        print("Make sure ffmpeg is installed and available in PATH")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def extract_mp4_from_jpg(jpg_path, output_path=None, output_format='mp4', gif_quality='medium', gif_loop=True):
    """
    Extract MP4 video from Google Motion Photo JPG
    output_format: 'mp4', 'gif', or 'both'
    gif_loop: If True, GIF will loop infinitely. If False, GIF will play once.
    """
    jpg_path = Path(jpg_path)
    
    if not jpg_path.exists():
        print(f"✗ File not found: {jpg_path}")
        return False
    
    if jpg_path.suffix.lower() not in ['.jpg', '.jpeg']:
        print(f"✗ Not a JPG file: {jpg_path}")
        return False
    
    print(f"Processing: {jpg_path}")
    
    mp4_start, mp4_size = find_mp4_in_jpg(jpg_path)
    
    if mp4_start is None:
        print("✗ No embedded MP4 video found in this JPG")
        print("  This might not be a Google Motion Photo, or the format is different")
        return False
    
    temp_mp4_path = jpg_path.with_suffix('.temp.mp4')
    
    try:
        with open(jpg_path, 'rb') as f:
            f.seek(mp4_start)
            mp4_data = f.read(mp4_size)
        
        with open(temp_mp4_path, 'wb') as f:
            f.write(mp4_data)
        
        print(f"✓ Extracted MP4 video data: {mp4_size:,} bytes")
        
        success = True
        
        if output_format in ['mp4', 'both']:
            mp4_output = output_path if output_path and output_path.endswith('.mp4') else jpg_path.with_suffix('.mp4')
            try:
                if temp_mp4_path != mp4_output:
                    os.rename(temp_mp4_path, mp4_output)
                print(f"✓ Saved MP4: {mp4_output}")
            except Exception as e:
                print(f"✗ Error saving MP4: {e}")
                success = False
        
        if output_format in ['gif', 'both']:
            gif_output = output_path if output_path and output_path.endswith('.gif') else jpg_path.with_suffix('.gif')
            
            mp4_source = temp_mp4_path if temp_mp4_path.exists() else jpg_path.with_suffix('.mp4')
            
            if convert_mp4_to_gif(mp4_source, gif_output, quality=gif_quality, gif_loop=gif_loop):
                print(f"✓ Saved GIF: {gif_output}")
            else:
                success = False
        
        if temp_mp4_path.exists() and output_format != 'mp4':
            os.remove(temp_mp4_path)
        
        return success
        
    except Exception as e:
        print(f"✗ Error extracting MP4: {e}")
        if temp_mp4_path.exists():
            os.remove(temp_mp4_path)
        return False

def analyze_jpg_structure(jpg_path):
    """
    Analyze the structure of a JPG file to help debug Motion Photo extraction
    """
    try:
        with open(jpg_path, 'rb') as f:
            data = f.read()
        
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
            pos = data.find(marker)
            if pos != -1:
                print(f"  {name}: found at byte {pos}")
                start = max(0, pos - 10)
                end = min(len(data), pos + len(marker) + 10)
                context = data[start:end]
                print(f"    Context: {context}")
        
        mp4_sigs = [
            b'\x00\x00\x00\x18ftypmp4',
            b'\x00\x00\x00\x1cftypmp4',
            b'\x00\x00\x00\x20ftypmp4',
        ]
        
        for i, sig in enumerate(mp4_sigs):
            pos = data.find(sig)
            if pos != -1:
                print(f"  MP4 signature {i+1}: found at byte {pos}")
        
    except Exception as e:
        print(f"Error analyzing file: {e}")

def batch_extract(input_dir, output_dir=None, output_format='mp4', gif_loop=True):
    """
    Extract MP4 videos from all JPG files in a directory
    gif_loop: If True, GIF will loop infinitely. If False, GIF will play once.
    """
    input_dir = Path(input_dir)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    jpg_files = list(input_dir.glob('*.jpg')) + list(input_dir.glob('*.jpeg'))
    
    if not jpg_files:
        print(f"No JPG files found in {input_dir}")
        return
    
    print(f"Found {len(jpg_files)} JPG files to process")
    
    success_count = 0
    for jpg_file in jpg_files:
        if output_dir:
            if output_format == 'gif':
                output_path = output_dir / jpg_file.with_suffix('.gif').name
            else:
                output_path = output_dir / jpg_file.with_suffix('.mp4').name
        else:
            output_path = None
        
        if extract_mp4_from_jpg(jpg_file, output_path, output_format, gif_loop=gif_loop):
            success_count += 1
        print()  # Empty line between files
    
    print(f"Successfully extracted {success_count} out of {len(jpg_files)} files")

def main():
    if len(sys.argv) < 2:
        print("Google Motion Photo Extractor")
        print("Usage:")
        print("  python motion_extractor.py <input.jpg> [output.mp4/gif]")
        print("  python motion_extractor.py <input.jpg> --gif [output.gif]")
        print("  python motion_extractor.py <input.jpg> --gif-tiny [output.gif]")
        print("  python motion_extractor.py <input.jpg> --gif-low [output.gif]")
        print("  python motion_extractor.py <input.jpg> --gif-medium [output.gif]")
        print("  python motion_extractor.py <input.jpg> --gif-high [output.gif]")
        print("  python motion_extractor.py <input.jpg> --both [basename]")
        print("  python motion_extractor.py <input_directory> --batch [output_directory] [--gif/--both]")
        print("  python motion_extractor.py <input.jpg> --analyze")
        print("\nExamples:")
        print("  python motion_extractor.py photo.jpg                    # Extract as MP4")
        print("  python motion_extractor.py photo.jpg --gif              # Extract as GIF (medium quality)")
        print("  python motion_extractor.py photo.jpg --gif-tiny         # Extract as tiny GIF (~1-2MB)")
        print("  python motion_extractor.py photo.jpg --gif-low          # Extract as low quality GIF")
        print("  python motion_extractor.py photo.jpg --gif-medium       # Extract as medium quality GIF")
        print("  python motion_extractor.py photo.jpg --gif-high         # Extract as high quality GIF")
        print("  python motion_extractor.py photo.jpg --both             # Extract both MP4 and GIF")
        print("  python motion_extractor.py photo.jpg video.mp4          # Custom MP4 name")
        print("  python motion_extractor.py photo.jpg animation.gif      # Custom GIF name")
        print("  python motion_extractor.py photos/ --batch --gif        # Batch convert to GIF")
        print("  python motion_extractor.py photos/ --batch --both       # Batch convert to both formats")
        print("  python motion_extractor.py photo.jpg --analyze          # Analyze file structure")
        print("\nGIF Quality Options:")
        print("  --gif-tiny:   Maximum compression, ~1-2MB, 64 colors, 80% FPS")
        print("  --gif-low:    Heavy compression, ~2-3MB, 128 colors, 90% FPS")
        print("  --gif-medium: Balanced quality, ~3-4MB, 192 colors, full FPS")
        print("  --gif-high:   Best quality, ~5-7MB, 256 colors, full FPS")
        print("  Frame rate and resolution automatically match the source video")
        return
    
    input_path = sys.argv[1]
    
    # Check for analysis mode
    if '--analyze' in sys.argv:
        analyze_jpg_structure(input_path)
        return
    
    # Check for batch mode
    if '--batch' in sys.argv:
        batch_idx = sys.argv.index('--batch')
        output_dir = sys.argv[batch_idx + 1] if len(sys.argv) > batch_idx + 1 and not sys.argv[batch_idx + 1].startswith('--') else None
        
        # Determine output format for batch
        if '--gif' in sys.argv:
            output_format = 'gif'
        elif '--both' in sys.argv:
            output_format = 'both'
        else:
            output_format = 'mp4'
        
        gif_loop = not ('--gif-no-loop' in sys.argv)
        batch_extract(input_path, output_dir, output_format, gif_loop)
        return
    
    # Single file extraction
    output_path = None
    output_format = 'mp4'  # default
    gif_quality = 'medium'  # default GIF quality
    gif_loop = True  # default GIF loops infinitely
    
    # Check for --gif-no-loop flag
    if '--gif-no-loop' in sys.argv:
        gif_loop = False
    
    # Check for format flags
    if '--gif' in sys.argv:
        output_format = 'gif'
        # Check if custom output path is provided
        gif_idx = sys.argv.index('--gif')
        if len(sys.argv) > gif_idx + 1 and not sys.argv[gif_idx + 1].startswith('--'):
            output_path = sys.argv[gif_idx + 1]
    elif '--gif-tiny' in sys.argv:
        output_format = 'gif'
        gif_quality = 'tiny'
        gif_idx = sys.argv.index('--gif-tiny')
        if len(sys.argv) > gif_idx + 1 and not sys.argv[gif_idx + 1].startswith('--'):
            output_path = sys.argv[gif_idx + 1]
    elif '--gif-low' in sys.argv:
        output_format = 'gif'
        gif_quality = 'low'
        gif_idx = sys.argv.index('--gif-low')
        if len(sys.argv) > gif_idx + 1 and not sys.argv[gif_idx + 1].startswith('--'):
            output_path = sys.argv[gif_idx + 1]
    elif '--gif-medium' in sys.argv:
        output_format = 'gif'
        gif_quality = 'medium'
        gif_idx = sys.argv.index('--gif-medium')
        if len(sys.argv) > gif_idx + 1 and not sys.argv[gif_idx + 1].startswith('--'):
            output_path = sys.argv[gif_idx + 1]
    elif '--gif-high' in sys.argv:
        output_format = 'gif'
        gif_quality = 'high'
        gif_idx = sys.argv.index('--gif-high')
        if len(sys.argv) > gif_idx + 1 and not sys.argv[gif_idx + 1].startswith('--'):
            output_path = sys.argv[gif_idx + 1]
    elif '--both' in sys.argv:
        output_format = 'both'
        # For 'both', we ignore custom output path and use default naming
    else:
        # Check if output path is provided (and it's not a flag)
        if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
            output_path = sys.argv[2]
            # Determine format from extension
            if output_path.lower().endswith('.gif'):
                output_format = 'gif'
    
    extract_mp4_from_jpg(input_path, output_path, output_format, gif_quality, gif_loop)

if __name__ == "__main__":
    main()