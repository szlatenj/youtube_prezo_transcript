#!/usr/bin/env python3
"""
Setup script for YouTube Presentation Extractor with UV
"""

import os
import sys
import subprocess
import platform

def check_uv_installed():
    """Check if UV is installed."""
    try:
        result = subprocess.run(['uv', '--version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def install_uv():
    """Install UV if not already installed."""
    print("UV not found. Installing UV...")
    
    system = platform.system().lower()
    
    if system == "windows":
        print("Installing UV on Windows...")
        try:
            subprocess.run([
                "powershell", "-c", 
                "irm https://astral.sh/uv/install.ps1 | iex"
            ], check=True)
            print("✓ UV installed successfully!")
        except subprocess.CalledProcessError:
            print("✗ Failed to install UV. Please install manually:")
            print("  pip install uv")
            return False
    else:
        print("Installing UV on Unix-like system...")
        try:
            subprocess.run([
                "curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"
            ], shell=True, check=True)
            print("✓ UV installed successfully!")
        except subprocess.CalledProcessError:
            print("✗ Failed to install UV. Please install manually:")
            print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
    
    return True

def setup_project():
    """Set up the project with UV."""
    print("\nSetting up YouTube Presentation Extractor...")
    
    # Check if pyproject.toml exists
    if not os.path.exists('pyproject.toml'):
        print("✗ pyproject.toml not found. Please run this script from the project directory.")
        return False
    
    # Install dependencies
    print("Installing dependencies with UV...")
    try:
        subprocess.run(['uv', 'sync'], check=True)
        print("✓ Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies.")
        return False
    
    return True

def test_installation():
    """Test the installation."""
    print("\nTesting installation...")
    try:
        result = subprocess.run(['uv', 'run', 'python', 'test_installation.py'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ Installation test passed!")
            return True
        else:
            print("✗ Installation test failed:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ Installation test timed out.")
        return False
    except Exception as e:
        print(f"✗ Installation test failed: {e}")
        return False

def show_next_steps():
    """Show next steps to the user."""
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nYou can now use the YouTube Presentation Extractor:")
    print("\nBasic usage:")
    print("  uv run python main.py \"https://youtube.com/watch?v=VIDEO_ID\"")
    print("\nAdvanced usage:")
    print("  uv run python main.py \"URL\" --sensitivity 0.5 --format markdown")
    print("\nBatch processing:")
    print("  uv run python batch_processor.py sample_urls.txt")
    print("\nInstall globally (optional):")
    print("  uv pip install -e .")
    print("  youtube-extractor \"URL\"")
    print("\nFor more information, see:")
    print("  README.md - Complete documentation")
    print("  UV_INSTALL.md - UV-specific guide")
    print("  INSTALL.md - Quick installation guide")

def main():
    """Main setup function."""
    print("YouTube Presentation Extractor - UV Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✓ Python {sys.version.split()[0]} detected")
    
    # Check/install UV
    if not check_uv_installed():
        if not install_uv():
            sys.exit(1)
    else:
        print("✓ UV is already installed")
    
    # Set up project
    if not setup_project():
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("\nInstallation test failed. Please check the errors above.")
        sys.exit(1)
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main() 