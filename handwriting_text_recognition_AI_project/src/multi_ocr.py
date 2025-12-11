from PIL import Image
import requests
from io import BytesIO
from smart_correction import smart_correct


def load_image_from_input(image_input: str) -> Image.Image:
    if image_input.startswith(('http://', 'https://')):
        response = requests.get(image_input, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    else:
        return Image.open(image_input).convert("RGB")


def ocr_trocr(image_input: str) -> dict:
    try:
        from text_recognizer import recognize_text
        import time
        start = time.time()
        text = recognize_text(image_input)
        elapsed = time.time() - start

        corrected = smart_correct(text)

        return {
            'engine': 'TrOCR (AI)',
            'text_raw': text,
            'text': corrected['best_result'],
            'corrections': corrected['corrections_applied'],
            'time': f"{elapsed:.2f}s",
            'best_for': 'Handwriting',
            'success': True
        }
    except Exception as e:
        return {
            'engine': 'TrOCR (AI)',
            'text': '',
            'error': str(e),
            'success': False
        }


def ocr_easyocr(image_input: str) -> dict:
    try:
        import easyocr
        import time
        import torch

        if not hasattr(ocr_easyocr, 'reader'):
            use_gpu = torch.cuda.is_available() or torch.backends.mps.is_available()
            ocr_easyocr.reader = easyocr.Reader(['en'], gpu=use_gpu)

        image = load_image_from_input(image_input)

        start = time.time()
        results = ocr_easyocr.reader.readtext(image, detail=0)
        text = ' '.join(results)
        elapsed = time.time() - start

        corrected = smart_correct(text)

        return {
            'engine': 'EasyOCR',
            'text_raw': text,
            'text': corrected['best_result'],
            'corrections': corrected['corrections_applied'],
            'time': f"{elapsed:.2f}s",
            'best_for': 'Mixed text',
            'success': True
        }
    except Exception as e:
        return {
            'engine': 'EasyOCR',
            'text': '',
            'error': str(e),
            'success': False
        }


def ocr_tesseract(image_input: str) -> dict:
    try:
        import pytesseract
        import time

        image = load_image_from_input(image_input)

        start = time.time()
        text = pytesseract.image_to_string(image).strip()
        elapsed = time.time() - start

        return {
            'engine': 'Tesseract',
            'text': text,
            'time': f"{elapsed:.2f}s",
            'best_for': 'Printed text',
            'success': True
        }
    except Exception as e:
        return {
            'engine': 'Tesseract',
            'text': '',
            'error': str(e),
            'success': False
        }


def recognize_multi(image_input: str, engines=['trocr', 'easyocr']) -> list:
    results = []

    if 'trocr' in engines:
        results.append(ocr_trocr(image_input))

    if 'easyocr' in engines:
        results.append(ocr_easyocr(image_input))

    if 'tesseract' in engines:
        results.append(ocr_tesseract(image_input))

    return results
