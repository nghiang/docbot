import logging

from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)


class PaddleOCRWrapper:
    def __init__(self):
        logger.info("Initializing PaddleOCR...")
        self.ocr = PaddleOCR(
            text_detection_model_name="PP-OCRv5_server_det",
            text_recognition_model_name="PP-OCRv5_server_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        logger.info("PaddleOCR initialized successfully")

    def ocr_image(self, image_path: str) -> list[str]:
        """Run OCR on an image and return a list of recognized text strings."""
        result = self.ocr.predict(image_path)
        texts: list[str] = []
        try:
            # PaddleOCR v3 predict() returns a generator of dicts with 'rec_texts'
            for page_result in result:
                if isinstance(page_result, dict):
                    rec_texts = page_result.get("rec_texts", [])
                    texts.extend(rec_texts)
                elif isinstance(page_result, (list, tuple)):
                    # Legacy format: list of [box, (text, confidence)]
                    for line in page_result:
                        if isinstance(line, (list, tuple)) and len(line) >= 2:
                            text_info = line[1]
                            if isinstance(text_info, (list, tuple)):
                                texts.append(str(text_info[0]))
                            elif isinstance(text_info, str):
                                texts.append(text_info)
        except Exception as e:
            logger.warning(f"Error parsing OCR result: {e}")
        return texts


# Global instance to be initialized at worker startup
paddle_ocr: PaddleOCRWrapper | None = None


def get_paddle_ocr() -> PaddleOCRWrapper | None:
    """Get the global PaddleOCR instance."""
    global paddle_ocr
    if paddle_ocr is None:
        try:
            paddle_ocr = PaddleOCRWrapper()
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
    return paddle_ocr
