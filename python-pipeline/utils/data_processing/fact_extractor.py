import spacy
from textblob import TextBlob
from typing import List, Tuple
from fuzzywuzzy import fuzz
from core.config import settings

class FactExtractor:
    def __init__(self, nlp):
        self.nlp = nlp
        
        # Enhanced word lists for better classification
        self.opinion_words = [
            'believe', 'think', 'feel', 'seems', 'appears', 'might', 'could', 
            'should', 'opinion', 'argue', 'suggest', 'claim', 'allegedly',
            'supposedly', 'presumably', 'perhaps', 'maybe', 'probably',
            'likely', 'unlikely', 'doubt', 'suspect', 'assume'
        ]
        
        self.fact_indicators = [
            'reported', 'announced', 'confirmed', 'according to', 'data shows',
            'study', 'research', 'statistics', 'number', 'percent', 'percentage',
            'dollar', 'million', 'billion', 'year', 'month', 'day', 'time',
            'date', 'official', 'government', 'agency', 'department', 'court',
            'law', 'legal', 'regulation', 'policy', 'company', 'corporation'
        ]
    
    def extract(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract fact bullets and separate musings using NER and rules"""
        doc = self.nlp(text[:5000])  # Limit for processing
        
        facts = []
        musings = []
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text or len(sent_text) < 20:
                continue
            
            # Use TextBlob for sentiment
            try:
                blob = TextBlob(sent_text)
                sentiment = blob.sentiment.polarity  #type:ignore
            except:
                sentiment = 0.0
            
            # Check for entities (facts often contain entities)
            has_entities = len(sent.ents) > 0
            has_numbers = any(token.like_num for token in sent)
            has_dates = any(ent.label_ in ['DATE', 'TIME'] for ent in sent.ents)
            
            # Check for opinion indicators
            has_opinion = any(word in sent_text.lower() for word in self.opinion_words)
            
            # Check for factual indicators
            has_fact_indicator = any(indicator in sent_text.lower() for indicator in self.fact_indicators)
            
            # Classification logic with scoring
            fact_score = 0
            opinion_score = 0
            
            # Positive fact indicators
            if has_fact_indicator:
                fact_score += 3
            if has_entities:
                fact_score += 2
            if has_numbers:
                fact_score += 2
            if has_dates:
                fact_score += 2
            if abs(sentiment) < 0.3:  # Neutral sentiment
                fact_score += 1
            
            # Positive opinion indicators
            if has_opinion:
                opinion_score += 3
            if abs(sentiment) > 0.6:  # Strong sentiment
                opinion_score += 2
            if any(word in sent_text.lower() for word in ['amazing', 'terrible', 'wonderful', 'awful']):
                opinion_score += 2
            
            # Clean up the text
            clean_text = sent_text.replace('\\n', ' ').replace('\\t', ' ').strip()
            clean_text = ' '.join(clean_text.split())  # Remove extra whitespace
            
            # Classify based on scores
            if fact_score > opinion_score and len(clean_text) < 300:
                facts.append(clean_text)
            elif opinion_score > fact_score and len(clean_text) < 300:
                musings.append(clean_text)
        
        return facts[:settings.MAX_FACTS_PER_CLUSTER], musings[:settings.MAX_MUSINGS_PER_CLUSTER]
    
    def merge_similar_bullets(self, bullets: List[str]) -> Tuple[List[str], List[float]]:
        """Merge similar bullets using fuzzy matching"""
        if len(bullets) <= 1:
            return bullets, []
        
        threshold = settings.SIMILARITY_THRESHOLD * 100  # Convert to percentage
        merged = []
        used = set()
        similarity_scores = []
        
        for i, bullet1 in enumerate(bullets):
            if i in used:
                continue
                
            similar_group = [bullet1]
            group_scores = []
            
            for j, bullet2 in enumerate(bullets[i+1:], i+1):
                if j in used:
                    continue
                    
                # Multiple fuzzy matching strategies
                ratio1 = fuzz.ratio(bullet1, bullet2)
                ratio2 = fuzz.token_sort_ratio(bullet1, bullet2)
                ratio3 = fuzz.token_set_ratio(bullet1, bullet2)
                
                # Use the highest ratio
                best_ratio = max(ratio1, ratio2, ratio3)
                
                if best_ratio > threshold:
                    similar_group.append(bullet2)
                    used.add(j)
                    group_scores.append(best_ratio / 100.0)
            
            # Keep the longest bullet from similar group (usually most informative)
            merged.append(max(similar_group, key=len))
            used.add(i)
            
            if group_scores:
                similarity_scores.extend(group_scores)
        
        return merged, similarity_scores
