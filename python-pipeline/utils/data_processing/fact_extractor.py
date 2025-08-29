import spacy
from typing import List, Tuple, Dict, Any
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from core.config import settings

class FactExtractor:
    def __init__(self, nlp_model):
        self.nlp = nlp_model
        
        # Keywords that indicate background/context information
        self.context_indicators = [
            "background", "context", "historically", "previously", "in the past",
            "according to", "experts say", "analysts believe", "research shows",
            "studies indicate", "data suggests", "statistics show"
        ]
        
        self.background_indicators = [
            "since", "for years", "over time", "traditionally", "has been",
            "originated", "began", "started", "founded", "established",
            "timeline", "chronology", "sequence of events"
        ]
        
        self.fact_indicators = [
            "confirmed", "reported", "announced", "stated", "declared",
            "according to official", "government said", "police reported",
            "data shows", "statistics reveal", "numbers indicate"
        ]

    def extract(self, text: str) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Extract facts, musings, context, and background from text
        Returns: (facts, musings, context, background)
        """
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        facts = []
        musings = []
        context = []
        background = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Classify sentence type
            if self._is_factual(sentence_lower):
                facts.append(sentence)
            elif self._is_context(sentence_lower):
                context.append(sentence)
            elif self._is_background(sentence_lower):
                background.append(sentence)
            elif self._is_opinion(sentence_lower):
                musings.append(sentence)
            else:
                # Default to facts if unclear
                facts.append(sentence)
        
        return facts[:settings.MAX_FACTS_PER_CLUSTER], musings[:settings.MAX_MUSINGS_PER_CLUSTER], context, background
    
    def merge_similar_bullets(self, bullets: List[str], similarity_threshold: float = 0.8) -> Tuple[List[str], List[float]]:
        """
        Merge similar bullet points to remove duplicates
        Returns: (merged_bullets, similarity_scores)
        """
        if not bullets or len(bullets) <= 1:
            return bullets, [1.0] * len(bullets)
        
        try:
            # Use TF-IDF to compute similarity
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=1000
            )
            
            # Fit and transform the bullets
            tfidf_matrix = vectorizer.fit_transform(bullets)
            
            # Compute cosine similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find similar bullets and merge them
            merged_bullets = []
            used_indices = set()
            similarity_scores = []
            
            for i, bullet in enumerate(bullets):
                if i in used_indices:
                    continue
                
                # Find similar bullets
                similar_indices = []
                for j in range(i + 1, len(bullets)):
                    if j not in used_indices and similarity_matrix[i][j] >= similarity_threshold:
                        similar_indices.append(j)
                
                if similar_indices:
                    # Merge similar bullets (keep the longest one as representative)
                    candidates = [bullet] + [bullets[j] for j in similar_indices]
                    representative = max(candidates, key=len)
                    merged_bullets.append(representative)
                    
                    # Mark indices as used
                    used_indices.add(i)
                    used_indices.update(similar_indices)
                    
                    # Calculate average similarity score
                    similarities = [similarity_matrix[i][j] for j in similar_indices]
                    avg_similarity = np.mean([1.0] + similarities) if similarities else 1.0
                    similarity_scores.append(float(avg_similarity))
                else:
                    # No similar bullets found
                    merged_bullets.append(bullet)
                    used_indices.add(i)
                    similarity_scores.append(1.0)
            
            return merged_bullets, similarity_scores
            
        except Exception as e:
            # Fallback: return original bullets if similarity computation fails
            print(f"Warning: Could not compute similarity for bullet merging: {e}")
            return bullets, [1.0] * len(bullets)
    
    def _is_factual(self, sentence: str) -> bool:
        """Check if sentence contains factual information"""
        return any(indicator in sentence for indicator in self.fact_indicators)
    
    def _is_context(self, sentence: str) -> bool:
        """Check if sentence provides context"""
        return any(indicator in sentence for indicator in self.context_indicators)
    
    def _is_background(self, sentence: str) -> bool:
        """Check if sentence provides background information"""
        return any(indicator in sentence for indicator in self.background_indicators)
    
    def _is_opinion(self, sentence: str) -> bool:
        """Check if sentence contains opinions/musings"""
        opinion_indicators = [
            "i think", "i believe", "in my opinion", "it seems", "appears to",
            "might", "could", "should", "would", "may", "perhaps", "possibly"
        ]
        return any(indicator in sentence for indicator in opinion_indicators)
