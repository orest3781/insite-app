#!/usr/bin/env python3
"""
Test processing a single file to see the exact error.
"""
import sys
import logging
from pathlib import Path
from src.core.config import ConfigManager
from src.models.database import Database
from src.services.processing_orchestrator import ProcessingOrchestrator
from src.services.ocr_adapter import OCRAdapter
from src.services.llm_adapter import OllamaAdapter
from src.services.queue_manager import QueueManager

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_single_file():
    """Test processing a single image file."""
    try:
        logger.info("="*60)
        logger.info("TESTING SINGLE FILE PROCESSING")
        logger.info("="*60)
        
        # Initialize components
        portable_root = Path(__file__).parent
        config = ConfigManager(portable_root)
        db_path = config.get('database_path') or str(portable_root / 'data' / 'database.db')
        db = Database(db_path)
        
        # Initialize services
        ocr = OCRAdapter(config)
        llm = OllamaAdapter(config)
        queue = QueueManager(db)
        
        logger.info("\nServices initialized successfully")
        
        # Check Ollama connection
        logger.info("\nChecking Ollama connection...")
        is_connected = llm.verify_connection()
        logger.info(f"Ollama connected: {is_connected}")
        
        if not is_connected:
            logger.error("❌ Ollama is not running or not accessible!")
            logger.error("Please start Ollama and try again.")
            return False
        
        # Get a file from the queue
        logger.info("\nGetting file from queue...")
        stats = queue.get_statistics()
        logger.info(f"Queue statistics: {stats}")
        
        next_item = queue.get_next_item()
        if not next_item:
            logger.error("❌ No items in queue to process")
            return False
        
        file_path = next_item['file_path']
        logger.info(f"\nProcessing file: {file_path}")
        
        # Try to process it manually to see the error
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            logger.error(f"❌ File does not exist: {file_path}")
            return False
        
        # Check if it's an image
        file_ext = file_path_obj.suffix.lower()
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        is_image = file_ext in image_extensions
        
        logger.info(f"File extension: {file_ext}")
        logger.info(f"Is image: {is_image}")
        
        if is_image:
            logger.info("\nTesting vision analysis...")
            try:
                vision_results = llm.analyze_image_vision(file_path)
                logger.info(f"✅ Vision analysis succeeded!")
                logger.info(f"Tags: {vision_results['tags'].response_text}")
                logger.info(f"Description length: {len(vision_results['description'].response_text)} chars")
                return True
            except Exception as e:
                logger.exception(f"❌ Vision analysis failed: {e}")
                return False
        else:
            logger.info("\nTesting OCR...")
            try:
                from src.models.processing import OCRMode
                ocr_results = ocr.process_pdf(file_path, mode=OCRMode.FAST)
                logger.info(f"✅ OCR succeeded!")
                logger.info(f"Pages processed: {len(ocr_results)}")
                return True
            except Exception as e:
                logger.exception(f"❌ OCR failed: {e}")
                return False
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_single_file()
    sys.exit(0 if success else 1)
