#!/usr/bin/env python3
"""
Debug script to test transcript extraction and PDF generation.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from transcript_parser import TranscriptParser
from document_generator import DocumentGenerator, PresentationSlide
from config import Config
from scene_detector import SceneChange

def debug_transcript_extraction():
    """Debug transcript extraction for a specific video."""
    
    # Test with the Rick Astley video
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("=== Debug Transcript Extraction ===")
    print(f"Video URL: {video_url}")
    
    # Initialize transcript parser
    parser = TranscriptParser()
    
    # Check if we have saved transcript files in both locations
    original_file = "output/original_transcript.txt"
    enhanced_file = "output/enhanced_transcript.txt"
    test_original_file = "test_output/test_original_transcript.txt"
    test_enhanced_file = "test_output/test_enhanced_transcript.txt"
    
    # Check output directory
    if os.path.exists(original_file):
        print(f"✅ Found original transcript: {original_file}")
        
        # Read and display some content
        with open(original_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Original transcript length: {len(content)} characters")
            print("First 200 characters:")
            print(content[:200])
            print("...")
    else:
        print(f"❌ Original transcript not found: {original_file}")
    
    if os.path.exists(enhanced_file):
        print(f"✅ Found enhanced transcript: {enhanced_file}")
        
        # Read and display some content
        with open(enhanced_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Enhanced transcript length: {len(content)} characters")
            print("First 200 characters:")
            print(content[:200])
            print("...")
    else:
        print(f"❌ Enhanced transcript not found: {enhanced_file}")
    
    # Check test_output directory
    if os.path.exists(test_original_file):
        print(f"✅ Found test original transcript: {test_original_file}")
        
        # Read and display some content
        with open(test_original_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Test original transcript length: {len(content)} characters")
            print("First 200 characters:")
            print(content[:200])
            print("...")
    else:
        print(f"❌ Test original transcript not found: {test_original_file}")
    
    if os.path.exists(test_enhanced_file):
        print(f"✅ Found test enhanced transcript: {test_enhanced_file}")
        
        # Read and display some content
        with open(test_enhanced_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Test enhanced transcript length: {len(content)} characters")
            print("First 200 characters:")
            print(content[:200])
            print("...")
    else:
        print(f"❌ Test enhanced transcript not found: {test_enhanced_file}")
    
    # Test transcript parser methods
    print("\n=== Testing Transcript Parser Methods ===")
    
    # Load subtitles from the output directory
    subtitle_files = []
    for file in os.listdir("output"):
        if file.endswith(('.srt', '.vtt', '.json')):
            subtitle_files.append(os.path.join("output", file))
    
    if subtitle_files:
        print(f"Found subtitle files: {subtitle_files}")
        
        if parser.load_subtitles(subtitle_files):
            print(f"✅ Loaded {len(parser.segments)} transcript segments")
            
            # Test getting text for specific timestamps
            test_timestamps = [30.0, 60.0, 90.0, 120.0, 150.0]
            
            for timestamp in test_timestamps:
                text = parser.get_text_for_timestamp(timestamp, window=10.0)
                enhanced_text = parser.get_enhanced_text_for_timestamp(timestamp, window=10.0)
                
                print(f"\nTimestamp {timestamp}s:")
                print(f"  Original text: '{text}'")
                print(f"  Enhanced text: '{enhanced_text}'")
                
                if text:
                    print(f"  ✅ Found text ({len(text)} chars)")
                else:
                    print(f"  ❌ No text found")
        else:
            print("❌ Failed to load subtitles")
    else:
        print("❌ No subtitle files found in output directory")
    
    # Test slide creation
    print("\n=== Testing Slide Creation ===")
    
    # Create some test scene changes with correct constructor
    test_scenes = [
        SceneChange(timestamp=30.0, confidence=0.8, change_type='content'),
        SceneChange(timestamp=60.0, confidence=0.9, change_type='content'),
        SceneChange(timestamp=90.0, confidence=0.7, change_type='content'),
        SceneChange(timestamp=120.0, confidence=0.8, change_type='content'),
        SceneChange(timestamp=150.0, confidence=0.9, change_type='content'),
    ]
    
    # Initialize document generator
    config = Config()
    doc_gen = DocumentGenerator(config)
    
    # Create slides
    slides = doc_gen._create_slides(test_scenes, parser)
    
    print(f"Created {len(slides)} test slides:")
    
    for i, slide in enumerate(slides):
        print(f"\nSlide {i+1} (timestamp: {slide.timestamp}s):")
        print(f"  Screenshot: {slide.screenshot_path}")
        print(f"  Transcript: '{slide.transcript_text}'")
        print(f"  Enhanced: '{slide.enhanced_text}'")
        print(f"  Key points: {slide.key_points}")
        
        if slide.transcript_text:
            print(f"  ✅ Has transcript text ({len(slide.transcript_text)} chars)")
        else:
            print(f"  ❌ No transcript text")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    debug_transcript_extraction() 