import ballerina/http;
import ballerina/log;
import ballerina_gateway.types;

// HTTP client for article processing service with 15-minute timeout
final http:Client articleProcessingClient = check new ("http://127.0.0.1:8091", {
    timeout: 900.0,  // 15 minutes timeout
    httpVersion: "1.1"
});

// HTTP client for auto processing service with 15-minute timeout
final http:Client autoProcessingClient = check new ("http://127.0.0.1:8091", {
    timeout: 900.0,  // 15 minutes timeout
    httpVersion: "1.1"
});

// Forward article processing request to Python service - SIMPLIFIED VERSION
public function forwardArticleProcessingRequest(types:ArticleProcessingRequest request) returns types:ArticleProcessingResponse|types:ClusterProcessingErrorResponse|error {
    
    // Manually construct JSON payload to ensure proper format
    json[] articlesJson = [];
    foreach types:ProcessingArticle article in request.articles {
        json articleJson = {
            "title": article.title,
            "content": article.content,
            "source": article.'source,
            "published_at": article.published_at,
            "url": article.url,
            "image_url": article.image_url
        };
        articlesJson.push(articleJson);
    }
    
    json requestPayload = {
        "articles": articlesJson,
        "n_clusters": request.n_clusters,
        "store_clusters": request.store_clusters,
        "force_new_clusters": request.force_new_clusters
    };
    
    log:printInfo("Sending request to Python service", payload_size = requestPayload.toString().length());
    log:printInfo("Request payload preview", payload_preview = requestPayload.toString().substring(0, 200) + "...");
    
    // Use the simpler approach - pass JSON directly with headers
    http:Response|error response = articleProcessingClient->post("/process-with-storage", requestPayload, {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Ballerina-HTTP-Client"
    });
    
    if response is error {
        log:printError("Error calling article processing service", 'error = response);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Article processing service is unavailable: " + response.message(),
            error_code: "SERVICE_UNAVAILABLE",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Log response status for debugging
    log:printInfo("Python service response", status_code = response.statusCode);
    
    // Check HTTP status
    if response.statusCode != 200 {
        json|error errorPayload = response.getJsonPayload();
        string errorMessage = "Article processing failed with status: " + response.statusCode.toString();
        
        if errorPayload is json {
            log:printError("Python service error response", error_payload = errorPayload.toString());
            if errorPayload is map<json> {
                json messageField = errorPayload["message"];
                if messageField is string {
                    errorMessage = messageField;
                } else {
                    json detailField = errorPayload["detail"];
                    if detailField is string {
                        errorMessage = detailField;
                    } else if detailField is json[] {
                        // Handle FastAPI validation errors
                        string[] validationErrors = [];
                        foreach json detail in detailField {
                            if detail is map<json> {
                                json msgField = detail["msg"];
                                json locField = detail["loc"];
                                if msgField is string && locField is json[] {
                                    string location = "";
                                    foreach json loc in locField {
                                        if loc is string {
                                            location += loc + ".";
                                        } else if loc is int {
                                            location += loc.toString() + ".";
                                        }
                                    }
                                    validationErrors.push(location + ": " + msgField);
                                }
                            }
                        }
                        if validationErrors.length() > 0 {
                            errorMessage = "Validation errors: " + string:'join(", ", ...validationErrors);
                        }
                    }
                }
            }
        } else {
            log:printError("Failed to parse error response", parse_error = errorPayload.toString());
        }
        
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: errorMessage,
            error_code: "PROCESSING_FAILED",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Parse successful response
    json|error responsePayload = response.getJsonPayload();
    if responsePayload is error {
        log:printError("Error parsing article processing response", 'error = responsePayload);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Invalid response from processing service",
            error_code: "INVALID_RESPONSE",
            task_id: ()
        };
        return errorResponse;
    }
    
    log:printInfo("Received successful response from Python service", response_size = responsePayload.toString().length());
    
    // Convert JSON response to typed response
    types:ArticleProcessingResponse|error typedResponse = responsePayload.cloneWithType(types:ArticleProcessingResponse);
    if typedResponse is error {
        log:printError("Error converting article processing response", 'error = typedResponse, response = responsePayload.toString());
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Invalid response format from processing service: " + typedResponse.message(),
            error_code: "RESPONSE_FORMAT_ERROR",
            task_id: ()
        };
        return errorResponse;
    }
    
    return typedResponse;
}

// Forward auto processing request to Python service
public function forwardAutoProcessingRequest(types:AutoProcessingQueryParams queryParams) returns types:AutoProcessingResponse|types:ClusterProcessingErrorResponse|error {
    
    // Build query parameters
    map<string> params = {};
    
    if queryParams.n_clusters is int {
        params["n_clusters"] = queryParams.n_clusters.toString();
    }
    
    if queryParams.force_new_clusters is boolean {
        params["force_new_clusters"] = queryParams.force_new_clusters.toString();
    }
    
    if queryParams.days_back is int {
        params["days_back"] = queryParams.days_back.toString();
    }
    
    if queryParams.max_articles is int {
        params["max_articles"] = queryParams.max_articles.toString();
    }
    
    // Build query string
    string queryString = buildClusterQueryString(params);
    string endpoint = "/scrape-process-store" + queryString;
    
    log:printInfo("Calling auto processing endpoint", endpoint = endpoint);
    
    // Use empty JSON object as body for POST request
    json emptyBody = {};
    
    // Forward request to Python service
    http:Response|error response = autoProcessingClient->post(endpoint, emptyBody, {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Ballerina-HTTP-Client"
    });
    
    if response is error {
        log:printError("Error calling auto processing service", 'error = response);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Auto processing service is unavailable: " + response.message(),
            error_code: "SERVICE_UNAVAILABLE",
            task_id: ()
        };
        return errorResponse;
    }
    
    log:printInfo("Auto processing service response", status_code = response.statusCode);
    
    // Check HTTP status
    if response.statusCode != 200 {
        json|error errorPayload = response.getJsonPayload();
        string errorMessage = "Auto processing failed with status: " + response.statusCode.toString();
        
        if errorPayload is json {
            log:printError("Auto processing service error response", error_payload = errorPayload.toString());
            if errorPayload is map<json> {
                json messageField = errorPayload["message"];
                if messageField is string {
                    errorMessage = messageField;
                } else {
                    json detailField = errorPayload["detail"];
                    if detailField is string {
                        errorMessage = detailField;
                    }
                }
            }
        }
        
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: errorMessage,
            error_code: "PROCESSING_FAILED",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Parse successful response
    json|error responsePayload = response.getJsonPayload();
    if responsePayload is error {
        log:printError("Error parsing auto processing response", 'error = responsePayload);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Invalid response from processing service",
            error_code: "INVALID_RESPONSE",
            task_id: ()
        };
        return errorResponse;
    }
    
    log:printInfo("Received successful auto processing response", response_size = responsePayload.toString().length());
    
    // Convert JSON response to typed response
    types:AutoProcessingResponse|error typedResponse = responsePayload.cloneWithType(types:AutoProcessingResponse);
    if typedResponse is error {
        log:printError("Error converting auto processing response", 'error = typedResponse, response = responsePayload.toString());
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Invalid response format from processing service: " + typedResponse.message(),
            error_code: "RESPONSE_FORMAT_ERROR",
            task_id: ()
        };
        return errorResponse;
    }
    
    return typedResponse;
}

// Validate article processing request - Enhanced validation
public isolated function validateArticleProcessingRequest(types:ArticleProcessingRequest request) returns types:ClusterProcessingErrorResponse? {
    
    // Validate articles array
    if request.articles.length() == 0 {
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Articles array cannot be empty",
            error_code: "EMPTY_ARTICLES",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Minimum 2 articles required for clustering
    if request.articles.length() < 2 {
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "At least 2 articles are required for clustering",
            error_code: "INSUFFICIENT_ARTICLES",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Validate n_clusters
    if request.n_clusters < 2 || request.n_clusters > 20 {
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "n_clusters must be between 2 and 20",
            error_code: "INVALID_CLUSTER_COUNT",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Validate each article
    foreach int i in 0 ..< request.articles.length() {
        types:ProcessingArticle article = request.articles[i];
        
        if article.title.trim() == "" {
            types:ClusterProcessingErrorResponse errorResponse = {
                success: false,
                message: string `Article at index ${i} has empty title`,
                error_code: "EMPTY_TITLE",
                task_id: ()
            };
            return errorResponse;
        }
        
        if article.content.trim() == "" {
            types:ClusterProcessingErrorResponse errorResponse = {
                success: false,
                message: string `Article at index ${i} has empty content`,
                error_code: "EMPTY_CONTENT",
                task_id: ()
            };
            return errorResponse;
        }
        
        // Validate content length (minimum 50 characters as per Python service)
        if article.content.trim().length() < 50 {
            types:ClusterProcessingErrorResponse errorResponse = {
                success: false,
                message: string `Article at index ${i} content must be at least 50 characters long`,
                error_code: "CONTENT_TOO_SHORT",
                task_id: ()
            };
            return errorResponse;
        }
        
        if article.'source.trim() == "" {
            types:ClusterProcessingErrorResponse errorResponse = {
                success: false,
                message: string `Article at index ${i} has empty source`,
                error_code: "EMPTY_SOURCE",
                task_id: ()
            };
            return errorResponse;
        }
        
        if article.url.trim() == "" {
            types:ClusterProcessingErrorResponse errorResponse = {
                success: false,
                message: string `Article at index ${i} has empty URL`,
                error_code: "EMPTY_URL",
                task_id: ()
            };
            return errorResponse;
        }
        
        // Validate published_at format if provided
        if article.published_at.trim() != "" {
            // Basic ISO date format validation
            if !isValidISODateFormat(article.published_at) {
                types:ClusterProcessingErrorResponse errorResponse = {
                    success: false,
                    message: string `Article at index ${i} has invalid published_at format. Expected ISO format (e.g., 2025-08-29T14:30:00Z)`,
                    error_code: "INVALID_DATE_FORMAT",
                    task_id: ()
                };
                return errorResponse;
            }
        }
    }
    
    return ();
}

// Helper function to validate ISO date format
isolated function isValidISODateFormat(string dateString) returns boolean {
    // Basic regex pattern for ISO 8601 format
    string:RegExp isoPattern = re `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$`;
    return isoPattern.isFullMatch(dateString);
}

// Validate auto processing query parameters
public isolated function validateAutoProcessingParams(types:AutoProcessingQueryParams queryParams) returns types:ClusterProcessingErrorResponse? {
    
    // Validate n_clusters
    if queryParams.n_clusters is int && (queryParams.n_clusters < 2 || queryParams.n_clusters > 20) {
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "n_clusters must be between 2 and 20",
            error_code: "INVALID_CLUSTER_COUNT",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Validate days_back
    if queryParams.days_back is int && (queryParams.days_back < 1 || queryParams.days_back > 30) {
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "days_back must be between 1 and 30",
            error_code: "INVALID_DAYS_BACK",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Validate max_articles
    if queryParams.max_articles is int && (queryParams.max_articles < 10 || queryParams.max_articles > 10000) {
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "max_articles must be between 10 and 10000",
            error_code: "INVALID_MAX_ARTICLES",
            task_id: ()
        };
        return errorResponse;
    }
    
    return ();
}

// Helper function to build query string
isolated function buildClusterQueryString(map<string> params) returns string {
    string[] pairs = [];
    foreach string key in params.keys() {
        string value = params.get(key);
        pairs.push(key + "=" + value);
    }
    return pairs.length() > 0 ? "?" + string:'join("&", ...pairs) : "";
}