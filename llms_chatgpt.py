from openai import OpenAI
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from config import system_prompts_chatgpy

# Load environment variables
load_dotenv()


class ChatGPT:
    """
    A class to interact with ChatGPT API
    """
    
    def __init__(self):
        self.api_key = os.getenv('CHATGPT_API_KEY')
        self.model = os.getenv('CHATGPT_MODEL', 'gpt-4o-mini')
        
        if not self.api_key:
            raise ValueError("CHATGPT_API_KEY not found in environment variables")
        
        # Initialize OpenAI client with modern SDK
        self.client = OpenAI(api_key=self.api_key)
        
    def chat(self, user_message: str, use_system_prompt: bool = True, custom_system_prompt: str = None, 
             json_output: bool = False, max_tokens: int = 2000) -> str:
        try:
            messages = []
            
            # Add system prompt if requested
            if use_system_prompt or custom_system_prompt:
                system_prompt = custom_system_prompt if custom_system_prompt else system_prompts_chatgpy
                messages.append({"role": "system", "content": system_prompt})
            
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": max_tokens
            }
            
            # Add JSON output format if requested (for compatible models)
            if json_output and "gpt-4" in self.model.lower():
                api_params["response_format"] = {"type": "json_object"}
            
            # Make API call using modern SDK
            response = self.client.chat.completions.create(**api_params)
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error calling ChatGPT API: {e}")
            raise
    
    def chat_with_context(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error calling ChatGPT API: {e}")
            raise
    
    def analyze_news(self, news_content: str) -> str:

        prompt = f"""
        請分析以下新聞內容，提供：
        1. 主要重點摘要
        2. 對股價可能的影響
        3. 投資建議
        
        新聞內容：
        {news_content}
        """
        
        return self.chat(prompt, use_system_prompt=True)


# Example usage
if __name__ == "__main__":
    try:
        chatgpt = ChatGPT()
        
        # Simple chat
        response = chatgpt.chat("Hello, how are you?")
        print("ChatGPT Response:", response)
        
        # News analysis example
        sample_news = "Apple Inc. reported strong quarterly earnings..."
        analysis = chatgpt.analyze_news(sample_news)
        print("News Analysis:", analysis)
        
    except Exception as e:
        print(f"Error: {e}")
