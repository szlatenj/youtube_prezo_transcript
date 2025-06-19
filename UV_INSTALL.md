# YouTube Presentation Extractor - UV Installation Guide

## What is UV?

[UV](https://github.com/astral-sh/uv) is a fast Python package manager and installer, written in Rust. It's designed to be a drop-in replacement for pip, pip-tools, and virtualenv.

## Prerequisites

- Python 3.8 or higher
- UV installed on your system

### Install UV

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

## Installation

### Option 1: Install in Development Mode

```bash
# Clone or download the project
cd youtube_prezo_transcript

# Create virtual environment and install dependencies
uv sync

# Activate the virtual environment
uv run --help
```

### Option 2: Install Globally

```bash
# Install the package globally
uv pip install -e .

# Now you can use the commands from anywhere
youtube-extractor "https://youtube.com/watch?v=VIDEO_ID"
youtube-extractor-batch sample_urls.txt
```

## Usage with UV

### Basic Usage

```bash
# Run the main script
uv run python main.py "https://youtube.com/watch?v=VIDEO_ID"

# Or use the installed command
uv run youtube-extractor "https://youtube.com/watch?v=VIDEO_ID"
```

### Batch Processing

```bash
# Run batch processor
uv run python batch_processor.py sample_urls.txt

# Or use the installed command
uv run youtube-extractor-batch sample_urls.txt
```

### Development

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run flake8 .

# Type checking
uv run mypy .
```

## UV Commands

### Package Management

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Remove dependency
uv remove package-name

# Update dependencies
uv sync --upgrade
```

### Virtual Environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Run commands in virtual environment
uv run python main.py "URL"
```

### Project Management

```bash
# Initialize new project
uv init

# Build package
uv build

# Publish package
uv publish
```

## Advantages of UV

1. **Speed**: UV is significantly faster than pip
2. **Reliability**: Better dependency resolution
3. **Compatibility**: Drop-in replacement for pip
4. **Lock Files**: Reproducible builds with uv.lock
5. **Modern**: Built with modern Python packaging standards

## Troubleshooting

### Common Issues

1. **UV not found**
   ```bash
   # Install UV first
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Permission errors**
   ```bash
   # Use --user flag
   uv pip install --user -e .
   ```

3. **Virtual environment issues**
   ```bash
   # Remove and recreate
   rm -rf .venv
   uv sync
   ```

### Migration from pip

If you're migrating from pip:

```bash
# Remove old virtual environment
rm -rf venv/

# Remove requirements.txt (optional)
# rm requirements.txt

# Use UV instead
uv sync
```

## Configuration

The project uses `pyproject.toml` for configuration, which is the modern Python standard. UV automatically reads this file for:

- Dependencies
- Development dependencies
- Scripts
- Build configuration
- Tool configurations (black, flake8, mypy)

## Next Steps

1. Run `uv sync` to install dependencies
2. Test installation: `uv run python test_installation.py`
3. Try extracting a presentation: `uv run python main.py "YOUR_URL"`
4. Read the full README.md for detailed usage instructions 