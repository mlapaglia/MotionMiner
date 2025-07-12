# MotionMiner

![MotionMiner Logo](logo.png)

**Extract videos from Google Motion Photos with ease!**

MotionMiner is a powerful Python tool that extracts embedded MP4 videos from Google Motion Photos (JPG files) and converts them to various formats including MP4 and GIF animations.

## 🚀 Features

- **Extract MP4 videos** from Google Motion Photos
- **Convert to GIF animations** with customizable quality settings
- **Batch processing** for multiple files
- **Multiple output formats**: MP4, GIF, or both
- **Quality presets** for GIF output (tiny, low, medium, high)
- **File structure analysis** to examine Motion Photo internals
- **Cross-platform support** (Windows, macOS, Linux)

## 📋 Requirements

- **Python 3.6+**
- **FFmpeg** (for video conversion)

## 🛠️ Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Install FFmpeg

FFmpeg is required for video processing. Choose your platform:

#### Windows
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system PATH
4. Test installation: `ffmpeg -version`

#### macOS
```bash
# Using Homebrew
brew install ffmpeg

# Using MacPorts
port install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Linux (CentOS/RHEL/Fedora)
```bash
# CentOS/RHEL
sudo yum install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

### Step 3: Verify Installation

Test that everything is working:
```bash
python main.py --help
```

## 🎯 Usage

### Basic Usage

Extract MP4 from a single Motion Photo:
```bash
python main.py photo.jpg
```

Extract as GIF animation:
```bash
python main.py photo.jpg --gif
```

Extract both MP4 and GIF:
```bash
python main.py photo.jpg --both
```

### Output Options

Specify custom output filename:
```bash
python main.py photo.jpg -o my_video.mp4
python main.py photo.jpg -o my_animation.gif --gif
```

### GIF Quality Settings

MotionMiner offers 4 quality presets for GIF output:

| Quality | Colors | File Size | Description |
|---------|---------|-----------|-------------|
| `--gif-tiny` | 64 | ~1-2MB | Maximum compression |
| `--gif-low` | 128 | ~2-3MB | Heavy compression, decent quality |
| `--gif-medium` | 192 | ~3-4MB | Balanced quality and size (default) |
| `--gif-high` | 256 | ~5-7MB | Best quality |

Examples:
```bash
python main.py photo.jpg --gif-tiny      # Small file size
python main.py photo.jpg --gif-high      # Best quality
```

### Custom GIF Width

Adjust GIF width (height is automatically calculated):
```bash
python main.py photo.jpg --gif --gif-width 640
```

### Batch Processing

Process all JPG files in a directory:
```bash
python main.py photos/ --batch
```

Batch process with custom output directory:
```bash
python main.py photos/ --batch --batch-output extracted_videos/
```

Batch convert to GIFs:
```bash
python main.py photos/ --batch --gif-low
```

### File Analysis

Analyze Motion Photo structure without extracting:
```bash
python main.py photo.jpg --analyze
```

## 📖 Command Reference

### Required Arguments
- `input` - Input JPG file or directory containing JPG files

### Optional Arguments
- `-o, --output` - Output file path (auto-generated if not provided)
- `--mp4` - Extract as MP4 video (default)
- `--gif` - Extract as GIF animation
- `--both` - Extract both MP4 and GIF
- `--gif-tiny` - Extract as tiny GIF (64 colors, ~1-2MB)
- `--gif-low` - Extract as low quality GIF (128 colors, ~2-3MB)
- `--gif-medium` - Extract as medium quality GIF (192 colors, ~3-4MB)
- `--gif-high` - Extract as high quality GIF (256 colors, ~5-7MB)
- `--gif-width` - GIF width in pixels (default: 480)
- `--batch` - Process all JPG files in input directory
- `--batch-output` - Output directory for batch processing
- `--analyze` - Analyze file structure without extracting

## 💡 Examples

### Single File Examples
```bash
# Extract MP4 from Motion Photo
python main.py IMG_20231201_123456.jpg

# Extract high-quality GIF
python main.py IMG_20231201_123456.jpg --gif-high

# Extract both formats with custom output
python main.py motion_photo.jpg --both -o my_video.mp4

# Analyze file structure
python main.py motion_photo.jpg --analyze
```

### Batch Processing Examples
```bash
# Process all photos in current directory
python main.py . --batch

# Process photos and save to specific directory
python main.py photos/ --batch --batch-output extracted/

# Batch convert to tiny GIFs for web use
python main.py photos/ --batch --gif-tiny --batch-output web_gifs/

# Process with custom GIF settings
python main.py photos/ --batch --gif --gif-width 320 --batch-output small_gifs/
```

## 🔧 Troubleshooting

### Common Issues

**"No embedded MP4 video found"**
- The file might not be a Google Motion Photo
- Some Motion Photos have different internal structures
- Use `--analyze` to examine the file structure

**"FFmpeg not found"**
- Make sure FFmpeg is installed and in your system PATH
- Test with `ffmpeg -version` in your terminal

**"Permission denied"**
- Check file permissions for input files
- Ensure you have write permissions in the output directory

### Getting Help

View all available options:
```bash
python main.py --help
```

## 📁 Project Structure

```
MotionMiner/
├── main.py          # Main application entry point
├── cli.py           # Command-line interface
├── extractor.py     # Motion Photo extraction logic
├── converter.py     # Video conversion utilities
├── analyzer.py      # File structure analysis
├── config.py        # Configuration and settings
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🙏 Acknowledgments

- Thanks to Google for creating Motion Photos
- FFmpeg community for excellent video processing tools
- Python community for amazing libraries

---

**Happy extracting!** 🎬✨