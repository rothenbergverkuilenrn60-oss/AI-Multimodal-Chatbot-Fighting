import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class OllamaEngine:
    def __init__(self, model_name=None):
        self.base_url = os.getenv("OLLAMA_API_URL")
        self.default_model = model_name or "qwen3-vl:8b"
        
        self.client = AsyncOpenAI(
            api_key="ollama",  
            base_url=self.base_url,
            max_retries=3,
        )

    def _format_history(self, history):
        openai_message = []
        
        for msgdict in history:
            content = msgdict.get('content', '')
            
            if isinstance(content, list):
                processed_content = ""
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        processed_content += item.get("text", "")
                content = processed_content
            
            if content and content.strip():
                openai_message.append({
                    "role": msgdict['role'], 
                    "content": str(content)
                })
        
        return openai_message

    async def chat(self, history: list, temperature: float = 0.7, model_name: str = None, max_chars: int = None):
        model = model_name or self.default_model
        openai_message = self._format_history(history)

        if not openai_message:
            yield history
            return
        
        history.append({"role": "assistant", "content": ""})

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_message,
                temperature=temperature,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    
                    if max_chars:
                        current_length = len(history[-1]["content"])
                        remaining_chars = max_chars - current_length
                        
                        if remaining_chars <= 0:
                            if "[已达到字数限制]" not in history[-1]["content"]:
                                history[-1]["content"] += " [已达到字数限制]"
                            yield history
                            return
                        
                        if len(content) > remaining_chars:
                            content = content[:remaining_chars]
                            history[-1]["content"] += content
                            history[-1]["content"] += " [已达到字数限制]"
                            yield history
                            return
                    
                    history[-1]["content"] += content
                    yield history  # 每次产生新字符都 yield 最新的整个 history
        
        except Exception as e:
            error_msg = f"API调用出错: {str(e)}"
            history.append({"role": "assistant", "content": error_msg})
            yield history