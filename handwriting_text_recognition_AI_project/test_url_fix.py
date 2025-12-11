#!/usr/bin/env python3
"""
Test script to verify URL image loading is working correctly
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from text_recognizer import load_image

# Test with a sample image URL
test_urls = [
    "https://raw.githubusercontent.com/tesseract-ocr/docs/master/images/eurotext.png",
    "https://raw.githubusercontent.com/microsoft/unilm/master/trocr/img/example.jpg"
]

print("Testing URL image loading...\n")

for url in test_urls:
    print(f"Testing: {url}")
    try:
        image = load_image(url)
        print(f"✅ SUCCESS: Loaded image with size {image.size}")
        print(f"   Format: {image.mode}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
    print()

print("URL loading test complete!")
