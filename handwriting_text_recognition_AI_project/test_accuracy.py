#!/usr/bin/env python3
"""
Test script for OCR accuracy metrics
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from accuracy_metrics import (
    calculate_cer,
    calculate_wer,
    calculate_accuracy,
    get_detailed_metrics,
    compare_engines
)


def test_basic_metrics():
    """Test basic accuracy metrics with simple examples"""
    print("=" * 60)
    print("Testing Basic Accuracy Metrics")
    print("=" * 60)

    # Test 1: Perfect match
    ground_truth = "Hello World"
    predicted = "Hello World"
    metrics = get_detailed_metrics(ground_truth, predicted)

    print("\nTest 1: Perfect Match")
    print(f"Ground Truth: '{ground_truth}'")
    print(f"Predicted:    '{predicted}'")
    print(f"Character Accuracy: {metrics['character_accuracy']}% (expected: 100%)")
    print(f"Word Accuracy: {metrics['word_accuracy']}% (expected: 100%)")
    print(f"CER: {metrics['character_error_rate']}% (expected: 0%)")
    print(f"WER: {metrics['word_error_rate']}% (expected: 0%)")

    # Test 2: One character error
    ground_truth = "Hello World"
    predicted = "Helo World"  # Missing 'l'
    metrics = get_detailed_metrics(ground_truth, predicted)

    print("\nTest 2: One Character Missing")
    print(f"Ground Truth: '{ground_truth}'")
    print(f"Predicted:    '{predicted}'")
    print(f"Character Accuracy: {metrics['character_accuracy']}%")
    print(f"Word Accuracy: {metrics['word_accuracy']}%")
    print(f"CER: {metrics['character_error_rate']}%")
    print(f"Levenshtein Distance: {metrics['levenshtein_distance']}")

    # Test 3: One word error
    ground_truth = "Hello World"
    predicted = "Hello Earth"
    metrics = get_detailed_metrics(ground_truth, predicted)

    print("\nTest 3: One Word Different")
    print(f"Ground Truth: '{ground_truth}'")
    print(f"Predicted:    '{predicted}'")
    print(f"Character Accuracy: {metrics['character_accuracy']}%")
    print(f"Word Accuracy: {metrics['word_accuracy']}%")
    print(f"WER: {metrics['word_error_rate']}%")

    # Test 4: Case insensitivity (metrics normalize to lowercase)
    ground_truth = "Hello World"
    predicted = "hello world"
    metrics = get_detailed_metrics(ground_truth, predicted)

    print("\nTest 4: Case Difference")
    print(f"Ground Truth: '{ground_truth}'")
    print(f"Predicted:    '{predicted}'")
    print(f"Character Accuracy: {metrics['character_accuracy']}% (expected: 100%)")
    print(f"Note: Metrics normalize text to lowercase for comparison")


def test_handwriting_scenario():
    """Test realistic handwriting OCR scenario"""
    print("\n" + "=" * 60)
    print("Testing Realistic Handwriting Scenario")
    print("=" * 60)

    ground_truth = "The quick brown fox jumps over the lazy dog"
    predicted = "The quik brown fox junps over the lasy dog"  # Typical OCR errors

    metrics = get_detailed_metrics(ground_truth, predicted)

    print(f"\nGround Truth: '{ground_truth}'")
    print(f"Predicted:    '{predicted}'")
    print(f"\nMetrics:")
    print(f"  Character Accuracy: {metrics['character_accuracy']}%")
    print(f"  Word Accuracy: {metrics['word_accuracy']}%")
    print(f"  Character Error Rate: {metrics['character_error_rate']}%")
    print(f"  Word Error Rate: {metrics['word_error_rate']}%")
    print(f"  Levenshtein Distance: {metrics['levenshtein_distance']}")
    print(f"\nStatistics:")
    print(f"  Ground truth: {metrics['ground_truth_length']} chars, {metrics['ground_truth_word_count']} words")
    print(f"  Predicted: {metrics['predicted_length']} chars, {metrics['predicted_word_count']} words")


def test_engine_comparison():
    """Test comparing multiple OCR engines"""
    print("\n" + "=" * 60)
    print("Testing Multiple Engine Comparison")
    print("=" * 60)

    ground_truth = "Machine learning is fascinating"

    # Simulate results from different engines
    engine_results = [
        {
            'engine': 'TrOCR',
            'text': 'Machine learning is facinating',  # spelling error
            'time': '0.15s',
            'success': True
        },
        {
            'engine': 'EasyOCR',
            'text': 'Machine leaming is fascinating',  # OCR error
            'time': '0.42s',
            'success': True
        },
        {
            'engine': 'Tesseract',
            'text': 'Machine learning fascinating',  # missing word
            'time': '0.08s',
            'success': True
        }
    ]

    results_with_metrics = compare_engines(ground_truth, engine_results)

    print(f"\nGround Truth: '{ground_truth}'")
    print("\nEngine Results (sorted by accuracy):")

    for i, result in enumerate(results_with_metrics, 1):
        metrics = result['accuracy_metrics']
        print(f"\n{i}. {result['engine']}")
        print(f"   Text: '{result['text']}'")
        print(f"   Character Accuracy: {metrics['character_accuracy']}%")
        print(f"   Word Accuracy: {metrics['word_accuracy']}%")
        print(f"   Time: {result['time']}")


if __name__ == '__main__':
    try:
        test_basic_metrics()
        test_handwriting_scenario()
        test_engine_comparison()

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
