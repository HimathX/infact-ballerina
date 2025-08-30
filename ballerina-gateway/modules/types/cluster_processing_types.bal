// Article processing request types
public type ProcessingArticle record {|
    string title;
    string content;
    string 'source;
    string published_at;
    string url;
    string? image_url;
|};

public type ArticleProcessingRequest record {|
    ProcessingArticle[] articles;
    int n_clusters;
    boolean store_clusters;
    boolean force_new_clusters;
|};

// Article reference in cluster details
public type ArticleReference record {|
    string article_id;
    string title;
    string 'source;
    string url;
    string published_at;
|};

// Cluster details
public type ClusterDetails record {|
    string[] facts;
    string[] musings;
    string generated_article;
    string factual_summary;
    string contextual_analysis;
    string context;
    string background;
    string[] keywords;
    string[] sources;
    decimal[] similarity_scores;
    string created_at;
    string updated_at;
|};

// Storage result for each cluster
public type StorageResult record {|
    string cluster_id;
    string cluster_name;
    string action; // "created", "merged", or "failed"
    int articles_count;
    string[] article_ids;
    ArticleReference[] article_references;
    ClusterDetails cluster_details;
|};

// Processing summary
public type ProcessingSummary record {|
    int total_articles_processed;
    int total_clusters_created;
    int successful_storage_operations;
    int failed_operations;
    int total_facts_extracted;
    int total_musings_extracted;
    int unique_sources;
    int articles_with_urls;
|};

// Article processing response
public type ArticleProcessingResponse record {|
    boolean success;
    string task_id;
    string status;
    string message;
    int clusters_processed;
    int clusters_stored;
    int clusters_merged;
    StorageResult[] storage_results;
    string timestamp;
    decimal processing_time;
    ProcessingSummary summary;
|};

// Auto processing storage result (simplified)
public type AutoProcessingStorageResult record {|
    string cluster_id;
    string action; // "created" or "merged"
    string articles; // reference_to_articles
|};

// Auto processing response
public type AutoProcessingResponse record {|
    boolean success;
    string task_id;
    int clusters_stored;
    int clusters_merged;
    AutoProcessingStorageResult[] storage_results;
|};

// Error response for cluster processing
public type ClusterProcessingErrorResponse record {|
    boolean success;
    string message;
    string? error_code;
    string? task_id;
|};

// Query parameters for auto processing
public type AutoProcessingQueryParams record {|
    int? n_clusters;
    boolean? force_new_clusters;
    int? days_back;
    int? max_articles;
|};

// Count response type
public type CountResponse record {|
    boolean success;
    int count;
|};