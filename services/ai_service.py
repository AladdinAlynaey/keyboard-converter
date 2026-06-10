import requests
from typing import Optional, List, Dict, Any
from configuration.config import Config, logger

class AIIntegrationDisabledError(Exception):
    """Raised when trying to call AI services while they are disabled in settings."""
    pass

class AIService:
    @classmethod
    def get_available_models(cls) -> List[Dict[str, str]]:
        """
        Returns models available to the platform.
        """
        return [
            {
                "id": "openrouter/free",
                "name": "Auto Select (Free Model Router)"
            },
            {
                "id": "nvidia/nemotron-3-ultra-550b-a55b:free",
                "name": "Nemotron 3 Ultra 550B (Free)"
            },
            {
                "id": "meta-llama/llama-3.3-70b-instruct:free",
                "name": "Llama 3.3 70B Instruct (Free)"
            },
            {
                "id": "meta-llama/llama-3.2-3b-instruct:free",
                "name": "Llama 3.2 3B Instruct (Free)"
            },
            {
                "id": "meta-llama/llama-3-8b-instruct",
                "name": "Llama 3 8B Instruct (Paid)"
            }
        ]

    @classmethod
    def enhance_text(cls, text: str, mode: int, model: Optional[str] = None, 
                     temperature: float = 0.3, custom_prompt_prefix: Optional[str] = "") -> str:
        """
        Queries OpenRouter API for AI-assisted corrections.
        Supports 3 AI modes (2 = Grammar/Spelling, 3 = Enhancement, 4 = Completion).
        """
        if not Config.AI_ENABLED or not Config.OPENROUTER_API_KEY:
            raise AIIntegrationDisabledError("AI operations are disabled on this server instance.")

        model_name = model or Config.DEFAULT_AI_MODEL
        
        # System instructions according to the requested mode
        system_prompts = {
            2: (
                "You are an expert editor. Correct any grammar, spelling, punctuation, and context errors "
                "in the text provided. Maintain the original language, writing script/alphabet, line breaks, "
                "formatting, and intent. Crucially, do NOT translate or transliterate the text (e.g., if the input is "
                "in Arabic script, your output MUST be in Arabic script; do not Romanize or write it in English letters). "
                "Output ONLY the corrected text itself. Do not include any explanations, introduction, or extra comments."
            ),
            3: (
                "You are an expert copywriter. Rewrite and enhance the style of the text provided to make it "
                "sound premium, fluent, and professional. Retain the original language, writing script/alphabet, "
                "line breaks, formatting, and message intent. Do NOT translate or transliterate the text into another alphabet. "
                "Output ONLY the enhanced text itself. Do not include explanations."
            ),
            4: (
                "You are a text completion helper. Predict and append the natural completion of the text provided. "
                "Preserve the original language, writing script/alphabet, formatting, and tone. Output ONLY the completed "
                "text itself (including the original input text as the beginning). Do not include any conversation or meta-commentary."
            )
        }

        system_instruction = system_prompts.get(mode)
        if not system_instruction:
            raise ValueError(f"Invalid AI conversion mode: {mode}")

        if custom_prompt_prefix:
            system_instruction = f"{custom_prompt_prefix}\n\n{system_instruction}"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:5000",
            "X-Title": "Smart Keyboard Converter AI"
        }
        
        payload = {
            "model": model_name,
            "temperature": max(0.0, min(temperature, 2.0)),
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": text}
            ]
        }

        try:
            logger.info(f"Dispatching AI request to OpenRouter model={model_name}, mode={mode}")
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API call failed: {response.text}")
                raise RuntimeError(f"OpenRouter returned error: {response.status_code}")
                
            res_data = response.json()
            choices = res_data.get("choices", [])
            if not choices:
                logger.error(f"OpenRouter returned empty choices: {res_data}")
                raise RuntimeError("Empty response received from AI model.")
                
            enhanced_text = choices[0].get("message", {}).get("content", "").strip()
            return enhanced_text
            
        except requests.exceptions.Timeout:
            logger.error("AI service timed out.")
            raise RuntimeError("Request to the AI service timed out. Please try again later.")
        except Exception as e:
            logger.error(f"Error querying OpenRouter API: {e}")
            raise e
