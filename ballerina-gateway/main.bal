import ballerina_gateway.types;
import ballerina_gateway.utils;

import ballerina/http;
import ballerina/log;

// News extraction service with comprehensive timeout configuration
service /news on new http:Listener(9090, {
    timeout: 900, // 15 minutes timeout for the listener
    requestLimits: {
        maxUriLength: 4096,
        maxHeaderSize: 8192,
        maxEntityBodySize: 10485760 // 10MB
    }
}) {

    resource function post process\-with\-storage(@http:Payload types:ArticleProcessingRequest request) returns types:ArticleProcessingResponse|types:ClusterProcessingErrorResponse {
        do {
            // Validate request
            types:ClusterProcessingErrorResponse? validationError = utils:validateArticleProcessingRequest(request);
            if validationError is types:ClusterProcessingErrorResponse {
                return validationError;
            }

            // Forward request to Python service
            types:ArticleProcessingResponse|types:ClusterProcessingErrorResponse|error result = utils:forwardArticleProcessingRequest(request);
            if result is error {
                types:ClusterProcessingErrorResponse errorResponse = {
                    success: false,
                    message: "Internal server error during article processing",
                    error_code: "INTERNAL_ERROR",
                    task_id: ()
                };
                return errorResponse;
            }
            return result;

        } on fail error e {
            log:printError("Error in article processing", 'error = e);
            types:ClusterProcessingErrorResponse errorResponse = {
                success: false,
                message: "Internal server error during article processing",
                error_code: "INTERNAL_ERROR",
                task_id: ()
            };
            return errorResponse;
        }
    }

    // Auto processing endpoint
    resource function post scrape\-process\-store(int? n_clusters = (), boolean? force_new_clusters = (), int? days_back = (), int? max_articles = ()) returns types:AutoProcessingResponse|types:ClusterProcessingErrorResponse {
        do {
            // Build query parameters
            types:AutoProcessingQueryParams queryParams = {
                n_clusters: n_clusters,
                force_new_clusters: force_new_clusters,
                days_back: days_back,
                max_articles: max_articles
            };

            // Validate parameters
            types:ClusterProcessingErrorResponse? validationError = utils:validateAutoProcessingParams(queryParams);
            if validationError is types:ClusterProcessingErrorResponse {
                return validationError;
            }

            // Forward request to Python service
            types:AutoProcessingResponse|types:ClusterProcessingErrorResponse|error result = utils:forwardAutoProcessingRequest(queryParams);
            if result is error {
                types:ClusterProcessingErrorResponse errorResponse = {
                    success: false,
                    message: "Internal server error during auto processing",
                    error_code: "INTERNAL_ERROR",
                    task_id: ()
                };
                return errorResponse;
            }
            return result;

        } on fail error e {
            log:printError("Error in auto processing", 'error = e);
            types:ClusterProcessingErrorResponse errorResponse = {
                success: false,
                message: "Internal server error during auto processing",
                error_code: "INTERNAL_ERROR",
                task_id: ()
            };
            return errorResponse;
        }
    }

    // Endpoint to fetch articles from News API
    resource function post fetchArticles(http:Caller caller, http:Request request) returns error? {
        json payload = check request.getJsonPayload();

        string? query = utils:extractStringField(payload, "query");
        int? pageSize = utils:extractIntField(payload, "pageSize");
        int finalPageSize = pageSize ?: 20;

        types:NewsArticle[] articles = check utils:fetchAndStoreArticles(query = query, pageSize = finalPageSize);

        json response = {
            "status": "success",
            "message": "Articles fetched and stored successfully",
            "count": articles.length()
        };

        check caller->respond(response);
    }

    // Manual feed endpoint to accept articles and check for duplicates
    resource function post 'feed\-manual(@http:Payload json? payload) returns json|error {
        if payload is () {
            return error("Payload is required");
        }

        json articlesJson = check payload.articles;
        json[] articleArray = check articlesJson.ensureType();

        types:ManualFeedResponse response = check utils:processManualFeedArticles(articleArray);
        return response;
    }

    // RSS extraction endpoint - Enhanced version with comprehensive timeout handling
    resource function post 'rss\-extract(http:Caller caller, http:Request request) returns error? {
        json|error payloadResult = request.getJsonPayload();
        if payloadResult is error {
            json errorResponse = {
                "status": "error",
                "message": "Invalid JSON payload",
                "error_code": "INVALID_PAYLOAD"
            };
            check caller->respond(errorResponse);
            return;
        }

        json payload = payloadResult;

        // Extract fields from JSON payload with defaults
        string fromDate = utils:extractStringField(payload, "from_date") ?: "2025-08-22";
        string toDate = utils:extractStringField(payload, "to_date") ?: "2025-08-24";
        int maxArticles = utils:extractIntField(payload, "max_articles") ?: 10;
        boolean stripHtml = utils:extractBooleanField(payload, "strip_html") ?: true;
        boolean fetchFullContent = utils:extractBooleanField(payload, "fetch_full_content") ?: true;
        boolean removeDuplicates = utils:extractBooleanField(payload, "remove_duplicates") ?: true;
        boolean includeMetadata = utils:extractBooleanField(payload, "include_metadata") ?: true;
        boolean verbose = utils:extractBooleanField(payload, "verbose") ?: false;
        int minContentLength = utils:extractIntField(payload, "min_content_length") ?: 50;

        // Build request for FastAPI service
        json requestBody = {
            "from_date": fromDate,
            "to_date": toDate,
            "max_articles": maxArticles,
            "strip_html": stripHtml,
            "fetch_full_content": fetchFullContent,
            "remove_duplicates": removeDuplicates,
            "include_metadata": includeMetadata,
            "verbose": verbose,
            "min_content_length": minContentLength
        };

        // Send immediate acknowledgment to client
        json acknowledgmentResponse = {
            "status": "processing",
            "message": "RSS extraction started. This may take several minutes.",
            "request_params": {
                "from_date": fromDate,
                "to_date": toDate,
                "max_articles": maxArticles
            }
        };
        check caller->respond(acknowledgmentResponse);

        // Process RSS extraction in background (fire and forget)
        _ = start processRssExtractionAsync(requestBody);
    }

    // Get article count endpoint
    resource function get count(http:Caller caller, http:Request request) returns error? {
        int count = check utils:countNewsArticles();

        json response = {
            "status": "success",
            "count": count
        };

        check caller->respond(response);
    }

    // GET /articles - List extracted articles with pagination and sorting
    resource function get articles(@http:Query int? 'limit, @http:Query int? skip,
            @http:Query string? sort_by, @http:Query int? sort_order)
                            returns types:ArticlesListResponse|types:ErrorResponse|http:InternalServerError {

        // Set defaults
        int finalLimit = 'limit ?: 20;
        int finalSkip = skip ?: 0;
        string finalSortBy = sort_by ?: "extracted_at";
        int finalSortOrder = sort_order ?: -1;

        // Validate query parameters
        types:ErrorResponse? validationError = utils:validateArticlesQueryParams('limit, skip, sort_by, sort_order);
        if validationError is types:ErrorResponse {
            return validationError;
        }

        // Get articles with pagination
        types:ArticlesListResponse|error result = utils:getArticlesWithPagination(
                'limit = finalLimit,
                skip = finalSkip,
                sortBy = finalSortBy,
                sortOrder = finalSortOrder
        );

        if result is error {
            log:printError("Error fetching articles", result);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Internal server error while fetching articles",
                    error_code: "INTERNAL_ERROR"
                }
            };
        }

        return result;
    }

    // GET /articles/recent - Get recent articles
    resource function get recent(@http:Query int? 'limit, @http:Query int? days_back,
            @http:Query string? 'source)
                                returns types:RecentArticlesResponse|types:ErrorResponse|http:InternalServerError {

        // Set defaults
        int finalLimit = 'limit ?: 20;
        int finalDaysBack = days_back ?: 7;

        // Validate query parameters
        types:ErrorResponse? validationError = utils:validateRecentArticlesQueryParams('limit, days_back);
        if validationError is types:ErrorResponse {
            return validationError;
        }

        // Get recent articles
        types:RecentArticlesResponse|error result = utils:getRecentArticles(
                'limit = finalLimit,
                daysBack = finalDaysBack,
                sourceFilter = 'source
        );

        if result is error {
            log:printError("Error fetching recent articles", result);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Internal server error while fetching recent articles",
                    error_code: "INTERNAL_ERROR"
                }
            };
        }

        return result;
    }

    // GET /articles/stats - Get article statistics
    resource function get stats() returns types:ArticleStatsResponse|http:InternalServerError {

        types:ArticleStatsResponse|error result = utils:getArticleStats();

        if result is error {
            log:printError("Error fetching article statistics", result);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Internal server error while fetching statistics",
                    error_code: "INTERNAL_ERROR"
                }
            };
        }

        return result;
    }

    // GET /articles/{article_id} - Get specific article by MongoDB ObjectId
    resource function get [string article_id]() returns types:SingleArticleResponse|types:ErrorResponse|http:NotFound|http:InternalServerError {

        types:SingleArticleResponse|types:ErrorResponse|error result = utils:getArticleById(article_id);

        if result is error {
            log:printError("Error fetching article by ID", result);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Internal server error while fetching article",
                    error_code: "INTERNAL_ERROR"
                }
            };
        }

        if result is types:ErrorResponse {
            if result.error_code == "ARTICLE_NOT_FOUND" {
                return <http:NotFound>{
                    body: result
                };
            }
            return result;
        }

        return result;
    }

    // DELETE /articles/{article_id} - Delete specific article
    resource function delete [string article_id]() returns types:DeleteArticleResponse|types:ErrorResponse|http:NotFound|http:InternalServerError {

        types:DeleteArticleResponse|types:ErrorResponse|error result = utils:deleteArticleById(article_id);

        if result is error {
            log:printError("Error deleting article by ID", result);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Internal server error while deleting article",
                    error_code: "INTERNAL_ERROR"
                }
            };
        }

        if result is types:ErrorResponse {
            if result.error_code == "ARTICLE_NOT_FOUND" {
                return <http:NotFound>{
                    body: result
                };
            }
            return result;
        }

        return result;
    }

    // Get all clusters endpoint
    resource function get allClusters(int? 'limit = 20, int? skip = 0, string? sort_by = "created_at", int? sort_order = -1) returns types:ClusterListResponse|types:ErrorResponse|http:InternalServerError {
        // Validate parameters
        types:ErrorResponse? validationError = utils:validateAllClustersParams('limit = 'limit, skip = skip, sortBy = sort_by, sortOrder = sort_order);
        if validationError is types:ErrorResponse {
            return validationError;
        }

        // Use provided values or defaults
        int limitValue = 'limit ?: 20;
        int skipValue = skip ?: 0;
        string sortByValue = sort_by ?: "created_at";
        int sortOrderValue = sort_order ?: -1;

        types:ClusterListResponse|error result = utils:getAllClusters(
                'limit = limitValue,
                skip = skipValue,
                sortBy = sortByValue,
                sortOrder = sortOrderValue
        );

        if result is error {
            log:printError("Error getting all clusters", 'error = result);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Failed to retrieve clusters: " + result.message(),
                    error_code: "RETRIEVAL_FAILED"
                }
            };
        }

        return result;
    }

    // Get specific cluster by ID
    resource function get clusters/[string cluster_id]() returns types:SingleClusterResponse|types:ErrorResponse|http:InternalServerError {
        // Validate cluster ID
        types:ErrorResponse? validationError = utils:validateClusterId(clusterId = cluster_id);
        if validationError is types:ErrorResponse {
            return validationError;
        }

        types:SingleClusterResponse|error result = utils:getClusterById(clusterId = cluster_id);

        if result is error {
            log:printError("Error getting cluster by ID", 'error = result, cluster_id = cluster_id);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Failed to retrieve cluster: " + result.message(),
                    error_code: "RETRIEVAL_FAILED"
                }
            };
        }

        return result;
    }

    // Get articles belonging to a specific cluster
    resource function get clusters/[string cluster_id]/articles(string? sort_by = "published_at", int? sort_order = -1) returns types:ClusterArticlesResponse|types:ErrorResponse|http:InternalServerError {
        // Validate cluster ID
        types:ErrorResponse? clusterValidationError = utils:validateClusterId(clusterId = cluster_id);
        if clusterValidationError is types:ErrorResponse {
            return clusterValidationError;
        }

        // Validate article sorting parameters
        types:ErrorResponse? sortValidationError = utils:validateArticleSortParams(sortBy = sort_by, sortOrder = sort_order);
        if sortValidationError is types:ErrorResponse {
            return sortValidationError;
        }

        // Use provided values or defaults
        string sortByValue = sort_by ?: "published_at";
        int sortOrderValue = sort_order ?: -1;

        types:ClusterArticlesResponse|error result = utils:getClusterArticles(
                clusterId = cluster_id,
                sortBy = sortByValue,
                sortOrder = sortOrderValue
        );

        if result is error {
            log:printError("Error getting cluster articles", 'error = result, cluster_id = cluster_id);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Failed to retrieve cluster articles: " + result.message(),
                    error_code: "CLUSTER_ARTICLES_RETRIEVAL_FAILED"
                }
            };
        }

        return result;
    }

    // Search clusters by query
    resource function post search(@http:Payload types:ClusterSearchRequest searchRequest) returns types:ClusterSearchResponse|types:ErrorResponse|http:InternalServerError {
        // Validate search request
        types:ErrorResponse? validationError = utils:validateClusterSearchRequest(searchRequest = searchRequest);
        if validationError is types:ErrorResponse {
            return validationError;
        }

        types:ClusterSearchResponse|error result = utils:searchClusters(searchRequest = searchRequest);

        if result is error {
            log:printError("Error searching clusters", 'error = result, query = searchRequest.query);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Failed to search clusters: " + result.message(),
                    error_code: "SEARCH_FAILED"
                }
            };
        }

        return result;
    }

    // Get clusters with highest article counts
    resource function get trending\-topics(int? days_back = (), int? min_articles = 1) returns types:TopClustersResponse|types:ErrorResponse|http:InternalServerError {
        // Validate trending topics parameters
        types:ErrorResponse? validationError = utils:validateTrendingTopicsParams(daysBack = days_back, minArticles = min_articles);
        if validationError is types:ErrorResponse {
            return validationError;
        }

        // Use provided values or defaults
        int minArticlesValue = min_articles ?: 1;

        types:TopClustersResponse|error result = utils:getTopClustersByArticleCount(
                daysBack = days_back,
                minArticles = minArticlesValue
        );

        if result is error {
            log:printError("Error getting top clusters by article count", 'error = result, days_back = days_back, min_articles = minArticlesValue);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Failed to retrieve top clusters: " + result.message(),
                    error_code: "TOP_CLUSTERS_RETRIEVAL_FAILED"
                }
            };
        }

        return result;
    }

    // Get weekly digest of all clusters from the last 7 days
    resource function get weekly\-digest() returns types:WeeklyDigestResponse|types:ErrorResponse|http:InternalServerError {
        types:WeeklyDigestResponse|error result = utils:getWeeklyDigest();

        if result is error {
            log:printError("Error getting weekly digest", 'error = result);
            return <http:InternalServerError>{
                body: {
                    success: false,
                    message: "Failed to retrieve weekly digest: " + result.message(),
                    error_code: "WEEKLY_DIGEST_RETRIEVAL_FAILED"
                }
            };
        }

        return result;
    }
}

// Async function to process RSS extraction without blocking the main thread
function processRssExtractionAsync(json requestBody) {
    json|error extractionResponse = utils:callRssExtractionService(requestBody);

    if extractionResponse is error {
        log:printError("RSS extraction failed", extractionResponse);
        return;
    }

    // Convert response to article array
    json[]|error articleArray = extractionResponse.ensureType();

    if articleArray is error {
        log:printError("Invalid response format from RSS extraction service", articleArray);
        return;
    }

    // Process articles with duplicate checking
    types:ManualFeedResponse|error response = utils:processRssExtractedArticles(articleArray);

    if response is error {
        log:printError("Failed to process extracted articles", response);
        return;
    }

}
