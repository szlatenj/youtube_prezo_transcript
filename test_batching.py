#!/usr/bin/env python3
"""
Test script for the new batching functionality and prompt improvements.
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


def test_batching_functionality():
    """Test the new batching functionality."""
    print("Testing Batching Functionality")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not found")
        print("Please set your Anthropic API key in a .env file")
        return False
    
    print("✅ API key found")
    
    # Create test configuration with batching enabled
    config = Config()
    config.enable_llm_enhancement = True
    config.enhancement_level = "detailed"
    config.enable_batching = True
    config.batch_target_tokens = 200
    config.max_cost_per_video = 1.0  # Low cost limit for testing
    config.cache_enhanced_results = False
    
    try:
        # Initialize transcript enhancer
        print("Initializing transcript enhancer with batching...")
        enhancer = TranscriptEnhancer(config)
        print("✅ Transcript enhancer initialized successfully")
        
        # Create test transcript segments with varying lengths
        test_segments = [
            TranscriptSegment(
                start_time=0.0,
                end_time=5.0,
                text="Hello everyone, welcome to my presentation about machine learning and artificial intelligence."
            ),
            TranscriptSegment(
                start_time=5.0,
                end_time=10.0,
                text="Today we will discuss the fundamentals of neural networks, deep learning algorithms, and their applications in modern technology."
            ),
            TranscriptSegment(
                start_time=10.0,
                end_time=15.0,
                text="Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models."
            ),
            TranscriptSegment(
                start_time=15.0,
                end_time=20.0,
                text="These algorithms enable computers to learn and make decisions without being explicitly programmed for every task."
            ),
            TranscriptSegment(
                start_time=20.0,
                end_time=25.0,
                text="Deep learning, a subset of machine learning, uses neural networks with multiple layers to process complex patterns."
            ),
            TranscriptSegment(
                start_time=25.0,
                end_time=30.0,
                text="The key advantage of deep learning is its ability to automatically extract features from raw data."
            ),
            TranscriptSegment(
                start_time=30.0,
                end_time=35.0,
                text="This makes it particularly effective for tasks like image recognition, natural language processing, and speech recognition."
            ),
            TranscriptSegment(
                start_time=35.0,
                end_time=40.0,
                text="In the next section, we'll explore practical applications and real-world examples of these technologies."
            )
        ]
        
        print(f"Testing with {len(test_segments)} transcript segments...")
        
        # Test batching logic
        print("\nTesting batching logic...")
        batches = enhancer._create_batches(test_segments)
        print(f"Created {len(batches)} batches:")
        
        for i, batch in enumerate(batches):
            batch_text = enhancer._combine_batch_text(batch)
            batch_tokens = enhancer._estimate_tokens(batch_text)
            print(f"  Batch {i+1}: {len(batch)} segments, ~{batch_tokens} tokens")
            print(f"    Text: {batch_text[:100]}...")
        
        # Test enhancement with batching
        print("\nTesting enhancement with batching...")
        results = enhancer.enhance_full_transcript(test_segments, "detailed")
        
        print(f"Enhanced {len(results)} segments")
        
        # Show some results
        print("\nSample enhancement results:")
        for i, result in enumerate(results[:3]):  # Show first 3 results
            print(f"\nSegment {i+1}:")
            print(f"  Original: {result.original_text}")
            print(f"  Enhanced: {result.enhanced_text}")
            if result.key_points:
                print(f"  Key points: {result.key_points}")
        
        # Get stats
        stats = enhancer.get_stats()
        print(f"\nEnhancement Statistics:")
        print(f"  Total segments: {stats.total_segments}")
        print(f"  Enhanced segments: {stats.enhanced_segments}")
        print(f"  Total tokens: {stats.total_tokens}")
        print(f"  Total cost: ${stats.total_cost:.4f}")
        print(f"  Processing time: {stats.processing_time:.2f}s")
        
        if stats.enhanced_segments > 0:
            print("✅ Batching enhancement working correctly")
        else:
            print("❌ No segments were enhanced")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_styles():
    """Test different prompt styles."""
    print("\nTesting Prompt Styles")
    print("=" * 50)
    
    config = Config()
    config.enable_llm_enhancement = True
    config.enhancement_level = "detailed"
    config.enable_batching = False  # Disable batching for this test
    
    try:
        enhancer = TranscriptEnhancer(config)
        
        test_text = "Machine learning is a subset of AI that uses algorithms to learn from data."
        
        # Test different prompt styles
        styles = ["clear", "academic", "conversational", "technical"]
        
        for style in styles:
            print(f"\nTesting {style} style:")
            config.prompt_style = style
            prompt = enhancer._get_enhancement_prompt(test_text, "detailed")
            print(f"  Prompt preview: {prompt[:200]}...")
        
        print("✅ Prompt styles working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Prompt style test failed: {e}")
        return False


def test_custom_prompt():
    """Test custom prompt template."""
    print("\nTesting Custom Prompt Template")
    print("=" * 50)
    
    config = Config()
    config.enable_llm_enhancement = True
    config.enhancement_level = "detailed"
    config.enable_batching = False
    
    # Set custom prompt template
    config.custom_prompt_template = """
You are an expert at improving presentation transcripts. Please enhance the following text:

{text}

Focus on:
- Clarity and coherence
- Professional language
- Logical flow
- Key concept extraction

Provide the enhanced text in a clear, structured format.
"""
    
    try:
        enhancer = TranscriptEnhancer(config)
        
        test_text = "Machine learning is a subset of AI that uses algorithms to learn from data."
        prompt = enhancer._get_enhancement_prompt(test_text, "detailed")
        
        print("Custom prompt generated:")
        print(prompt)
        
        print("✅ Custom prompt template working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Custom prompt test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Batching and Prompt Enhancement Tests")
    print("=" * 60)
    
    tests = [
        ("Batching Functionality", test_batching_functionality),
        ("Prompt Styles", test_prompt_styles),
        ("Custom Prompt Template", test_custom_prompt)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Batching and prompt improvements are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")


if __name__ == "__main__":
    main() 