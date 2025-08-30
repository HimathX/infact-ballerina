import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
import spacy
import torch
from core.config import settings
from schemas.article import Article, ClusterResult
from .clustering import ArticleClusterer
from .fact_extractor import FactExtractor
from .ai_generator import AIGenerator
from utils.image_service import ImageService


class ClusteringResult:
    def __init__(self, clusters, cluster_names, n_clusters, embeddings_2d, cluster_sizes):
        self.clusters = clusters
        self.cluster_names = cluster_names
        self.n_clusters = n_clusters
        self.embeddings_2d = embeddings_2d
        self.cluster_sizes = cluster_sizes

class NLPProcessor:
    def __init__(self):
        self.nlp = None
        self.sentence_model = None
        self.clusterer = None
        self.fact_extractor = None
        self.ai_generator = None
        self.image_service = None
        self.initialized = False

    async def initialize(self):
        """Initialize all NLP models"""
        if self.initialized:
            return
        
        # Load spaCy model
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
        except OSError:
            print(f"spaCy model '{settings.SPACY_MODEL}' not found. Please install it with: python -m spacy download {settings.SPACY_MODEL}")
            # Use a minimal pipeline for demo purposes
            self.nlp = spacy.blank("en")
        
        # Load sentence transformer
        self.sentence_model = SentenceTransformer(settings.SENTENCE_MODEL_NAME)
        if settings.USE_GPU and torch.cuda.is_available():
            self.sentence_model = self.sentence_model.to('cuda')
        
        # Initialize components
        self.clusterer = ArticleClusterer(self.sentence_model)
        self.fact_extractor = FactExtractor(self.nlp)
        self.ai_generator = AIGenerator()
        self.image_service = ImageService()
        
        self.initialized = True

    async def preprocess_texts(self, texts: List[str]) -> List[str]:
        """Preprocess texts using spaCy"""
        processed = []
        for text in texts:
            doc = self.nlp(text[:settings.MAX_TEXT_LENGTH]) #type:ignore
            tokens = [token.lemma_.lower() for token in doc 
                     if not token.is_stop and not token.is_punct and token.is_alpha]
            processed.append(" ".join(tokens))
        return processed

    async def cluster_articles(
        self, 
        articles: List[Article], 
        n_clusters: Optional[int] = None
    ) -> ClusteringResult:
        """Cluster articles using embeddings and KMeans"""
        texts = [f"{art.title} {art.content}" for art in articles]
        processed_texts = await self.preprocess_texts(texts)
        
        # Generate embeddings
        embeddings = self._extract_embeddings(texts)
        
        # Cluster
        clusters, cluster_names, embeddings_2d = self.clusterer.cluster( #type:ignore
            embeddings, processed_texts, n_clusters
        )
        
        # Calculate cluster sizes
        cluster_sizes = {}
        for cluster_id in np.unique(clusters):
            cluster_sizes[cluster_id] = int(np.sum(clusters == cluster_id))
        
        return ClusteringResult(
            clusters=clusters.tolist(),
            cluster_names=cluster_names,
            n_clusters=len(np.unique(clusters)),
            embeddings_2d=embeddings_2d,
            cluster_sizes=cluster_sizes
        )

    def _extract_embeddings(self, texts: List[str]) -> np.ndarray:
        """Extract embeddings with batch processing"""
        embeddings = []
        batch_size = settings.EMBEDDING_BATCH_SIZE
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.sentence_model.encode( #type:ignore
                batch, convert_to_tensor=True, show_progress_bar=False
            )
            embeddings.extend(batch_embeddings.cpu().numpy())
        
        return np.array(embeddings)

    async def extract_facts_and_musings(self, articles: List[Article]) -> Dict[str, Any]:
        """Extract facts, musings, context, and background from articles"""
        all_facts = []
        all_musings = []
        all_context = []
        all_background = []
        
        for article in articles:
            text = f"{article.title} {article.content}"
            facts, musings, context, background = self.fact_extractor.extract(text) #type:ignore
            all_facts.extend(facts)
            all_musings.extend(musings)
            all_context.extend(context)
            all_background.extend(background)
        
        return {
            "facts": all_facts,
            "musings": all_musings,
            "context": all_context,
            "background": all_background,
            "stats": {
                "total_facts": len(all_facts),
                "total_musings": len(all_musings),
                "total_context": len(all_context),
                "total_background": len(all_background),
                "avg_facts_per_article": len(all_facts) / len(articles) if articles else 0,
                "avg_context_per_article": len(all_context) / len(articles) if articles else 0
            }
        }

    async def process_articles(
        self, 
        articles: List[Article], 
        n_clusters: Optional[int] = None
    ) -> List[ClusterResult]:
        """Complete processing pipeline with context and background"""
        # Step 1: Cluster articles
        clustering_result = await self.cluster_articles(articles, n_clusters)
        
        # Step 2: Process each cluster
        cluster_results = []
        
        for cluster_id in range(clustering_result.n_clusters):
            # Get articles in this cluster
            cluster_articles = [
                articles[i] for i in range(len(articles)) 
                if clustering_result.clusters[i] == cluster_id
            ]
            
            if not cluster_articles:
                continue
            
            # Extract sources and URLs from cluster articles
            sources = []
            article_urls = []
            source_counts = {}
            
            for article in cluster_articles:
                # Collect sources
                if article.source:
                    sources.append(article.source)
                    source_counts[article.source] = source_counts.get(article.source, 0) + 1
                
                # Collect URLs
                if article.url:
                    article_urls.append(article.url)
            
            # Remove duplicate sources while preserving order
            unique_sources = list(dict.fromkeys(sources))
            
            # Extract facts, musings, context, and background
            extraction_result = await self.extract_facts_and_musings(cluster_articles)
            
            # Deduplicate facts
            merged_facts, similarity_scores = self.fact_extractor.merge_similar_bullets( #type:ignore
                extraction_result["facts"]
            )
            
            # Deduplicate context and background lists
            merged_context_items = self._deduplicate_list(extraction_result["context"])
            merged_background_items = self._deduplicate_list(extraction_result["background"])
            
            # Generate article
            cluster_name = clustering_result.cluster_names.get(cluster_id, f"Cluster {cluster_id}")
            
            # Generate different types of content
            factual_summary = await self.ai_generator.generate_factual_summary( #type:ignore
                merged_facts, cluster_name
            )
            
            # Generate context and background paragraphs
            context_paragraph = await self.ai_generator.generate_context_paragraph( #type:ignore
                merged_context_items, cluster_name
            )
            
            background_paragraph = await self.ai_generator.generate_background_paragraph( #type:ignore
                merged_background_items, cluster_name
            )
            
            contextual_analysis = await self.ai_generator.generate_contextual_analysis( #type:ignore
                merged_context_items, merged_background_items, cluster_name
            )
            
            comprehensive_article = await self.ai_generator.generate_comprehensive_article( #type:ignore
                merged_facts, extraction_result["musings"], 
                merged_context_items, merged_background_items, cluster_name
            )
            
            # Get image URL for cluster
            cluster_image_url = None
            if self.image_service:
                cluster_image_url = self.image_service.get_cluster_image_url(
                    cluster_articles, cluster_name
                )
            
            cluster_result = ClusterResult(
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                articles_count=len(cluster_articles),
                facts=merged_facts[:settings.MAX_FACTS_PER_CLUSTER],
                musings=extraction_result["musings"][:settings.MAX_MUSINGS_PER_CLUSTER],
                context=context_paragraph,
                background=background_paragraph,
                generated_article=comprehensive_article,
                factual_summary=factual_summary,
                contextual_analysis=contextual_analysis,
                similarity_scores=similarity_scores,
                image_url=cluster_image_url,  # ✅ This is being set
                sources=unique_sources,  # Add sources
                article_urls=article_urls,  # Add URLs
                source_counts=source_counts  # Add source counts
            )
            
            cluster_results.append(cluster_result)
        
        return cluster_results
        
        return cluster_results
    
    def _deduplicate_list(self, items: List[str]) -> List[str]:
        """Remove duplicate items while preserving order"""
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
