import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from gensim import corpora, models
from core.config import settings

class ArticleClusterer:
    def __init__(self, sentence_model):
        self.sentence_model = sentence_model
    
    def cluster(
        self, 
        embeddings: np.ndarray, 
        processed_texts: List[str], 
        n_clusters: Optional[int] = None
    ) -> Tuple[np.ndarray, Dict[int, str], np.ndarray]:
        """Cluster articles and return cluster assignments with names"""
        
        if n_clusters is None:
            n_clusters = min(
                max(settings.MIN_CLUSTERS, len(processed_texts) // 20), 
                settings.MAX_CLUSTERS
            )
        
        # Ensure we don't have more clusters than articles
        n_clusters = min(n_clusters, len(processed_texts))
        
        try:
            # TF-IDF for feature enhancement
            tfidf = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
            tfidf_features = tfidf.fit_transform(processed_texts).toarray() #type:ignore
            
            # Combine embeddings with TF-IDF
            combined_features = np.hstack([embeddings, tfidf_features * 0.3])
            
            # KMeans clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(combined_features)
            
            # Generate cluster names using LDA
            cluster_names = self._name_clusters_lda(processed_texts, clusters)
            
            # PCA for visualization
            pca = PCA(n_components=2)
            embeddings_2d = pca.fit_transform(embeddings)
            
            return clusters, cluster_names, embeddings_2d
        except Exception as e:
            print(f"Clustering error: {e}")
            # Fallback: assign all to single cluster
            clusters = np.zeros(len(embeddings), dtype=int)
            cluster_names = {0: "General News"}
            embeddings_2d = np.random.rand(len(embeddings), 2)
            return clusters, cluster_names, embeddings_2d
    
    def _name_clusters_lda(self, texts: List[str], clusters: np.ndarray) -> Dict[int, str]:
        """Name clusters using LDA topic modeling"""
        cluster_names = {}
        
        for cluster_id in np.unique(clusters):
            cluster_texts = [texts[i] for i in range(len(texts)) if clusters[i] == cluster_id]
            
            if not cluster_texts:
                cluster_names[cluster_id] = f"Cluster {cluster_id}"
                continue
            
            # Tokenize
            tokenized = [text.split() for text in cluster_texts if text.strip()]
            
            if not tokenized or not any(tokens for tokens in tokenized):
                cluster_names[cluster_id] = f"Cluster {cluster_id}"
                continue
            
            try:
                # Create dictionary and corpus
                dictionary = corpora.Dictionary(tokenized)
                corpus = [dictionary.doc2bow(text) for text in tokenized]
                
                # LDA model
                if len(corpus) > 0 and dictionary.num_docs > 0:
                    lda = models.LdaModel(
                        corpus=corpus,
                        id2word=dictionary,
                        num_topics=1,
                        random_state=42,
                        passes=10,
                        alpha='auto'
                    )
                    
                    # Get top words
                    topics = lda.show_topics(num_topics=1, num_words=5, formatted=False)
                    if topics:
                        words = [word for word, _ in topics[0][1]]
                        cluster_names[cluster_id] = " ".join(words[:3]).title()
                    else:
                        cluster_names[cluster_id] = f"Cluster {cluster_id}"
                else:
                    cluster_names[cluster_id] = f"Cluster {cluster_id}"
            except Exception as e:
                print(f"LDA naming error for cluster {cluster_id}: {e}")
                cluster_names[cluster_id] = f"Cluster {cluster_id}"
        
        return cluster_names
