import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import base64
from pathlib import Path

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from app.models import ModerationResult
from app.utils.serialization import safe_json_response

logger = logging.getLogger(__name__)

class GeminiModerationService:
    """
    Advanced AI Content Moderation using Google Gemini
    Supports multi-modal analysis with human-in-loop integration
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.enabled = GEMINI_AVAILABLE and self.api_key is not None
        
        if self.enabled:
            genai.configure(api_key=self.api_key)
            
            # Initialize models for different content types
            self.text_model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }
            )
            
            self.vision_model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-8b",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }
            )
            
            logger.info("✅ Gemini AI moderation service initialized successfully")
        else:
            logger.warning("⚠️ Gemini AI not available - using simulation mode")
    
    async def analyze_content(
        self, 
        content_id: str, 
        content_type: str,
        file_path: Optional[str] = None,
        text_content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ModerationResult:
        """
        Comprehensive content analysis using Gemini AI
        
        Args:
            content_id: Unique content identifier
            content_type: Type of content (image, video, text, etc.)
            file_path: Path to content file
            text_content: Text content for analysis
            metadata: Additional content metadata
            
        Returns:
            ModerationResult with confidence score and decision
        """
        
        if not self.enabled:
            return await self._simulate_moderation(content_id)
        
        try:
            logger.info(f"Starting Gemini analysis for content {content_id}")
            
            # Route to appropriate analysis method
            if content_type.startswith('image'):
                result = await self._analyze_image(content_id, file_path, text_content, metadata)
            elif content_type.startswith('video'):
                result = await self._analyze_video(content_id, file_path, text_content, metadata)
            elif content_type == 'text':
                result = await self._analyze_text(content_id, text_content, metadata)
            else:
                result = await self._analyze_mixed_content(content_id, file_path, text_content, metadata)
            
            logger.info(f"Gemini analysis completed for {content_id}: {result.action} (confidence: {result.ai_confidence})")
            return result
            
        except Exception as e:
            logger.error(f"Gemini analysis failed for {content_id}: {str(e)}")
            # Fallback to simulation on error
            return await self._simulate_moderation(content_id)
    
    async def _analyze_image(
        self, 
        content_id: str, 
        file_path: str, 
        text_content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ModerationResult:
        """Analyze image content using Gemini Vision"""
        
        try:
            # Read image file
            if not file_path or not Path(file_path).exists():
                raise FileNotFoundError(f"Image file not found: {file_path}")
            
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # Prepare prompt for comprehensive analysis
            prompt = self._create_image_analysis_prompt(text_content, metadata)
            
            # Upload image and analyze
            image_part = {
                "mime_type": self._get_mime_type(file_path),
                "data": image_data
            }
            
            response = await asyncio.to_thread(
                self.vision_model.generate_content,
                [prompt, image_part]
            )
            
            # Parse response and calculate confidence
            analysis = self._parse_gemini_response(response.text)
            confidence = self._calculate_confidence(analysis)
            action = self._determine_action(confidence, analysis)
            
            return ModerationResult(
                content_id=content_id,
                ai_confidence=confidence,
                action=action,
                reason=analysis.get('reasoning', 'Gemini AI analysis completed'),
                categories=analysis.get('categories', []),
                details=analysis
            )
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            raise
    
    async def _analyze_video(
        self, 
        content_id: str, 
        file_path: str, 
        text_content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ModerationResult:
        """Analyze video content using Gemini"""
        
        try:
            # For now, extract frames and analyze as images
            # TODO: Implement full video analysis when available
            logger.info(f"Video analysis for {content_id} - using frame extraction")
            
            # Extract key frames (simplified approach)
            frames = await self._extract_video_frames(file_path)
            
            # Analyze representative frames
            frame_results = []
            for i, frame_path in enumerate(frames[:3]):  # Analyze first 3 frames
                frame_result = await self._analyze_image(f"{content_id}_frame_{i}", frame_path, text_content, metadata)
                frame_results.append(frame_result)
            
            # Aggregate results
            avg_confidence = sum(r.ai_confidence for r in frame_results) / len(frame_results)
            combined_categories = list(set().union(*[r.categories for r in frame_results if r.categories]))
            
            # Determine overall action
            action = self._determine_action(avg_confidence, {'categories': combined_categories})
            
            return ModerationResult(
                content_id=content_id,
                ai_confidence=avg_confidence,
                action=action,
                reason=f"Video analysis based on {len(frame_results)} frames",
                categories=combined_categories,
                details={'frame_analyses': [r.model_dump() for r in frame_results]}
            )
            
        except Exception as e:
            logger.error(f"Video analysis failed: {str(e)}")
            raise
    
    async def _analyze_text(
        self, 
        content_id: str, 
        text_content: str,
        metadata: Optional[Dict] = None
    ) -> ModerationResult:
        """Analyze text content using Gemini"""
        
        try:
            # Create comprehensive text analysis prompt
            prompt = self._create_text_analysis_prompt(text_content, metadata)
            
            response = await asyncio.to_thread(
                self.text_model.generate_content,
                prompt
            )
            
            # Parse response
            analysis = self._parse_gemini_response(response.text)
            confidence = self._calculate_confidence(analysis)
            action = self._determine_action(confidence, analysis)
            
            return ModerationResult(
                content_id=content_id,
                ai_confidence=confidence,
                action=action,
                reason=analysis.get('reasoning', 'Text analysis completed'),
                categories=analysis.get('categories', []),
                details=analysis
            )
            
        except Exception as e:
            logger.error(f"Text analysis failed: {str(e)}")
            raise
    
    async def _analyze_mixed_content(
        self, 
        content_id: str, 
        file_path: Optional[str] = None, 
        text_content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ModerationResult:
        """Analyze mixed content (image + text)"""
        
        try:
            results = []
            
            # Analyze image if present
            if file_path and Path(file_path).exists():
                image_result = await self._analyze_image(content_id, file_path, text_content, metadata)
                results.append(image_result)
            
            # Analyze text if present
            if text_content and text_content.strip():
                text_result = await self._analyze_text(content_id, text_content, metadata)
                results.append(text_result)
            
            if not results:
                raise ValueError("No content to analyze")
            
            # Combine results - use most conservative approach
            min_confidence = min(r.ai_confidence for r in results)
            combined_categories = list(set().union(*[r.categories for r in results if r.categories]))
            
            action = self._determine_action(min_confidence, {'categories': combined_categories})
            
            return ModerationResult(
                content_id=content_id,
                ai_confidence=min_confidence,
                action=action,
                reason="Combined multi-modal analysis",
                categories=combined_categories,
                details={'component_analyses': [r.model_dump() for r in results]}
            )
            
        except Exception as e:
            logger.error(f"Mixed content analysis failed: {str(e)}")
            raise
    
    def _create_image_analysis_prompt(self, text_content: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """Create comprehensive image analysis prompt"""
        
        prompt = """
        You are an expert content moderator for a digital signage platform. Analyze this image for:

        1. **Content Safety**:
           - Adult/sexual content
           - Violence or disturbing imagery
           - Hate speech or discriminatory symbols
           - Drug or alcohol references
           - Dangerous activities

        2. **Brand Safety**:
           - Professional quality and appearance
           - Appropriate for public display
           - Cultural sensitivity
           - Age-appropriate content

        3. **Quality Assessment**:
           - Image clarity and resolution
           - Professional composition
           - Text readability (if any)
           - Visual appeal

        4. **Compliance**:
           - Advertising standards compliance
           - Copyright/trademark issues
           - Accessibility considerations

        """
        
        if text_content:
            prompt += f"\n5. **Associated Text**: {text_content[:500]}\n"
        
        if metadata:
            prompt += f"\n6. **Context**: {json.dumps(metadata, indent=2)[:300]}\n"
        
        prompt += """
        Provide your analysis in JSON format:
        {
            "safety_score": 0-100,
            "quality_score": 0-100,
            "brand_safety_score": 0-100,
            "compliance_score": 0-100,
            "overall_confidence": 0-100,
            "categories": ["list", "of", "detected", "categories"],
            "concerns": ["list", "of", "any", "concerns"],
            "reasoning": "detailed explanation of your assessment",
            "recommendation": "approve|review|reject"
        }
        """
        
        return prompt
    
    def _create_text_analysis_prompt(self, text_content: str, metadata: Optional[Dict] = None) -> str:
        """Create comprehensive text analysis prompt"""
        
        prompt = f"""
        You are an expert content moderator for a digital signage platform. Analyze this text content:

        TEXT: "{text_content}"

        Evaluate for:

        1. **Content Safety**:
           - Hate speech or discriminatory language
           - Adult or inappropriate content
           - Violence or threatening language
           - Misleading or false information

        2. **Brand Safety**:
           - Professional tone and language
           - Appropriate for public display
           - Cultural sensitivity
           - Business appropriate content

        3. **Quality Assessment**:
           - Grammar and spelling
           - Clarity and readability
           - Professional presentation
           - Factual accuracy

        4. **Compliance**:
           - Advertising standards
           - Truth in advertising
           - Accessibility guidelines
           - Legal compliance

        """
        
        if metadata:
            prompt += f"\nContext: {json.dumps(metadata, indent=2)[:300]}\n"
        
        prompt += """
        Provide your analysis in JSON format:
        {
            "safety_score": 0-100,
            "quality_score": 0-100,
            "brand_safety_score": 0-100,
            "compliance_score": 0-100,
            "overall_confidence": 0-100,
            "categories": ["detected", "content", "categories"],
            "concerns": ["any", "specific", "concerns"],
            "reasoning": "detailed explanation",
            "recommendation": "approve|review|reject"
        }
        """
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response and extract analysis"""
        
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)
                return analysis
            else:
                # Fallback parsing
                return {
                    'overall_confidence': 85,
                    'reasoning': response_text[:500],
                    'recommendation': 'review',
                    'categories': ['general_content']
                }
                
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Gemini response as JSON: {response_text[:200]}")
            return {
                'overall_confidence': 80,
                'reasoning': 'Analysis completed but response format unexpected',
                'recommendation': 'review',
                'categories': ['unknown']
            }
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        
        confidence = analysis.get('overall_confidence', 80)
        
        # Adjust based on specific scores
        safety_score = analysis.get('safety_score', 80)
        quality_score = analysis.get('quality_score', 80)
        brand_safety_score = analysis.get('brand_safety_score', 80)
        compliance_score = analysis.get('compliance_score', 80)
        
        # Weighted average (safety is most important)
        weighted_score = (
            safety_score * 0.4 +
            compliance_score * 0.3 +
            brand_safety_score * 0.2 +
            quality_score * 0.1
        )
        
        # Use the minimum of declared confidence and calculated score
        final_confidence = min(confidence, weighted_score) / 100.0
        
        return round(final_confidence, 3)
    
    def _determine_action(self, confidence: float, analysis: Dict[str, Any]) -> str:
        """Determine moderation action based on confidence and analysis"""
        
        recommendation = analysis.get('recommendation', '').lower()
        concerns = analysis.get('concerns', [])
        
        # Override thresholds based on specific concerns
        if any('hate' in str(concern).lower() or 'violence' in str(concern).lower() 
               or 'adult' in str(concern).lower() for concern in concerns):
            return "rejected"
        
        # Standard confidence-based thresholds
        if confidence >= 0.95 and recommendation == 'approve':
            return "approved"
        elif confidence >= 0.70:
            return "needs_review"
        else:
            return "rejected"
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file"""
        
        extension = Path(file_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mov': 'video/quicktime'
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    
    async def _extract_video_frames(self, video_path: str) -> List[str]:
        """Extract key frames from video for analysis"""
        
        # Simplified implementation - in production, use FFmpeg
        # For now, return empty list to indicate video analysis not fully implemented
        logger.warning("Video frame extraction not implemented - using fallback")
        return []
    
    async def _simulate_moderation(self, content_id: str) -> ModerationResult:
        """Fallback simulation when Gemini is not available"""
        
        import random
        
        confidence = round(random.uniform(0.4, 0.99), 3)
        
        if confidence > 0.95:
            action = "approved"
            reason = "High confidence - auto-approved"
        elif confidence >= 0.70:
            action = "needs_review"
            reason = "Medium confidence - requires human review"
        else:
            action = "rejected"
            reason = "Low confidence - auto-rejected"
        
        logger.info(f"Simulated moderation for {content_id}: {action} (confidence: {confidence})")
        
        return ModerationResult(
            content_id=content_id,
            ai_confidence=confidence,
            action=action,
            reason=f"[SIMULATION] {reason}",
            categories=["simulated_content"],
            details={"simulation": True}
        )

    async def explain_decision(self, result: ModerationResult) -> str:
        """Generate human-readable explanation for moderation decision"""
        
        if not self.enabled:
            return f"Simulated analysis resulted in {result.action} with {result.ai_confidence:.1%} confidence."
        
        try:
            prompt = f"""
            Explain this content moderation decision in simple terms for content creators:
            
            Decision: {result.action}
            Confidence: {result.ai_confidence:.1%}
            Categories: {result.categories}
            Reason: {result.reason}
            
            Provide a clear, helpful explanation that:
            1. Explains why this decision was made
            2. Gives specific feedback about the content
            3. Offers suggestions for improvement if rejected/needs review
            4. Uses encouraging, professional tone
            
            Keep it under 200 words and be specific.
            """
            
            response = await asyncio.to_thread(
                self.text_model.generate_content,
                prompt
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {str(e)}")
            return f"Content was {result.action} based on AI analysis with {result.ai_confidence:.1%} confidence. {result.reason}"


# Global service instance
gemini_service = GeminiModerationService()
