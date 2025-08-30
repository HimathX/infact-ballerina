import ballerina/http;
import ballerina/log;
import ballerina_gateway.utils;
import ballerina_gateway.types;

// News extraction service with comprehensive timeout configuration
service /news on new http:Listener(9090, {
    timeout: 900,  // 15 minutes timeout for the listener
    requestLimits: {
        maxUriLength: 4096,
        maxHeaderSize: 8192,
        maxEntityBodySize: 10485760  // 10MB
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

        // Get all articles endpoint
    resource function get articles(http:Caller caller, http:Request request) returns error? {
        types:NewsArticle[] articles = check utils:getAllNewsArticles();
        
        json response = {
            "status": "success",
            "articles": articles,
            "count": articles.length()
        };
        
        check caller->respond(response);
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
    resource function get .(@http:Query int? 'limit, @http:Query int? skip, 
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
    
    log:printInfo("RSS extraction completed successfully. Inserted: " + response.inserted_count.toString() + ", Skipped: " + response.skipped_count.toString());
}