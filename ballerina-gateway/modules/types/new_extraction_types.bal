import ballerina/time;

// News article record type for storing in MongoDB with required structure
public type NewsArticle record {|
    string? title;           // The headline of the article
    string? content;         // The main content or summary
    string? 'source;         // The news source/publisher
    string? published_at;    // Published time in ISO 8601 format
    string? url;             // Original article URL
    string? image_url;       // Article image URL if available, else null
    string? extracted_at;    // Timestamp when article was extracted/added
|};

// Input article record type for manual feed endpoint
public type InputArticle record {|
    string? title;
    string? content;
    string? 'source;
    string? url;
    string? image_url;
    string? published_at;
|};

// Response record for manual feed endpoint
public type ManualFeedResponse record {|
    string status;
    string[] inserted_titles;
    string[] skipped_titles;
    int inserted_count;
    int skipped_count;
    int total_count;
|};

// RSS extraction request payload record
public type RssExtractionRequest record {|
    time:Date? from_date;
    time:Date? to_date;
    int? max_articles;
    boolean? strip_html;
    boolean? fetch_full_content;
    boolean? remove_duplicates;
    boolean? include_metadata;
    boolean? verbose;
    int? min_content_length;
|};

// RSS extracted article record (from extraction service response)
public type RssExtractedArticle record {|
    string? title;
    string? content;
    string? url;
    string? published_at;
    string? 'source;
    string? image_url;
|};