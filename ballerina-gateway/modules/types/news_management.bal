// Pagination metadata record
public type PaginationInfo record {|
    int total;
    int 'limit;
    int skip;
    boolean has_next;
    boolean has_prev;
|};

// Articles list response with pagination
public type ArticlesListResponse record {|
    boolean success;
    NewsArticle[] articles;
    PaginationInfo pagination;
|};

// Recent articles response
public type RecentArticlesResponse record {|
    boolean success;
    NewsArticle[] articles;
    int total_count;
    int days_back;
    string? source_filter;
|};

// Source statistics record
public type SourceStats record {|
    string 'source;
    int count;
|};

// Article statistics response
public type ArticleStatsResponse record {|
    boolean success;
    int total_articles;
    SourceStats[] articles_by_source;
    int recent_articles_7_days;
|};

// Single article response
public type SingleArticleResponse record {|
    boolean success;
    NewsArticle article;
|};

// Delete article response
public type DeleteArticleResponse record {|
    boolean success;
    string message;
    string article_id;
|};

// Error response record
public type ErrorResponse record {|
    boolean success;
    string message;
    string? error_code;
|};

// Query parameters for articles listing
public type ArticlesQueryParams record {|
    int? 'limit;
    int? skip;
    string? sort_by;
    int? sort_order;
|};

// Query parameters for recent articles
public type RecentArticlesQueryParams record {|
    int? 'limit;
    int? days_back;
    string? 'source;
|};