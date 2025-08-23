import google.generativeai as genai
from typing import List
import os
from core.config import settings
import asyncio

class AIGenerator:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash') 
            self.configured = True
        else:
            self.model = None
            self.configured = False
            print("Warning: GEMINI_API_KEY not configured. AI generation will return placeholder text.")
    
    async def generate_article(
        self, 
        facts: List[str], 
        musings: List[str], 
        cluster_name: str
    ) -> str:
        """Generate desensationalized article using Gemini API"""
        if not self.configured:
            return self._generate_placeholder_article(facts, musings, cluster_name)
        
        try:
            facts_text = "\n• ".join(facts) if facts else "No specific facts available."
            musings_text = "\n• ".join(musings) if musings else "No opinions or commentary available."
            
            prompt = f"""Generate a professional, neutral news article about "{cluster_name}" based on these verified facts:

VERIFIED FACTS:
• {facts_text}

Requirements:
1. Write in objective, journalistic style
2. Use only the facts provided - do not add speculation
3. Structure the article with a clear headline and body
4. Keep the tone neutral and factual
5. After the main article, add a brief "Analysis & Commentary" section if relevant opinions are available

AVAILABLE COMMENTARY:
• {musings_text}

Format the output as a complete news article with proper structure."""

            # Run the generation in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            
            return response.text
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._generate_placeholder_article(facts, musings, cluster_name)
    
    def _generate_placeholder_article(
        self, 
        facts: List[str], 
        musings: List[str], 
        cluster_name: str
    ) -> str:
        """Generate a simple article structure when AI is not available"""
        
        article = f"# {cluster_name}\n\n"
        
        if facts:
            article += "## Key Facts\n\n"
            for fact in facts:
                article += f"• {fact}\n"
            article += "\n"
        
        article += "## Summary\n\n"
        article += f"Based on the available information about {cluster_name}, "
        
        if facts:
            article += f"several key developments have been reported. "
            article += "The situation continues to evolve as more information becomes available.\n\n"
        else:
            article += "limited factual information is currently available.\n\n"
        
        if musings:
            article += "## Analysis & Commentary\n\n"
            for musing in musings:
                article += f"• {musing}\n"
        
        return article
