"""
Scene detection module for YouTube Presentation Extractor
Detects significant visual changes in video frames
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from skimage.metrics import structural_similarity as ssim
from scenedetect import detect, ContentDetector, AdaptiveDetector

from config import Config


@dataclass
class SceneChange:
    """Represents a detected scene change."""
    timestamp: float
    confidence: float
    change_type: str  # 'content', 'histogram', 'ssim'


class SceneDetector:
    """Detects significant scene changes in video frames."""
    
    def __init__(self, config: Config):
        self.config = config
        self.last_capture_time = 0.0
    
    def detect_scenes(self, frames: List[Tuple[float, np.ndarray]]) -> List[SceneChange]:
        """
        Detect scene changes in a sequence of frames.
        
        Args:
            frames: List of (timestamp, frame) tuples
            
        Returns:
            List of SceneChange objects
        """
        if len(frames) < 2:
            return []
        
        print("Detecting scene changes...")
        scene_changes = []
        
        # Use multiple detection methods
        ssim_changes = self._detect_ssim_changes(frames)
        histogram_changes = self._detect_histogram_changes(frames)
        
        # Combine and filter changes
        all_changes = ssim_changes + histogram_changes
        all_changes.sort(key=lambda x: x.timestamp)
        
        # Apply minimum time between captures filter
        filtered_changes = []
        for change in all_changes:
            if change.timestamp - self.last_capture_time >= self.config.min_time_between_captures:
                filtered_changes.append(change)
                self.last_capture_time = change.timestamp
        
        print(f"Detected {len(filtered_changes)} significant scene changes")
        return filtered_changes
    
    def _detect_ssim_changes(self, frames: List[Tuple[float, np.ndarray]]) -> List[SceneChange]:
        """Detect changes using Structural Similarity Index."""
        changes = []
        
        for i in range(1, len(frames)):
            prev_timestamp, prev_frame = frames[i-1]
            curr_timestamp, curr_frame = frames[i]
            
            # Convert to grayscale for SSIM
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate SSIM
            similarity = ssim(prev_gray, curr_gray)
            confidence = 1.0 - similarity
            
            if confidence > self.config.scene_change_threshold:
                changes.append(SceneChange(
                    timestamp=curr_timestamp,
                    confidence=confidence,
                    change_type='ssim'
                ))
        
        return changes
    
    def _detect_histogram_changes(self, frames: List[Tuple[float, np.ndarray]]) -> List[SceneChange]:
        """Detect changes using histogram comparison."""
        changes = []
        
        for i in range(1, len(frames)):
            prev_timestamp, prev_frame = frames[i-1]
            curr_timestamp, curr_frame = frames[i]
            
            # Calculate histograms for each color channel
            prev_hist = cv2.calcHist([prev_frame], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
            curr_hist = cv2.calcHist([curr_frame], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
            
            # Normalize histograms
            cv2.normalize(prev_hist, prev_hist, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(curr_hist, curr_hist, 0, 1, cv2.NORM_MINMAX)
            
            # Calculate correlation
            correlation = cv2.compareHist(prev_hist, curr_hist, cv2.HISTCMP_CORREL)
            confidence = 1.0 - correlation
            
            if confidence > self.config.histogram_threshold:
                changes.append(SceneChange(
                    timestamp=curr_timestamp,
                    confidence=confidence,
                    change_type='histogram'
                ))
        
        return changes
    
    def detect_scenes_advanced(self, video_path: str) -> List[SceneChange]:
        """
        Use PySceneDetect for advanced scene detection.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of SceneChange objects
        """
        try:
            # Use ContentDetector for content-based scene detection
            scenes = detect(video_path, ContentDetector(threshold=self.config.scene_change_threshold))
            
            changes = []
            for scene in scenes:
                # Convert frame number to timestamp
                timestamp = scene[0].get_seconds()
                
                # Skip if too close to last capture
                if timestamp - self.last_capture_time >= self.config.min_time_between_captures:
                    changes.append(SceneChange(
                        timestamp=timestamp,
                        confidence=0.8,  # PySceneDetect doesn't provide confidence
                        change_type='content'
                    ))
                    self.last_capture_time = timestamp
            
            return changes
            
        except Exception as e:
            print(f"Warning: Advanced scene detection failed: {e}")
            return []
    
    def filter_changes_by_confidence(self, changes: List[SceneChange], min_confidence: float = 0.5) -> List[SceneChange]:
        """Filter scene changes by confidence threshold."""
        return [change for change in changes if change.confidence >= min_confidence]
    
    def merge_nearby_changes(self, changes: List[SceneChange], time_threshold: float = 1.0) -> List[SceneChange]:
        """Merge scene changes that occur close together in time."""
        if not changes:
            return []
        
        merged = [changes[0]]
        
        for change in changes[1:]:
            last_change = merged[-1]
            
            if change.timestamp - last_change.timestamp <= time_threshold:
                # Merge by keeping the one with higher confidence
                if change.confidence > last_change.confidence:
                    merged[-1] = change
            else:
                merged.append(change)
        
        return merged
    
    def skip_intro_outro(self, changes: List[SceneChange], video_duration: float) -> List[SceneChange]:
        """Skip scene changes in intro/outro sections."""
        if not self.config.skip_intro_outro:
            return changes
        
        filtered = []
        for change in changes:
            # Skip changes in intro (first N seconds)
            if change.timestamp < self.config.intro_outro_duration:
                continue
            
            # Skip changes in outro (last N seconds)
            if change.timestamp > video_duration - self.config.intro_outro_duration:
                continue
            
            filtered.append(change)
        
        return filtered 