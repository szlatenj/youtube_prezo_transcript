"""
Transcript parser module for YouTube Presentation Extractor
Handles subtitle files and transcript synchronization
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import srt
from datetime import timedelta


@dataclass
class TranscriptSegment:
    """Represents a segment of transcript text."""
    start_time: float
    end_time: float
    text: str
    confidence: float = 1.0
    enhanced_text: str = ""  # Enhanced version of the text
    key_points: List[str] = None  # Key points extracted from this segment
    summary: str = ""  # Brief summary of this segment
    
    def __post_init__(self):
        """Initialize default values for enhanced fields."""
        if self.key_points is None:
            self.key_points = []
        if not self.enhanced_text:
            self.enhanced_text = self.text


class TranscriptParser:
    """Parses and manages transcript/subtitle data."""
    
    def __init__(self):
        self.segments = []
        self.language = "en"
        self.enhancement_stats = {}  # Store enhancement statistics
    
    def set_enhanced_segments(self, enhanced_results: List) -> None:
        """
        Update segments with enhanced content.
        
        Args:
            enhanced_results: List of EnhancementResult objects
        """
        if len(enhanced_results) != len(self.segments):
            print(f"Warning: Enhanced results count ({len(enhanced_results)}) "
                  f"doesn't match segment count ({len(self.segments)})")
            return
        
        for i, result in enumerate(enhanced_results):
            if i < len(self.segments):
                self.segments[i].enhanced_text = result.enhanced_text
                self.segments[i].key_points = result.key_points
                self.segments[i].summary = result.summary
    
    def get_enhanced_text_for_timestamp(self, timestamp: float, window: float = 5.0) -> str:
        """
        Get enhanced text for a specific timestamp.
        
        Args:
            timestamp: Time in seconds
            window: Time window to search in
            
        Returns:
            Enhanced text for the timestamp
        """
        segments = self.get_segments_for_timestamp(timestamp, window)
        if not segments:
            return ""
        
        # Combine enhanced text from all segments within the window
        enhanced_texts = []
        for segment in segments:
            if segment.enhanced_text and segment.enhanced_text != segment.text:
                enhanced_texts.append(segment.enhanced_text)
            else:
                enhanced_texts.append(segment.text)
        
        return " ".join(enhanced_texts)
    
    def get_key_points_for_timestamp(self, timestamp: float, window: float = 5.0) -> List[str]:
        """
        Get key points for a specific timestamp.
        
        Args:
            timestamp: Time in seconds
            window: Time window to search in
            
        Returns:
            List of key points
        """
        segments = self.get_segments_for_timestamp(timestamp, window)
        key_points = []
        
        for segment in segments:
            key_points.extend(segment.key_points)
        
        return key_points
    
    def get_enhanced_segments_in_range(self, start_time: float, end_time: float) -> List[TranscriptSegment]:
        """
        Get enhanced segments within a time range.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            List of enhanced transcript segments
        """
        segments = self.get_segments_in_range(start_time, end_time)
        
        # Filter segments that have enhanced content
        enhanced_segments = []
        for segment in segments:
            if segment.enhanced_text and segment.enhanced_text != segment.text:
                enhanced_segments.append(segment)
        
        return enhanced_segments
    
    def has_enhanced_content(self) -> bool:
        """
        Check if any segments have enhanced content.
        
        Returns:
            True if enhanced content exists
        """
        return any(seg.enhanced_text and seg.enhanced_text != seg.text for seg in self.segments)
    
    def get_enhancement_coverage(self) -> float:
        """
        Get the percentage of segments that have enhanced content.
        
        Returns:
            Percentage of enhanced segments (0.0 to 1.0)
        """
        if not self.segments:
            return 0.0
        
        enhanced_count = sum(1 for seg in self.segments 
                           if seg.enhanced_text and seg.enhanced_text != seg.text)
        return enhanced_count / len(self.segments)
    
    def load_subtitles(self, subtitle_files: List[str]) -> bool:
        """
        Load subtitle files, preferring manual captions over auto-generated.
        
        Args:
            subtitle_files: List of subtitle file paths
            
        Returns:
            True if subtitles were loaded successfully
        """
        if not subtitle_files:
            return False
        
        # Prefer manual captions over auto-generated ones
        manual_files = [f for f in subtitle_files if "manual" in f.lower() or not any(x in f.lower() for x in ["auto", "generated"])]
        auto_files = [f for f in subtitle_files if any(x in f.lower() for x in ["auto", "generated"])]
        
        # Try manual captions first
        for file_path in manual_files:
            if self._parse_subtitle_file(file_path):
                print(f"Loaded manual captions from: {Path(file_path).name}")
                return True
        
        # Fall back to auto-generated captions
        for file_path in auto_files:
            if self._parse_subtitle_file(file_path):
                print(f"Loaded auto-generated captions from: {Path(file_path).name}")
                return True
        
        return False
    
    def _parse_subtitle_file(self, file_path: str) -> bool:
        """Parse a subtitle file based on its format."""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.srt':
                return self._parse_srt_file(file_path)
            elif file_path.suffix.lower() == '.vtt':
                return self._parse_vtt_file(file_path)
            elif file_path.suffix.lower() == '.json':
                return self._parse_json_file(file_path)
            else:
                print(f"Unsupported subtitle format: {file_path.suffix}")
                return False
                
        except Exception as e:
            print(f"Error parsing subtitle file {file_path}: {e}")
            return False
    
    def _parse_srt_file(self, file_path: Path) -> bool:
        """Parse SRT subtitle file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT content
            subs = list(srt.parse(content))
            
            self.segments = []
            for sub in subs:
                segment = TranscriptSegment(
                    start_time=sub.start.total_seconds(),
                    end_time=sub.end.total_seconds(),
                    text=sub.content.strip()
                )
                self.segments.append(segment)
            
            return len(self.segments) > 0
            
        except Exception as e:
            print(f"Error parsing SRT file: {e}")
            return False
    
    def _parse_vtt_file(self, file_path: Path) -> bool:
        """Parse VTT subtitle file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.segments = []
            current_segment = None
            
            for line in lines:
                line = line.strip()
                
                # Skip header and empty lines
                if line == 'WEBVTT' or line == '' or line.startswith('NOTE'):
                    continue
                
                # Parse timestamp line
                if '-->' in line:
                    if current_segment:
                        self.segments.append(current_segment)
                    
                    start_str, end_str = line.split(' --> ')
                    start_time = self._parse_timestamp(start_str)
                    end_time = self._parse_timestamp(end_str)
                    
                    current_segment = TranscriptSegment(
                        start_time=start_time,
                        end_time=end_time,
                        text=""
                    )
                
                # Parse text line
                elif current_segment is not None:
                    if current_segment.text:
                        current_segment.text += " "
                    current_segment.text += line
            
            # Add last segment
            if current_segment:
                self.segments.append(current_segment)
            
            return len(self.segments) > 0
            
        except Exception as e:
            print(f"Error parsing VTT file: {e}")
            return False
    
    def _parse_json_file(self, file_path: Path) -> bool:
        """Parse JSON subtitle file (YouTube format)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.segments = []
            
            # Handle different JSON formats
            if 'events' in data:
                # YouTube format
                for event in data['events']:
                    if 'segs' in event:
                        text = ""
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                text += seg['utf8']
                        
                        if text.strip():
                            segment = TranscriptSegment(
                                start_time=event.get('tStartMs', 0) / 1000.0,
                                end_time=(event.get('tStartMs', 0) + event.get('dDurationMs', 0)) / 1000.0,
                                text=text.strip()
                            )
                            self.segments.append(segment)
            
            elif 'captions' in data:
                # Alternative format
                for caption in data['captions']:
                    segment = TranscriptSegment(
                        start_time=caption.get('start', 0),
                        end_time=caption.get('end', 0),
                        text=caption.get('text', '').strip()
                    )
                    self.segments.append(segment)
            
            return len(self.segments) > 0
            
        except Exception as e:
            print(f"Error parsing JSON file: {e}")
            return False
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse timestamp string to seconds."""
        # Handle different timestamp formats
        if '.' in timestamp_str:
            # Format: HH:MM:SS.mmm
            parts = timestamp_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        else:
            # Format: HH:MM:SS
            parts = timestamp_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
    
    def get_segments_for_timestamp(self, timestamp: float, window: float = 5.0) -> List[TranscriptSegment]:
        """
        Get transcript segments that overlap with a given timestamp.
        
        Args:
            timestamp: Time in seconds
            window: Time window around timestamp to consider
            
        Returns:
            List of overlapping transcript segments
        """
        segments = []
        
        for segment in self.segments:
            # Check if segment overlaps with timestamp
            if (segment.start_time <= timestamp + window and 
                segment.end_time >= timestamp - window):
                segments.append(segment)
        
        return segments
    
    def get_text_for_timestamp(self, timestamp: float, window: float = 5.0) -> str:
        """
        Get combined transcript text for a given timestamp.
        
        Args:
            timestamp: Time in seconds
            window: Time window around timestamp to consider
            
        Returns:
            Combined transcript text
        """
        segments = self.get_segments_for_timestamp(timestamp, window)
        
        if not segments:
            return ""
        
        # Sort by start time and combine text
        segments.sort(key=lambda x: x.start_time)
        text_parts = [seg.text for seg in segments]
        
        return " ".join(text_parts)
    
    def get_segments_in_range(self, start_time: float, end_time: float) -> List[TranscriptSegment]:
        """
        Get all transcript segments within a time range.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            List of transcript segments in range
        """
        segments = []
        
        for segment in self.segments:
            if (segment.start_time <= end_time and 
                segment.end_time >= start_time):
                segments.append(segment)
        
        return segments
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize transcript text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common subtitle artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed text
        text = re.sub(r'\(.*?\)', '', text)  # Remove parenthetical text
        
        # Clean up punctuation
        text = text.strip()
        
        return text
    
    def get_full_transcript(self) -> str:
        """Get the complete transcript text."""
        if not self.segments:
            return ""
        
        text_parts = [self.clean_text(seg.text) for seg in self.segments]
        return " ".join(text_parts)
    
    def get_statistics(self) -> Dict:
        """Get transcript statistics."""
        if not self.segments:
            return {}
        
        total_duration = max(seg.end_time for seg in self.segments)
        total_words = sum(len(seg.text.split()) for seg in self.segments)
        
        return {
            'total_segments': len(self.segments),
            'total_duration': total_duration,
            'total_words': total_words,
            'words_per_minute': (total_words / total_duration) * 60 if total_duration > 0 else 0
        }
    
    def save_original_transcript(self, output_path: str) -> bool:
        """
        Save the original transcript with timestamps to a file.
        
        Args:
            output_path: Path to save the transcript file
            
        Returns:
            True if saved successfully
        """
        if not self.segments:
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("Original Transcript with Timestamps\n")
                f.write("=" * 50 + "\n\n")
                
                for i, segment in enumerate(self.segments, 1):
                    start_time = self._format_timestamp(segment.start_time)
                    end_time = self._format_timestamp(segment.end_time)
                    
                    f.write(f"Segment {i} [{start_time} - {end_time}]\n")
                    f.write(f"{segment.text}\n\n")
                
                # Add statistics
                stats = self.get_statistics()
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Total segments: {stats.get('total_segments', 0)}\n")
                f.write(f"Total words: {stats.get('total_words', 0)}\n")
                f.write(f"Duration: {stats.get('duration', 0):.2f} seconds\n")
            
            print(f"Original transcript saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving transcript: {e}")
            return False
    
    def save_enhanced_transcript(self, output_path: str) -> bool:
        """
        Save the enhanced transcript with timestamps to a file.
        
        Args:
            output_path: Path to save the enhanced transcript file
            
        Returns:
            True if saved successfully
        """
        if not self.segments:
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("Enhanced Transcript with Timestamps\n")
                f.write("=" * 50 + "\n\n")
                
                for i, segment in enumerate(self.segments, 1):
                    start_time = self._format_timestamp(segment.start_time)
                    end_time = self._format_timestamp(segment.end_time)
                    
                    f.write(f"Segment {i} [{start_time} - {end_time}]\n")
                    
                    # Write enhanced text if available, otherwise original
                    if segment.enhanced_text and segment.enhanced_text != segment.text:
                        f.write(f"Enhanced: {segment.enhanced_text}\n")
                        f.write(f"Original: {segment.text}\n")
                        
                        # Add key points if available
                        if segment.key_points:
                            f.write("Key Points:\n")
                            for point in segment.key_points:
                                f.write(f"  - {point}\n")
                    else:
                        f.write(f"{segment.text}\n")
                    
                    f.write("\n")
                
                # Add enhancement statistics
                enhanced_count = sum(1 for seg in self.segments 
                                   if seg.enhanced_text and seg.enhanced_text != seg.text)
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Total segments: {len(self.segments)}\n")
                f.write(f"Enhanced segments: {enhanced_count}\n")
                f.write(f"Enhancement coverage: {(enhanced_count/len(self.segments)*100):.1f}%\n")
            
            print(f"Enhanced transcript saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving enhanced transcript: {e}")
            return False
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}" 