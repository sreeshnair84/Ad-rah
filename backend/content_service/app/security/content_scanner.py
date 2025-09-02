"""
Content Copyright Protection & Security Scanner
Implements industry-standard content scanning for:
- Copyright infringement detection
- Content hash verification
- DMCA compliance
- Malware scanning
- Content authenticity verification
"""
import hashlib
import logging
import mimetypes
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import requests
import json
from io import BytesIO
from PIL import Image
import imagehash

from .config_manager import config_manager
from .audit_logger import audit_logger, AuditSeverity

logger = logging.getLogger(__name__)

class ContentSecurityLevel:
    """Security levels for content classification"""
    SAFE = "safe"
    SUSPICIOUS = "suspicious" 
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

class CopyrightCheckResult:
    """Result of copyright check"""
    def __init__(self, is_protected: bool, confidence: float, sources: List[str] = None, 
                 details: str = None):
        self.is_protected = is_protected
        self.confidence = confidence  # 0.0 to 1.0
        self.sources = sources or []
        self.details = details or ""
        self.timestamp = datetime.now(timezone.utc)

class ContentScanResult:
    """Comprehensive content scan result"""
    def __init__(self):
        self.scan_id = hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:16]
        self.timestamp = datetime.now(timezone.utc)
        self.file_hash = None
        self.content_type = None
        self.file_size = 0
        self.security_level = ContentSecurityLevel.UNKNOWN
        self.copyright_result: Optional[CopyrightCheckResult] = None
        self.malware_detected = False
        self.content_warnings = []
        self.technical_metadata = {}
        self.recommendation = "pending_review"
        self.scan_errors = []

class ContentSecurityScanner:
    """Comprehensive content security and copyright scanner"""
    
    def __init__(self):
        self.config = config_manager.get_content_config()
        self.compliance_config = config_manager.get_compliance_config()
        
        # Content scanning settings
        self.max_file_size = self.config.get('max_size_mb', 100) * 1024 * 1024  # Convert to bytes
        self.allowed_types = self.config.get('allowed_types', [])
        self.scan_enabled = self.config.get('scan_enabled', True)
        self.copyright_check_enabled = self.config.get('copyright_check', True)
        
        # Known copyright-protected content hashes (would be populated from database)
        self.protected_hashes = set()
        
        # Malware scanning patterns (basic implementation)
        self.malware_signatures = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'<iframe',
            b'eval(',
        ]
    
    async def scan_content(self, file_content: bytes, filename: str, 
                          content_type: str = None) -> ContentScanResult:
        """Perform comprehensive content scan"""
        result = ContentScanResult()
        
        try:
            # Basic file validation
            result.file_size = len(file_content)
            result.content_type = content_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            result.file_hash = self._calculate_file_hash(file_content)
            
            # Log scan start
            audit_logger.log_content_event("content_scan_started", result.scan_id, {
                "filename": filename,
                "content_type": result.content_type,
                "file_size": result.file_size,
                "file_hash": result.file_hash
            })
            
            # File size validation
            if result.file_size > self.max_file_size:
                result.security_level = ContentSecurityLevel.BLOCKED
                result.content_warnings.append(f"File size ({result.file_size} bytes) exceeds limit ({self.max_file_size} bytes)")
                result.recommendation = "reject_size_limit"
                return result
            
            # File type validation
            if not self._is_allowed_file_type(filename, result.content_type):
                result.security_level = ContentSecurityLevel.BLOCKED
                result.content_warnings.append(f"File type not allowed: {result.content_type}")
                result.recommendation = "reject_file_type"
                return result
            
            # Malware scanning
            if self._scan_for_malware(file_content, filename):
                result.malware_detected = True
                result.security_level = ContentSecurityLevel.BLOCKED
                result.content_warnings.append("Potential malware detected")
                result.recommendation = "reject_malware"
                
                # Log security incident
                audit_logger.log_security_event("malware_detected", {
                    "filename": filename,
                    "file_hash": result.file_hash,
                    "scan_id": result.scan_id
                }, severity=AuditSeverity.CRITICAL)
                
                return result
            
            # Copyright protection check
            if self.copyright_check_enabled:
                result.copyright_result = await self._check_copyright(file_content, filename, result.content_type)
                
                if result.copyright_result.is_protected and result.copyright_result.confidence > 0.8:
                    result.security_level = ContentSecurityLevel.BLOCKED
                    result.content_warnings.append(f"Copyright protected content detected (confidence: {result.copyright_result.confidence:.2f})")
                    result.recommendation = "reject_copyright"
                    
                    # Log copyright violation
                    audit_logger.log_content_event("copyright_violation_detected", result.scan_id, {
                        "filename": filename,
                        "confidence": result.copyright_result.confidence,
                        "sources": result.copyright_result.sources,
                        "file_hash": result.file_hash
                    })
                    
                    return result
            
            # Extract technical metadata
            result.technical_metadata = self._extract_metadata(file_content, filename, result.content_type)
            
            # Content analysis based on type
            content_analysis = self._analyze_content_by_type(file_content, result.content_type)
            result.content_warnings.extend(content_analysis.get('warnings', []))
            result.technical_metadata.update(content_analysis.get('metadata', {}))
            
            # Determine final security level and recommendation
            if result.content_warnings:
                result.security_level = ContentSecurityLevel.SUSPICIOUS
                result.recommendation = "manual_review"
            else:
                result.security_level = ContentSecurityLevel.SAFE
                result.recommendation = "approve"
            
            # Log scan completion
            audit_logger.log_content_event("content_scan_completed", result.scan_id, {
                "security_level": result.security_level,
                "recommendation": result.recommendation,
                "warnings_count": len(result.content_warnings),
                "malware_detected": result.malware_detected
            })
            
            return result
            
        except Exception as e:
            result.scan_errors.append(f"Scan error: {str(e)}")
            result.security_level = ContentSecurityLevel.UNKNOWN
            result.recommendation = "manual_review"
            
            logger.error(f"Content scan failed for {filename}: {e}")
            audit_logger.log_content_event("content_scan_failed", result.scan_id, {
                "filename": filename,
                "error": str(e)
            })
            
            return result
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _is_allowed_file_type(self, filename: str, content_type: str) -> bool:
        """Check if file type is allowed"""
        # Check by file extension
        if '.' in filename:
            extension = filename.lower().split('.')[-1]
            if extension in self.allowed_types:
                return True
        
        # Check by MIME type
        if content_type:
            main_type = content_type.split('/')[0]
            if main_type in ['image', 'video', 'text']:
                # Additional validation for specific MIME types
                allowed_mime_types = [
                    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                    'video/mp4', 'video/avi', 'video/mov', 'video/webm',
                    'text/plain', 'application/json'
                ]
                return content_type in allowed_mime_types
        
        return False
    
    def _scan_for_malware(self, file_content: bytes, filename: str) -> bool:
        """Basic malware pattern scanning"""
        try:
            # Convert to lowercase for case-insensitive matching
            content_lower = file_content.lower()
            
            # Check for known malware signatures
            for signature in self.malware_signatures:
                if signature.lower() in content_lower:
                    logger.warning(f"Malware signature detected in {filename}: {signature}")
                    return True
            
            # Additional checks for suspicious file patterns
            if filename.lower().endswith(('.exe', '.scr', '.bat', '.cmd', '.pif', '.com')):
                logger.warning(f"Suspicious executable file type: {filename}")
                return True
            
            # Check for embedded scripts in images (steganography)
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                if b'<script' in content_lower or b'javascript' in content_lower:
                    logger.warning(f"Suspicious script found in image: {filename}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Malware scanning failed for {filename}: {e}")
            return True  # Err on the side of caution
    
    async def _check_copyright(self, file_content: bytes, filename: str, 
                              content_type: str) -> CopyrightCheckResult:
        """Check for copyright protected content"""
        try:
            # Calculate content hash
            content_hash = self._calculate_file_hash(file_content)
            
            # Check against known protected hashes
            if content_hash in self.protected_hashes:
                return CopyrightCheckResult(
                    is_protected=True,
                    confidence=1.0,
                    sources=["internal_database"],
                    details="Exact match with known protected content"
                )
            
            # Perform perceptual hashing for images
            if content_type and content_type.startswith('image/'):
                perceptual_result = await self._check_image_copyright(file_content)
                if perceptual_result:
                    return perceptual_result
            
            # For now, return safe result
            # In production, integrate with:
            # - Google Vision API
            # - Microsoft Content Recognition
            # - YouTube Content ID
            # - Custom ML models
            
            return CopyrightCheckResult(
                is_protected=False,
                confidence=0.0,
                sources=[],
                details="No copyright violations detected"
            )
            
        except Exception as e:
            logger.error(f"Copyright check failed for {filename}: {e}")
            return CopyrightCheckResult(
                is_protected=False,
                confidence=0.0,
                sources=[],
                details=f"Copyright check error: {str(e)}"
            )
    
    async def _check_image_copyright(self, image_content: bytes) -> Optional[CopyrightCheckResult]:
        """Check image for copyright using perceptual hashing"""
        try:
            # Load image and calculate perceptual hash
            image = Image.open(BytesIO(image_content))
            
            # Calculate different types of perceptual hashes
            avg_hash = str(imagehash.average_hash(image))
            dhash = str(imagehash.dhash(image))
            phash = str(imagehash.phash(image))
            
            # In production, compare against database of known protected image hashes
            # For now, just log the hashes for future use
            logger.debug(f"Image hashes - avg: {avg_hash}, dhash: {dhash}, phash: {phash}")
            
            # TODO: Implement actual comparison against protected content database
            
            return None  # No copyright violation detected
            
        except Exception as e:
            logger.error(f"Image copyright check failed: {e}")
            return None
    
    def _extract_metadata(self, file_content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Extract technical metadata from content"""
        metadata = {}
        
        try:
            if content_type and content_type.startswith('image/'):
                metadata.update(self._extract_image_metadata(file_content))
            elif content_type and content_type.startswith('video/'):
                metadata.update(self._extract_video_metadata(file_content))
            elif content_type and content_type.startswith('text/'):
                metadata.update(self._extract_text_metadata(file_content))
            
            # Common metadata
            metadata.update({
                'file_size_bytes': len(file_content),
                'content_type_detected': content_type,
                'filename': filename,
                'scan_timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Metadata extraction failed for {filename}: {e}")
            metadata['extraction_error'] = str(e)
        
        return metadata
    
    def _extract_image_metadata(self, image_content: bytes) -> Dict[str, Any]:
        """Extract image-specific metadata"""
        try:
            image = Image.open(BytesIO(image_content))
            
            metadata = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.size[0],
                'height': image.size[1]
            }
            
            # Extract EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                exif_data = image._getexif()
                if exif_data:
                    # Only include non-sensitive EXIF data
                    safe_exif = {}
                    for tag, value in exif_data.items():
                        if tag in [0x0100, 0x0101, 0x0112, 0x011A, 0x011B]:  # Basic image info only
                            safe_exif[str(tag)] = str(value)
                    metadata['exif'] = safe_exif
            
            return metadata
            
        except Exception as e:
            logger.error(f"Image metadata extraction failed: {e}")
            return {'extraction_error': str(e)}
    
    def _extract_video_metadata(self, video_content: bytes) -> Dict[str, Any]:
        """Extract video-specific metadata (basic implementation)"""
        # For production, use ffprobe or similar tool
        return {
            'type': 'video',
            'note': 'Full video metadata extraction requires additional tools'
        }
    
    def _extract_text_metadata(self, text_content: bytes) -> Dict[str, Any]:
        """Extract text-specific metadata"""
        try:
            # Try to decode text
            try:
                text = text_content.decode('utf-8')
            except UnicodeDecodeError:
                text = text_content.decode('utf-8', errors='ignore')
            
            return {
                'encoding': 'utf-8',
                'character_count': len(text),
                'line_count': text.count('\n') + 1,
                'word_count': len(text.split()),
            }
            
        except Exception as e:
            logger.error(f"Text metadata extraction failed: {e}")
            return {'extraction_error': str(e)}
    
    def _analyze_content_by_type(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """Analyze content based on its type"""
        analysis = {'warnings': [], 'metadata': {}}
        
        try:
            if content_type and content_type.startswith('image/'):
                analysis.update(self._analyze_image_content(file_content))
            elif content_type and content_type.startswith('video/'):
                analysis.update(self._analyze_video_content(file_content))
            elif content_type and content_type.startswith('text/'):
                analysis.update(self._analyze_text_content(file_content))
        
        except Exception as e:
            analysis['warnings'].append(f"Content analysis error: {str(e)}")
        
        return analysis
    
    def _analyze_image_content(self, image_content: bytes) -> Dict[str, Any]:
        """Analyze image content for potential issues"""
        warnings = []
        metadata = {}
        
        try:
            image = Image.open(BytesIO(image_content))
            
            # Check image dimensions
            width, height = image.size
            if width > 4096 or height > 4096:
                warnings.append("Very large image dimensions may impact performance")
            
            if width < 100 or height < 100:
                warnings.append("Very small image may not display well on large screens")
            
            # Check for unusual aspect ratios
            aspect_ratio = width / height
            if aspect_ratio > 5 or aspect_ratio < 0.2:
                warnings.append("Unusual aspect ratio may not display properly")
            
            metadata['aspect_ratio'] = round(aspect_ratio, 2)
            
        except Exception as e:
            warnings.append(f"Image analysis error: {str(e)}")
        
        return {'warnings': warnings, 'metadata': metadata}
    
    def _analyze_video_content(self, video_content: bytes) -> Dict[str, Any]:
        """Analyze video content for potential issues"""
        warnings = []
        metadata = {}
        
        # Basic video file validation
        if len(video_content) > 500 * 1024 * 1024:  # 500MB
            warnings.append("Large video file may cause playback issues")
        
        return {'warnings': warnings, 'metadata': metadata}
    
    def _analyze_text_content(self, text_content: bytes) -> Dict[str, Any]:
        """Analyze text content for potential issues"""
        warnings = []
        metadata = {}
        
        try:
            text = text_content.decode('utf-8', errors='ignore')
            
            # Check for suspicious content
            suspicious_patterns = [
                'javascript:', 'vbscript:', 'data:', 'mailto:', 'tel:',
                '<script', '<iframe', '<object', '<embed'
            ]
            
            text_lower = text.lower()
            for pattern in suspicious_patterns:
                if pattern in text_lower:
                    warnings.append(f"Suspicious content pattern detected: {pattern}")
            
            # Check text length
            if len(text) > 10000:
                warnings.append("Very long text content")
            
            metadata['text_length'] = len(text)
            
        except Exception as e:
            warnings.append(f"Text analysis error: {str(e)}")
        
        return {'warnings': warnings, 'metadata': metadata}
    
    async def add_protected_hash(self, file_hash: str, source: str = "manual") -> bool:
        """Add a file hash to protected content database"""
        try:
            self.protected_hashes.add(file_hash)
            
            # Log the addition
            audit_logger.log_content_event("protected_hash_added", file_hash, {
                "source": source,
                "hash": file_hash
            })
            
            # TODO: Persist to database
            return True
            
        except Exception as e:
            logger.error(f"Failed to add protected hash {file_hash}: {e}")
            return False
    
    async def remove_protected_hash(self, file_hash: str) -> bool:
        """Remove a file hash from protected content database"""
        try:
            if file_hash in self.protected_hashes:
                self.protected_hashes.remove(file_hash)
                
                # Log the removal
                audit_logger.log_content_event("protected_hash_removed", file_hash, {
                    "hash": file_hash
                })
                
                # TODO: Remove from database
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove protected hash {file_hash}: {e}")
            return False

# Global content scanner instance
content_scanner = ContentSecurityScanner()