import ballerina/time;
import ballerinax/mongodb;
import ballerina_gateway.types;
import ballerina_gateway.config;

// Get articles with pagination and sorting
public function getArticlesWithPagination(int 'limit = 20, int skip = 0, string sortBy = "extracted_at", int sortOrder = -1) returns types:ArticlesListResponse|error {
    mongodb:Collection newsCollection = check config:getNewsCollection();
    
    // Get total count first
    int totalCount = check newsCollection->countDocuments();
    
    // Create sort document
    map<json> sortDoc = {[sortBy]: sortOrder};
    
    // Create FindOptions with sort, limit, and skip
    mongodb:FindOptions findOptions = {
        sort: sortDoc,
        'limit: 'limit,
        skip: skip
    };
    
    // Use find with FindOptions
    stream<types:NewsArticle, error?> articleStream = check newsCollection->find(
        targetType = types:NewsArticle,
        findOptions = findOptions
    );
    
    // Convert stream to array
    types:NewsArticle[] articles = [];
    record {| types:NewsArticle value; |}? streamResult = check articleStream.next();
    while streamResult is record {| types:NewsArticle value; |} {
        articles.push(streamResult.value);
        streamResult = check articleStream.next();
    }
    check articleStream.close();
    
    // Build pagination info
    types:PaginationInfo paginationInfo = {
        total: totalCount,
        'limit: 'limit,
        skip: skip,
        has_next: (skip + 'limit) < totalCount,
        has_prev: skip > 0
    };
    
    return {
        success: true,
        articles: articles,
        pagination: paginationInfo
    };
}

// Get recent articles within specified days
public function getRecentArticles(int 'limit = 20, int daysBack = 7, string? sourceFilter = ()) returns types:RecentArticlesResponse|error {
    mongodb:Collection newsCollection = check config:getNewsCollection();
    
    // Calculate date threshold
    time:Utc currentTime = time:utcNow();
    time:Seconds secondsToSubtract = <time:Seconds>(daysBack * 24 * 60 * 60);
    time:Utc thresholdTime = time:utcAddSeconds(currentTime, -secondsToSubtract);
    string thresholdTimeString = time:utcToString(thresholdTime);
    
    // Build filter
    map<json> queryFilter = {
        "extracted_at": {
            "$gte": thresholdTimeString
        }
    };
    
    // Add source filter if provided
    if sourceFilter is string {
        queryFilter["source"] = sourceFilter;
    }
    
    // Get total count with filter first
    int totalCount = check newsCollection->countDocuments(filter = queryFilter);
    
    // Create sort document
    map<json> sortDoc = {"extracted_at": -1};
    
    // Create FindOptions with sort and limit
    mongodb:FindOptions findOptions = {
        sort: sortDoc,
        'limit: 'limit
    };
    
    // Use find with filter and FindOptions
    stream<types:NewsArticle, error?> articleStream = check newsCollection->find(
        filter = queryFilter,
        targetType = types:NewsArticle,
        findOptions = findOptions
    );
    
    // Convert stream to array
    types:NewsArticle[] articles = [];
    record {| types:NewsArticle value; |}? streamResult = check articleStream.next();
    while streamResult is record {| types:NewsArticle value; |} {
        articles.push(streamResult.value);
        streamResult = check articleStream.next();
    }
    check articleStream.close();
    
    return {
        success: true,
        articles: articles,
        total_count: totalCount,
        days_back: daysBack,
        source_filter: sourceFilter
    };
}

// Get article statistics using aggregation with proper null handling
public function getArticleStats() returns types:ArticleStatsResponse|error {
    mongodb:Collection newsCollection = check config:getNewsCollection();
    
    // Get total articles count
    int totalArticles = check newsCollection->countDocuments();
    
    // Get articles by source using aggregation with null handling
    map<json>[] sourceAggregationPipeline = [
        {
            "$group": {
                "_id": {
                    "$ifNull": ["$source", "Unknown"]
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "source": "$_id",
                "count": "$count"
            }
        },
        {
            "$sort": {"count": -1}
        }
    ];
    
    stream<json, error?> sourceStatsStream = check newsCollection->aggregate(sourceAggregationPipeline);
    
    // Convert aggregation stream to array
    json[] sourceStatsJson = [];
    record {| json value; |}? streamResult = check sourceStatsStream.next();
    while streamResult is record {| json value; |} {
        sourceStatsJson.push(streamResult.value);
        streamResult = check sourceStatsStream.next();
    }
    check sourceStatsStream.close();
    
    types:SourceStats[] sourceStats = [];
    foreach json statJson in sourceStatsJson {
        types:SourceStats sourceStat = check statJson.cloneWithType(types:SourceStats);
        sourceStats.push(sourceStat);
    }
    
    // Get recent articles count (last 7 days)
    time:Utc currentTime = time:utcNow();
    time:Seconds sevenDaysInSeconds = <time:Seconds>(7 * 24 * 60 * 60);
    time:Utc sevenDaysAgo = time:utcAddSeconds(currentTime, -sevenDaysInSeconds);
    string sevenDaysAgoString = time:utcToString(sevenDaysAgo);
    
    map<json> recentFilter = {
        "extracted_at": {
            "$gte": sevenDaysAgoString
        }
    };
    
    int recentArticlesCount = check newsCollection->countDocuments(filter = recentFilter);
    
    return {
        success: true,
        total_articles: totalArticles,
        articles_by_source: sourceStats,
        recent_articles_7_days: recentArticlesCount
    };
}

// Get single article by ObjectId
public function getArticleById(string articleId) returns types:SingleArticleResponse|types:ErrorResponse|error {
    // Validate ObjectId format
    if !isValidObjectId(articleId) {
        return {
            success: false,
            message: "Invalid article ID format",
            error_code: "INVALID_OBJECT_ID"
        };
    }
    
    mongodb:Collection newsCollection = check config:getNewsCollection();
    
    map<json> queryFilter = {
        "_id": {"$oid": articleId}
    };
    
    stream<types:NewsArticle, error?> articleStream = check newsCollection->find(
        filter = queryFilter, 
        targetType = types:NewsArticle
    );
    
    // Convert stream to array
    types:NewsArticle[] articles = [];
    record {| types:NewsArticle value; |}? streamResult = check articleStream.next();
    while streamResult is record {| types:NewsArticle value; |} {
        articles.push(streamResult.value);
        streamResult = check articleStream.next();
    }
    check articleStream.close();
    
    if articles.length() == 0 {
        return {
            success: false,
            message: "Article not found",
            error_code: "ARTICLE_NOT_FOUND"
        };
    }
    
    return {
        success: true,
        article: articles[0]
    };
}

// Delete article by ObjectId
public function deleteArticleById(string articleId) returns types:DeleteArticleResponse|types:ErrorResponse|error {
    // Validate ObjectId format
    if !isValidObjectId(articleId) {
        return {
            success: false,
            message: "Invalid article ID format",
            error_code: "INVALID_OBJECT_ID"
        };
    }
    
    mongodb:Collection newsCollection = check config:getNewsCollection();
    
    map<json> queryFilter = {
        "_id": {"$oid": articleId}
    };
    
    // Check if article exists before deletion
    int existingCount = check newsCollection->countDocuments(filter = queryFilter);
    if existingCount == 0 {
        return {
            success: false,
            message: "Article not found",
            error_code: "ARTICLE_NOT_FOUND"
        };
    }
    
    // Delete the article
    mongodb:DeleteResult deleteResult = check newsCollection->deleteOne(filter = queryFilter);
    
    if deleteResult.deletedCount > 0 {
        return {
            success: true,
            message: "Article deleted successfully",
            article_id: articleId
        };
    } else {
        return {
            success: false,
            message: "Failed to delete article",
            error_code: "DELETE_FAILED"
        };
    }
}

// Validate ObjectId format (basic validation)
function isValidObjectId(string objectId) returns boolean {
    // MongoDB ObjectId is 24 characters long and contains only hexadecimal characters
    if objectId.length() != 24 {
        return false;
    }
    
    // Check if all characters are hexadecimal
    string:RegExp hexPattern = re `^[0-9a-fA-F]+$`;
    return hexPattern.isFullMatch(objectId);
}

// Validate query parameters for articles listing
public function validateArticlesQueryParams(int? 'limit, int? skip, string? sort_by, int? sort_order) returns types:ErrorResponse? {
    // Validate limit
    if 'limit is int && ('limit < 1 || 'limit > 200) {
        return {
            success: false,
            message: "Limit must be between 1 and 200",
            error_code: "INVALID_LIMIT"
        };
    }
    
    // Validate skip
    if skip is int && skip < 0 {
        return {
            success: false,
            message: "Skip must be greater than or equal to 0",
            error_code: "INVALID_SKIP"
        };
    }
    
    // Validate sort order
    if sort_order is int && (sort_order != 1 && sort_order != -1) {
        return {
            success: false,
            message: "Sort order must be 1 (ascending) or -1 (descending)",
            error_code: "INVALID_SORT_ORDER"
        };
    }
    
    return ();
}

// Validate query parameters for recent articles
public function validateRecentArticlesQueryParams(int? 'limit, int? days_back) returns types:ErrorResponse? {
    // Validate limit
    if 'limit is int && ('limit < 1 || 'limit > 200) {
        return {
            success: false,
            message: "Limit must be between 1 and 200",
            error_code: "INVALID_LIMIT"
        };
    }
    
    // Validate days back
    if days_back is int && (days_back < 1 || days_back > 30) {
        return {
            success: false,
            message: "Days back must be between 1 and 30",
            error_code: "INVALID_DAYS_BACK"
        };
    }
    
    return ();
}