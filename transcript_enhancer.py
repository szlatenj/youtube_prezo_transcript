"""
Transcript enhancer module for YouTube Presentation Extractor
Handles LLM interactions with Anthropic Claude for transcript enhancement
"""

import os
import json
import time
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import anthropic
from anthropic import Anthropic
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

from config import Config
from transcript_parser import TranscriptSegment


@dataclass
class EnhancementResult:
    """Result of transcript enhancement."""
    original_text: str
    enhanced_text: str
    key_points: List[str]
    summary: str
    confidence: float
    tokens_used: int
    cost: float


@dataclass
class EnhancementStats:
    """Statistics for enhancement process."""
    total_segments: int
    enhanced_segments: int
    total_tokens: int
    total_cost: float
    processing_time: float
    errors: List[str]


class TranscriptEnhancer:
    """Handles transcript enhancement using Anthropic Claude."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.stats = EnhancementStats(0, 0, 0, 0.0, 0.0, [])
        self.cache = {}
        
        # Setup logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize Anthropic client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Anthropic client with API key."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not found")
        
        try:
            self.client = Anthropic(api_key=api_key)
            print("Anthropic client initialized successfully")
        except Exception as e:
            raise Exception(f"Failed to initialize Anthropic client: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Rough approximation: 1 token ≈ 4 characters for English text.
        For more accurate estimation, we can use a slightly more conservative ratio.
        """
        # More conservative estimation: 1 token ≈ 3.5 characters
        return max(1, len(text) // 3.5)
    
    def _create_batches(self, segments: List[TranscriptSegment], target_tokens: int = None) -> List[List[TranscriptSegment]]:
        """
        Create batches of segments that approximately match the target token count.
        
        Args:
            segments: List of transcript segments
            target_tokens: Target token count per batch (uses config if None)
            
        Returns:
            List of segment batches
        """
        if target_tokens is None:
            target_tokens = self.config.batch_target_tokens
        
        if not self.config.enable_batching:
            # Return each segment as its own batch
            return [[segment] for segment in segments]
        
        batches = []
        current_batch = []
        current_tokens = 0
        
        # Allow much more flexibility in batch size (up to 50% over target)
        # This ensures we get closer to the target token count
        max_tokens = int(target_tokens * 1.5)
        min_tokens = int(target_tokens * 0.7)  # Don't create batches that are too small
        
        for segment in segments:
            segment_tokens = self._estimate_tokens(segment.text)
            
            # If adding this segment would exceed max_tokens and we have a substantial batch, start new batch
            if current_tokens + segment_tokens > max_tokens and current_tokens >= min_tokens:
                batches.append(current_batch)
                current_batch = [segment]
                current_tokens = segment_tokens
            else:
                current_batch.append(segment)
                current_tokens += segment_tokens
        
        # Add the last batch if it has content
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _combine_batch_text(self, segments: List[TranscriptSegment]) -> str:
        """Combine text from multiple segments into a single string."""
        return " ".join([seg.text for seg in segments])
    
    def _distribute_enhanced_text(self, enhanced_text: str, segments: List[TranscriptSegment]) -> List[str]:
        """
        Distribute enhanced text back to individual segments.
        This is a simple approach that splits the enhanced text proportionally.
        """
        if not segments:
            return []
        
        # Simple approach: split enhanced text by sentences and distribute
        sentences = re.split(r'[.!?]+', enhanced_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Distribute sentences to segments
        enhanced_segments = []
        sentences_per_segment = len(sentences) // len(segments)
        remainder = len(sentences) % len(segments)
        
        sentence_index = 0
        for i, segment in enumerate(segments):
            # Calculate how many sentences this segment gets
            num_sentences = sentences_per_segment + (1 if i < remainder else 0)
            
            if sentence_index < len(sentences):
                segment_sentences = sentences[sentence_index:sentence_index + num_sentences]
                enhanced_text = ". ".join(segment_sentences) + "."
                enhanced_segments.append(enhanced_text)
                sentence_index += num_sentences
            else:
                # Fallback to original text if not enough sentences
                enhanced_segments.append(segment.text)
        
        return enhanced_segments
    
    def enhance_transcript_segment(self, segment: TranscriptSegment, 
                                 enhancement_level: str = "detailed") -> EnhancementResult:
        """
        Enhance a single transcript segment.
        
        Args:
            segment: Transcript segment to enhance
            enhancement_level: Level of enhancement (basic, detailed, academic)
            
        Returns:
            EnhancementResult with enhanced content
        """
        # Check cache first
        cache_key = f"{segment.text}_{enhancement_level}"
        if cache_key in self.cache and self.config.cache_enhanced_results:
            return self.cache[cache_key]
        
        # Get appropriate prompt
        prompt = self._get_enhancement_prompt(segment.text, enhancement_level)
        
        try:
            # Call Claude API
            response = self._call_claude_api(prompt, enhancement_level)
            
            # Parse response
            result = self._parse_enhancement_response(response, segment.text)
            
            # Update stats
            self._update_stats(result.tokens_used, result.cost)
            
            # Cache result
            if self.config.cache_enhanced_results:
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to enhance segment: {e}")
            self.stats.errors.append(str(e))
            
            # Return fallback result
            return EnhancementResult(
                original_text=segment.text,
                enhanced_text=segment.text,  # Keep original
                key_points=[],
                summary="",
                confidence=0.0,
                tokens_used=0,
                cost=0.0
            )
    
    def enhance_full_transcript(self, segments: List[TranscriptSegment], 
                              enhancement_level: str = "detailed") -> List[EnhancementResult]:
        """
        Enhance all transcript segments using batching for efficiency.
        
        Args:
            segments: List of transcript segments
            enhancement_level: Level of enhancement
            
        Returns:
            List of EnhancementResult objects
        """
        self.stats = EnhancementStats(0, 0, 0, 0.0, 0.0, [])
        self.stats.total_segments = len(segments)
        
        start_time = time.time()
        results = []
        
        print(f"Enhancing {len(segments)} transcript segments using batching...")
        
        # Create batches using config target tokens
        batches = self._create_batches(segments)
        print(f"Created {len(batches)} batches for processing")
        
        for batch_idx, batch in enumerate(batches):
            print(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} segments)...")
            
            # Combine batch text
            batch_text = self._combine_batch_text(batch)
            batch_tokens = self._estimate_tokens(batch_text)
            
            print(f"  Batch tokens: ~{batch_tokens}")
            
            # Check cache for batch
            cache_key = f"{batch_text}_{enhancement_level}"
            if cache_key in self.cache and self.config.cache_enhanced_results:
                enhanced_batch_text = self.cache[cache_key]
                print("  Using cached result")
            else:
                # Get enhancement prompt for batch
                prompt = self._get_enhancement_prompt(batch_text, enhancement_level)
                
                try:
                    # Call Claude API for batch
                    response = self._call_claude_api(prompt, enhancement_level)
                    
                    # Parse response
                    enhanced_batch_text = self._parse_enhanced_text(response)
                    
                    # Cache result
                    if self.config.cache_enhanced_results:
                        self.cache[cache_key] = enhanced_batch_text
                    
                    # Update stats
                    tokens_used = self._estimate_tokens(response)
                    cost = (tokens_used / 1000) * 0.003  # Approximate cost
                    self._update_stats(tokens_used, cost)
                    
                except Exception as e:
                    self.logger.error(f"Failed to enhance batch {batch_idx + 1}: {e}")
                    self.stats.errors.append(str(e))
                    # Use original text as fallback
                    enhanced_batch_text = batch_text
            
            # Distribute enhanced text back to individual segments
            enhanced_segments = self._distribute_enhanced_text(enhanced_batch_text, batch)
            
            # Create results for each segment in the batch
            for i, segment in enumerate(batch):
                enhanced_text = enhanced_segments[i] if i < len(enhanced_segments) else segment.text
                
                result = EnhancementResult(
                    original_text=segment.text,
                    enhanced_text=enhanced_text,
                    key_points=[],  # Will be extracted separately if needed
                    summary=self._generate_summary(enhanced_text),
                    confidence=0.9,
                    tokens_used=0,  # Already counted in batch
                    cost=0.0  # Already counted in batch
                )
                
                results.append(result)
            
            # Check cost limits
            if self.config.max_cost_per_video > 0 and self.stats.total_cost > self.config.max_cost_per_video:
                print(f"Cost limit reached (${self.stats.total_cost:.2f}). Stopping enhancement.")
                break
            
            # Rate limiting
            time.sleep(0.1)  # Small delay to avoid rate limits
        
        self.stats.processing_time = time.time() - start_time
        self.stats.enhanced_segments = len(results)
        
        print(f"Enhancement completed: {self.stats.enhanced_segments} segments, "
              f"${self.stats.total_cost:.2f} cost, {self.stats.processing_time:.1f}s")
        
        return results
    
    def extract_key_points(self, segments: List[TranscriptSegment]) -> List[str]:
        """
        Extract key points from transcript segments.
        
        Args:
            segments: List of transcript segments
            
        Returns:
            List of key points
        """
        # Combine all text
        full_text = " ".join([seg.text for seg in segments])
        
        prompt = f"""
Please extract the key points from this presentation transcript. 
Focus on the main concepts, important facts, and central ideas.

Transcript:
{full_text}

Please provide a list of key points, one per line, starting with a bullet point (-).
Focus on the most important concepts and insights.
"""
        
        try:
            response = self._call_claude_api(prompt, "basic")
            key_points = self._parse_key_points(response)
            return key_points
        except Exception as e:
            self.logger.error(f"Failed to extract key points: {e}")
            return []
    
    def generate_slide_summary(self, segments: List[TranscriptSegment], 
                             slide_number: int) -> str:
        """
        Generate a summary for a specific slide.
        
        Args:
            segments: Transcript segments for the slide
            slide_number: Slide number
            
        Returns:
            Summary text
        """
        if not segments:
            return ""
        
        # Combine segment text
        slide_text = " ".join([seg.text for seg in segments])
        
        prompt = f"""
Please provide a concise summary of this slide content from a presentation.

Slide {slide_number} Content:
{slide_text}

Please provide a brief, clear summary (2-3 sentences) that captures the main points of this slide.
"""
        
        try:
            response = self._call_claude_api(prompt, "basic")
            return response.strip()
        except Exception as e:
            self.logger.error(f"Failed to generate slide summary: {e}")
            return ""
    
    def _get_enhancement_prompt(self, text: str, level: str) -> str:
        """Get enhancement prompt based on level and configuration."""
        
        # Use custom prompt template if provided
        if self.config.custom_prompt_template:
            return self.config.custom_prompt_template.format(
                text=text,
                level=level,
                style=self.config.prompt_style
            )
        
        # Get base prompt based on level
        if level == "basic":
            base_prompt = self._get_basic_prompt()
        elif level == "detailed":
            base_prompt = self._get_detailed_prompt()
        elif level == "academic":
            base_prompt = self._get_academic_prompt()
        else:
            raise ValueError(f"Unknown enhancement level: {level}")
        
        # Apply style modifications
        styled_prompt = self._apply_prompt_style(base_prompt)
        
        return styled_prompt.format(text=text)
    
    def _get_basic_prompt(self) -> str:
        """Get basic enhancement prompt template."""
        return """
Improve this transcript segment:
- Fix grammar and spelling errors
- Improve sentence structure and clarity
- Use paragraphs where appropriate
- Keep factual and descriptive tone

Transcript: {text}

Provide only the corrected text.
"""
    
    def _get_detailed_prompt(self) -> str:
        """Get detailed enhancement prompt template."""
        return """
Enhance this transcript segment covering multiple slides (approximately 6 minutes of content):
- Fix transcription errors
- Improve sentence structure and clarity
- Add factual explanations and context
- Structure content logically
- Keep text concise and focused
- Extract key concepts

Transcript: {text}

Format response as:
ENHANCED_TEXT: [enhanced transcript - keep concise]
KEY_POINTS: [bullet points of key concepts]
"""
    
    def _get_academic_prompt(self) -> str:
        """Get academic enhancement prompt template."""
        return """
Convert to academic language:
- Use formal, scholarly language
- Improve sentence structure and clarity
- Add proper context and explanations
- Structure content logically
- Include key concepts and definitions

Transcript: {text}

Format response as:
ACADEMIC_TEXT: [academic version]
KEY_CONCEPTS: [important concepts and definitions]
"""
    
    def _apply_prompt_style(self, base_prompt: str) -> str:
        """Apply style modifications to the base prompt."""
        if self.config.prompt_style == "clear":
            return base_prompt
        elif self.config.prompt_style == "academic":
            return base_prompt.replace(
                "Please improve this transcript segment",
                "Please enhance this transcript segment using academic language"
            ).replace(
                "Please enhance this transcript segment",
                "Please enhance this transcript segment using academic language"
            ).replace(
                "Please convert this transcript segment",
                "Please convert this transcript segment using formal academic language"
            )
        elif self.config.prompt_style == "conversational":
            return base_prompt.replace(
                "Please improve this transcript segment",
                "Please make this transcript segment more conversational and engaging"
            ).replace(
                "Please enhance this transcript segment",
                "Please make this transcript segment more conversational and engaging"
            ).replace(
                "Please convert this transcript segment",
                "Please make this transcript segment more conversational and accessible"
            )
        elif self.config.prompt_style == "technical":
            return base_prompt.replace(
                "Please improve this transcript segment",
                "Please enhance this transcript segment with technical precision and clarity"
            ).replace(
                "Please enhance this transcript segment",
                "Please enhance this transcript segment with technical precision and clarity"
            ).replace(
                "Please convert this transcript segment",
                "Please convert this transcript segment into precise technical language"
            )
        else:
            return base_prompt
    
    def _parse_enhanced_text(self, response: str) -> str:
        """Parse enhanced text from API response."""
        # Parse based on response format
        if "ENHANCED_TEXT:" in response:
            # Detailed format
            parts = response.split("ENHANCED_TEXT:")
            if len(parts) > 1:
                enhanced_part = parts[1].split("KEY_POINTS:")
                return enhanced_part[0].strip()
        elif "ACADEMIC_TEXT:" in response:
            # Academic format
            parts = response.split("ACADEMIC_TEXT:")
            if len(parts) > 1:
                academic_part = parts[1].split("KEY_CONCEPTS:")
                return academic_part[0].strip()
        
        # Basic format - just enhanced text
        return response.strip()
    
    def _call_claude_api(self, prompt: str, enhancement_level: str) -> str:
        """Call Claude API with retry logic."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.config.anthropic_model,
                    max_tokens=self.config.max_tokens_per_request,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                return response.content[0].text
                
            except anthropic.RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    self.logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"API call failed, retrying... Error: {e}")
                    time.sleep(retry_delay)
                else:
                    raise
    
    def _parse_enhancement_response(self, response: str, original_text: str) -> EnhancementResult:
        """Parse Claude API response into EnhancementResult."""
        # Estimate tokens used (rough approximation)
        tokens_used = self._estimate_tokens(response)
        
        # Calculate cost (approximate)
        cost_per_1k_tokens = 0.003  # Claude-3-Sonnet input cost
        cost = (tokens_used / 1000) * cost_per_1k_tokens
        
        # Parse based on response format
        if "ENHANCED_TEXT:" in response:
            # Detailed format
            parts = response.split("ENHANCED_TEXT:")
            if len(parts) > 1:
                enhanced_part = parts[1].split("KEY_POINTS:")
                enhanced_text = enhanced_part[0].strip()
                key_points = self._parse_key_points(enhanced_part[1] if len(enhanced_part) > 1 else "")
            else:
                enhanced_text = response.strip()
                key_points = []
        elif "ACADEMIC_TEXT:" in response:
            # Academic format
            parts = response.split("ACADEMIC_TEXT:")
            if len(parts) > 1:
                academic_part = parts[1].split("KEY_CONCEPTS:")
                enhanced_text = academic_part[0].strip()
                key_points = self._parse_key_points(academic_part[1] if len(academic_part) > 1 else "")
            else:
                enhanced_text = response.strip()
                key_points = []
        else:
            # Basic format - just enhanced text
            enhanced_text = response.strip()
            key_points = []
        
        # Generate summary
        summary = self._generate_summary(enhanced_text)
        
        return EnhancementResult(
            original_text=original_text,
            enhanced_text=enhanced_text,
            key_points=key_points,
            summary=summary,
            confidence=0.9,  # High confidence for Claude
            tokens_used=int(tokens_used),
            cost=cost
        )
    
    def _parse_key_points(self, text: str) -> List[str]:
        """Parse key points from text."""
        if not text:
            return []
        
        lines = text.strip().split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                key_points.append(line[1:].strip())
            elif line and not line.startswith('KEY_POINTS:') and not line.startswith('KEY_CONCEPTS:'):
                key_points.append(line)
        
        return key_points
    
    def _generate_summary(self, text: str) -> str:
        """Generate a brief summary of the text."""
        if len(text) < 100:
            return text
        
        # Simple summary: first sentence or first 100 characters
        sentences = text.split('.')
        if sentences:
            return sentences[0].strip() + '.'
        
        return text[:100] + '...'
    
    def _update_stats(self, tokens: int, cost: float):
        """Update enhancement statistics."""
        self.stats.total_tokens += tokens
        self.stats.total_cost += cost
        self.stats.enhanced_segments += 1
    
    def get_stats(self) -> EnhancementStats:
        """Get current enhancement statistics."""
        return self.stats
    
    def clear_cache(self):
        """Clear the enhancement cache."""
        self.cache.clear()
    
    def save_cache(self, filepath: str):
        """Save cache to file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save cache: {e}")
    
    def load_cache(self, filepath: str):
        """Load cache from file."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    self.cache = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load cache: {e}") 