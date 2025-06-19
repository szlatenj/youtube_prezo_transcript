#!/usr/bin/env python3
"""
Test script to verify YouTube Presentation Extractor installation
"""

import sys
import importlib

def test_imports():
    """Test if all required modules can be imported."""
    required_modules = [
        'cv2',
        'numpy',
        'PIL',
        'skimage',
        'scenedetect',
        'jinja2',
        'srt'
    ]
    
    print("Testing module imports...")
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    return failed_imports

def test_local_modules():
    """Test if local modules can be imported."""
    local_modules = [
        'config',
        'video_processor',
        'scene_detector',
        'transcript_parser',
        'document_generator'
    ]
    
    print("\nTesting local module imports...")
    failed_imports = []
    
    for module in local_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    return failed_imports

def test_ytdlp():
    """Test if yt-dlp is available."""
    print("\nTesting yt-dlp availability...")
    try:
        import subprocess
        result = subprocess.run(['yt-dlp', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ yt-dlp version: {result.stdout.strip()}")
            return True
        else:
            print("✗ yt-dlp not found or not working")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ yt-dlp not found. Please install it: pip install yt-dlp")
        return False

def main():
    """Run all tests."""
    print("YouTube Presentation Extractor - Installation Test")
    print("=" * 50)
    
    # Test Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("⚠ Warning: Python 3.8 or higher is recommended")
    
    # Test imports
    failed_required = test_imports()
    failed_local = test_local_modules()
    ytdlp_ok = test_ytdlp()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    if not failed_required and not failed_local and ytdlp_ok:
        print("✓ All tests passed! Installation is complete.")
        print("\nYou can now use the YouTube Presentation Extractor:")
        print("python main.py \"https://youtube.com/watch?v=VIDEO_ID\"")
        return True
    else:
        print("✗ Some tests failed. Please fix the issues below:")
        
        if failed_required:
            print(f"\nMissing required modules: {', '.join(failed_required)}")
            print("Install them with: pip install -r requirements.txt")
        
        if failed_local:
            print(f"\nMissing local modules: {', '.join(failed_local)}")
            print("Make sure all Python files are in the same directory")
        
        if not ytdlp_ok:
            print("\nyt-dlp is not properly installed")
            print("Install it with: pip install yt-dlp")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 