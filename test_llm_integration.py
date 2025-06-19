#!/usr/bin/env python3
"""
Test script for LLM integration
Tests the transcript enhancer functionality
"""

import os
import sys

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


def test_llm_integration():
    """Test the LLM integration functionality."""
    print("Testing LLM Integration...")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not found")
        print("Please set your Anthropic API key using one of these methods:")
        print()
        print("Method 1: Create a .env file in the project directory:")
        print("  echo 'ANTHROPIC_API_KEY=your-api-key-here' > .env")
        print()
        print("Method 2: Set environment variable:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print()
        print("Method 3: Copy env_example.txt to .env and edit:")
        print("  cp env_example.txt .env")
        print("  # Then edit .env with your actual API key")
        return False
    
    print("✅ API key found")
    
    # Create test configuration
    config = Config()
    config.enable_llm_enhancement = True
    config.enhancement_level = "basic"
    config.max_cost_per_video = 1.0  # Low cost limit for testing
    config.cache_enhanced_results = False
    
    try:
        # Initialize transcript enhancer
        print("Initializing transcript enhancer...")
        enhancer = TranscriptEnhancer(config)
        print("✅ Transcript enhancer initialized successfully")
        
        # Create test transcript segments
        test_segments = [
            TranscriptSegment(
                start_time=0.0,
                end_time=5.0,
                text="Hello everyone welcome to my presentation about machine learning."
            ),
            TranscriptSegment(
                start_time=5.0,
                end_time=10.0,
                text="Today we will discuss the basics of neural networks and deep learning."
            ),
            TranscriptSegment(
                start_time=10.0,
                end_time=15.0,
                text="Machine learning is a subset of artificial intelligence."
            )
        ]
        
        print(f"Testing with {len(test_segments)} transcript segments...")
        
        # Test single segment enhancement
        print("\nTesting single segment enhancement...")
        result = enhancer.enhance_transcript_segment(test_segments[0], "basic")
        
        print(f"Original: {result.original_text}")
        print(f"Enhanced: {result.enhanced_text}")
        print(f"Cost: ${result.cost:.4f}")
        print(f"Tokens used: {result.tokens_used}")
        
        if result.enhanced_text != result.original_text:
            print("✅ Single segment enhancement working")
        else:
            print("⚠️  Enhancement returned same text (might be expected for basic level)")
        
        # Test full transcript enhancement (limited to 2 segments for cost control)
        print("\nTesting full transcript enhancement (limited)...")
        limited_segments = test_segments[:2]
        results = enhancer.enhance_full_transcript(limited_segments, "basic")
        
        print(f"Enhanced {len(results)} segments")
        
        # Get stats
        stats = enhancer.get_stats()
        print(f"Total cost: ${stats.total_cost:.4f}")
        print(f"Total tokens: {stats.total_tokens}")
        print(f"Processing time: {stats.processing_time:.2f}s")
        
        if stats.enhanced_segments > 0:
            print("✅ Full transcript enhancement working")
        else:
            print("❌ No segments were enhanced")
            return False
        
        # Test key points extraction
        print("\nTesting key points extraction...")
        key_points = enhancer.extract_key_points(test_segments)
        
        if key_points:
            print("✅ Key points extracted successfully:")
            for i, point in enumerate(key_points[:3], 1):  # Show first 3 points
                print(f"  {i}. {point}")
        else:
            print("⚠️  No key points extracted")
        
        print("\n" + "=" * 50)
        print("✅ LLM Integration Test Completed Successfully!")
        print(f"Total cost for testing: ${stats.total_cost:.4f}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration loading with LLM settings."""
    print("\nTesting Configuration...")
    print("=" * 30)
    
    try:
        config = Config()
        
        # Test default LLM settings
        print(f"Default enable_llm_enhancement: {config.enable_llm_enhancement}")
        print(f"Default enhancement_level: {config.enhancement_level}")
        print(f"Default max_cost_per_video: ${config.max_cost_per_video}")
        print(f"Default anthropic_model: {config.anthropic_model}")
        
        # Test setting LLM options
        config.enable_llm_enhancement = True
        config.enhancement_level = "academic"
        config.max_cost_per_video = 10.0
        
        print(f"Modified enable_llm_enhancement: {config.enable_llm_enhancement}")
        print(f"Modified enhancement_level: {config.enhancement_level}")
        print(f"Modified max_cost_per_video: ${config.max_cost_per_video}")
        
        print("✅ Configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def main():
    """Main test function."""
    print("LLM Integration Test Suite")
    print("=" * 50)
    
    # Test configuration first
    config_ok = test_configuration()
    
    # Test LLM integration
    llm_ok = test_llm_integration()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"LLM Integration: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    
    if config_ok and llm_ok:
        print("\n🎉 All tests passed! LLM integration is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 