from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import logging
from dataclasses import dataclass, asdict
import json

from core.database import client, db
from schemas.article import ClusterResult, Article

logger = logging.getLogger(__name__)

@dataclass
class StoredCluster:
    """Data class for stored cluster information"""
    cluster_id: str  # MongoDB ObjectId as string
    cluster_name: str
    keywords: List[str]
    facts: List[str]
    musings: List[str]
    articles_count: int
    created_at: datetime
    updated_at: datetime
    embedding: List[float]  # Cluster centroid embedding
    articles: List[Dict]  # Stored article data
    similarity_threshold: float = 0.7
    generated_article: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for MongoDB storage"""
        return asdict(self)

class ClusterStorageManager:
    """Manages cluster storage, comparison, and merging in MongoDB"""
    
    def __init__(self, similarity_threshold: float = 0.75):
        self.db = db
        self.clusters_collection = db["topic_clusters"]
        self.articles_collection = db["articles"]
        self.similarity_threshold = similarity_threshold
        
        # Create indexes for efficient querying
        self._create_indexes()
        
        # Initialize TF-IDF vectorizer for text comparison
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def _create_indexes(self):
        """Create MongoDB indexes for efficient querying"""
        try:
            # Index on cluster name and creation time
            self.clusters_collection.create_index([("cluster_name", 1)])
            self.clusters_collection.create_index([("created_at", -1)])
            self.clusters_collection.create_index([("keywords", 1)])
            
            # Compound index for recent clusters
            self.clusters_collection.create_index([
                ("created_at", -1), 
                ("articles_count", -1)
            ])
            
            # Index for articles
            self.articles_collection.create_index([("url", 1)], unique=True, sparse=True)
            self.articles_collection.create_index([("title", 1)])
            self.articles_collection.create_index([("source", 1)])
            self.articles_collection.create_index([("published_at", -1)])
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def compute_cluster_embedding(self, cluster_result: ClusterResult, articles: List[Article]) -> List[float]:
        """Compute embedding representation of a cluster"""
        try:
            # Combine all text content from the cluster
            cluster_texts = []
            cluster_texts.extend(cluster_result.facts)
            cluster_texts.extend(cluster_result.musings)
            cluster_texts.append(cluster_result.cluster_name)
            
            # Add article titles and content snippets
            for article in articles:
                cluster_texts.append(article.title)
                # Add first 200 chars of content
                cluster_texts.append(article.content[:200])
            
            # Create TF-IDF representation
            combined_text = " ".join(cluster_texts)
            
            if hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                # Use existing vocabulary
                tfidf_matrix = self.tfidf_vectorizer.transform([combined_text])
            else:
                # Fit on current text (for first time)
                tfidf_matrix = self.tfidf_vectorizer.fit_transform([combined_text])
            
            # Convert to dense array and return as list
            embedding = tfidf_matrix.toarray()[0].tolist() #type:ignore
            return embedding
            
        except Exception as e:
            logger.error(f"Error computing cluster embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1000

    def extract_keywords(self, cluster_result: ClusterResult, articles: List[Article]) -> List[str]:
        """Extract keywords from cluster content"""
        try:
            # Combine text for keyword extraction
            all_text = f"{cluster_result.cluster_name} "
            all_text += " ".join(cluster_result.facts)
            all_text += " ".join([article.title for article in articles])
            
            # Simple keyword extraction (you could use more advanced methods)
            words = all_text.lower().split()
            word_freq = {}
            
            for word in words:
                if len(word) > 3 and word.isalpha():  # Filter short and non-alphabetic words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            return [word for word, freq in keywords]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def find_similar_clusters(self, 
                            new_cluster_embedding: List[float], 
                            keywords: List[str],
                            days_back: int = 7) -> List[Dict]:
        """Find existing clusters similar to the new one"""
        try:
            # Get recent clusters for comparison
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            recent_clusters = list(self.clusters_collection.find({
                "created_at": {"$gte": cutoff_date}
            }))
            
            if not recent_clusters:
                return []
            
            similar_clusters = []
            
            for stored_cluster in recent_clusters:
                try:
                    # Calculate embedding similarity
                    stored_embedding = stored_cluster.get('embedding', [])
                    if not stored_embedding:
                        continue
                    
                    # Ensure same dimensions
                    min_len = min(len(new_cluster_embedding), len(stored_embedding))
                    if min_len == 0:
                        continue
                    
                    new_emb = np.array(new_cluster_embedding[:min_len]).reshape(1, -1)
                    stored_emb = np.array(stored_embedding[:min_len]).reshape(1, -1)
                    
                    embedding_similarity = cosine_similarity(new_emb, stored_emb)[0][0]
                    
                    # Calculate keyword overlap
                    stored_keywords = stored_cluster.get('keywords', [])
                    keyword_overlap = len(set(keywords) & set(stored_keywords)) / max(len(keywords), len(stored_keywords), 1)
                    
                    # Calculate cluster name similarity (simple word overlap)
                    new_name_words = set(stored_cluster.get('cluster_name', '').lower().split())
                    stored_name_words = set(keywords)  # Use keywords as proxy for new cluster name
                    name_similarity = len(new_name_words & stored_name_words) / max(len(new_name_words), len(stored_name_words), 1)
                    
                    # Combined similarity score
                    combined_similarity = (
                        0.5 * embedding_similarity +
                        0.3 * keyword_overlap +
                        0.2 * name_similarity
                    )
                    
                    if combined_similarity >= self.similarity_threshold:
                        similar_clusters.append({
                            'cluster_id': stored_cluster['_id'],
                            'cluster_name': stored_cluster['cluster_name'],
                            'similarity_score': combined_similarity,
                            'embedding_similarity': embedding_similarity,
                            'keyword_overlap': keyword_overlap,
                            'name_similarity': name_similarity,
                            'articles_count': stored_cluster.get('articles_count', 0)
                        })
                
                except Exception as e:
                    logger.warning(f"Error comparing with cluster {stored_cluster.get('_id')}: {e}")
                    continue
            
            # Sort by similarity score
            similar_clusters.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_clusters
            
        except Exception as e:
            logger.error(f"Error finding similar clusters: {e}")
            return []
    
    async def store_or_merge_cluster(self, 
                                   cluster_result: ClusterResult, 
                                   articles: List[Article],
                                   force_new: bool = False) -> Tuple[str, str]:
        """
        Store new cluster or merge with existing similar cluster
        Returns: (cluster_id, action) where action is 'created', 'merged', or 'updated'
        """
        try:
            # First, store individual articles
            article_ids = []
            for article in articles:
                article_id = await self._store_article(article)
                if article_id:
                    article_ids.append(article_id)
            
            # Extract keywords and compute embedding
            keywords = self.extract_keywords(cluster_result, articles)
            embedding = self.compute_cluster_embedding(cluster_result, articles)
            
            if not force_new:
                # Find similar existing clusters
                similar_clusters = self.find_similar_clusters(embedding, keywords)
                
                if similar_clusters:
                    # Merge with the most similar cluster
                    best_match = similar_clusters[0]
                    cluster_id = await self._merge_with_existing_cluster(
                        best_match['cluster_id'],
                        cluster_result,
                        articles,
                        article_ids,
                        keywords,
                        embedding
                    )
                    return str(cluster_id), 'merged'
            
            # Create new cluster
            cluster_id = await self._create_new_cluster(
                cluster_result, 
                articles, 
                article_ids, 
                keywords, 
                embedding
            )
            return str(cluster_id), 'created'
            
        except Exception as e:
            logger.error(f"Error storing cluster: {e}")
            raise
    
    async def _store_article(self, article: Article) -> Optional[str]:
        """Store individual article and return its ID"""
        try:
            article_doc = {
                'title': article.title,
                'content': article.content,
                'source': article.source,
                'published_at': article.published_at,
                'url': article.url,
                'created_at': datetime.now(),
                'content_length': len(article.content),
                'word_count': len(article.content.split())
            }
            
            # Try to insert, handle duplicates
            try:
                result = self.articles_collection.insert_one(article_doc)
                return str(result.inserted_id)
            except DuplicateKeyError:
                # Article already exists, find and return existing ID
                existing = self.articles_collection.find_one({'url': article.url})
                return str(existing['_id']) if existing else None
                
        except Exception as e:
            logger.warning(f"Error storing article: {e}")
            return None
    
    async def _create_new_cluster(self, 
                                cluster_result: ClusterResult,
                                articles: List[Article],
                                article_ids: List[str],
                                keywords: List[str],
                                embedding: List[float]) -> ObjectId:
        """Create a new cluster in the database"""
        
        cluster_doc = {
            'cluster_name': cluster_result.cluster_name,
            'keywords': keywords,
            'facts': cluster_result.facts,
            'musings': cluster_result.musings,
            'generated_article': cluster_result.generated_article,
            'articles_count': len(articles),
            'article_ids': article_ids,
            'embedding': embedding,
            'similarity_scores': cluster_result.similarity_scores,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'sources': list(set([article.source for article in articles if article.source])),
            'date_range': {
                'earliest': min([article.published_at for article in articles if article.published_at], default=None),
                'latest': max([article.published_at for article in articles if article.published_at], default=None)
            }
        }
        
        result = self.clusters_collection.insert_one(cluster_doc)
        logger.info(f"Created new cluster: {cluster_result.cluster_name} with {len(articles)} articles")
        return result.inserted_id
    
    async def _merge_with_existing_cluster(self,
                                         existing_cluster_id: ObjectId,
                                         new_cluster_result: ClusterResult,
                                         new_articles: List[Article],
                                         new_article_ids: List[str],
                                         new_keywords: List[str],
                                         new_embedding: List[float]) -> ObjectId:
        """Merge new cluster data with existing cluster"""
        
        try:
            # Get existing cluster
            existing = self.clusters_collection.find_one({'_id': existing_cluster_id})
            if not existing:
                raise ValueError(f"Existing cluster {existing_cluster_id} not found")
            
            # Merge data
            updated_doc = {
                'facts': list(set(existing.get('facts', []) + new_cluster_result.facts)),
                'musings': list(set(existing.get('musings', []) + new_cluster_result.musings)),
                'keywords': list(set(existing.get('keywords', []) + new_keywords)),
                'articles_count': existing.get('articles_count', 0) + len(new_articles),
                'article_ids': list(set(existing.get('article_ids', []) + new_article_ids)),
                'updated_at': datetime.now(),
                'sources': list(set(existing.get('sources', []) + 
                                  [article.source for article in new_articles if article.source])),
            }
            
            # Update embedding (weighted average)
            existing_embedding = existing.get('embedding', [])
            if existing_embedding and new_embedding:
                existing_weight = existing.get('articles_count', 1)
                new_weight = len(new_articles)
                total_weight = existing_weight + new_weight
                
                # Ensure same dimensions
                min_len = min(len(existing_embedding), len(new_embedding))
                if min_len > 0:
                    weighted_embedding = [
                        (existing_embedding[i] * existing_weight + new_embedding[i] * new_weight) / total_weight
                        for i in range(min_len)
                    ]
                    updated_doc['embedding'] = weighted_embedding
            
            # Update date range
            existing_dates = existing.get('date_range', {})
            new_dates = [article.published_at for article in new_articles if article.published_at]
            
            if new_dates:
                updated_doc['date_range'] = {
                    'earliest': min(filter(None, [existing_dates.get('earliest')] + new_dates)),
                    'latest': max(filter(None, [existing_dates.get('latest')] + new_dates))
                }
            
            # Update the cluster
            self.clusters_collection.update_one(
                {'_id': existing_cluster_id},
                {'$set': updated_doc}
            )
            
            logger.info(f"Merged cluster {existing['cluster_name']} with {len(new_articles)} new articles")
            return existing_cluster_id
            
        except Exception as e:
            logger.error(f"Error merging cluster: {e}")
            raise
    
    def get_recent_clusters(self, days_back: int = 7, limit: int = 50) -> List[Dict]:
        """Get recent clusters from the database"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            clusters = list(self.clusters_collection.find(
                {"created_at": {"$gte": cutoff_date}},
                sort=[("updated_at", -1)],
                limit=limit
            ))
            
            # Convert ObjectId to string for JSON serialization
            for cluster in clusters:
                cluster['_id'] = str(cluster['_id'])
                cluster['article_ids'] = [str(aid) for aid in cluster.get('article_ids', [])]
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error getting recent clusters: {e}")
            return []
    
    def get_cluster_by_id(self, cluster_id: str) -> Optional[Dict]:
        """Get a specific cluster by ID"""
        try:
            cluster = self.clusters_collection.find_one({'_id': ObjectId(cluster_id)})
            if cluster:
                cluster['_id'] = str(cluster['_id'])
                cluster['article_ids'] = [str(aid) for aid in cluster.get('article_ids', [])]
            return cluster
        except Exception as e:
            logger.error(f"Error getting cluster {cluster_id}: {e}")
            return None
    
    def search_clusters(self, query: str, limit: int = 20) -> List[Dict]:
        """Search clusters by keywords or cluster name"""
        try:
            # Text search on cluster name and keywords
            clusters = list(self.clusters_collection.find(
                {
                    "$or": [
                        {"cluster_name": {"$regex": query, "$options": "i"}},
                        {"keywords": {"$in": [query]}},
                        {"facts": {"$elemMatch": {"$regex": query, "$options": "i"}}},
                    ]
                },
                sort=[("updated_at", -1)],
                limit=limit
            ))
            
            # Convert ObjectId to string
            for cluster in clusters:
                cluster['_id'] = str(cluster['_id'])
                cluster['article_ids'] = [str(aid) for aid in cluster.get('article_ids', [])]
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error searching clusters: {e}")
            return []
    
    def get_cluster_statistics(self) -> Dict:
        """Get statistics about stored clusters"""
        try:
            total_clusters = self.clusters_collection.count_documents({})
            total_articles = self.articles_collection.count_documents({})
            
            # Get recent activity
            recent_date = datetime.now() - timedelta(days=7)
            recent_clusters = self.clusters_collection.count_documents({
                "created_at": {"$gte": recent_date}
            })
            
            # Get top sources
            pipeline = [
                {"$unwind": "$sources"},
                {"$group": {"_id": "$sources", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            top_sources = list(self.clusters_collection.aggregate(pipeline))
            
            return {
                "total_clusters": total_clusters,
                "total_articles": total_articles,
                "recent_clusters_7d": recent_clusters,
                "top_sources": top_sources,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cluster statistics: {e}")
            return {}
    
    async def cleanup_old_clusters(self, days_to_keep: int = 30) -> int:
        """Clean up old clusters and articles"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Find old clusters
            old_clusters = self.clusters_collection.find({
                "created_at": {"$lt": cutoff_date}
            })
            
            deleted_count = 0
            for cluster in old_clusters:
                # Optionally delete associated articles
                article_ids = cluster.get('article_ids', [])
                if article_ids:
                    self.articles_collection.delete_many({
                        '_id': {'$in': [ObjectId(aid) for aid in article_ids]}
                    })
                
                # Delete cluster
                self.clusters_collection.delete_one({'_id': cluster['_id']})
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old clusters")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old clusters: {e}")
            return 0