# YouTube Presentation Extractor

A powerful Python tool that converts YouTube presentation videos into structured documents containing screenshots of slides and synchronized transcript text, with optional AI-powered transcript enhancement using Anthropic's Claude.

## Features

- **Automatic Video Download**: Downloads YouTube videos using yt-dlp
- **Intelligent Scene Detection**: Uses multiple algorithms (SSIM, histogram comparison, PySceneDetect) to detect significant visual changes
- **Transcript Synchronization**: Extracts and synchronizes subtitles/transcripts with slides
- **AI-Powered Transcript Enhancement**: Optional enhancement using Anthropic's Claude for improved clarity and key point extraction
- **Multiple Output Formats**: Generates HTML, Markdown, and PDF documents
- **Professional Styling**: Clean, responsive HTML output with navigation
- **Configurable Settings**: Adjustable sensitivity, timing, and output options
- **Error Handling**: Robust error handling with informative messages
- **Cost Management**: Built-in cost tracking and limits for AI enhancement
- **Space Efficient**: Screenshots are not saved to disk to save space and improve performance

## Installation

### Prerequisites

- Python 3.8 or higher
- yt-dlp (for video downloading)
- Anthropic API key (for transcript enhancement - optional)

### Option 1: Install with UV (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast Python package manager written in Rust.

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync

# Test installation
uv run python test_installation.py

# Run the tool
uv run python main.py "https://youtube.com/watch?v=VIDEO_ID"
```

### Option 2: Install with pip

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install yt-dlp (if not already installed)
pip install yt-dlp

# Test installation
python test_installation.py
```

### Setting up AI Enhancement (Optional)

To use the AI transcript enhancement feature:

1. **Get an Anthropic API key**:
   - Sign up at [Anthropic Console](https://console.anthropic.com/)
   - Create an API key
   - Note your API key for the next step

2. **Set the API key** (choose one method):

   **Option A: Environment Variable**
   ```bash
   # On Linux/macOS:
   export ANTHROPIC_API_KEY="your-api-key-here"
   
   # On Windows (PowerShell):
   $env:ANTHROPIC_API_KEY="your-api-key-here"
   
   # On Windows (Command Prompt):
   set ANTHROPIC_API_KEY=your-api-key-here
   ```

   **Option B: .env File (Recommended)**
   ```bash
   # Create a .env file in the project directory
   echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
   
   # Or manually create .env file with:
   # ANTHROPIC_API_KEY=your-api-key-here
   ```

3. **Test the enhancement**:
   ```bash
   python main.py "https://youtube.com/watch?v=VIDEO_ID" --enhance-transcript
   ```

### Optional Dependencies

For OCR capabilities (future enhancement):
```bash
# Install Tesseract OCR
# On Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# On Windows:
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
```

## Usage

### Basic Usage

```bash
# Extract presentation from YouTube video
python main.py "https://youtube.com/watch?v=VIDEO_ID"

# With UV
uv run python main.py "https://youtube.com/watch?v=VIDEO_ID"

# Specify output format and filename
python main.py "https://youtube.com/watch?v=VIDEO_ID" --output presentation.html --format html
```

### AI Transcript Enhancement

```bash
# Enable basic transcript enhancement
python main.py "https://youtube.com/watch?v=VIDEO_ID" --enhance-transcript

# Use detailed enhancement (default)
python main.py "https://youtube.com/watch?v=VIDEO_ID" --enhance-transcript --enhancement-level detailed

# Use academic enhancement for scholarly content
python main.py "https://youtube.com/watch?v=VIDEO_ID" --enhance-transcript --enhancement-level academic

# Set cost limit for enhancement
python main.py "https://youtube.com/watch?v=VIDEO_ID" --enhance-transcript --max-cost 3.0

# Disable caching of enhanced results
python main.py "https://youtube.com/watch?v=VIDEO_ID" --enhance-transcript --no-cache
```

### Advanced Usage

```bash
# Adjust scene detection sensitivity
python main.py "https://youtube.com/watch?v=VIDEO_ID" --sensitivity 0.5

# Set minimum time between screenshots
python main.py "https://youtube.com/watch?v=VIDEO_ID" --min-time 3.0

# Generate Markdown output
python main.py "https://youtube.com/watch?v=VIDEO_ID" --format markdown

# Generate PDF output
python main.py "https://youtube.com/watch?v=VIDEO_ID" --format pdf --output presentation.pdf

# Custom output directory
python main.py "https://youtube.com/watch?v=VIDEO_ID" --output-dir my_presentations

# Disable intro/outro skipping
python main.py "https://youtube.com/watch?v=VIDEO_ID" --no-intro-outro

# Save configuration for reuse
python main.py "https://youtube.com/watch?v=VIDEO_ID" --save-config my_config.json

# Use saved configuration
python main.py "https://youtube.com/watch?v=VIDEO_ID" --config my_config.json
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `youtube_url` | YouTube video URL (required) | - |
| `--output, -o` | Output filename | `presentation.html` |
| `--format, -f` | Output format (`html`, `markdown`, or `pdf`) | `html` |
| `--output-dir, -d` | Output directory | `output` |
| `--sensitivity, -s` | Scene change detection sensitivity (0.1-1.0) | `0.3` |
| `--min-time, -m` | Minimum time between screenshots (seconds) | `2.0` |
| `--enhance-transcript, -et` | Enable AI transcript enhancement | `False` |
| `--enhancement-level, -el` | Enhancement level (`basic`, `detailed`, `academic`) | `detailed` |
| `--max-cost, -mc` | Maximum cost per video for enhancement (USD) | `5.0` |
| `--no-cache` | Don't cache enhanced results | `False` |
| `--config` | Path to configuration file | - |
| `--save-config` | Save current settings to configuration file | - |
| `--no-intro-outro` | Don't skip intro/outro sections | - |
| `--no-timestamps` | Don't include timestamps in output | - |
| `--no-navigation` | Don't include navigation in output | - |
| `--verbose, -v` | Enable verbose output | - |

## AI Transcript Enhancement

The tool includes optional AI-powered transcript enhancement using Anthropic's Claude model. This feature can:

### Enhancement Levels

- **Basic**: Fixes typos, improves sentence structure, maintains original meaning
- **Detailed**: Adds context, extracts key points, improves clarity and flow
- **Academic**: Converts to formal scholarly language with proper citations

### Features

- **Intelligent Batching**: Groups transcript segments into ~200 token batches for efficient processing
- **Prompt Customization**: Supports custom prompt templates and different styles (clear, academic, conversational, technical)
- **Cost Management**: Built-in cost tracking and limits to prevent unexpected charges
- **Caching**: Optional caching of enhanced results to avoid re-processing
- **Error Handling**: Graceful fallback to original transcripts if enhancement fails
- **Progress Tracking**: Real-time progress updates during enhancement
- **Statistics**: Detailed cost and processing statistics

### Batching System

The enhancement system uses intelligent batching to optimize API calls:

- **Target Batch Size**: ~200 tokens per batch (configurable)
- **Token Estimation**: Uses character-based estimation (1 token ≈ 4 characters)
- **Smart Distribution**: Distributes enhanced text back to individual segments
- **Configurable**: Can be disabled to process segments individually

### Prompt Customization

You can customize how the LLM processes your transcripts:

#### Prompt Styles
- **Clear**: Standard professional enhancement
- **Academic**: Formal scholarly language
- **Conversational**: Engaging, accessible language
- **Technical**: Precise technical language

#### Custom Templates
You can provide your own prompt template using placeholders:
- `{text}`: The transcript text to enhance
- `{level}`: Enhancement level (basic, detailed, academic)
- `{style}`: Prompt style

Example custom template:
```json
{
  "custom_prompt_template": "You are an expert at improving presentation transcripts. Please enhance: {text}. Focus on clarity and professional language."
}
```

### Cost Estimation

Approximate costs for transcript enhancement:
- **Basic**: ~$0.001-0.003 per segment
- **Detailed**: ~$0.002-0.005 per segment  
- **Academic**: ~$0.003-0.007 per segment

With batching, costs are typically 30-50% lower due to fewer API calls.

A typical 10-minute presentation with 50 segments might cost $0.05-0.20 with batching.

### Output Integration

Enhanced transcripts are integrated into all output formats:
- **HTML**: Enhanced text prominently displayed with original as reference
- **Markdown**: Enhanced text with key points and collapsible original transcript
- **PDF**: Enhanced content with proper formatting and structure

## Configuration

The tool uses a configuration system that can be customized via JSON files or command-line arguments.

### Default Configuration

```json
{
  "scene_change_threshold": 0.3,
  "min_time_between_captures": 2.0,
  "histogram_threshold": 0.15,
  "target_resolution": null,
  "frame_rate": 1,
  "skip_intro_outro": true,
  "intro_outro_duration": 30.0,
  "screenshot_format": "PNG",
  "screenshot_quality": 95,
  "output_directory": "output",
  "output_format": "HTML",
  "include_timestamps": true,
  "include_navigation": true,
  "enable_llm_enhancement": false,
  "enhancement_level": "detailed",
  "anthropic_model": "claude-3-7-sonnet-20250219",
  "max_tokens_per_request": 1000,
  "max_cost_per_video": 5.0,
  "cache_enhanced_results": true,
  "cache_file": "enhancement_cache.json",
  "batch_target_tokens": 200,
  "enable_batching": true,
  "batch_overlap_tolerance": 0.2,
  "custom_prompt_template": null,
  "prompt_style": "clear"
}
```

### Configuration Options

- **scene_change_threshold**: SSIM threshold for detecting scene changes (0.1-1.0)
- **min_time_between_captures**: Minimum seconds between screenshots
- **histogram_threshold**: Histogram comparison threshold
- **target_resolution**: Target resolution for processing (width, height) or null for original
- **frame_rate**: Frames per second to process
- **skip_intro_outro**: Whether to skip intro/outro sections
- **intro_outro_duration**: Seconds to skip from start/end
- **screenshot_format**: Image format (PNG or JPEG)
- **screenshot_quality**: JPEG quality (1-100)
- **output_directory**: Directory for output files
- **output_format**: Output format (HTML, MARKDOWN, or PDF)
- **include_timestamps**: Include timestamps in output
- **include_navigation**: Include navigation in output
- **enable_llm_enhancement**: Enable AI transcript enhancement
- **enhancement_level**: Level of enhancement (basic, detailed, academic)
- **anthropic_model**: Claude model to use for enhancement
- **max_tokens_per_request**: Maximum tokens per API request
- **max_cost_per_video**: Maximum cost per video in USD
- **cache_enhanced_results**: Cache enhancement results
- **cache_file**: Cache file path
- **batch_target_tokens**: Target tokens per batch for transcript enhancement
- **enable_batching**: Enable batching for transcript enhancement
- **batch_overlap_tolerance**: Allow overlap in batch sizes (0.0-1.0)
- **custom_prompt_template**: Custom prompt template (optional)
- **prompt_style**: Prompt style (clear, academic, conversational, technical)

## Output Formats

### HTML Output

The HTML output includes:
- Professional styling with responsive design
- Navigation sidebar with slide links
- Screenshots embedded inline
- Synchronized transcript text
- Timestamps for reference
- Metadata (video title, duration, generation date)

### Markdown Output

The Markdown output includes:
- Table of contents with timestamps
- Screenshots as image links
- Transcript text for each slide
- Clean, readable formatting

### PDF Output

The PDF output includes:
- Professional page layout with proper margins
- One slide per page with page breaks
- Embedded screenshots with consistent sizing
- Formatted transcript text
- Timestamps and metadata
- Print-optimized styling

**PDF Generation Methods:**
- **WeasyPrint** (primary): Converts HTML to PDF with CSS styling
- **ReportLab** (fallback): Direct PDF generation with custom layout
- **HTML fallback**: If PDF generation fails, creates HTML file instead

## Project Structure

```
youtube_prezo_transcript/
├── main.py              # Entry point and CLI interface
├── config.py           # Configuration settings
├── video_processor.py  # Video download and frame extraction
├── scene_detector.py   # Scene change detection logic
├── transcript_parser.py # Subtitle/transcript handling
├── document_generator.py # HTML/Markdown/PDF output generation
├── batch_processor.py  # Batch processing for multiple videos
├── test_installation.py # Installation verification
├── pyproject.toml      # Project configuration (UV/pip)
├── requirements.txt    # Python dependencies (pip)
├── sample_config.json  # Sample configuration file
├── sample_urls.txt     # Sample URLs for batch processing
├── INSTALL.md         # Quick installation guide
├── UV_INSTALL.md      # UV-specific installation guide
└── README.md          # This file
```

## How It Works

1. **Video Download**: Uses yt-dlp to download the YouTube video and extract metadata
2. **Subtitle Extraction**: Downloads and parses subtitle files (SRT, VTT, JSON)
3. **Frame Extraction**: Extracts frames from the video at specified intervals
4. **Scene Detection**: Uses multiple algorithms to detect significant visual changes:
   - Structural Similarity Index (SSIM)
   - Histogram comparison
   - PySceneDetect library
5. **Slide Reference Generation**: Creates references for detected scene changes (screenshots not saved to disk)
6. **Transcript Synchronization**: Matches transcript segments to slide timestamps
7. **Document Generation**: Creates HTML, Markdown, or PDF document with transcript content

## Scene Detection Algorithms

### SSIM (Structural Similarity Index)
- Compares structural information between consecutive frames
- More accurate than pixel-by-pixel comparison
- Configurable threshold for sensitivity

### Histogram Comparison
- Compares color histograms between frames
- Good for detecting color changes
- Less sensitive to minor movements

### PySceneDetect
- Advanced scene detection library
- Content-based detection algorithm
- Fallback when other methods fail

## Error Handling

The tool includes comprehensive error handling for:
- Invalid YouTube URLs
- Network connectivity issues
- Missing subtitle files
- Video format compatibility
- Memory limitations
- File system errors
- PDF generation failures

## Performance Optimization

- **Chunked Processing**: Processes video in chunks to manage memory
- **Configurable Resolution**: Option to downscale for faster processing
- **Efficient Algorithms**: Optimized frame comparison methods
- **Progress Indicators**: Shows progress for long videos

## Troubleshooting

### Common Issues

1. **"yt-dlp not found"**
   ```bash
   # With pip
   pip install yt-dlp
   
   # With UV
   uv add yt-dlp
   ```

2. **"No subtitle files found"**
   - The video might not have subtitles
   - Try videos with manual captions
   - Auto-generated captions are used as fallback

3. **"No scene changes detected"**
   - Adjust sensitivity with `--sensitivity` option
   - Try videos with clear slide transitions
   - Check if video contains presentation content

4. **Memory issues with long videos**
   - Reduce target resolution
   - Increase frame interval
   - Process shorter video segments

5. **PDF generation fails**
   - Install WeasyPrint: `pip install weasyprint`
   - Install ReportLab: `pip install reportlab`
   - Check system dependencies for WeasyPrint

### Debug Mode

Use the `--verbose` flag for detailed error information:
```bash
python main.py "https://youtube.com/watch?v=VIDEO_ID" --verbose
```

## Examples

### Example 1: Basic Presentation Extraction
```bash
python main.py "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

### Example 2: High-Sensitivity Detection
```bash
python main.py "https://youtube.com/watch?v=dQw4w9WgXcQ" --sensitivity 0.1 --min-time 1.0
```

### Example 3: Markdown Output with Custom Settings
```bash
python main.py "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --format markdown \
  --output my_presentation.md \
  --output-dir presentations \
  --no-timestamps
```

### Example 4: PDF Generation
```bash
python main.py "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --format pdf \
  --output presentation.pdf \
  --sensitivity 0.4
```

### Example 5: Using UV
```bash
# Install and run with UV
uv sync
uv run python main.py "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Or install globally
uv pip install -e .
youtube-extractor "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube video downloading
- [OpenCV](https://opencv.org/) for computer vision capabilities
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) for advanced scene detection
- [Jinja2](https://jinja.palletsprojects.com/) for HTML templating
- [WeasyPrint](https://weasyprint.org/) for HTML to PDF conversion
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [UV](https://github.com/astral-sh/uv) for fast Python package management 