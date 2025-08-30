import asyncio
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from bson import ObjectId
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

from core.database import db, article_collection
from schemas.article import Article, ClusterResult
from schemas.cluster_storage import StoredCluster, SimilarCluster

logger = logging.getLogger(__name__)

class ClusterStorageManager:
    """Manages storage and retrieval of article clusters in MongoDB"""
    
    def __init__(self):
        self.db = db
        self.clusters_collection: Collection = self.db.clusters
        self.articles_collection: Collection = self.db.articles
        
        # Create indexes for better performance
        self._create_indexes()
        
        # Initialize TF-IDF vectorizer for similarity calculations
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Cluster indexes
            self.clusters_collection.create_index([("keywords", 1)])
            self.clusters_collection.create_index([("created_at", DESCENDING)])
            self.clusters_collection.create_index([("updated_at", DESCENDING)])
            self.clusters_collection.create_index([("sources", 1)])
            self.clusters_collection.create_index([("cluster_name", "text"), ("facts", "text")])
            
            # Article indexes
            self.articles_collection.create_index([("cluster_id", 1)])
            self.articles_collection.create_index([("title", "text"), ("content", "text")])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
    
    async def store_or_merge_cluster(
        self,
        cluster_result: ClusterResult,
        articles: List[Article],
        force_new: bool = False
    ) -> Tuple[str, str]:
        """
        Store a new cluster or merge with existing similar cluster
        
        Returns:
            Tuple of (cluster_id, action) where action is 'created', 'merged', or 'updated'
        """
        try:
            # Extract keywords and compute embedding
            keywords = self.extract_keywords(cluster_result, articles)
            embedding = self.compute_cluster_embedding(cluster_result, articles)
            sources = list(set([article.source for article in articles if article.source]))
            
            # Check for similar clusters unless forced to create new
            if not force_new:
                similar_clusters = self.find_similar_clusters(
                    new_cluster_embedding=embedding,
                    keywords=keywords,
                    days_back=7
                )
                
                if similar_clusters:
                    # Merge with most similar cluster
                    most_similar = similar_clusters[0]
                    merged_cluster_id = await self._merge_with_existing_cluster(
                        existing_cluster_id=most_similar['cluster_id'],
                        new_cluster_result=cluster_result,
                        new_articles=articles,
                        new_keywords=keywords,
                        new_embedding=embedding,
                        new_sources=sources
                    )
                    return str(merged_cluster_id), "merged"
            
            # Create new cluster
            cluster_id = await self._create_new_cluster(
                cluster_result=cluster_result,
                articles=articles,
                keywords=keywords,
                embedding=embedding,
                sources=sources
            )
            
            return str(cluster_id), "created"
            
        except Exception as e:
            logger.error(f"Error storing cluster: {e}")
            raise Exception(f"Failed to store cluster: {str(e)}")
    
    async def _create_new_cluster(
        self,
        cluster_result: ClusterResult,
        articles: List[Article],
        keywords: List[str],
        embedding: List[float],
        sources: List[str]
    ) -> ObjectId:
        """Create a new cluster in the database"""
        try:
            # Store articles first and get their IDs
            article_ids = []
            for article in articles:
                article_doc = {
                    "title": article.title,
                    "content": article.content,
                    "source": article.source,
                    "url": article.url,
                    "published_at": article.published_at,
                    "created_at": datetime.now()
                }
                
                # Check if article already exists
                existing = self.articles_collection.find_one({"title": article.title, "source": article.source})
                if existing:
                    article_ids.append(existing["_id"])
                else:
                    result = self.articles_collection.insert_one(article_doc)
                    article_ids.append(result.inserted_id)
            
            # Create cluster document
            article_urls = [article.url for article in articles if article.url]
            
            # Handle embedding conversion safely
            if embedding is not None:
                if isinstance(embedding, np.ndarray):
                    # It's a numpy array
                    embedding_list = embedding.tolist()
                elif isinstance(embedding, list):
                    # It's already a list
                    embedding_list = embedding
                else:
                    # Convert to list if it's another type
                    embedding_list = list(embedding) if embedding is not None else []
            else:
                embedding_list = []
            
            cluster_doc = {
                "_id": ObjectId(),
                "cluster_name": cluster_result.cluster_name,
                "facts": cluster_result.facts,
                "musings": cluster_result.musings,
                "generated_article": cluster_result.generated_article,
                "factual_summary": cluster_result.factual_summary,
                "contextual_analysis": cluster_result.contextual_analysis,
                "context": cluster_result.context,
                "background": cluster_result.background,
                "image_url": cluster_result.image_url,
                "articles_count": cluster_result.articles_count,
                "sources": cluster_result.sources,
                "article_urls": cluster_result.article_urls,
                "article_ids": article_ids,
                "keywords": keywords,
                "embedding": embedding_list,  # Use the safely converted embedding
                "similarity_scores": cluster_result.similarity_scores,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "source_counts": cluster_result.source_counts
            }
            
            result = self.clusters_collection.insert_one(cluster_doc)
            
            # Update articles with cluster reference
            self.articles_collection.update_many(
                {"_id": {"$in": article_ids}},
                {"$set": {"cluster_id": result.inserted_id}}
            )
            
            logger.info(f"Created new cluster with ID: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"Error creating new cluster: {e}")
            raise
    
    async def _merge_with_existing_cluster(
        self,
        existing_cluster_id: str,
        new_cluster_result: ClusterResult,
        new_articles: List[Article],
        new_keywords: List[str],
        new_embedding: List[float],
        new_sources: List[str]
    ) -> str:
        """Merge new cluster data with existing cluster"""
        try:
            existing_cluster = self.clusters_collection.find_one({"_id": ObjectId(existing_cluster_id)})
            if not existing_cluster:
                raise Exception(f"Existing cluster {existing_cluster_id} not found")
            
            # Store new articles
            new_article_ids = []
            for article in new_articles:
                article_doc = {
                    "title": article.title,
                    "content": article.content,
                    "source": article.source,
                    "url": article.url,
                    "published_at": article.published_at,
                    "created_at": datetime.now(),
                    "cluster_id": ObjectId(existing_cluster_id)
                }
                
                # Check for duplicates
                existing_article = self.articles_collection.find_one({
                    "title": article.title,
                    "source": article.source
                })
                
                if not existing_article:
                    result = self.articles_collection.insert_one(article_doc)
                    new_article_ids.append(result.inserted_id)
                else:
                    new_article_ids.append(existing_article["_id"])
            
            # Merge cluster data
            merged_keywords = list(set(existing_cluster.get("keywords", []) + new_keywords))
            merged_facts = list(set(existing_cluster.get("facts", []) + new_cluster_result.facts))
            merged_musings = list(set(existing_cluster.get("musings", []) + new_cluster_result.musings))
            merged_sources = list(set(existing_cluster.get("sources", []) + new_sources))
            merged_article_ids = list(set(existing_cluster.get("article_ids", []) + new_article_ids))
            
            # Merge article URLs
            new_article_urls = [article.url for article in new_articles if article.url]
            merged_article_urls = list(set(existing_cluster.get("article_urls", []) + new_article_urls))
            
            # Compute new embedding (average of existing and new)
            existing_embedding = existing_cluster.get("embedding", [])
            if existing_embedding and len(existing_embedding) == len(new_embedding):
                merged_embedding = [
                    (existing + new) / 2 
                    for existing, new in zip(existing_embedding, new_embedding)
                ]
            else:
                merged_embedding = new_embedding
            
            # Update cluster
            update_doc = {
                "$set": {
                    "keywords": merged_keywords,
                    "facts": merged_facts,
                    "musings": merged_musings,
                    "sources": merged_sources,
                    "articles_count": len(merged_article_ids),
                    "article_ids": merged_article_ids,
                    "article_urls": merged_article_urls,
                    "embedding": merged_embedding,
                    "updated_at": datetime.now()
                }
            }
            
            # Update generated article if new one is longer/better
            if len(new_cluster_result.generated_article) > len(existing_cluster.get("generated_article", "")):
                update_doc["$set"]["generated_article"] = new_cluster_result.generated_article
            
            self.clusters_collection.update_one(
                {"_id": ObjectId(existing_cluster_id)},
                update_doc
            )
            
            logger.info(f"Merged cluster data into existing cluster: {existing_cluster_id}")
            return existing_cluster_id
            
        except Exception as e:
            logger.error(f"Error merging clusters: {e}")
            raise
    
    def extract_keywords(self, cluster_result: ClusterResult, articles: List[Article]) -> List[str]:
        """Extract keywords from cluster and articles"""
        try:
            keywords = set()
            
            # Extract from cluster name
            cluster_words = re.findall(r'\b\w+\b', cluster_result.cluster_name.lower())
            keywords.update([word for word in cluster_words if len(word) > 3])
            
            # Extract from facts
            for fact in cluster_result.facts:
                fact_words = re.findall(r'\b\w+\b', fact.lower())
                keywords.update([word for word in fact_words if len(word) > 4])
            
            # Extract from article titles
            for article in articles:
                title_words = re.findall(r'\b\w+\b', article.title.lower())
                keywords.update([word for word in title_words if len(word) > 3])
            
            # Remove common words
            stop_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other', 'more', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
            
            filtered_keywords = [kw for kw in keywords if kw not in stop_words]
            
            return sorted(filtered_keywords)[:20]  # Return top 20 keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def compute_cluster_embedding(self, cluster_result: ClusterResult, articles: List[Article]) -> List[float]:
        """Compute embedding vector for cluster"""
        try:
            # Combine all text content
            text_content = []
            text_content.append(cluster_result.cluster_name)
            text_content.extend(cluster_result.facts)
            text_content.extend(cluster_result.musings)
            
            for article in articles:
                text_content.append(article.title)
                if article.content:
                    # Take first 500 chars of content to avoid memory issues
                    text_content.append(article.content[:500])
            
            # Combine all text
            combined_text = " ".join(text_content)
            
            # Create TF-IDF embedding
            try:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform([combined_text])
                embedding = tfidf_matrix.toarray()[0].tolist() #type:ignore
            except:
                # Fallback: simple word frequency embedding
                words = re.findall(r'\b\w+\b', combined_text.lower())
                word_freq = {}
                for word in words:
                    if len(word) > 3:
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                # Convert to fixed-size embedding (100 dimensions)
                top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:100]
                embedding = [freq for _, freq in top_words]
                
                # Pad to 100 dimensions
                while len(embedding) < 100:
                    embedding.append(0.0)
                
                embedding = embedding[:100]  # Truncate if needed
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error computing embedding: {e}")
            return [0.0] * 100  # Return zero embedding as fallback
    
    def find_similar_clusters(
        self,
        new_cluster_embedding: List[float],
        keywords: List[str],
        days_back: int = 7,
        similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """Find existing clusters similar to a new cluster"""
        try:
            # Get recent clusters
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_clusters = list(self.clusters_collection.find({
                "created_at": {"$gte": cutoff_date}
            }))
            
            similar_clusters = []
            
            for cluster in recent_clusters:
                similarity_score = 0.0
                
                # Keyword similarity
                cluster_keywords = cluster.get("keywords", [])
                if keywords and cluster_keywords:
                    keyword_overlap = len(set(keywords) & set(cluster_keywords))
                    keyword_similarity = keyword_overlap / max(len(keywords), len(cluster_keywords))
                    similarity_score += keyword_similarity * 0.4
                
                # Embedding similarity
                cluster_embedding = cluster.get("embedding", [])
                if (cluster_embedding and new_cluster_embedding and 
                    len(cluster_embedding) == len(new_cluster_embedding)):
                    try:
                        embedding_similarity = cosine_similarity(
                            np.array([new_cluster_embedding]), np.array([cluster_embedding])
                        )[0][0]
                        similarity_score += embedding_similarity * 0.6
                    except:
                        pass
                
                if similarity_score >= similarity_threshold:
                    similar_clusters.append({
                        "cluster_id": str(cluster["_id"]),
                        "cluster_name": cluster["cluster_name"],
                        "similarity_score": similarity_score,
                        "keywords": cluster_keywords,
                        "articles_count": cluster.get("articles_count", 0),
                        "created_at": cluster["created_at"],
                        "sources": cluster.get("sources", [])
                    })
            
            # Sort by similarity score
            similar_clusters.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return similar_clusters[:5]  # Return top 5 similar clusters
            
        except Exception as e:
            logger.error(f"Error finding similar clusters: {e}")
            return []
    
    def get_cluster_by_id(self, cluster_id: str) -> Optional[Dict]:
        """Get a specific cluster by ID"""
        try:
            cluster = self.clusters_collection.find_one({"_id": ObjectId(cluster_id)})
            if cluster:
                cluster["_id"] = str(cluster["_id"])
                # Convert ObjectIds in article_ids to strings
                if "article_ids" in cluster:
                    cluster["article_ids"] = [str(aid) for aid in cluster["article_ids"]]
            return cluster
        except Exception as e:
            logger.error(f"Error getting cluster by ID: {e}")
            return None
    
    def get_recent_clusters(self, days_back: int = 7, limit: int = 50) -> List[Dict]:
        """Get recently created/updated clusters"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            clusters = list(self.clusters_collection.find({
                "created_at": {"$gte": cutoff_date}
            }).sort("created_at", DESCENDING).limit(limit))
            
            # Convert ObjectIds to strings
            for cluster in clusters:
                cluster["_id"] = str(cluster["_id"])
                if "article_ids" in cluster:
                    cluster["article_ids"] = [str(aid) for aid in cluster["article_ids"]]
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error getting recent clusters: {e}")
            return []
    
    def search_clusters(self, query: str, limit: int = 20) -> List[Dict]:
        """Search clusters by text query"""
        try:
            # Text search on cluster name and facts
            clusters = list(self.clusters_collection.find({
                "$text": {"$search": query}
            }).limit(limit))
            
            # If no text search results, try keyword matching
            if not clusters:
                clusters = list(self.clusters_collection.find({
                    "$or": [
                        {"keywords": {"$regex": query, "$options": "i"}},
                        {"cluster_name": {"$regex": query, "$options": "i"}},
                        {"sources": {"$regex": query, "$options": "i"}}
                    ]
                }).limit(limit))
            
            # Convert ObjectIds to strings
            for cluster in clusters:
                cluster["_id"] = str(cluster["_id"])
                if "article_ids" in cluster:
                    cluster["article_ids"] = [str(aid) for aid in cluster["article_ids"]]
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error searching clusters: {e}")
            return []
    
    def get_cluster_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about stored clusters"""
        try:
            # Basic counts
            total_clusters = self.clusters_collection.count_documents({})
            total_articles = self.articles_collection.count_documents({})
            
            # Clusters by source
            source_pipeline = [
                {"$unwind": "$sources"},
                {"$group": {"_id": "$sources", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            clusters_by_source = list(self.clusters_collection.aggregate(source_pipeline))
            
            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_clusters = self.clusters_collection.count_documents({
                "created_at": {"$gte": week_ago}
            })
            
            # Average cluster size
            avg_size_pipeline = [
                {"$group": {"_id": None, "avg_size": {"$avg": "$articles_count"}}}
            ]
            avg_result = list(self.clusters_collection.aggregate(avg_size_pipeline))
            avg_cluster_size = avg_result[0]["avg_size"] if avg_result else 0
            
            # Largest cluster
            largest_cluster = self.clusters_collection.find_one(
                sort=[("articles_count", DESCENDING)]
            )
            
            # Top keywords
            keyword_pipeline = [
                {"$unwind": "$keywords"},
                {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            top_keywords = list(self.clusters_collection.aggregate(keyword_pipeline))
            
            return {
                "total_clusters": total_clusters,
                "total_articles": total_articles,
                "recent_clusters_7_days": recent_clusters,
                "average_cluster_size": round(avg_cluster_size, 2),
                "clusters_by_source": clusters_by_source,
                "top_keywords": top_keywords,
                "largest_cluster": {
                    "name": largest_cluster.get("cluster_name", "") if largest_cluster else "",
                    "articles_count": largest_cluster.get("articles_count", 0) if largest_cluster else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cluster statistics: {e}")
            return {}
    
    async def cleanup_old_clusters(self, days_to_keep: int = 30) -> int:
        """Clean up old clusters and articles"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Get clusters to delete
            old_clusters = list(self.clusters_collection.find({
                "created_at": {"$lt": cutoff_date}
            }))
            
            deleted_count = 0
            
            for cluster in old_clusters:
                # Delete associated articles
                self.articles_collection.delete_many({
                    "cluster_id": cluster["_id"]
                })
                
                # Delete cluster
                self.clusters_collection.delete_one({"_id": cluster["_id"]})
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old clusters")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
