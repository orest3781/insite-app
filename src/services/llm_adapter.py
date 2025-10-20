"""
LLM engine adapter for Ollama integration.

Provides AI capabilities for classification and description generation.
"""

import logging
import json
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

import requests

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of prompts used by the system."""
    CLASSIFICATION = "classification"
    DESCRIPTION = "description"
    REVIEW = "review"


@dataclass
class LLMResult:
    """Result from LLM processing."""
    response_text: str
    model_name: str
    prompt_type: PromptType
    tokens_used: int = 0
    confidence: float = 0.0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class OllamaAdapter:
    """
    Adapter for Ollama local LLM service.
    
    Features:
    - Model selection and validation
    - Prompt template system
    - Classification and description generation
    - Response parsing and validation
    """
    
    def __init__(self, config_manager):
        """
        Initialize Ollama adapter.
        
        Args:
            config_manager: ConfigManager instance for LLM settings
        """
        self.config = config_manager
        
        # Get Ollama configuration
        self.host = self.config.get('ollama_host', 'http://localhost:11434')
        self.model_name = self.config.get('ollama_default_model', 'llama3.2')
        self.temperature = self.config.get('ollama_temperature', 0.4)
        self.max_tokens = self.config.get('ollama_max_tokens', 270)
        
        # Get model-specific defaults
        self.default_model_vision = self.config.get('ollama_default_model_vision', None)
        self.default_model_ocr = self.config.get('ollama_default_model_ocr', None)
        self.default_model_text = self.config.get('ollama_default_model_text', None)
        
        logger.info(f"Ollama Adapter initialized (host={self.host}, model={self.model_name})")
        logger.info(f"Model defaults - Vision: {self.default_model_vision}, OCR: {self.default_model_ocr}, Text: {self.default_model_text}")
        
        # Verify connectivity and log available models
        if not self.verify_connection():
            logger.warning("Ollama service not reachable - LLM features will be unavailable")
        else:
            # Log available vision models
            self._log_available_vision_models()
    
    def _log_available_vision_models(self):
        """Log which vision models are available."""
        try:
            available = self.list_models()
            vision_models = [
                'qwen2.5vl:7b', 'qwen2.5vl:72b', 'llava:7b', 'llava:34b',
                'qwen2-vl:7b', 'qwen2-vl:2b', 'llama3.2-vision', 'minicpm-v'
            ]
            found = [m for m in vision_models if m in available]
            
            if found:
                logger.info(f"Available vision models: {', '.join(found)}")
            else:
                logger.warning("No vision models found - image analysis will use fallback")
        except Exception as e:
            logger.debug(f"Could not check vision models: {e}")
    
    def verify_connection(self) -> bool:
        """
        Verify Ollama service is reachable.
        
        Returns:
            True if service is available
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.debug("Ollama service is reachable")
                return True
            else:
                logger.warning(f"Ollama returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cannot reach Ollama service: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """
        Get list of available models from Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                logger.debug(f"Available models: {models}")
                return models
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def validate_model(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a model is available.
        
        Args:
            model_name: Model name to check (default: configured model)
        
        Returns:
            True if model is available
        """
        model = model_name or self.model_name
        available_models = self.list_models()
        return model in available_models
    
    def pull_model(self, model_name: Optional[str] = None, timeout: int = 600) -> bool:
        """
        Pull (download) a model from Ollama.
        
        Args:
            model_name: Model name to pull (default: configured model)
            timeout: Timeout in seconds (default: 600 = 10 minutes)
        
        Returns:
            True if model was pulled successfully
        """
        model = model_name or self.model_name
        
        try:
            logger.info(f"Pulling model '{model}' from Ollama (this may take several minutes)...")
            
            # Send pull request (streaming)
            response = requests.post(
                f"{self.host}/api/pull",
                json={"name": model},
                stream=True,
                timeout=timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to pull model: {response.status_code}")
                return False
            
            # Process streaming response
            last_status = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        status = data.get('status', '')
                        
                        # Log progress updates
                        if status != last_status:
                            logger.info(f"Pull status: {status}")
                            last_status = status
                        
                        # Check for completion
                        if status == "success" or data.get('status') == "success":
                            logger.info(f"Successfully pulled model '{model}'")
                            return True
                            
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"Model '{model}' pull completed")
            return True
            
        except requests.Timeout:
            logger.error(f"Model pull timed out after {timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False
    
    def generate_classification(self, ocr_text: str, 
                              custom_prompt: Optional[str] = None) -> LLMResult:
        """
        Generate classification tags from OCR text.
        
        Args:
            ocr_text: Extracted text from OCR
            custom_prompt: Optional custom prompt template
        
        Returns:
            LLMResult with classification tags
        """
        # Build prompt
        if custom_prompt:
            prompt = custom_prompt.format(text=ocr_text)
        else:
            prompt = self._build_classification_prompt(ocr_text)
        
        # Use OCR-specific model if configured, otherwise use text model default, otherwise use general default
        model_override = self.default_model_ocr or self.default_model_text
        
        # Generate response
        return self._generate(prompt, PromptType.CLASSIFICATION, model_override=model_override)
    
    def generate_description(self, ocr_text: str, tags: List[str],
                           custom_prompt: Optional[str] = None) -> LLMResult:
        """
        Generate two-sentence description from OCR text and tags.
        
        Args:
            ocr_text: Extracted text from OCR
            tags: Classification tags
            custom_prompt: Optional custom prompt template
        
        Returns:
            LLMResult with description
        """
        # Build prompt
        if custom_prompt:
            prompt = custom_prompt.format(text=ocr_text, tags=', '.join(tags))
        else:
            prompt = self._build_description_prompt(ocr_text, tags)
        
        # Use text-specific model default if configured
        model_override = self.default_model_text
        
        # Generate response
        return self._generate(prompt, PromptType.DESCRIPTION, model_override=model_override)
        return self._generate(prompt, PromptType.DESCRIPTION)
    
    def analyze_image_vision(self, image_path: str) -> Dict[str, LLMResult]:
        """
        Analyze an image using vision model to generate tags and description.
        
        Uses the best available vision model to analyze image content:
        - qwen2.5vl:7b (7B) - Best balance of speed and quality (YOU HAVE THIS!)
        - qwen2.5vl:72b (72B) - Ultimate quality, slower (YOU HAVE THIS!)
        - llava:7b (7B) - Fast and reliable (YOU HAVE THIS!)
        - llava:34b (34B) - High quality LLaVA (YOU HAVE THIS!)
        - Other models as fallbacks
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dictionary with 'tags' and 'description' LLMResult objects
        """
        import base64
        from pathlib import Path
        
        # Read and encode image
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to read image {image_path}: {e}")
            return self._get_fallback_vision_results(Path(image_path).name)
        
        # Try best vision models in order of preference
        # Start with user-configured default if available
        vision_models = []
        if self.default_model_vision:
            vision_models.append(self.default_model_vision)
        
        # Then add standard vision models in priority order
        vision_models.extend([
            'qwen2.5vl:7b',     # Best: Qwen 2.5 VL 7B - excellent vision
            'llava:7b',         # Good: Fast and reliable
            'llava:34b',        # Premium: Large LLaVA model
            'qwen2.5vl:72b',    # Premium: Massive 72B model (slowest, try last)
            'qwen2-vl:7b',      # Alternative: Qwen 2.0 VL
            'qwen2-vl:2b',      # Alternative: Smaller Qwen 2.0
            'llama3.2-vision',  # Alternative: Meta's vision model
            'minicpm-v',        # Fallback: Efficient vision model
            'llava'             # Fallback: Default LLaVA
        ])
        
        for model in vision_models:
            try:
                if self._try_vision_model(model, image_data, image_path):
                    logger.info(f"Trying vision model: {model}")
                    result = self._analyze_with_vision_model(model, image_data, image_path)
                    logger.info(f"Successfully analyzed with {model}")
                    return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}, trying next model...")
                continue
        
        # Fallback if no vision models work
        logger.warning("All vision models failed or unavailable, using fallback")
        return self._get_fallback_vision_results(Path(image_path).name)
    
    def _try_vision_model(self, model_name: str, image_data: str, image_path: str) -> bool:
        """Check if a vision model is available or can be pulled."""
        try:
            # Check if model exists
            if self.validate_model(model_name):
                logger.info(f"Vision model '{model_name}' is available")
                return True
            
            # Try to pull if auto-pull enabled
            auto_pull = self.config.get('ollama_auto_pull_models', True)
            if auto_pull:
                logger.info(f"Vision model '{model_name}' not found, attempting to pull...")
                if self.pull_model(model_name):
                    logger.info(f"Successfully pulled vision model '{model_name}'")
                    return True
                else:
                    logger.warning(f"Failed to pull vision model '{model_name}'")
                    return False
            else:
                logger.debug(f"Vision model '{model_name}' not available, auto-pull disabled")
                return False
        except Exception as e:
            logger.error(f"Error checking vision model '{model_name}': {e}")
            return False
    
    def _analyze_with_vision_model(self, model_name: str, image_data: str, 
                                   image_path: str) -> Dict[str, LLMResult]:
        """Perform vision analysis with specified model."""
        from pathlib import Path
        import requests.exceptions
        
        try:
            # Generate tags
            tags_result = self._generate_vision_tags(model_name, image_data, image_path)
            
            # Check if tags generation timed out (would be using fallback)
            if tags_result.confidence < 0.5:  # Fallback has low confidence
                logger.warning(f"Vision model {model_name} had issues, using fallback")
                raise TimeoutError(f"Model {model_name} timed out or failed")
            
            # Generate description
            description_result = self._generate_vision_description(model_name, image_data, image_path)
            
            return {
                'tags': tags_result,
                'description': description_result
            }
        except (requests.exceptions.Timeout, TimeoutError) as e:
            logger.warning(f"Model {model_name} timed out: {e}")
            raise  # Re-raise to try next model
        except Exception as e:
            logger.error(f"Error with model {model_name}: {e}")
            raise  # Re-raise to try next model
    
    def _generate_vision_tags(self, model_name: str, image_data: str, 
                             image_path: str) -> LLMResult:
        """Generate classification tags from image using vision model."""
        prompt = """Analyze this image and provide EXACTLY 6 relevant classification tags.

Tags should describe:
1. Content type (e.g., wallpaper, screenshot, photograph, diagram, artwork)
2. Subject matter (e.g., landscape, portrait, abstract, architecture, nature)
3. Color palette (e.g., vibrant, monochrome, warm-tones, cool-tones, high-contrast)
4. Composition (e.g., wide-angle, close-up, panoramic, symmetrical)
5. Style/aesthetic (e.g., minimalist, detailed, modern, vintage, professional)
6. Purpose/use (e.g., desktop-background, presentation, documentation, artistic)

Requirements:
- Use snake_case format (lowercase with underscores)
- Be specific and descriptive
- No generic terms like "image" or "visual"
- One tag per line

Output ONLY the 6 tags, nothing else:"""
        
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent tagging
                    "num_predict": 150
                }
            }
            
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=300  # 5 minutes for vision models (72B can be slow)
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').strip()
                eval_count = data.get('eval_count', 0)
                
                # Log raw vision model response for debugging
                logger.info(f"RAW VISION TAGS RESPONSE from {model_name}:")
                logger.info(f"{response_text}")
                
                # Parse tags from response
                tags = [tag.strip() for tag in response_text.split('\n') if tag.strip()]
                logger.info(f"PARSED {len(tags)} tags from newline split: {tags}")
                
                # Ensure snake_case
                tags = [tag.replace('-', '_') for tag in tags]
                
                # Enforce 6-tag limit strictly
                tags = tags[:6]
                logger.info(f"KEEPING first 6 tags: {tags}")
                
                # Join with commas for consistent format
                tags_str = ', '.join(tags)
                logger.info(f"Final tags string: {tags_str}")
                
                return LLMResult(
                    response_text=tags_str,
                    model_name=model_name,
                    prompt_type=PromptType.CLASSIFICATION,
                    tokens_used=eval_count,
                    confidence=0.85  # Vision models are generally reliable
                )
            else:
                logger.error(f"Vision tag generation failed: {response.status_code}")
                return self._get_fallback_tags()
                
        except Exception as e:
            logger.error(f"Error generating vision tags: {e}")
            return self._get_fallback_tags()
    
    def _generate_vision_description(self, model_name: str, image_data: str,
                                    image_path: str) -> LLMResult:
        """Generate description from image using vision model."""
        from pathlib import Path
        
        file_name = Path(image_path).name
        
        prompt = f"""Analyze this image file ({file_name}) and provide a detailed description.

Write EXACTLY TWO SENTENCES that describe:
1. What the image shows (content, subjects, scene)
2. Visual characteristics (colors, composition, style, quality)

Requirements:
- Be specific and descriptive
- Mention resolution/aspect ratio if apparent (e.g., ultra-wide, standard, portrait)
- Describe dominant colors and visual style
- No speculation about file origins or metadata
- Professional tone

Output ONLY the two-sentence description:"""
        
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.4,
                    "num_predict": 200
                }
            }
            
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=300  # 5 minutes for vision models
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').strip()
                eval_count = data.get('eval_count', 0)
                
                logger.info(f"Vision description generated ({eval_count} tokens)")
                
                return LLMResult(
                    response_text=response_text,
                    model_name=model_name,
                    prompt_type=PromptType.DESCRIPTION,
                    tokens_used=eval_count,
                    confidence=0.80
                )
            else:
                logger.error(f"Vision description generation failed: {response.status_code}")
                return self._get_fallback_description(file_name)
                
        except Exception as e:
            logger.error(f"Error generating vision description: {e}")
            return self._get_fallback_description(file_name)
    
    def _get_fallback_vision_results(self, file_name: str) -> Dict[str, LLMResult]:
        """Get fallback results when vision analysis fails."""
        return {
            'tags': self._get_fallback_tags(),
            'description': self._get_fallback_description(file_name)
        }
    
    def _get_fallback_tags(self) -> LLMResult:
        """Get fallback tags when vision analysis fails."""
        return LLMResult(
            response_text='visual-content, image-file, unclassified',
            model_name='fallback',
            prompt_type=PromptType.CLASSIFICATION,
            tokens_used=0,
            confidence=0.1
        )
    
    def _get_fallback_description(self, file_name: str) -> LLMResult:
        """Get fallback description when vision analysis fails."""
        return LLMResult(
            response_text=f"Image file: {file_name}. Vision analysis unavailable - no vision model could be loaded.",
            model_name='fallback',
            prompt_type=PromptType.DESCRIPTION,
            tokens_used=0,
            confidence=0.1
        )
    
    def _generate(self, prompt: str, prompt_type: PromptType, model_override: Optional[str] = None) -> LLMResult:
        """
        Generate LLM response from prompt.
        
        Args:
            prompt: Full prompt text
            prompt_type: Type of prompt being used
            model_override: Optional model override (for task-specific models)
        
        Returns:
            LLMResult with response
        """
        try:
            # Use override model if provided, otherwise use default
            model_to_use = model_override or self.model_name
            
            # Prepare request
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            logger.debug(f"Sending request to Ollama (model={model_to_use})")
            
            # Make request
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=60  # 1 minute timeout for generation
            )
            
            if response.status_code != 200:
                error_details = ""
                try:
                    error_data = response.json()
                    error_details = error_data.get('error', '')
                except:
                    error_details = response.text[:200] if response.text else ""
                
                logger.error(f"Ollama request failed: {response.status_code}")
                
                # Handle 404 - Model not found
                if response.status_code == 404:
                    # Check if auto-pull is enabled
                    auto_pull = self.config.get('ollama_auto_pull_models', True)
                    
                    if auto_pull:
                        logger.info(f"Model '{self.model_name}' not found. Attempting auto-pull...")
                        
                        # Try to pull the model
                        if self.pull_model(self.model_name):
                            logger.info(f"Model '{self.model_name}' pulled successfully. Retrying request...")
                            
                            # Retry the request with the newly pulled model
                            retry_response = requests.post(
                                f"{self.host}/api/generate",
                                json=payload,
                                timeout=60
                            )
                            
                            if retry_response.status_code == 200:
                                # Parse successful retry response
                                data = retry_response.json()
                                response_text = data.get('response', '').strip()
                                eval_count = data.get('eval_count', 0)
                                
                                logger.info(f"Retry successful after auto-pull")
                                
                                return LLMResult(
                                    response_text=response_text,
                                    model_name=self.model_name,
                                    prompt_type=prompt_type,
                                    tokens_used=eval_count,
                                    metadata={
                                        'duration_ns': data.get('total_duration', 0),
                                        'prompt_eval_count': data.get('prompt_eval_count', 0),
                                        'eval_count': eval_count,
                                        'auto_pulled': True
                                    }
                                )
                        else:
                            logger.error(f"Failed to auto-pull model '{self.model_name}'")
                    
                    error_message = f"Model '{self.model_name}' not found. Please ensure Ollama is running and the model is downloaded: ollama pull {self.model_name}"
                else:
                    error_message = f"Status {response.status_code}: {error_details}"
                
                return LLMResult(
                    response_text="",
                    model_name=self.model_name,
                    prompt_type=prompt_type,
                    error_code="LLM_REQUEST_FAILED",
                    error_message=error_message
                )
            
            # Parse response
            data = response.json()
            response_text = data.get('response', '').strip()
            
            # Extract tokens used
            total_duration = data.get('total_duration', 0)
            eval_count = data.get('eval_count', 0)
            
            logger.debug(f"LLM response received: {len(response_text)} chars, {eval_count} tokens")
            
            return LLMResult(
                response_text=response_text,
                model_name=self.model_name,
                prompt_type=prompt_type,
                tokens_used=eval_count,
                metadata={
                    'duration_ns': total_duration,
                    'prompt_eval_count': data.get('prompt_eval_count', 0),
                    'eval_count': eval_count
                }
            )
        
        except requests.Timeout:
            logger.error("Ollama request timed out")
            return LLMResult(
                response_text="",
                model_name=self.model_name,
                prompt_type=prompt_type,
                error_code="LLM_TIMEOUT",
                error_message="Request timed out after 60 seconds"
            )
        
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return LLMResult(
                response_text="",
                model_name=self.model_name,
                prompt_type=prompt_type,
                error_code="LLM_ERROR",
                error_message=str(e)
            )
    
    def _build_classification_prompt(self, ocr_text: str) -> str:
        """
        Build classification prompt from OCR text.
        
        Args:
            ocr_text: Extracted text
        
        Returns:
            Formatted prompt
        """
        # Limit text length to avoid token overflow
        max_text_length = 2000
        if len(ocr_text) > max_text_length:
            ocr_text = ocr_text[:max_text_length] + "..."
        
        prompt = f"""Analyze the following document text and classify it with appropriate tags.

Document Text:
{ocr_text}

Provide EXACTLY 6 tags in the following categories:
1. type:* (e.g., type:invoice, type:receipt, type:contract, type:letter, type:form, type:report)
2. domain:* (e.g., domain:finance, domain:legal, domain:hr, domain:sales, domain:support)
3. status:* (e.g., status:draft, status:signed, status:paid, status:unpaid, status:rejected)
4. Three additional relevant tags

Tags must be snake_case, singular, and specific. Use colons for namespacing (category:value).

Output ONLY the tags, one per line, no explanations:"""
        
        return prompt
    
    def _build_description_prompt(self, ocr_text: str, tags: List[str]) -> str:
        """
        Build description prompt from OCR text and tags.
        
        Args:
            ocr_text: Extracted text
            tags: Classification tags
        
        Returns:
            Formatted prompt
        """
        # Limit text length
        max_text_length = 2000
        if len(ocr_text) > max_text_length:
            ocr_text = ocr_text[:max_text_length] + "..."
        
        tags_str = ', '.join(tags)
        
        prompt = f"""Based on the following document text and tags, write EXACTLY TWO SENTENCES that describe what this document is.

Document Text:
{ocr_text}

Tags: {tags_str}

Requirements:
- Write EXACTLY two sentences
- Be concise and factual
- No speculation or assumptions
- Use ISO date format (YYYY-MM-DD) for any dates
- Mask sensitive information (account numbers, SSNs)

Output ONLY the two-sentence description:"""
        
        return prompt
    
    def test_vision_capability(self) -> Dict[str, Any]:
        """
        Test vision model availability and capability.
        
        Returns:
            Dictionary with test results and available models
        """
        results = {
            'ollama_connected': False,
            'available_models': [],
            'vision_models': [],
            'recommended_model': None,
            'test_status': 'failed'
        }
        
        try:
            # Test Ollama connection
            if not self.verify_connection():
                results['error'] = 'Ollama service not reachable'
                return results
            
            results['ollama_connected'] = True
            
            # Get all available models
            all_models = self.list_models()
            results['available_models'] = all_models
            
            # Check for vision models
            vision_model_names = [
                'qwen2.5vl:7b', 'qwen2.5vl:72b', 'llava:7b', 'llava:34b',
                'qwen2-vl:7b', 'qwen2-vl:2b', 'llama3.2-vision', 'minicpm-v', 'llava'
            ]
            
            found_vision = [m for m in vision_model_names if m in all_models]
            results['vision_models'] = found_vision
            
            if found_vision:
                results['recommended_model'] = found_vision[0]
                results['test_status'] = 'success'
                logger.info(f"Vision test passed! Found models: {found_vision}")
            else:
                results['test_status'] = 'no_vision_models'
                results['error'] = 'No vision models installed'
                logger.warning("No vision models found")
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Vision capability test failed: {e}")
            return results
