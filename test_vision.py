"""
Quick test script to verify Ollama vision models are accessible.
Run this to ensure the app can use your vision models.
"""

import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import from src modules
from src.core.config import ConfigManager
from src.services.llm_adapter import OllamaAdapter

def main():
    print("=" * 70)
    print("OLLAMA VISION MODEL TEST")
    print("=" * 70)
    
    # Initialize config and adapter
    print("\n1. Initializing Ollama adapter...")
    config = ConfigManager(portable_root=Path(__file__).parent)
    adapter = OllamaAdapter(config)
    
    # Test vision capability
    print("\n2. Testing vision model availability...")
    results = adapter.test_vision_capability()
    
    # Display results
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    print(f"\nOllama Connected: {'✅ YES' if results['ollama_connected'] else '❌ NO'}")
    print(f"Test Status: {results['test_status'].upper()}")
    
    if results['available_models']:
        print(f"\nAll Available Models ({len(results['available_models'])}):")
        for model in results['available_models'][:10]:  # Show first 10
            print(f"  • {model}")
        if len(results['available_models']) > 10:
            print(f"  ... and {len(results['available_models']) - 10} more")
    
    if results['vision_models']:
        print(f"\n✅ Vision Models Found ({len(results['vision_models'])}):")
        for model in results['vision_models']:
            marker = "⭐" if model == results['recommended_model'] else "  "
            print(f"  {marker} {model}")
        
        print(f"\n🎯 Recommended Model: {results['recommended_model']}")
        print("\n✅ Your app is ready to analyze images with vision models!")
    else:
        print("\n⚠️  No vision models found!")
        print("\nTo install a vision model, run:")
        print("  ollama pull qwen2.5vl:7b")
    
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
