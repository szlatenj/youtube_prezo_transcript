# Quick Installation Guide

## Prerequisites

- Python 3.8 or higher
- Internet connection for downloading dependencies

## Option 1: Install with UV (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast Python package manager written in Rust.

### Step 1: Install UV

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

### Step 2: Install Dependencies

```bash
# Install all dependencies and create virtual environment
uv sync

# Test installation
uv run python test_installation.py
```

### Step 3: Basic Usage

```bash
# Extract a presentation from a YouTube video
uv run python main.py "https://youtube.com/watch?v=VIDEO_ID"

# The output will be saved in the 'output' directory
```

### Step 4: Advanced Usage

```bash
# Adjust sensitivity for better scene detection
uv run python main.py "https://youtube.com/watch?v=VIDEO_ID" --sensitivity 0.5

# Generate Markdown output
uv run python main.py "https://youtube.com/watch?v=VIDEO_ID" --format markdown

# Custom output directory
uv run python main.py "https://youtube.com/watch?v=VIDEO_ID" --output-dir my_presentations
```

### Step 5: Install Globally (Optional)

```bash
# Install the package globally for easier access
uv pip install -e .

# Now you can use the commands from anywhere
youtube-extractor "https://youtube.com/watch?v=VIDEO_ID"
youtube-extractor-batch sample_urls.txt
```

## Option 2: Install with pip

### Step 1: Install Dependencies

```bash
# Install all required Python packages
pip install -r requirements.txt

# Install yt-dlp (if not already installed)
pip install yt-dlp
```

### Step 2: Test Installation

```bash
# Run the installation test
python test_installation.py
```

If all tests pass, you're ready to use the tool!

### Step 3: Basic Usage

```bash
# Extract a presentation from a YouTube video
python main.py "https://youtube.com/watch?v=VIDEO_ID"

# The output will be saved in the 'output' directory
```

### Step 4: Advanced Usage

```bash
# Adjust sensitivity for better scene detection
python main.py "https://youtube.com/watch?v=VIDEO_ID" --sensitivity 0.5

# Generate Markdown output
python main.py "https://youtube.com/watch?v=VIDEO_ID" --format markdown

# Custom output directory
python main.py "https://youtube.com/watch?v=VIDEO_ID" --output-dir my_presentations
```

## Step 5: Batch Processing (Optional)

```bash
# Create a text file with YouTube URLs (one per line)
# Edit sample_urls.txt with your URLs

# Process multiple videos
# With UV:
uv run python batch_processor.py sample_urls.txt

# With pip:
python batch_processor.py sample_urls.txt
```

## Troubleshooting

### Common Issues

1. **"yt-dlp not found"**
   ```bash
   # With pip
   pip install yt-dlp
   
   # With UV
   uv add yt-dlp
   ```

2. **Missing dependencies**
   ```bash
   # With pip
   pip install -r requirements.txt
   
   # With UV
   uv sync
   ```

3. **Permission errors on Windows**
   - Run PowerShell as Administrator
   - Or use: `python -m pip install -r requirements.txt`

4. **Memory issues with long videos**
   - Use lower resolution: `--target_resolution 1280 720`
   - Increase frame interval: `--frame_rate 0.5`

5. **UV not found**
   ```bash
   # Install UV first
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Getting Help

- Check the full README.md for detailed documentation
- Use `--verbose` flag for detailed error information
- Ensure the YouTube video has subtitles/captions for best results
- For UV-specific help, see UV_INSTALL.md

## UV Advantages

- **Speed**: UV is significantly faster than pip
- **Reliability**: Better dependency resolution
- **Lock Files**: Reproducible builds with uv.lock
- **Modern**: Built with modern Python packaging standards

## Next Steps

1. Read the full README.md for complete documentation
2. Try different sensitivity settings for your videos
3. Experiment with different output formats
4. Use batch processing for multiple videos
5. Customize the configuration file for your needs 