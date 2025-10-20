"""
OCR engine adapter for Tesseract integration.

Provides OCR capabilities with fast baseline and high-accuracy modes.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available - OCR functionality disabled")


class OCRMode(Enum):
    """OCR processing modes."""
    FAST = "fast"  # Fast baseline for quick processing
    HIGH_ACCURACY = "high_accuracy"  # High-accuracy mode with preprocessing


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence: float = 0.0
    language: str = "eng"
    mode: OCRMode = OCRMode.FAST
    preprocessing_applied: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class OCRAdapter:
    """
    Adapter for Tesseract OCR engine.
    
    Features:
    - Fast baseline mode for quick processing
    - High-accuracy mode with preprocessing
    - Multi-language support
    - Page-level processing for PDFs
    - Confidence scoring
    """
    
    def __init__(self, config_manager):
        """
        Initialize OCR adapter.
        
        Args:
            config_manager: ConfigManager instance for OCR settings
        """
        self.config = config_manager
        
        # Check availability
        if not PYTESSERACT_AVAILABLE:
            logger.error("pytesseract not installed")
            raise RuntimeError("pytesseract is required but not installed")
        
        # Get Tesseract path from config
        tesseract_path = self.config.get('paths.tesseract_cmd')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Using Tesseract at: {tesseract_path}")
        
        # Verify Tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.error(f"Tesseract not found or not working: {e}")
            raise RuntimeError(f"Tesseract initialization failed: {e}")
        
        # Load configuration
        self.default_language = self.config.get('ocr_language', 'eng')
        self.psm = self.config.get('ocr_psm', 3)  # Page segmentation mode
        self.oem = self.config.get('ocr_oem', 3)  # OCR engine mode
        
        logger.info(f"OCR Adapter initialized (lang={self.default_language}, psm={self.psm}, oem={self.oem})")
    
    def process_image(self, image_path: str, mode: OCRMode = OCRMode.FAST,
                     language: Optional[str] = None) -> OCRResult:
        """
        Process a single image with OCR.
        
        Args:
            image_path: Path to image file
            mode: OCR processing mode
            language: Language code (default: from config)
        
        Returns:
            OCRResult with extracted text and metadata
        """
        try:
            image = Image.open(image_path)
            return self.process_pil_image(image, mode, language)
        
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            return OCRResult(
                text="",
                error_code="OCR_FILE_NOT_FOUND",
                error_message=f"File not found: {image_path}"
            )
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return OCRResult(
                text="",
                error_code="OCR_PROCESS_ERROR",
                error_message=str(e)
            )
    
    def process_pil_image(self, image: Image.Image, mode: OCRMode = OCRMode.FAST,
                         language: Optional[str] = None) -> OCRResult:
        """
        Process a PIL Image object with OCR.
        
        Args:
            image: PIL Image object
            mode: OCR processing mode
            language: Language code (default: from config)
        
        Returns:
            OCRResult with extracted text and metadata
        """
        lang = language or self.default_language
        preprocessing_applied = False
        
        try:
            # Apply preprocessing for high-accuracy mode
            if mode == OCRMode.HIGH_ACCURACY:
                image = self._preprocess_image(image)
                preprocessing_applied = True
            
            # Configure Tesseract
            config = self._build_tesseract_config(mode)
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang=lang, config=config)
            
            # Get confidence score
            try:
                data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
                confidences = [float(conf) for conf in data['conf'] if conf != -1]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            except:
                avg_confidence = 0.0
            
            logger.debug(f"OCR complete: {len(text)} chars, {avg_confidence:.1f}% confidence")
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                language=lang,
                mode=mode,
                preprocessing_applied=preprocessing_applied
            )
        
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return OCRResult(
                text="",
                language=lang,
                mode=mode,
                error_code="OCR_PROCESS_ERROR",
                error_message=str(e)
            )
    
    def process_pdf(self, pdf_path: str, mode: OCRMode = OCRMode.FAST,
                   language: Optional[str] = None,
                   page_range: Optional[Tuple[int, int]] = None) -> List[OCRResult]:
        """
        Process a PDF file with OCR (per-page).
        
        Args:
            pdf_path: Path to PDF file
            mode: OCR processing mode
            language: Language code (default: from config)
            page_range: Optional tuple of (start_page, end_page) for partial processing
        
        Returns:
            List of OCRResult objects (one per page)
        """
        try:
            from pdf2image import convert_from_path
        except ImportError:
            logger.error("pdf2image not installed - cannot process PDFs")
            return [OCRResult(
                text="",
                error_code="OCR_PDF_UNAVAILABLE",
                error_message="pdf2image library not installed"
            )]
        
        try:
            # Convert PDF to images
            if page_range:
                first_page, last_page = page_range
                images = convert_from_path(pdf_path, first_page=first_page, last_page=last_page)
            else:
                images = convert_from_path(pdf_path)
            
            logger.info(f"Processing PDF with {len(images)} pages")
            
            # Process each page
            results = []
            for page_num, image in enumerate(images, start=1):
                logger.debug(f"Processing page {page_num}/{len(images)}")
                result = self.process_pil_image(image, mode, language)
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return [OCRResult(
                text="",
                error_code="OCR_PDF_ERROR",
                error_message=str(e)
            )]
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available Tesseract language packs.
        
        Returns:
            List of language codes
        """
        try:
            langs = pytesseract.get_languages()
            logger.debug(f"Available languages: {langs}")
            return langs
        except Exception as e:
            logger.error(f"Error getting languages: {e}")
            return ['eng']  # Fallback to English
    
    def validate_language(self, language: str) -> bool:
        """
        Check if a language pack is available.
        
        Args:
            language: Language code to check
        
        Returns:
            True if language is available
        """
        return language in self.get_available_languages()
    
    def _build_tesseract_config(self, mode: OCRMode) -> str:
        """
        Build Tesseract configuration string.
        
        Args:
            mode: OCR processing mode
        
        Returns:
            Configuration string for pytesseract
        """
        configs = []
        
        # PSM (Page Segmentation Mode)
        psm = self.psm
        if mode == OCRMode.FAST:
            psm = self.config.get('ocr_psm_fast', psm)
        elif mode == OCRMode.HIGH_ACCURACY:
            psm = self.config.get('ocr_psm_accurate', psm)
        
        configs.append(f'--psm {psm}')
        
        # OEM (OCR Engine Mode)
        configs.append(f'--oem {self.oem}')
        
        return ' '.join(configs)
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Apply preprocessing to improve OCR accuracy.
        
        Args:
            image: PIL Image to preprocess
        
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Increase DPI if needed (Tesseract works best at 300 DPI)
            target_dpi = 300
            if hasattr(image, 'info') and 'dpi' in image.info:
                current_dpi = image.info['dpi'][0]
                if current_dpi < target_dpi:
                    scale_factor = target_dpi / current_dpi
                    new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Apply contrast enhancement (optional, based on config)
            if self.config.get('ocr_enhance_contrast', True):
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)
            
            return image
        
        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}, using original image")
            return image
