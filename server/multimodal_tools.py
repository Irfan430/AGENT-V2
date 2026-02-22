"""
Multi-modal tools for image, audio, and video processing.
Integrates with vision models, Whisper API, and media processing libraries.
"""

import logging
import os
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

try:
    from PIL import Image
    import io
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

logger = logging.getLogger(__name__)

class MultiModalTools:
    """
    Handles multi-modal processing including images, audio, and video.
    """
    
    def __init__(self):
        """Initialize multi-modal tools."""
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        self.supported_audio_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
        self.supported_video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        logger.info("Multi-modal tools initialized")
    
    async def analyze_image(self, image_path: str, query: str = "") -> Dict[str, Any]:
        """
        Analyze an image using vision model.
        
        Args:
            image_path: Path to image file
            query: Optional query about the image
            
        Returns:
            Analysis results
        """
        try:
            # Validate file exists
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}"
                }
            
            # Validate file format
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in self.supported_image_formats:
                return {
                    "success": False,
                    "error": f"Unsupported image format: {file_ext}"
                }
            
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Prepare analysis prompt
            analysis_prompt = query or "Describe what you see in this image in detail."
            
            logger.info(f"Analyzing image: {image_path}")
            
            return {
                "success": True,
                "image_path": image_path,
                "file_size": os.path.getsize(image_path),
                "format": file_ext,
                "encoded": image_data[:100] + "...",  # Preview
                "analysis_prompt": analysis_prompt,
                "ready_for_vision_model": True
            }
        
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transcribe_audio(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper API.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            Transcription results
        """
        try:
            # Validate file exists
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "error": f"Audio file not found: {audio_path}"
                }
            
            # Validate file format
            file_ext = Path(audio_path).suffix.lower()
            if file_ext not in self.supported_audio_formats:
                return {
                    "success": False,
                    "error": f"Unsupported audio format: {file_ext}"
                }
            
            # Check file size (16MB limit)
            file_size = os.path.getsize(audio_path)
            if file_size > 16 * 1024 * 1024:
                return {
                    "success": False,
                    "error": f"Audio file too large: {file_size / 1024 / 1024:.1f}MB (max 16MB)"
                }
            
            logger.info(f"Transcribing audio: {audio_path}")
            
            return {
                "success": True,
                "audio_path": audio_path,
                "file_size": file_size,
                "format": file_ext,
                "language": language,
                "ready_for_transcription": True,
                "note": "Audio ready for Whisper API transcription"
            }
        
        except Exception as e:
            logger.error(f"Error preparing audio transcription: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_video_frames(self, video_path: str, 
                                  frame_interval: int = 1) -> Dict[str, Any]:
        """
        Extract frames from video file.
        
        Args:
            video_path: Path to video file
            frame_interval: Extract every nth frame
            
        Returns:
            Frame extraction results
        """
        try:
            # Validate file exists
            if not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": f"Video file not found: {video_path}"
                }
            
            # Validate file format
            file_ext = Path(video_path).suffix.lower()
            if file_ext not in self.supported_video_formats:
                return {
                    "success": False,
                    "error": f"Unsupported video format: {file_ext}"
                }
            
            logger.info(f"Preparing frame extraction: {video_path}")
            
            return {
                "success": True,
                "video_path": video_path,
                "file_size": os.path.getsize(video_path),
                "format": file_ext,
                "frame_interval": frame_interval,
                "ready_for_processing": True,
                "note": "Video ready for frame extraction"
            }
        
        except Exception as e:
            logger.error(f"Error preparing video processing: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Extract metadata from image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image metadata
        """
        try:
            if not PILLOW_AVAILABLE:
                return {
                    "success": False,
                    "error": "Pillow library not available"
                }
            
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}"
                }
            
            # Open image and extract metadata
            with Image.open(image_path) as img:
                metadata = {
                    "success": True,
                    "path": image_path,
                    "format": img.format,
                    "size": {
                        "width": img.width,
                        "height": img.height,
                        "pixels": img.width * img.height
                    },
                    "mode": img.mode,
                    "file_size": os.path.getsize(image_path),
                    "exif_data": {}
                }
                
                # Try to extract EXIF data
                try:
                    exif_data = img._getexif()
                    if exif_data:
                        metadata["exif_data"] = {str(k): str(v) for k, v in exif_data.items()}
                except:
                    pass
                
                return metadata
        
        except Exception as e:
            logger.error(f"Error extracting image metadata: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def convert_image_format(self, image_path: str, 
                                  output_format: str = "png") -> Dict[str, Any]:
        """
        Convert image to different format.
        
        Args:
            image_path: Path to source image
            output_format: Target format (png, jpg, webp, etc.)
            
        Returns:
            Conversion results
        """
        try:
            if not PILLOW_AVAILABLE:
                return {
                    "success": False,
                    "error": "Pillow library not available"
                }
            
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}"
                }
            
            # Open and convert image
            with Image.open(image_path) as img:
                # Convert RGBA to RGB if needed for JPEG
                if output_format.lower() == 'jpg' and img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Generate output path
                input_path = Path(image_path)
                output_path = input_path.with_suffix(f'.{output_format}')
                
                # Save converted image
                img.save(output_path, format=output_format.upper())
                
                logger.info(f"Converted image: {image_path} -> {output_path}")
                
                return {
                    "success": True,
                    "original_path": image_path,
                    "output_path": str(output_path),
                    "original_format": img.format,
                    "output_format": output_format,
                    "file_size": os.path.getsize(output_path)
                }
        
        except Exception as e:
            logger.error(f"Error converting image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def resize_image(self, image_path: str, 
                          width: int, height: int) -> Dict[str, Any]:
        """
        Resize image to specified dimensions.
        
        Args:
            image_path: Path to image
            width: Target width
            height: Target height
            
        Returns:
            Resize results
        """
        try:
            if not PILLOW_AVAILABLE:
                return {
                    "success": False,
                    "error": "Pillow library not available"
                }
            
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}"
                }
            
            # Open and resize image
            with Image.open(image_path) as img:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Generate output path
                input_path = Path(image_path)
                output_path = input_path.with_stem(f"{input_path.stem}_resized")
                
                # Save resized image
                resized.save(output_path)
                
                logger.info(f"Resized image: {image_path} -> {width}x{height}")
                
                return {
                    "success": True,
                    "original_path": image_path,
                    "output_path": str(output_path),
                    "original_size": {"width": img.width, "height": img.height},
                    "new_size": {"width": width, "height": height},
                    "file_size": os.path.getsize(output_path)
                }
        
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported media formats."""
        return {
            "images": self.supported_image_formats,
            "audio": self.supported_audio_formats,
            "video": self.supported_video_formats
        }

# Global multi-modal tools instance
_multimodal_tools: Optional[MultiModalTools] = None

def get_multimodal_tools() -> MultiModalTools:
    """Get or create the global multi-modal tools instance."""
    global _multimodal_tools
    if _multimodal_tools is None:
        _multimodal_tools = MultiModalTools()
    return _multimodal_tools
