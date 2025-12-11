import os
from pathlib import Path
from typing import Union
from PIL import Image
import requests
import hashlib
from functools import lru_cache
from io import BytesIO
from model_loader import model_loader
from config import MAX_NEW_TOKENS, SUPPORTED_FORMATS, MAX_IMAGE_SIZE_MB, MAX_IMAGE_DIMENSION
from smart_correction import smart_correct

_text_cache = {}


def validate_image_input(image_input: str) -> None:
    if not image_input or not isinstance(image_input, str):
        raise ValueError("Image input must be a non-empty string")

    if image_input.startswith(('http://', 'https://')):
        return

    if not os.path.isfile(image_input):
        raise ValueError(f"File not found: {image_input}")

    file_ext = Path(image_input).suffix.lower()
    if file_ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported image format: {file_ext}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    file_size_mb = os.path.getsize(image_input) / (1024 * 1024)
    if file_size_mb > MAX_IMAGE_SIZE_MB:
        raise ValueError(
            f"Image file too large: {file_size_mb:.2f}MB. "
            f"Maximum allowed: {MAX_IMAGE_SIZE_MB}MB"
        )


def preprocess_image(image: Image.Image, enable_preprocessing: bool = False) -> Image.Image:
    if not enable_preprocessing:
        return image

    from PIL import ImageEnhance

    enhancer = ImageEnhance.Contrast(image)
    enhanced = enhancer.enhance(1.3)

    return enhanced


def load_image(image_input: str) -> Image.Image:
    try:
        if image_input.startswith(('http://', 'https://')):
            response = requests.get(image_input, timeout=10)
            response.raise_for_status()

            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > MAX_IMAGE_SIZE_MB:
                    raise ValueError(
                        f"Image too large: {size_mb:.2f}MB. "
                        f"Maximum allowed: {MAX_IMAGE_SIZE_MB}MB"
                    )

            image = Image.open(BytesIO(response.content)).convert("RGB")
        else:
            image = Image.open(image_input).convert("RGB")

        width, height = image.size

        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            if width > height:
                new_width = MAX_IMAGE_DIMENSION
                new_height = int((MAX_IMAGE_DIMENSION / width) * height)
            else:
                new_height = MAX_IMAGE_DIMENSION
                new_width = int((MAX_IMAGE_DIMENSION / height) * width)

            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return image
    except requests.RequestException as e:
        raise ValueError(f"Failed to load image from URL: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to load image: {str(e)}")


def _get_image_hash(image: Image.Image) -> str:
    img_bytes = image.tobytes()
    return hashlib.md5(img_bytes).hexdigest()


def recognize_text(image_input: str) -> str:
    validate_image_input(image_input)

    image = load_image(image_input)

    image_hash = _get_image_hash(image)
    if image_hash in _text_cache:
        return _text_cache[image_hash]

    try:
        model, processor = model_loader.load()
    except Exception as e:
        raise Exception(f"Model loading failed: {str(e)}")

    try:
        pixel_values = processor(images=image, return_tensors="pt").pixel_values

        device = model_loader.get_device()
        pixel_values = pixel_values.to(device)

        generated_ids = model.generate(pixel_values, max_new_tokens=MAX_NEW_TOKENS)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        raw_text = generated_text.strip()
        corrected = smart_correct(raw_text)

        result = corrected['best_result']
        _text_cache[image_hash] = result

        if len(_text_cache) > 100:
            oldest_key = next(iter(_text_cache))
            del _text_cache[oldest_key]

        return result
    except Exception as e:
        raise Exception(f"Text recognition failed: {str(e)}")
