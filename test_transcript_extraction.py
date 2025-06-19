#!/usr/bin/env python3
"""
Test script for transcript extraction and saving
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import Config
from video_processor import VideoProcessor
from transcript_parser import TranscriptParser


def test_transcript_extraction(youtube_url: str):
    """Test transcript extraction from a YouTube video."""
    print("Testing Transcript Extraction...")
    print("=" * 50)
    
    # Create test configuration
    config = Config()
    config.output_directory = "test_output"
    os.makedirs(config.output_directory, exist_ok=True)
    
    try:
        # Initialize components
        video_processor = VideoProcessor(config)
        transcript_parser = TranscriptParser()
        
        # Download video
        print(f"Downloading video: {youtube_url}")
        metadata = video_processor.download_video(youtube_url)
        print(f"Video title: {metadata.title}")
        print(f"Duration: {metadata.duration:.2f} seconds")
        
        # Get subtitle files
        subtitle_files = video_processor.get_subtitle_files()
        print(f"\nFound {len(subtitle_files)} subtitle files:")
        for file in subtitle_files:
            print(f"  - {Path(file).name}")
        
        if not subtitle_files:
            print("❌ No subtitle files found!")
            print("This might be because:")
            print("  - The video doesn't have subtitles/captions")
            print("  - Subtitles are not available in English")
            print("  - yt-dlp failed to download subtitles")
            return False
        
        # Load subtitles
        if transcript_parser.load_subtitles(subtitle_files):
            stats = transcript_parser.get_statistics()
            print(f"\n✅ Successfully loaded transcript:")
            print(f"  - Total segments: {stats.get('total_segments', 0)}")
            print(f"  - Total words: {stats.get('total_words', 0)}")
            print(f"  - Duration: {stats.get('duration', 0):.2f} seconds")
            
            # Save original transcript
            original_path = os.path.join(config.output_directory, "test_original_transcript.txt")
            if transcript_parser.save_original_transcript(original_path):
                print(f"✅ Original transcript saved to: {original_path}")
            else:
                print("❌ Failed to save original transcript")
            
            # Save enhanced transcript (same as original for now)
            enhanced_path = os.path.join(config.output_directory, "test_enhanced_transcript.txt")
            if transcript_parser.save_enhanced_transcript(enhanced_path):
                print(f"✅ Enhanced transcript saved to: {enhanced_path}")
            else:
                print("❌ Failed to save enhanced transcript")
            
            # Show first few segments
            print(f"\nFirst 3 transcript segments:")
            for i, segment in enumerate(transcript_parser.segments[:3], 1):
                start_time = transcript_parser._format_timestamp(segment.start_time)
                end_time = transcript_parser._format_timestamp(segment.end_time)
                print(f"  {i}. [{start_time} - {end_time}] {segment.text[:100]}...")
            
            return True
        else:
            print("❌ Failed to parse subtitle files")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if 'video_processor' in locals():
            video_processor.cleanup()


def main():
    """Main test function."""
    if len(sys.argv) != 2:
        print("Usage: python test_transcript_extraction.py <youtube_url>")
        print("Example: python test_transcript_extraction.py 'https://youtube.com/watch?v=VIDEO_ID'")
        sys.exit(1)
    
    youtube_url = sys.argv[1]
    
    print("Transcript Extraction Test")
    print("=" * 50)
    print(f"URL: {youtube_url}")
    print()
    
    success = test_transcript_extraction(youtube_url)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
        print("Check the 'test_output' directory for transcript files.")
    else:
        print("❌ Test failed!")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 