"""
Video processing module for YouTube Presentation Extractor
Handles video download, frame extraction, and metadata extraction
"""

import os
import tempfile
import subprocess
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import cv2
import numpy as np
from pathlib import Path

from config import Config


@dataclass
class VideoMetadata:
    """Container for video metadata."""
    title: str
    duration: float
    width: int
    height: int
    fps: float
    video_id: str
    upload_date: str
    description: str


class VideoProcessor:
    """Handles video download and processing."""
    
    def __init__(self, config: Config):
        self.config = config
        self.temp_dir = None
        self.video_path = None
        self.metadata = None
    
    def download_video(self, youtube_url: str) -> VideoMetadata:
        """
        Download YouTube video and extract metadata.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            VideoMetadata object containing video information
            
        Raises:
            Exception: If download fails
        """
        print(f"Downloading video from: {youtube_url}")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="youtube_extractor_")
        
        try:
            # Download video using yt-dlp
            video_path = self._download_with_ytdlp(youtube_url)
            self.video_path = video_path
            
            # Extract metadata
            self.metadata = self._extract_metadata(youtube_url)
            
            print(f"Successfully downloaded: {self.metadata.title}")
            print(f"Duration: {self.metadata.duration:.2f} seconds")
            print(f"Resolution: {self.metadata.width}x{self.metadata.height}")
            
            return self.metadata
            
        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to download video: {str(e)}")
    
    def _download_with_ytdlp(self, youtube_url: str) -> str:
        """Download video using yt-dlp."""
        output_template = os.path.join(self.temp_dir, "%(id)s.%(ext)s")
        
        # Build format string based on video quality
        quality_map = {
            "144p": "worst[height<=144]",
            "240p": "worst[height<=240]",
            "360p": "worst[height<=360]",
            "480p": "worst[height<=480]",
            "720p": "best[height<=720]",
            "1080p": "best[height<=1080]",
            "1440p": "best[height<=1440]",
            "2160p": "best[height<=2160]"
        }
        
        format_spec = quality_map.get(self.config.video_quality, "best[height<=720]")
        
        # Enhanced yt-dlp command with better subtitle handling
        cmd = [
            "yt-dlp",
            "--format", format_spec,
            "--write-info-json",
            "--write-subs",
            "--write-auto-subs",
            "--sub-format", "srt",
            "--sub-lang", "en,en-US,en-GB",  # Try multiple English variants
            "--convert-subs", "srt",  # Convert all subtitles to SRT
            "--output", output_template,
            youtube_url
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout * 2
            )
            
            if result.returncode != 0:
                print(f"First attempt failed: {result.stderr}")
                print("Trying with fallback options...")
                
                # Fallback command with more basic options
                fallback_cmd = [
                    "yt-dlp",
                    "--format", format_spec,
                    "--write-info-json",
                    "--write-subs",
                    "--sub-format", "srt",
                    "--output", output_template,
                    youtube_url
                ]
                
                result = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout * 2
                )
                
                if result.returncode != 0:
                    print(f"Fallback attempt failed: {result.stderr}")
                    print("Trying with minimal options...")
                    
                    # Minimal command - just get the video
                    minimal_cmd = [
                        "yt-dlp",
                        "--format", format_spec,
                        "--write-info-json",
                        "--output", output_template,
                        youtube_url
                    ]
                    
                    result = subprocess.run(
                        minimal_cmd,
                        capture_output=True,
                        text=True,
                        timeout=self.config.timeout * 2
                    )
                    
                    if result.returncode != 0:
                        raise Exception(f"yt-dlp failed: {result.stderr}")
                    else:
                        print("Warning: Downloaded video but no subtitles found")
            
            # Find the downloaded video file
            video_files = list(Path(self.temp_dir).glob("*.mp4"))
            if not video_files:
                video_files = list(Path(self.temp_dir).glob("*.webm"))
            
            if not video_files:
                raise Exception("No video file found after download")
            
            return str(video_files[0])
            
        except subprocess.TimeoutExpired:
            raise Exception("Download timed out")
        except FileNotFoundError:
            raise Exception("yt-dlp not found. Please install it: pip install yt-dlp")
    
    def _extract_metadata(self, youtube_url: str) -> VideoMetadata:
        """Extract video metadata from JSON info file."""
        # Find the JSON info file
        json_files = list(Path(self.temp_dir).glob("*.info.json"))
        if not json_files:
            raise Exception("No metadata file found")
        
        with open(json_files[0], 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        # Get video properties using OpenCV
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        return VideoMetadata(
            title=info.get('title', 'Unknown'),
            duration=info.get('duration', 0),
            width=width,
            height=height,
            fps=fps,
            video_id=info.get('id', ''),
            upload_date=info.get('upload_date', ''),
            description=info.get('description', '')
        )
    
    def extract_frames(self, start_time: float = 0, end_time: Optional[float] = None) -> List[Tuple[float, np.ndarray]]:
        """
        Extract frames from video at specified intervals.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds (None for end of video)
            
        Returns:
            List of (timestamp, frame) tuples
        """
        if not self.video_path:
            raise Exception("No video loaded. Call download_video() first.")
        
        frames = []
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise Exception("Could not open video file")
        
        # Set start position
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
        
        frame_interval = 1.0 / self.config.frame_rate
        current_time = start_time
        
        if end_time is None:
            end_time = self.metadata.duration
        
        print(f"Extracting frames from {start_time:.2f}s to {end_time:.2f}s...")
        
        try:
            while current_time < end_time:
                cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Resize frame if target resolution is specified
                if self.config.target_resolution:
                    frame = cv2.resize(frame, self.config.target_resolution)
                
                frames.append((current_time, frame))
                current_time += frame_interval
                
        finally:
            cap.release()
        
        print(f"Extracted {len(frames)} frames")
        return frames
    
    def get_subtitle_files(self) -> List[str]:
        """Get list of available subtitle files."""
        if not self.temp_dir:
            return []
        
        subtitle_files = []
        for ext in ['*.srt', '*.vtt', '*.json']:
            subtitle_files.extend([str(f) for f in Path(self.temp_dir).glob(ext)])
        
        return subtitle_files
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up temp directory: {e}")
        
        self.temp_dir = None
        self.video_path = None
        self.metadata = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup() 