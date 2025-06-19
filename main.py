#!/usr/bin/env python3
"""
YouTube Presentation Extractor
Main entry point for extracting presentations from YouTube videos
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

from config import Config, load_config_from_file, save_config_to_file, get_resolution_presets
from video_processor import VideoProcessor
from scene_detector import SceneDetector
from transcript_parser import TranscriptParser
from document_generator import DocumentGenerator
from transcript_enhancer import TranscriptEnhancer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract presentations from YouTube videos with screenshots and transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "https://youtube.com/watch?v=VIDEO_ID"
  python main.py "https://youtube.com/watch?v=VIDEO_ID" --output presentation.html --sensitivity 0.3
  python main.py "https://youtube.com/watch?v=VIDEO_ID" --format markdown --output-dir my_presentations
  python main.py "https://youtube.com/watch?v=VIDEO_ID" --format pdf --output presentation.pdf
  python main.py "https://youtube.com/watch?v=VIDEO_ID" --resolution 1920 1080 --video-quality 1080p
  python main.py "https://youtube.com/watch?v=VIDEO_ID" --resolution-preset 1080p
  python main.py "https://youtube.com/watch?v=VIDEO_ID" --enhance-transcript --enhancement-level detailed
        """
    )
    
    parser.add_argument(
        "youtube_url",
        help="YouTube video URL to extract presentation from"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="presentation.html",
        help="Output filename (default: presentation.html)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["html", "markdown", "pdf"],
        default="html",
        help="Output format (default: html)"
    )
    
    parser.add_argument(
        "--output-dir", "-d",
        default="output",
        help="Output directory (default: output)"
    )
    
    parser.add_argument(
        "--sensitivity", "-s",
        type=float,
        default=0.3,
        help="Scene change detection sensitivity (0.1-1.0, default: 0.3)"
    )
    
    parser.add_argument(
        "--min-time", "-m",
        type=float,
        default=2.0,
        help="Minimum time between screenshots in seconds (default: 2.0)"
    )
    
    parser.add_argument(
        "--resolution", "-r",
        nargs=2,
        type=int,
        metavar=('WIDTH', 'HEIGHT'),
        help="Target resolution for processing (width height, e.g., 1920 1080)"
    )
    
    parser.add_argument(
        "--resolution-preset", "-rp",
        choices=list(get_resolution_presets().keys()),
        help="Use a preset resolution (144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p, 4k, hd, fullhd, qhd, uhd)"
    )
    
    parser.add_argument(
        "--video-quality", "-vq",
        choices=["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"],
        default="720p",
        help="Video quality to download (default: 720p)"
    )
    
    parser.add_argument(
        "--screenshot-resolution", "-sr",
        nargs=2,
        type=int,
        metavar=('WIDTH', 'HEIGHT'),
        help="Screenshot resolution (width height, e.g., 1280 720)"
    )
    
    # LLM Enhancement arguments
    parser.add_argument(
        "--enhance-transcript", "-et",
        action="store_true",
        help="Enable AI transcript enhancement using Claude"
    )
    
    parser.add_argument(
        "--enhancement-level", "-el",
        choices=["basic", "detailed", "academic"],
        default="detailed",
        help="Level of transcript enhancement (default: detailed)"
    )
    
    parser.add_argument(
        "--max-cost", "-mc",
        type=float,
        default=5.0,
        help="Maximum cost per video for enhancement in USD (default: 5.0)"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't cache enhanced results"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--save-config",
        help="Save current settings to configuration file"
    )
    
    parser.add_argument(
        "--no-intro-outro",
        action="store_true",
        help="Don't skip intro/outro sections"
    )
    
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Don't include timestamps in output"
    )
    
    parser.add_argument(
        "--no-navigation",
        action="store_true",
        help="Don't include navigation in output"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def validate_url(url: str) -> bool:
    """Validate YouTube URL format."""
    youtube_patterns = [
        r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
        r"https?://youtu\.be/[\w-]+",
        r"https?://(?:www\.)?youtube\.com/embed/[\w-]+"
    ]
    
    import re
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    return False


def main():
    """Main function."""
    args = parse_arguments()
    
    # Validate YouTube URL
    if not validate_url(args.youtube_url):
        print("Error: Invalid YouTube URL format")
        print("Supported formats:")
        print("  https://youtube.com/watch?v=VIDEO_ID")
        print("  https://youtu.be/VIDEO_ID")
        print("  https://youtube.com/embed/VIDEO_ID")
        sys.exit(1)
    
    # Load configuration
    config = Config()
    if args.config:
        config = load_config_from_file(args.config)
    
    # Override config with command line arguments
    config.output_directory = args.output_dir
    config.output_format = args.format.upper()
    config.scene_change_threshold = args.sensitivity
    config.min_time_between_captures = args.min_time
    config.skip_intro_outro = not args.no_intro_outro
    config.include_timestamps = not args.no_timestamps
    config.include_navigation = not args.no_navigation
    config.video_quality = args.video_quality
    
    # LLM Enhancement settings
    config.enable_llm_enhancement = args.enhance_transcript
    config.enhancement_level = args.enhancement_level
    config.max_cost_per_video = args.max_cost
    config.cache_enhanced_results = not args.no_cache
    
    # Handle resolution settings
    if args.resolution_preset:
        presets = get_resolution_presets()
        config.target_resolution = presets[args.resolution_preset]
        print(f"Using preset resolution: {args.resolution_preset} ({config.target_resolution[0]}x{config.target_resolution[1]})")
    elif args.resolution:
        config.target_resolution = tuple(args.resolution)
        print(f"Using custom resolution: {config.target_resolution[0]}x{config.target_resolution[1]}")
    
    # Handle screenshot resolution
    if args.screenshot_resolution:
        config.screenshot_resolution = tuple(args.screenshot_resolution)
        print(f"Using screenshot resolution: {config.screenshot_resolution[0]}x{config.screenshot_resolution[1]}")
    
    # Save configuration if requested
    if args.save_config:
        save_config_to_file(config, args.save_config)
        print(f"Configuration saved to: {args.save_config}")
    
    # Ensure output directory exists
    os.makedirs(config.output_directory, exist_ok=True)
    
    print("=" * 60)
    print("YouTube Presentation Extractor")
    print("=" * 60)
    print(f"URL: {args.youtube_url}")
    print(f"Output: {os.path.join(config.output_directory, args.output)}")
    print(f"Format: {config.output_format}")
    print(f"Video Quality: {config.video_quality}")
    if config.target_resolution:
        print(f"Target Resolution: {config.target_resolution[0]}x{config.target_resolution[1]}")
    if config.screenshot_resolution:
        print(f"Screenshot Resolution: {config.screenshot_resolution[0]}x{config.screenshot_resolution[1]}")
    print(f"Sensitivity: {config.scene_change_threshold}")
    print(f"Min time between captures: {config.min_time_between_captures}s")
    if config.enable_llm_enhancement:
        print(f"LLM Enhancement: {config.enhancement_level} level")
        print(f"Max cost: ${config.max_cost_per_video}")
    print("-" * 60)
    
    try:
        # Initialize components
        video_processor = VideoProcessor(config)
        scene_detector = SceneDetector(config)
        transcript_parser = TranscriptParser()
        document_generator = DocumentGenerator(config)
        
        # Initialize transcript enhancer if enabled
        transcript_enhancer = None
        if config.enable_llm_enhancement:
            try:
                transcript_enhancer = TranscriptEnhancer(config)
                print("LLM enhancement initialized successfully")
            except Exception as e:
                print(f"Warning: Failed to initialize LLM enhancement: {e}")
                print("Continuing without transcript enhancement...")
                config.enable_llm_enhancement = False
        
        # Download video
        print("\n1. Downloading video...")
        metadata = video_processor.download_video(args.youtube_url)
        
        # Load subtitles
        print("\n2. Loading subtitles...")
        subtitle_files = video_processor.get_subtitle_files()
        if subtitle_files:
            print(f"   Found {len(subtitle_files)} subtitle files:")
            for file in subtitle_files:
                print(f"     - {Path(file).name}")
            
            if transcript_parser.load_subtitles(subtitle_files):
                stats = transcript_parser.get_statistics()
                print(f"   Loaded {stats.get('total_segments', 0)} transcript segments")
                print(f"   Total words: {stats.get('total_words', 0)}")
                
                # Save original transcript
                original_transcript_path = os.path.join(config.output_directory, "original_transcript.txt")
                transcript_parser.save_original_transcript(original_transcript_path)
            else:
                print("   Warning: Could not parse subtitle files")
        else:
            print("   Warning: No subtitle files found")
            print("   This might be because:")
            print("     - The video doesn't have subtitles/captions")
            print("     - Subtitles are not available in the requested language")
            print("     - yt-dlp failed to download subtitles")
        
        # Extract frames
        print("\n3. Extracting video frames...")
        start_time = config.intro_outro_duration if config.skip_intro_outro else 0
        end_time = metadata.duration - config.intro_outro_duration if config.skip_intro_outro else None
        
        frames = video_processor.extract_frames(start_time, end_time)
        
        if not frames:
            print("Error: No frames extracted from video")
            sys.exit(1)
        
        # Detect scene changes
        print("\n4. Detecting scene changes...")
        scene_changes = scene_detector.detect_scenes(frames)
        
        if not scene_changes:
            print("Warning: No scene changes detected. Trying advanced detection...")
            scene_changes = scene_detector.detect_scenes_advanced(video_processor.video_path)
        
        if not scene_changes:
            print("Error: No scene changes detected. The video might not contain presentation slides.")
            sys.exit(1)
        
        # Filter and merge scene changes
        scene_changes = scene_detector.filter_changes_by_confidence(scene_changes, min_confidence=0.3)
        scene_changes = scene_detector.merge_nearby_changes(scene_changes, time_threshold=1.0)
        scene_changes = scene_detector.skip_intro_outro(scene_changes, metadata.duration)
        
        print(f"   Detected {len(scene_changes)} significant scene changes")
        
        # Generate slide references
        print("\n5. Generating slide references...")
        screenshot_paths = document_generator.save_screenshots(frames, scene_changes)
        
        # Create initial slides to determine time ranges
        print("\n6. Creating slide structure...")
        initial_slides = document_generator._create_slides(scene_changes, transcript_parser)
        print(f"   Created {len(initial_slides)} slides with time ranges")
        
        # Enhance transcripts based on slide time ranges if enabled
        if config.enable_llm_enhancement and transcript_enhancer:
            print("\n7. Enhancing transcripts based on slide time ranges...")
            try:
                # Enhance transcripts for each slide's time range
                enhanced_slides = document_generator._enhance_slides_with_llm(
                    initial_slides, transcript_parser, transcript_enhancer, config.enhancement_level
                )
                
                # Update the slides with enhanced content
                initial_slides = enhanced_slides
                
                # Save enhanced transcript
                enhanced_transcript_path = os.path.join(config.output_directory, "enhanced_transcript.txt")
                document_generator._save_enhanced_transcript_by_slides(enhanced_slides, enhanced_transcript_path)
                
                print(f"   Enhanced transcripts for {len(enhanced_slides)} slides")
                
            except Exception as e:
                print(f"   Warning: Transcript enhancement failed: {e}")
                print("   Continuing with original transcripts...")
        
        # Generate presentation document
        print("\n8. Generating presentation document...")
        output_path = document_generator.create_presentation_with_slides(
            slides=initial_slides,
            video_title=metadata.title,
            video_duration=metadata.duration,
            output_filename=args.output
        )
        
        # Cleanup
        video_processor.cleanup()
        
        # Save enhancement cache if available
        if transcript_enhancer and config.cache_enhanced_results:
            cache_path = os.path.join(config.output_directory, config.cache_file)
            transcript_enhancer.save_cache(cache_path)
        
        print("\n" + "=" * 60)
        print("Extraction completed successfully!")
        print(f"Output file: {output_path}")
        print(f"Total slides: {len(scene_changes)}")
        print(f"Video duration: {metadata.duration:.2f} seconds")
        
        if config.enable_llm_enhancement and transcript_enhancer:
            enh_stats = transcript_enhancer.get_stats()
            print(f"Enhanced segments: {enh_stats.enhanced_segments}")
            print(f"Total enhancement cost: ${enh_stats.total_cost:.2f}")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nExtraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 