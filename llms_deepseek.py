from openai import OpenAI
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from config import system_prompts_deepseek
from config import NEWS_ANALYSIS_PROMPT

# Load environment variables
load_dotenv()


class DeepSeek:
    """
    A class to interact with DeepSeek API using OpenAI SDK format
    """
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        
        # Initialize OpenAI client with DeepSeek endpoint
        self.client = OpenAI(
            api_key=self.api_key, 
            base_url="https://api.deepseek.com"
        )
        
    def chat(self, user_message: str, use_system_prompt: bool = True, custom_system_prompt: str = None, 
             json_output: bool = False, max_tokens: int = 2000) -> str:
        """
        Send a message to DeepSeek and get response
        
        Args:
            user_message (str): The user's message
            use_system_prompt (bool): Whether to use the default system prompt
            custom_system_prompt (str): Custom system prompt to use instead
            json_output (bool): Whether to enforce JSON output format
            max_tokens (int): Maximum tokens for response
            
        Returns:
            str: DeepSeek's response
        """
        try:
            messages = []
            
            # Add system prompt if requested
            if use_system_prompt or custom_system_prompt:
                system_prompt = custom_system_prompt if custom_system_prompt else system_prompts_deepseek
                messages.append({"role": "system", "content": system_prompt})
            
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Add JSON output format if requested
            if json_output:
                api_params["response_format"] = {'type': 'json_object'}
            
            # Make API call using OpenAI SDK format
            response = self.client.chat.completions.create(**api_params)
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            raise
    
    def chat_with_context(self, messages: List[Dict[str, str]]) -> str:
        """
        Send multiple messages with context to DeepSeek
        
        Args:
            messages (List[Dict]): List of messages with role and content
            
        Returns:
            str: DeepSeek's response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
                stream=False
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            raise
    
    def analyze_news_technical(self, news_content: str) -> str:
        """
        Analyze news content from technical analysis perspective using DeepSeek
        
        Args:
            news_content (str): News content to analyze
            
        Returns:
            str: Technical analysis result
        """
        prompt = f"""
        請從技術分析角度分析以下新聞內容，提供：
        1. 技術指標可能的影響
        2. 圖表模式的潛在變化
        3. 量化分析觀點
        4. 風險管理建議
        
        新聞內容：
        {news_content}
        """
        
        return self.chat(prompt, use_system_prompt=True)


# Example usage
if __name__ == "__main__":
    try:
        deepseek = DeepSeek()
        
        # Simple chat
        response = deepseek.chat("Hello, how are you?")
        print("DeepSeek Response:", response)
        
        # Technical analysis example
        sample_news = "Apple Inc. reported strong quarterly earnings..."
        analysis = deepseek.analyze_news_technical(sample_news)
        print("Technical Analysis:", analysis)
        
    except Exception as e:
        print(f"Error: {e}")
