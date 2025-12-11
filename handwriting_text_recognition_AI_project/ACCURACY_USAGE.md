# OCR Accuracy Measurement - Usage Guide

## Overview

Your OCR application now includes comprehensive accuracy measurement capabilities that allow you to evaluate the performance of your OCR engines by comparing their output against ground truth text.

## Features Added

### 1. Accuracy Metrics Module (`src/accuracy_metrics.py`)

Calculates the following metrics:

- **Character Accuracy**: Percentage of correctly recognized characters
- **Word Accuracy**: Percentage of correctly recognized words
- **Character Error Rate (CER)**: Industry-standard metric for OCR evaluation
- **Word Error Rate (WER)**: Measures word-level errors
- **Levenshtein Distance**: Edit distance between texts
- **Statistics**: Character counts, word counts, etc.

### 2. Web Interface Updates

The web interface now includes:

- **Ground Truth Input Field**: Yellow highlighted section where you can enter the correct text
- **Accuracy Metrics Display**: Beautiful color-coded metrics (green for excellent, yellow for fair, red for poor)
- **Automatic Calculation**: Metrics are calculated automatically when ground truth is provided

### 3. API Endpoints

Three new endpoints have been added:

#### `/calculate_accuracy` (POST)
Calculate accuracy for any text comparison.

**Request (JSON):**
```json
{
  "ground_truth": "Hello World",
  "predicted": "Helo World"
}
```

**Response:**
```json
{
  "success": true,
  "metrics": {
    "character_accuracy": 90.91,
    "word_accuracy": 50.0,
    "character_error_rate": 9.09,
    "word_error_rate": 50.0,
    "levenshtein_distance": 1,
    "ground_truth_length": 11,
    "predicted_length": 10,
    "ground_truth_word_count": 2,
    "predicted_word_count": 2
  }
}
```

#### `/recognize_with_accuracy` (POST)
Perform OCR and calculate accuracy in one request.

**Form Data:**
- `file`: Image file
- `ground_truth`: (optional) The correct text

#### `/recognize_multi_with_accuracy` (POST)
Run multiple OCR engines and compare their accuracy.

**Form Data:**
- `file`: Image file
- `ground_truth`: (optional) The correct text

**Response includes accuracy metrics for each engine, sorted by performance.**

## How to Use

### Web Interface

1. **Start the application:**
   ```bash
   python3 web_app.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5002`

3. **Upload an image:**
   - Drag and drop an image, or click to browse
   - Or enter an image URL

4. **Enter ground truth (optional):**
   - In the yellow "Ground Truth" section, type the correct text that should be in the image
   - This enables accuracy measurement

5. **View results:**
   - OCR recognized text is displayed
   - If ground truth was provided, accuracy metrics appear below with:
     - Color-coded accuracy percentages
     - Error rates
     - Detailed statistics

### Programmatic Usage

```python
from accuracy_metrics import get_detailed_metrics, compare_engines

# Calculate accuracy for a single result
ground_truth = "The quick brown fox"
predicted = "The quik brown fox"
metrics = get_detailed_metrics(ground_truth, predicted)

print(f"Character Accuracy: {metrics['character_accuracy']}%")
print(f"Word Accuracy: {metrics['word_accuracy']}%")

# Compare multiple OCR engines
engine_results = [
    {'engine': 'TrOCR', 'text': 'predicted text 1', 'success': True},
    {'engine': 'EasyOCR', 'text': 'predicted text 2', 'success': True}
]
results = compare_engines(ground_truth, engine_results)
# Results are sorted by accuracy, best first
```

### Testing

Run the test script to see example calculations:

```bash
python3 test_accuracy.py
```

## Accuracy Rating Guide

The metrics are color-coded based on accuracy:

- **🟢 Excellent** (95-100%): Outstanding OCR performance
- **🟢 Good** (85-94%): Very good, minor errors
- **🟡 Fair** (70-84%): Acceptable, some errors
- **🟠 Poor** (50-69%): Needs improvement
- **🔴 Bad** (<50%): Significant errors

## Understanding the Metrics

### Character Accuracy vs Word Accuracy

- **Character Accuracy**: More granular, shows how many individual characters are correct
- **Word Accuracy**: Stricter, a word is only counted as correct if 100% of its characters match

Example:
- Ground truth: "Hello World"
- Predicted: "Helo World"
- Character Accuracy: ~91% (1 char wrong out of 11)
- Word Accuracy: 50% (1 word wrong out of 2)

### CER and WER

- Lower is better (0% is perfect)
- Industry-standard metrics for OCR evaluation
- CER: Character Error Rate
- WER: Word Error Rate

### Levenshtein Distance

- Minimum number of single-character edits (insertions, deletions, substitutions) needed to change predicted text into ground truth
- Lower is better (0 is perfect match)

## API Examples

### Using curl

```bash
# Calculate accuracy
curl -X POST http://localhost:5002/calculate_accuracy \
  -H "Content-Type: application/json" \
  -d '{
    "ground_truth": "Hello World",
    "predicted": "Helo World"
  }'

# OCR with accuracy
curl -X POST http://localhost:5002/recognize_with_accuracy \
  -F "file=@image.jpg" \
  -F "ground_truth=Hello World"
```

### Using Python requests

```python
import requests

# Calculate accuracy
response = requests.post('http://localhost:5002/calculate_accuracy',
    json={
        'ground_truth': 'Hello World',
        'predicted': 'Helo World'
    }
)
print(response.json()['metrics'])

# OCR with accuracy
with open('image.jpg', 'rb') as f:
    response = requests.post('http://localhost:5002/recognize_with_accuracy',
        files={'file': f},
        data={'ground_truth': 'Hello World'}
    )
print(response.json()['accuracy_metrics'])
```

## Tips for Best Results

1. **Use exact ground truth**: The accuracy metrics are case-sensitive by default
2. **Test multiple images**: Accuracy can vary significantly based on image quality
3. **Compare engines**: Use the multi-engine endpoint to see which performs best for your use case
4. **Normalize if needed**: For case-insensitive comparison, the metrics internally normalize to lowercase for word-level comparisons

## Next Steps

- Create a dataset of test images with ground truth labels
- Build automated testing pipeline to track OCR accuracy over time
- Use metrics to optimize preprocessing or choose the best OCR engine for your needs
- Export results to CSV/JSON for analysis

## Support

If you encounter any issues or have questions about the accuracy metrics, please check:
- The test script: `test_accuracy.py`
- The implementation: `src/accuracy_metrics.py`
- The API endpoints: `web_app.py` (lines 276-475)
