#!/usr/bin/env python3
"""
Test script to verify batch sizes are now larger.
"""

from transcript_enhancer import TranscriptEnhancer
from transcript_parser import TranscriptSegment
from config import Config


def test_batch_sizes():
    """Test that batch sizes are now larger."""
    print("Testing Batch Sizes")
    print("=" * 50)
    
    # Create test configuration
    config = Config()
    config.enable_llm_enhancement = True
    config.batch_target_tokens = 1500
    config.enable_batching = True
    
    enhancer = TranscriptEnhancer(config)
    
    # Create many small segments (like real transcript segments)
    test_segments = []
    for i in range(50):
        # Create segments with varying lengths (like real transcripts)
        if i % 3 == 0:
            text = "Hello everyone, welcome to my presentation about machine learning."
        elif i % 3 == 1:
            text = "Today we will discuss the fundamentals of neural networks and deep learning algorithms."
        else:
            text = "Machine learning is a subset of artificial intelligence that focuses on algorithms."
        
        segment = TranscriptSegment(
            start_time=i * 5.0,
            end_time=(i + 1) * 5.0,
            text=text
        )
        test_segments.append(segment)
    
    print(f"Created {len(test_segments)} test segments")
    
    # Test batching
    batches = enhancer._create_batches(test_segments)
    print(f"Created {len(batches)} batches:")
    
    total_tokens = 0
    for i, batch in enumerate(batches):
        batch_text = enhancer._combine_batch_text(batch)
        batch_tokens = enhancer._estimate_tokens(batch_text)
        total_tokens += batch_tokens
        
        print(f"  Batch {i+1}: {len(batch)} segments, ~{batch_tokens} tokens")
        print(f"    Text: {batch_text[:100]}...")
        
        # Check if we're getting closer to target
        if batch_tokens >= 700:
            print(f"    ✅ Good size! ({batch_tokens} tokens)")
        else:
            print(f"    ⚠️  Still small ({batch_tokens} tokens)")
    
    avg_tokens = total_tokens / len(batches) if batches else 0
    print(f"\nAverage batch size: {avg_tokens:.1f} tokens")
    
    if avg_tokens >= 700:
        print("✅ Batching is now working with larger context windows!")
    else:
        print("⚠️  Batches are still too small. Consider increasing batch_target_tokens further.")


if __name__ == "__main__":
    test_batch_sizes() 