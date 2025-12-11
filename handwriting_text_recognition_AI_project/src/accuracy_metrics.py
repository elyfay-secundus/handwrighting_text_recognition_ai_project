import re
from typing import Dict, List


def calculate_levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return calculate_levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def normalize_text(text: str) -> str:
    """Normalize text for comparison by removing extra whitespace and converting to lowercase."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def calculate_cer(ground_truth: str, predicted: str) -> float:
    """
    Calculate Character Error Rate (CER).
    CER = (substitutions + deletions + insertions) / total characters in ground truth
    Returns value between 0 and 1, where 0 is perfect and 1 is completely wrong.
    """
    if not ground_truth:
        return 0.0 if not predicted else 1.0

    distance = calculate_levenshtein_distance(ground_truth, predicted)
    cer = distance / len(ground_truth)
    return min(cer, 1.0)


def calculate_wer(ground_truth: str, predicted: str) -> float:
    """
    Calculate Word Error Rate (WER).
    WER = (substitutions + deletions + insertions) / total words in ground truth
    Returns value between 0 and 1, where 0 is perfect and 1 is completely wrong.
    """
    gt_words = normalize_text(ground_truth).split()
    pred_words = normalize_text(predicted).split()

    if not gt_words:
        return 0.0 if not pred_words else 1.0

    distance = calculate_levenshtein_distance(' '.join(gt_words), ' '.join(pred_words))
    word_distance = 0

    m, n = len(gt_words), len(pred_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if gt_words[i-1] == pred_words[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    word_distance = dp[m][n]
    wer = word_distance / len(gt_words)
    return min(wer, 1.0)


def calculate_accuracy(ground_truth: str, predicted: str) -> float:
    """
    Calculate accuracy as percentage of correct characters.
    Returns value between 0 and 100.
    """
    if not ground_truth:
        return 100.0 if not predicted else 0.0

    cer = calculate_cer(ground_truth, predicted)
    accuracy = max(0.0, (1.0 - cer) * 100)
    return accuracy


def calculate_word_accuracy(ground_truth: str, predicted: str) -> float:
    """
    Calculate word-level accuracy as percentage of correct words.
    Returns value between 0 and 100.
    """
    gt_words = normalize_text(ground_truth).split()
    pred_words = normalize_text(predicted).split()

    if not gt_words:
        return 100.0 if not pred_words else 0.0

    correct_words = sum(1 for gt, pred in zip(gt_words, pred_words) if gt == pred)
    word_accuracy = (correct_words / len(gt_words)) * 100
    return word_accuracy


def get_detailed_metrics(ground_truth: str, predicted: str) -> Dict:
    """
    Calculate all accuracy metrics and return as a dictionary.

    Args:
        ground_truth: The correct/expected text
        predicted: The text predicted by OCR

    Returns:
        Dictionary containing all metrics
    """
    cer = calculate_cer(ground_truth, predicted)
    wer = calculate_wer(ground_truth, predicted)
    accuracy = calculate_accuracy(ground_truth, predicted)
    word_accuracy = calculate_word_accuracy(ground_truth, predicted)
    levenshtein = calculate_levenshtein_distance(ground_truth, predicted)

    return {
        'character_error_rate': round(cer * 100, 2),
        'word_error_rate': round(wer * 100, 2),
        'character_accuracy': round(accuracy, 2),
        'word_accuracy': round(word_accuracy, 2),
        'levenshtein_distance': levenshtein,
        'ground_truth_length': len(ground_truth),
        'predicted_length': len(predicted),
        'ground_truth_word_count': len(ground_truth.split()),
        'predicted_word_count': len(predicted.split())
    }


def compare_engines(ground_truth: str, engine_results: List[Dict]) -> List[Dict]:
    """
    Compare multiple OCR engine results against ground truth.

    Args:
        ground_truth: The correct/expected text
        engine_results: List of results from different OCR engines
                       Each result should have 'engine' and 'text' keys

    Returns:
        List of results with accuracy metrics added
    """
    results_with_metrics = []

    for result in engine_results:
        if result.get('success', True) and 'text' in result:
            metrics = get_detailed_metrics(ground_truth, result['text'])
            result_copy = result.copy()
            result_copy['accuracy_metrics'] = metrics
            results_with_metrics.append(result_copy)
        else:
            results_with_metrics.append(result)

    results_with_metrics.sort(
        key=lambda x: x.get('accuracy_metrics', {}).get('character_accuracy', 0),
        reverse=True
    )

    return results_with_metrics
