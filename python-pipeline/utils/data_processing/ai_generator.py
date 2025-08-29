import google.generativeai as genai
from typing import List, Dict, Any
import os

class AIGenerator:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def generate_factual_summary(
        self, 
        facts: List[str], 
        cluster_name: str
    ) -> str:
        """Generate a purely factual summary"""
        facts_text = "\n".join(f"• {fact}" for fact in facts[:15])
        
        prompt = f"""
        Create a factual, objective summary about "{cluster_name}" based on these verified facts:

        {facts_text}

        Requirements:
        - Only use information from the provided facts
        - Write in objective, neutral tone
        - No opinions or speculation
        - Focus on who, what, when, where, why
        - Maximum 200 words
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating factual summary: {str(e)}"
    
    async def generate_contextual_analysis(
        self, 
        context: List[str], 
        background: List[str], 
        cluster_name: str
    ) -> str:
        """Generate contextual analysis with background information"""
        context_text = "\n".join(f"• {ctx}" for ctx in context[:10])
        background_text = "\n".join(f"• {bg}" for bg in background[:10])
        
        prompt = f"""
        Create a contextual analysis about "{cluster_name}" using this information:

        CONTEXT:
        {context_text}

        BACKGROUND:
        {background_text}

        Requirements:
        - Explain the broader context and significance
        - Provide historical background where relevant
        - Connect current events to past developments
        - Explain why this matters
        - Use analytical but accessible language
        - Maximum 250 words
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating contextual analysis: {str(e)}"
    
    async def generate_comprehensive_article(
        self, 
        facts: List[str], 
        musings: List[str], 
        context: List[str],
        background: List[str],
        cluster_name: str
    ) -> str:
        """Generate a comprehensive article combining all elements"""
        # Limit items to prevent token overflow
        facts_text = "\n".join(f"• {fact}" for fact in facts[:10])
        context_text = "\n".join(f"• {ctx}" for ctx in context[:8])
        background_text = "\n".join(f"• {bg}" for bg in background[:8])
        
        prompt = f"""
        Write a comprehensive news article about "{cluster_name}" structured as follows:

        FACTS:
        {facts_text}

        CONTEXT:
        {context_text}

        BACKGROUND:
        {background_text}

        Structure the article with:
        1. Lead paragraph with key facts
        2. Context section explaining current situation
        3. Background section with historical information
        4. Analysis of significance and implications

        Requirements:
        - Professional news writing style
        - Clear section breaks
        - Objective and balanced
        - Maximum 400 words
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating comprehensive article: {str(e)}"
    
    async def generate_context_paragraph(
        self, 
        context_items: List[str], 
        cluster_name: str
    ) -> str:
        """Generate a coherent context paragraph"""
        if not context_items:
            return ""
            
        context_text = "\n".join(f"• {ctx}" for ctx in context_items[:8])
        
        prompt = f"""
        Create a coherent paragraph explaining the current context for "{cluster_name}" using these context points:

        {context_text}

        Requirements:
        - Write as a single, flowing paragraph
        - Explain the current situation and immediate circumstances
        - Use clear, accessible language
        - Connect the different context points logically
        - Maximum 150 words
        - Start with "The current situation regarding {cluster_name}..."
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating context paragraph: {str(e)}"
    
    async def generate_background_paragraph(
        self, 
        background_items: List[str], 
        cluster_name: str
    ) -> str:
        """Generate a coherent background paragraph"""
        if not background_items:
            return ""
            
        background_text = "\n".join(f"• {bg}" for bg in background_items[:8])
        
        prompt = f"""
        Create a coherent paragraph explaining the historical background for "{cluster_name}" using these background points:

        {background_text}

        Requirements:
        - Write as a single, flowing paragraph
        - Explain historical context and how we got to this point
        - Use clear, accessible language
        - Connect historical events chronologically where possible
        - Maximum 150 words
        - Start with "The background to {cluster_name}..."
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating background paragraph: {str(e)}"
