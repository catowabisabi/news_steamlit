import requests
import json
from typing import Dict, List, Optional


class NewsScraper:
    """
    A class to scrape news data from the enomars news API
    """
    
    def __init__(self):
        self.base_url = "http://news.enomars.org/api/news/"
        self.session = requests.Session()
        
    def get_news(self, stock_ticker: Optional[str] = None) -> Dict:
        """
        Fetch news from the API
        
        Args:
            stock_ticker (str, optional): Stock ticker symbol to filter news
            
        Returns:
            Dict: JSON response from the API
            
        Raises:
            requests.RequestException: If the API request fails
        """
        try:
            # Construct URL with ticker in path if provided
            if stock_ticker:
                url = f"{self.base_url}{stock_ticker}"
            else:
                url = self.base_url
                
            # Make the request with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Increase timeout to 300 seconds (5 minutes) and add headers
                    response = self.session.get(url, timeout=300, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    response.raise_for_status()  # Raises an HTTPError for bad responses
                    
                    return response.json()
                except requests.exceptions.Timeout as e:
                    print(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt == max_retries - 1:
                        raise
                except requests.exceptions.RequestException as e:
                    print(f"Request error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt == max_retries - 1:
                        raise
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            # Return empty news structure instead of raising
            return {"articles": [], "error": f"API request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            # Return empty news structure instead of raising
            return {"articles": [], "error": f"JSON parsing failed: {str(e)}"}
            
    def get_news_by_ticker(self, ticker: str) -> Dict:
        """
        Convenience method to get news for a specific stock ticker
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            Dict: JSON response from the API
        """
        return self.get_news(stock_ticker=ticker)
        
    def close(self):
        """Close the requests session"""
        self.session.close()
    
    def get_news_cleaned(self, news: Dict) -> Dict:
        """
        Clean news data by removing unwanted fields and format for display
        
        Args:
            news (Dict): Raw news data from API
            
        Returns:
            Dict: Cleaned news data with only essential fields
        """
        cleaned_news = {"articles": []}
        
        if "articles" in news:
            for article in news["articles"]:
                cleaned_article = {
                    "publishedAt": article.get("publishedAt", ""),
                    "title": article.get("title", ""),
                    "html_content": article.get("html_content", "")
                }
                cleaned_news["articles"].append(cleaned_article)
        
        return cleaned_news
    
    def print_news_formatted(self, news: Dict):
        """
        Print news in a formatted way with date, title, and content
        Each field limited to 200 characters
        
        Args:
            news (Dict): News data to print
        """
        if "articles" not in news:
            print("No articles found")
            return
            
        for i, article in enumerate(news["articles"], 1):
            print(f"\n{'='*60}")
            print(f"文章 {i}")
            print(f"{'='*60}")
            
            # Date (限200字)
            date = article.get("publishedAt", "Unknown")[:200]
            print(f"日期: {date}")
            
            # Title (限200字)
            title = article.get("title", "No title")[:200]
            print(f"題目: {title}")
            
            # Content (限200字)
            content = article.get("html_content", "No content")[:200]
            print(f"內容: {content}")
            
            if len(article.get("html_content", "")) > 200:
                print("... (內容已截斷)")
                
        print(f"\n{'='*60}")
        print(f"總共 {len(news['articles'])} 篇文章")




# Example usage
if __name__ == "__main__":
    scraper = NewsScraper()
    
    try:
        # Get news for a specific ticker
        all_news = scraper.get_news(stock_ticker="xpon")
        
        # Clean the news data (remove unwanted fields)
        cleaned_news = scraper.get_news_cleaned(all_news)
        
        # Print formatted news (date, title, content - each limited to 200 chars)
        scraper.print_news_formatted(cleaned_news)
        
        # If you want to see the raw JSON (uncomment below)
        # print("\nOriginal JSON:")
        # print(json.dumps(all_news, indent=2))
        
    except Exception as e:
        print(f"Failed to fetch news: {e}")
    finally:
        scraper.close()
