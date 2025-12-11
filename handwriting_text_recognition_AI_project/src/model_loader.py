from typing import Optional, Tuple
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from config import MODEL_NAME


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


class ModelLoader:

    def __init__(self):
        self._model: Optional[VisionEncoderDecoderModel] = None
        self._processor: Optional[TrOCRProcessor] = None
        self._device = None

    def load(self) -> Tuple[VisionEncoderDecoderModel, TrOCRProcessor]:
        if self._model is None or self._processor is None:
            try:
                self._device = get_device()

                print(f"Loading model: {MODEL_NAME}")
                print(f"Using device: {self._device}")

                if self._device.type == "mps":
                    print("🚀 Apple Silicon GPU detected - expect 10-20x speedup!")
                elif self._device.type == "cuda":
                    print("🚀 NVIDIA GPU detected - expect 10-20x speedup!")
                else:
                    print("⚠️  Using CPU - will be slower")

                print("Loading... (may take a minute on first run)")

                self._processor = TrOCRProcessor.from_pretrained(MODEL_NAME)

                self._model = VisionEncoderDecoderModel.from_pretrained(
                    MODEL_NAME,
                    low_cpu_mem_usage=True,
                    torch_dtype=torch.float32
                )

                self._model = self._model.to(self._device)

                print(f"✅ Model loaded successfully on {self._device}!")

            except Exception as e:
                raise Exception(f"Failed to load model: {str(e)}")

        return self._model, self._processor

    def get_device(self):
        return self._device if self._device else get_device()

    def is_loaded(self) -> bool:
        return self._model is not None and self._processor is not None


model_loader = ModelLoader()
