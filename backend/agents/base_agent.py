import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import re
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

load_dotenv()

class BaseAgent:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        self.api_key = api_key

    def _standardize_response(self, status: str, message: str, data: Any = None) -> Dict[str, Any]:
        """Standardize response format across all agents"""
        return {
            "status": status,
            "message": message,
            "data": data or {},
            "timestamp": self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()

    async def generate_response(self, prompt: str, default_response: Optional[str] = None) -> str:
        """Generate AI response asynchronously"""
        try:
            response = await self.model.generate_content_async(prompt)
            if response and response.text:
                return response.text.strip()
            return default_response or "I couldn't generate a proper response at the moment."
        except Exception as e:
            print(f"Error generating response: {e}")
            return default_response or "I encountered an error while processing your request."

    def generate_response_sync(self, prompt: str, default_response: Optional[str] = None) -> str:
        """Generate AI response synchronously"""
        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            return default_response or "I couldn't generate a proper response at the moment."
        except Exception as e:
            print(f"Error generating response: {e}")
            return default_response or "I encountered an error while processing your request."

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text with multiple fallback strategies"""
        if not text:
            return None
            
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Find JSON block with code markers
        json_patterns = [
            r'``````',
            r'``````',
            r'\{.*\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        return None

    async def generate_structured_response(self, prompt: str, default_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON response asynchronously"""
        try:
            # Enhanced prompt to ensure JSON output
            enhanced_prompt = f"""
            {prompt}
            
            IMPORTANT: Respond ONLY with valid JSON. No additional text or explanation.
            Use this exact structure format:
            {json.dumps(default_structure, indent=2)}
            """
            
            response_text = await self.generate_response(enhanced_prompt)
            parsed_json = self._extract_json_from_text(response_text)
            
            if parsed_json:
                # Merge with default structure to ensure all required fields exist
                return {**default_structure, **parsed_json}
            
            return default_structure
            
        except Exception as e:
            print(f"Error in structured response generation: {e}")
            return default_structure

    def generate_structured_response_sync(self, prompt: str, default_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON response synchronously"""
        try:
            # Enhanced prompt to ensure JSON output
            enhanced_prompt = f"""
            {prompt}
            
            IMPORTANT: Respond ONLY with valid JSON. No additional text or explanation.
            Use this exact structure format:
            {json.dumps(default_structure, indent=2)}
            """
            
            response_text = self.generate_response_sync(enhanced_prompt)
            parsed_json = self._extract_json_from_text(response_text)
            
            if parsed_json:
                # Merge with default structure to ensure all required fields exist
                return {**default_structure, **parsed_json}
            
            return default_structure
            
        except Exception as e:
            print(f"Error in structured response generation: {e}")
            return default_structure
