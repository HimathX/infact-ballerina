// Re-export all types from modules for easy access

// Simplified MongoDB cluster document type (let MongoDB handle internal structures)
public type MongoCluster record {|
    json _id; // Let MongoDB handle ObjectId structure automatically
    string cluster_name;
    string[] facts;
    string[] musings;
    string[] keywords;
    string[] sources;
    string[] article_urls;
    json[]? article_ids; // Array of MongoDB ObjectIds as json
    string generated_article;
    string factual_summary;
    string contextual_analysis;
    string? context;
    string? background;
    string? image_url;
    int articles_count;
    json? source_counts; // Key-value pairs as json
    decimal[]? similarity_scores; // Array of decimal/float values
    decimal[]? embedding; // Array of float values (ML embeddings)
    json? created_at; // Let MongoDB handle date structure
    json? updated_at; // Let MongoDB handle date structure
|};

// Core cluster record type (for API responses)
public type Cluster record {|
    string _id;
    string cluster_name;
    string[] facts;
    string[] musings;
    string[] keywords;
    string[] sources;
    string[] article_urls;
    string[]? article_ids; // Array of ObjectId strings
    string generated_article;
    string factual_summary;
    string contextual_analysis;
    string? context;
    string? background;
    string? image_url;
    int articles_count;
    json? source_counts;
    decimal[]? similarity_scores;
    decimal[]? embedding;
    string? created_at;
    string? updated_at;
|};

// Response types
public type ClusterListResponse record {|
    boolean success;
    Cluster[] clusters;
    int total_count;
    string timestamp;
|};

public type SingleClusterResponse record {|
    boolean success;
    Cluster cluster;
    string timestamp;
|};

public type ClusterSearchRequest record {|
    string query;
    int? 'limit;
    string[]? sources;
    string[]? keywords;
|};

public type ClusterSearchResponse record {|
    boolean success;
    Cluster[] clusters;
    int total_results;
    string search_query;
    string timestamp;
|};

public type ClusterArticlesResponse record {|
    boolean success;
    string cluster_id;
    NewsArticle[] articles;
    int total_articles;
    string timestamp;
|};

public type ClusterSummaryResponse record {|
    boolean success;
    string cluster_id;
    ClusterMetrics metrics;
    string timestamp;
|};

public type ClusterMetrics record {|
    int total_articles;
    int total_facts;
    int total_musings;
    int total_keywords;
    int unique_sources;
    string[] top_sources;
    string[] top_keywords;
    string created_date;
    string? last_updated;
    decimal avg_article_length;
    string dominant_source;
|};

public type ClustersBySourceResponse record {|
    boolean success;
    string 'source;
    Cluster[] clusters;
    int total_count;
    string timestamp;
|};

public type ClusterStatsResponse record {|
    boolean success;
    ClusterOverallStats stats;
    string timestamp;
|};

public type ClusterOverallStats record {|
    int total_clusters;
    int total_articles_clustered;
    int avg_articles_per_cluster;
    string[] top_sources;
    string[] trending_keywords;
    int clusters_created_today;
    int clusters_created_this_week;
    string most_active_source;
    decimal avg_facts_per_cluster;
    decimal avg_musings_per_cluster;
|};

public type HealthCheckResponse record {|
    boolean success;
    string status;
    string timestamp;
    HealthMetrics metrics;
|};

public type HealthMetrics record {|
    boolean database_connected;
    int total_clusters;
    int total_articles;
    string last_cluster_created;
    string uptime;
|};

public type TrendingTopicsResponse record {|
    boolean success;
    TrendingTopic[] trending_topics;
    string analysis_period;
    string timestamp;
|};

public type TrendingTopic record {|
    string topic;
    string[] keywords;
    int cluster_count;
    int article_count;
    string[] sources;
    decimal trend_score;
    string trend_direction;
|};

// New response type for top clusters by article count
public type TopClustersResponse record {|
    boolean success;
    Cluster[] clusters;
    int total_clusters;
    string analysis_period;
    int min_articles_threshold;
    string timestamp;
|};

// Weekly digest response type
public type WeeklyDigestResponse record {|
    boolean success;
    string digest_period;
    WeeklyDigestData digest;
    string timestamp;
|};

public type WeeklyDigestData record {|
    int total_clusters;
    int total_articles;
    Cluster[] clusters;
    WeeklyDigestStats stats;
    string[] top_keywords;
    string[] top_sources;
    string summary;
|};

public type WeeklyDigestStats record {|
    int avg_articles_per_cluster;
    int total_facts;
    int total_musings;
    int unique_sources;
    string most_active_source;
    string most_covered_topic;
    decimal avg_cluster_size;
|};

// Internal type for trending analysis processing
public type TopicAnalysis record {|
    string topic;
    string[] keywords;
    int cluster_count;
    int article_count;
    string[] sources;
    decimal trend_score;
    string trend_direction;
|};

public type FullClusterContentResponse record {|
    boolean success;
    string cluster_id;
    Cluster cluster_details;
    NewsArticle[] articles;
    ClusterMetrics metrics;
    string timestamp;
|};

public type DailyDigestResponse record {|
    boolean success;
    string digest_date;
    DailyDigestData digest;
    string timestamp;
|};

public type DailyDigestData record {|
    int clusters_created;
    int articles_processed;
    string[] top_topics;
    string[] active_sources;
    Cluster[] featured_clusters;
    TrendingTopic[] trending_topics;
    string summary;
|};