#!/usr/bin/env python3
"""
Test script for large context windows and improved batching.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

from transcript_enhancer import TranscriptEnhancer
from transcript_parser import TranscriptSegment
from config import Config


def test_large_context():
    """Test the large context window functionality."""
    print("Testing Large Context Windows")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not found")
        print("Please set your Anthropic API key in a .env file")
        return False
    
    print("✅ API key found")
    
    # Create test configuration with large context
    config = Config()
    config.enable_llm_enhancement = True
    config.enhancement_level = "detailed"
    config.enable_batching = True
    config.batch_target_tokens = 1000  # Test with 1000 tokens
    config.max_tokens_per_request = 4000  # Allow large responses
    config.max_cost_per_video = 2.0  # Reasonable cost limit for testing
    config.cache_enhanced_results = False
    
    try:
        # Initialize transcript enhancer
        print("Initializing transcript enhancer with large context...")
        enhancer = TranscriptEnhancer(config)
        print("✅ Transcript enhancer initialized successfully")
        
        # Create test transcript segments with longer content
        test_segments = [
            TranscriptSegment(
                start_time=0.0,
                end_time=10.0,
                text="Hello everyone, welcome to my comprehensive presentation about machine learning and artificial intelligence. Today we will explore the fascinating world of neural networks, deep learning algorithms, and their transformative applications in modern technology. This is a detailed introduction that covers the fundamental concepts that will guide our discussion throughout this presentation."
            ),
            TranscriptSegment(
                start_time=10.0,
                end_time=20.0,
                text="Machine learning represents a powerful subset of artificial intelligence that harnesses sophisticated algorithms and statistical models to enable computers to learn patterns and make decisions autonomously. These innovative systems can process vast amounts of data, identify complex patterns, and adapt their behavior based on experience without requiring explicit programming for each specific task they encounter."
            ),
            TranscriptSegment(
                start_time=20.0,
                end_time=30.0,
                text="Deep learning, a subset of machine learning, uses neural networks with multiple layers to process complex patterns and relationships in data. The key advantage of deep learning is its ability to automatically extract features from raw data, making it particularly effective for tasks like image recognition, natural language processing, speech recognition, and many other applications that require understanding complex patterns."
            ),
            TranscriptSegment(
                start_time=30.0,
                end_time=40.0,
                text="In the next section, we'll explore practical applications and real-world examples of these technologies, including how they're being used in healthcare, finance, transportation, and other industries. We'll also discuss the challenges and opportunities that come with implementing these advanced systems in production environments."
            ),
            TranscriptSegment(
                start_time=40.0,
                end_time=50.0,
                text="The future of artificial intelligence and machine learning holds tremendous potential for transforming how we work, live, and interact with technology. As these systems become more sophisticated and accessible, we can expect to see even more innovative applications that solve complex problems and create new opportunities across all sectors of society."
            )
        ]
        
        print(f"Testing with {len(test_segments)} transcript segments...")
        
        # Test batching logic with larger context
        print("\nTesting batching logic with large context...")
        batches = enhancer._create_batches(test_segments)
        print(f"Created {len(batches)} batches:")
        
        for i, batch in enumerate(batches):
            batch_text = enhancer._combine_batch_text(batch)
            batch_tokens = enhancer._estimate_tokens(batch_text)
            print(f"  Batch {i+1}: {len(batch)} segments, ~{batch_tokens} tokens")
            print(f"    Text length: {len(batch_text)} characters")
            print(f"    Preview: {batch_text[:150]}...")
        
        # Test enhancement with large context
        print("\nTesting enhancement with large context...")
        results = enhancer.enhance_full_transcript(test_segments, "detailed")
        
        print(f"Enhanced {len(results)} segments")
        
        # Show some results
        print("\nSample enhancement results:")
        for i, result in enumerate(results[:2]):  # Show first 2 results
            print(f"\nSegment {i+1}:")
            print(f"  Original length: {len(result.original_text)} chars")
            print(f"  Enhanced length: {len(result.enhanced_text)} chars")
            print(f"  Original: {result.original_text[:100]}...")
            print(f"  Enhanced: {result.enhanced_text[:100]}...")
            if result.key_points:
                print(f"  Key points: {len(result.key_points)} points")
        
        # Get stats
        stats = enhancer.get_stats()
        print(f"\nEnhancement Statistics:")
        print(f"  Total segments: {stats.total_segments}")
        print(f"  Enhanced segments: {stats.enhanced_segments}")
        print(f"  Total tokens: {stats.total_tokens}")
        print(f"  Total cost: ${stats.total_cost:.4f}")
        print(f"  Processing time: {stats.processing_time:.2f}s")
        
        if stats.enhanced_segments > 0:
            print("✅ Large context enhancement working correctly")
            return True
        else:
            print("❌ No segments were enhanced")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the large context test."""
    print("Large Context Window Test")
    print("=" * 60)
    
    success = test_large_context()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Large context test passed! The system is now using larger context windows.")
        print("\nTo use even larger context windows, you can:")
        print("1. Increase batch_target_tokens in config.py (e.g., to 1500 or 2000)")
        print("2. Increase max_tokens_per_request for longer responses")
        print("3. Adjust the token estimation ratio if needed")
    else:
        print("⚠️  Large context test failed. Please check the output above for details.")


if __name__ == "__main__":
    main() 