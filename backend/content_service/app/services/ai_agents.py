import os
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from PIL import Image
import io
import base64
import json
import logging

from .ai_agent_framework import (
    BaseAIAgent, ModelProvider, ContentType, AnalysisRequest, AnalysisResult,
    ModerationAction
)

logger = logging.getLogger(__name__)

class GeminiAgent(BaseAIAgent):
    """Google Gemini AI agent implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("gemini_agent", ModelProvider.GEMINI, config)
    
    def _initialize(self) -> None:
        """Initialize Gemini API"""
        try:
            api_key = self.config.get("api_key") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Gemini API key not found")
            
            genai.configure(api_key=api_key)
            
            # Configure the model
            model_name = self.config.get("model", "gemini-1.5-flash")
            self.model = genai.GenerativeModel(model_name)
            
            # Safety settings
            self.safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            self.enabled = True
            logger.info("Gemini agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini agent: {str(e)}")
            self.enabled = False
    
    async def analyze_content(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze content using Gemini"""
        
        if not self.enabled:
            raise RuntimeError("Gemini agent not initialized")
        
        try:
            if request.content_type == ContentType.TEXT:
                return await self._analyze_text(request)
            elif request.content_type == ContentType.IMAGE:
                return await self._analyze_image(request)
            elif request.content_type == ContentType.VIDEO:
                return await self._analyze_video(request)
            else:
                raise ValueError(f"Unsupported content type: {request.content_type}")
                
        except Exception as e:
            logger.error(f"Gemini analysis failed for {request.content_id}: {str(e)}")
            raise
    
    async def _analyze_text(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze text content"""
        
        prompt = f"""
        Analyze the following content for digital signage display:
        
        Content: {request.text_content}
        
        Provide a detailed analysis in JSON format with:
        1. confidence (0.0-1.0): Your confidence in the analysis
        2. action (approved/needs_review/rejected): Recommended action
        3. reasoning: Detailed explanation of your decision
        4. categories: Array of relevant content categories
        5. safety_scores: Object with safety metrics (0.0-1.0 each)
           - violence: Violence or gore content
           - hate_speech: Hate speech or discrimination
           - adult_content: Sexual or adult content
           - harassment: Bullying or harassment
           - misinformation: False or misleading information
           - spam: Spam or commercial abuse
        6. quality_score (0.0-1.0): Overall content quality
        7. brand_safety_score (0.0-1.0): Brand safety rating
        8. compliance_score (0.0-1.0): Regulatory compliance
        9. concerns: Array of specific concerns
        10. suggestions: Array of improvement suggestions
        
        Consider:
        - Professional appearance
        - Brand safety
        - Legal compliance
        - Target audience appropriateness
        - Message clarity and effectiveness
        """
        
        response = await self._generate_content_async(prompt)
        return self._parse_gemini_response(request, response)
    
    async def _analyze_image(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze image content"""
        
        if not request.file_path:
            raise ValueError("File path required for image analysis")
        
        try:
            # Load and prepare image
            image = Image.open(request.file_path)
            
            prompt = f"""
            Analyze this image for digital signage display:
            
            Provide detailed analysis in JSON format with:
            1. confidence (0.0-1.0): Your confidence in the analysis
            2. action (approved/needs_review/rejected): Recommended action
            3. reasoning: Detailed explanation
            4. categories: Array of content categories
            5. safety_scores: Object with safety metrics (0.0-1.0 each)
               - violence: Violence or disturbing imagery
               - hate_speech: Hate symbols or discriminatory content
               - adult_content: Sexual or adult imagery
               - inappropriate_content: Generally inappropriate content
               - fake_or_misleading: Deepfakes or misleading imagery
            6. quality_score (0.0-1.0): Image quality and professionalism
            7. brand_safety_score (0.0-1.0): Brand safety rating
            8. compliance_score (0.0-1.0): Legal/regulatory compliance
            9. concerns: Array of specific issues
            10. suggestions: Array of improvements
            
            Consider:
            - Visual quality and professionalism
            - Brand safety and appropriateness
            - Legal compliance (copyright, trademarks)
            - Target audience suitability
            - Technical quality (resolution, clarity)
            """
            
            response = await self._generate_content_async([prompt, image])
            return self._parse_gemini_response(request, response)
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            raise
    
    async def _analyze_video(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze video content"""
        
        if not request.file_path:
            raise ValueError("File path required for video analysis")
        
        try:
            # Upload video file
            video_file = genai.upload_file(path=request.file_path)
            
            # Wait for processing
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(1)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                raise RuntimeError("Video processing failed")
            
            prompt = f"""
            Analyze this video for digital signage display:
            
            Provide comprehensive analysis in JSON format with:
            1. confidence (0.0-1.0): Analysis confidence
            2. action (approved/needs_review/rejected): Recommended action
            3. reasoning: Detailed explanation
            4. categories: Array of content categories
            5. safety_scores: Object with safety metrics (0.0-1.0 each)
               - violence: Violence or disturbing content
               - hate_speech: Hate speech or discriminatory content
               - adult_content: Sexual or adult content
               - inappropriate_content: Generally inappropriate
               - misinformation: False or misleading content
               - audio_issues: Audio quality or content issues
            6. quality_score (0.0-1.0): Production quality
            7. brand_safety_score (0.0-1.0): Brand safety
            8. compliance_score (0.0-1.0): Legal compliance
            9. concerns: Array of specific issues
            10. suggestions: Array of improvements
            
            Consider:
            - Video and audio quality
            - Content appropriateness
            - Message effectiveness
            - Technical specifications
            - Legal compliance
            """
            
            response = await self._generate_content_async([prompt, video_file])
            
            # Clean up uploaded file
            genai.delete_file(video_file.name)
            
            return self._parse_gemini_response(request, response)
            
        except Exception as e:
            logger.error(f"Video analysis failed: {str(e)}")
            raise
    
    async def _generate_content_async(self, content) -> str:
        """Generate content asynchronously"""
        loop = asyncio.get_event_loop()
        
        def generate():
            response = self.model.generate_content(
                content,
                safety_settings=self.safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    max_output_tokens=2048,
                )
            )
            return response.text
        
        return await loop.run_in_executor(None, generate)
    
    def _parse_gemini_response(self, request: AnalysisRequest, response_text: str) -> AnalysisResult:
        """Parse Gemini response into AnalysisResult"""
        
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            # Map action strings to enum
            action_mapping = {
                "approved": ModerationAction.APPROVED,
                "needs_review": ModerationAction.NEEDS_REVIEW,
                "rejected": ModerationAction.REJECTED
            }
            
            action = action_mapping.get(data.get("action", "needs_review"), ModerationAction.NEEDS_REVIEW)
            
            return AnalysisResult(
                content_id=request.content_id,
                confidence=float(data.get("confidence", 0.5)),
                action=action,
                reasoning=data.get("reasoning", "Analysis completed"),
                categories=data.get("categories", []),
                safety_scores=data.get("safety_scores", {}),
                quality_score=float(data.get("quality_score", 0.5)),
                brand_safety_score=float(data.get("brand_safety_score", 0.5)),
                compliance_score=float(data.get("compliance_score", 0.5)),
                concerns=data.get("concerns", []),
                suggestions=data.get("suggestions", []),
                processing_time=0.0,  # Will be set by coordinator
                model_used="gemini",
                raw_response=data
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {str(e)}")
            # Return fallback result
            return AnalysisResult(
                content_id=request.content_id,
                confidence=0.3,
                action=ModerationAction.NEEDS_REVIEW,
                reasoning=f"Failed to parse AI response: {str(e)}",
                categories=["parsing_error"],
                safety_scores={"overall": 0.5},
                quality_score=0.5,
                brand_safety_score=0.5,
                compliance_score=0.5,
                concerns=["Response parsing failed"],
                suggestions=["Manual review recommended"],
                processing_time=0.0,
                model_used="gemini",
                raw_response={"error": str(e), "raw_text": response_text}
            )
    
    async def health_check(self) -> bool:
        """Check Gemini agent health"""
        try:
            if not self.enabled:
                return False
            
            # Simple health check with small request
            test_prompt = "Respond with 'OK' if you are working correctly."
            response = await self._generate_content_async(test_prompt)
            return "OK" in response or "ok" in response.lower()
            
        except Exception as e:
            logger.warning(f"Gemini health check failed: {str(e)}")
            return False
    
    def get_supported_content_types(self) -> List[ContentType]:
        """Return supported content types"""
        return [ContentType.TEXT, ContentType.IMAGE, ContentType.VIDEO]

class OpenAIAgent(BaseAIAgent):
    """OpenAI GPT agent implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("openai_agent", ModelProvider.OPENAI, config)
    
    def _initialize(self) -> None:
        """Initialize OpenAI API"""
        try:
            self.api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key not found")
            
            self.model_name = self.config.get("model", "gpt-4o")
            self.base_url = self.config.get("base_url", "https://api.openai.com/v1")
            
            self.enabled = True
            logger.info("OpenAI agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI agent: {str(e)}")
            self.enabled = False
    
    async def analyze_content(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze content using OpenAI"""
        
        if not self.enabled:
            raise RuntimeError("OpenAI agent not initialized")
        
        try:
            if request.content_type == ContentType.TEXT:
                return await self._analyze_text_openai(request)
            elif request.content_type == ContentType.IMAGE:
                return await self._analyze_image_openai(request)
            else:
                raise ValueError(f"Unsupported content type: {request.content_type}")
                
        except Exception as e:
            logger.error(f"OpenAI analysis failed for {request.content_id}: {str(e)}")
            raise
    
    async def _analyze_text_openai(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze text using OpenAI"""
        
        messages = [
            {
                "role": "system",
                "content": """You are a content moderation expert for digital signage. 
                Analyze content and respond with JSON containing: confidence, action (approved/needs_review/rejected), 
                reasoning, categories, safety_scores, quality_score, brand_safety_score, compliance_score, 
                concerns, and suggestions."""
            },
            {
                "role": "user",
                "content": f"Analyze this content for digital signage: {request.text_content}"
            }
        ]
        
        response_text = await self._call_openai_api(messages)
        return self._parse_openai_response(request, response_text)
    
    async def _analyze_image_openai(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze image using OpenAI Vision"""
        
        if not request.file_path:
            raise ValueError("File path required for image analysis")
        
        # Encode image as base64
        with open(request.file_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        messages = [
            {
                "role": "system",
                "content": "You are a content moderation expert. Analyze images and respond with JSON."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image for digital signage display safety and appropriateness."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
        
        response_text = await self._call_openai_api(messages)
        return self._parse_openai_response(request, response_text)
    
    async def _call_openai_api(self, messages: List[Dict]) -> str:
        """Call OpenAI API"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1500
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenAI API error: {response.status} - {error_text}")
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
    
    def _parse_openai_response(self, request: AnalysisRequest, response_text: str) -> AnalysisResult:
        """Parse OpenAI response"""
        # Similar to Gemini parsing but adapted for OpenAI response format
        # Implementation similar to _parse_gemini_response
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            action_mapping = {
                "approved": ModerationAction.APPROVED,
                "needs_review": ModerationAction.NEEDS_REVIEW,
                "rejected": ModerationAction.REJECTED
            }
            
            action = action_mapping.get(data.get("action", "needs_review"), ModerationAction.NEEDS_REVIEW)
            
            return AnalysisResult(
                content_id=request.content_id,
                confidence=float(data.get("confidence", 0.5)),
                action=action,
                reasoning=data.get("reasoning", "Analysis completed"),
                categories=data.get("categories", []),
                safety_scores=data.get("safety_scores", {}),
                quality_score=float(data.get("quality_score", 0.5)),
                brand_safety_score=float(data.get("brand_safety_score", 0.5)),
                compliance_score=float(data.get("compliance_score", 0.5)),
                concerns=data.get("concerns", []),
                suggestions=data.get("suggestions", []),
                processing_time=0.0,
                model_used="openai",
                raw_response=data
            )
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {str(e)}")
            return AnalysisResult(
                content_id=request.content_id,
                confidence=0.3,
                action=ModerationAction.NEEDS_REVIEW,
                reasoning=f"Failed to parse AI response: {str(e)}",
                categories=["parsing_error"],
                safety_scores={"overall": 0.5},
                quality_score=0.5,
                brand_safety_score=0.5,
                compliance_score=0.5,
                concerns=["Response parsing failed"],
                suggestions=["Manual review recommended"],
                processing_time=0.0,
                model_used="openai",
                raw_response={"error": str(e), "raw_text": response_text}
            )
    
    async def health_check(self) -> bool:
        """Check OpenAI agent health"""
        try:
            if not self.enabled:
                return False
            
            messages = [{"role": "user", "content": "Say 'OK' if you are working."}]
            response = await self._call_openai_api(messages)
            return "OK" in response or "ok" in response.lower()
            
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {str(e)}")
            return False
    
    def get_supported_content_types(self) -> List[ContentType]:
        """Return supported content types"""
        return [ContentType.TEXT, ContentType.IMAGE]

class OllamaAgent(BaseAIAgent):
    """Local Ollama agent implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("ollama_agent", ModelProvider.OLLAMA, config)
    
    def _initialize(self) -> None:
        """Initialize Ollama connection"""
        try:
            self.base_url = self.config.get("base_url", "http://localhost:11434")
            self.model_name = self.config.get("model", "llama3.2")
            
            self.enabled = True
            logger.info("Ollama agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama agent: {str(e)}")
            self.enabled = False
    
    async def analyze_content(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze content using Ollama"""
        
        if not self.enabled:
            raise RuntimeError("Ollama agent not initialized")
        
        if request.content_type != ContentType.TEXT:
            raise ValueError("Ollama agent currently supports text only")
        
        return await self._analyze_text_ollama(request)
    
    async def _analyze_text_ollama(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze text using Ollama"""
        
        prompt = f"""
        Analyze the following content for digital signage display safety and appropriateness:
        
        Content: {request.text_content}
        
        Respond with JSON containing:
        - confidence (0.0-1.0)
        - action (approved/needs_review/rejected)
        - reasoning
        - categories (array)
        - safety_scores (object with scores 0.0-1.0)
        - quality_score (0.0-1.0)
        - brand_safety_score (0.0-1.0)
        - compliance_score (0.0-1.0)
        - concerns (array)
        - suggestions (array)
        """
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.8
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Ollama API error: {response.status} - {error_text}")
                
                data = await response.json()
                response_text = data["response"]
                
        return self._parse_ollama_response(request, response_text)
    
    def _parse_ollama_response(self, request: AnalysisRequest, response_text: str) -> AnalysisResult:
        """Parse Ollama response"""
        # Similar parsing logic to other agents
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            action_mapping = {
                "approved": ModerationAction.APPROVED,
                "needs_review": ModerationAction.NEEDS_REVIEW,
                "rejected": ModerationAction.REJECTED
            }
            
            action = action_mapping.get(data.get("action", "needs_review"), ModerationAction.NEEDS_REVIEW)
            
            return AnalysisResult(
                content_id=request.content_id,
                confidence=float(data.get("confidence", 0.5)),
                action=action,
                reasoning=data.get("reasoning", "Analysis completed"),
                categories=data.get("categories", []),
                safety_scores=data.get("safety_scores", {}),
                quality_score=float(data.get("quality_score", 0.5)),
                brand_safety_score=float(data.get("brand_safety_score", 0.5)),
                compliance_score=float(data.get("compliance_score", 0.5)),
                concerns=data.get("concerns", []),
                suggestions=data.get("suggestions", []),
                processing_time=0.0,
                model_used="ollama",
                raw_response=data
            )
        except Exception as e:
            logger.error(f"Failed to parse Ollama response: {str(e)}")
            return AnalysisResult(
                content_id=request.content_id,
                confidence=0.3,
                action=ModerationAction.NEEDS_REVIEW,
                reasoning=f"Failed to parse AI response: {str(e)}",
                categories=["parsing_error"],
                safety_scores={"overall": 0.5},
                quality_score=0.5,
                brand_safety_score=0.5,
                compliance_score=0.5,
                concerns=["Response parsing failed"],
                suggestions=["Manual review recommended"],
                processing_time=0.0,
                model_used="ollama",
                raw_response={"error": str(e), "raw_text": response_text}
            )
    
    async def health_check(self) -> bool:
        """Check Ollama agent health"""
        try:
            if not self.enabled:
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"Ollama health check failed: {str(e)}")
            return False
    
    def get_supported_content_types(self) -> List[ContentType]:
        """Return supported content types"""
        return [ContentType.TEXT]

# Agent factory function
def create_agent(provider: ModelProvider, config: Dict[str, Any]) -> BaseAIAgent:
    """Create an AI agent based on provider"""
    
    if provider == ModelProvider.GEMINI:
        return GeminiAgent(config)
    elif provider == ModelProvider.OPENAI:
        return OpenAIAgent(config)
    elif provider == ModelProvider.OLLAMA:
        return OllamaAgent(config)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
