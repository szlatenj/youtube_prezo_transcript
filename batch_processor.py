#!/usr/bin/env python3
"""
Batch processor for YouTube Presentation Extractor
Process multiple YouTube videos in sequence
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import List, Dict
import time

from config import Config, load_config_from_file
from main import main as process_single_video


def parse_batch_arguments():
    """Parse command line arguments for batch processing."""
    parser = argparse.ArgumentParser(
        description="Batch process multiple YouTube videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_processor.py urls.txt
  python batch_processor.py urls.txt --config my_config.json --output-dir batch_output
  python batch_processor.py urls.txt --format markdown --sensitivity 0.5
        """
    )
    
    parser.add_argument(
        "urls_file",
        help="Text file containing YouTube URLs (one per line)"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--output-dir",
        default="batch_output",
        help="Base output directory for all videos (default: batch_output)"
    )
    
    parser.add_argument(
        "--format",
        choices=["html", "markdown"],
        default="html",
        help="Output format (default: html)"
    )
    
    parser.add_argument(
        "--sensitivity",
        type=float,
        default=0.3,
        help="Scene change detection sensitivity (0.1-1.0, default: 0.3)"
    )
    
    parser.add_argument(
        "--min-time",
        type=float,
        default=2.0,
        help="Minimum time between screenshots in seconds (default: 2.0)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Delay between videos in seconds (default: 5.0)"
    )
    
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing other videos if one fails"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def load_urls_from_file(file_path: str) -> List[str]:
    """Load YouTube URLs from a text file."""
    urls = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Validate URL format
                if not any(pattern in line for pattern in ['youtube.com', 'youtu.be']):
                    print(f"Warning: Line {line_num} doesn't look like a YouTube URL: {line}")
                    continue
                
                urls.append(line)
        
        return urls
        
    except FileNotFoundError:
        print(f"Error: URLs file not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading URLs file: {e}")
        return []


def create_video_output_dir(base_dir: str, video_title: str, video_id: str) -> str:
    """Create a safe output directory name for a video."""
    # Clean the title for use as directory name
    safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title[:50]  # Limit length
    
    # Create directory name
    dir_name = f"{safe_title}_{video_id}"
    dir_path = os.path.join(base_dir, dir_name)
    
    # Ensure directory exists
    os.makedirs(dir_path, exist_ok=True)
    
    return dir_path


def process_video_batch(urls: List[str], config: Config, args) -> Dict:
    """Process a batch of videos."""
    results = {
        'total': len(urls),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    print(f"Starting batch processing of {len(urls)} videos")
    print("=" * 60)
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing: {url}")
        print("-" * 40)
        
        try:
            # Create temporary sys.argv for the single video processor
            original_argv = sys.argv.copy()
            
            # Build command line arguments for single video processing
            single_args = [
                'main.py',
                url,
                '--output-dir', args.output_dir,
                '--format', args.format,
                '--sensitivity', str(args.sensitivity),
                '--min-time', str(args.min_time)
            ]
            
            if args.config:
                single_args.extend(['--config', args.config])
            
            if args.verbose:
                single_args.append('--verbose')
            
            # Temporarily replace sys.argv
            sys.argv = single_args
            
            # Process the video
            process_single_video()
            
            results['successful'] += 1
            print(f"✓ Successfully processed video {i}")
            
        except KeyboardInterrupt:
            print("\nBatch processing interrupted by user")
            break
        except Exception as e:
            error_msg = f"Failed to process video {i}: {str(e)}"
            print(f"✗ {error_msg}")
            results['errors'].append({
                'url': url,
                'index': i,
                'error': str(e)
            })
            results['failed'] += 1
            
            if not args.continue_on_error:
                print("Stopping batch processing due to error")
                break
        
        # Delay between videos (except for the last one)
        if i < len(urls) and args.delay > 0:
            print(f"Waiting {args.delay} seconds before next video...")
            time.sleep(args.delay)
        
        # Restore original sys.argv
        sys.argv = original_argv
    
    return results


def save_batch_results(results: Dict, output_file: str):
    """Save batch processing results to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\nBatch results saved to: {output_file}")
    except Exception as e:
        print(f"Warning: Could not save batch results: {e}")


def main():
    """Main function for batch processing."""
    args = parse_batch_arguments()
    
    # Load URLs from file
    urls = load_urls_from_file(args.urls_file)
    
    if not urls:
        print("No valid URLs found. Exiting.")
        sys.exit(1)
    
    # Load configuration
    config = Config()
    if args.config:
        config = load_config_from_file(args.config)
    
    # Override config with batch arguments
    config.output_directory = args.output_dir
    config.output_format = args.format.upper()
    config.scene_change_threshold = args.sensitivity
    config.min_time_between_captures = args.min_time
    
    # Ensure base output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("YouTube Presentation Extractor - Batch Processor")
    print("=" * 60)
    print(f"URLs file: {args.urls_file}")
    print(f"Total URLs: {len(urls)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Format: {args.format}")
    print(f"Continue on error: {args.continue_on_error}")
    print("-" * 60)
    
    # Process videos
    start_time = time.time()
    results = process_video_batch(urls, config, args)
    end_time = time.time()
    
    # Print summary
    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total videos: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    
    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors']:
            print(f"  Video {error['index']}: {error['error']}")
    
    # Save results
    results_file = os.path.join(args.output_dir, "batch_results.json")
    save_batch_results(results, results_file)
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main() 