import ballerina/http;
import ballerina/log;
import ballerina_gateway.types;

// HTTP client for article processing service with 15-minute timeout - Made isolated
final http:Client articleProcessingClient = check new ("http://127.0.0.1:8091", {
    timeout: 9000.0  // 15 minutes timeout
});

// HTTP client for auto processing service with 15-minute timeout - Made isolated
final http:Client autoProcessingClient = check new ("http://127.0.0.1:8091", {
    timeout: 9000.0  // 15 minutes timeout
});

// Forward article processing request to Python service - Removed isolated due to HTTP client access
public function forwardArticleProcessingRequest(types:ArticleProcessingRequest request) returns types:ArticleProcessingResponse|types:ClusterProcessingErrorResponse|error {
    
    // Convert request to JSON for forwarding
    json requestPayload = request.toJson();
    
    // Forward request to Python service
    http:Response|error response = articleProcessingClient->post("/process-with-storage", requestPayload, 
        headers = {"Content-Type": "application/json"});
    
    if response is error {
        log:printError("Error calling article processing service", 'error = response);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Article processing service is unavailable",
            error_code: "SERVICE_UNAVAILABLE",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Check HTTP status
    if response.statusCode != 200 {
        json|error errorPayload = response.getJsonPayload();
        string errorMessage = "Article processing failed";
        
        if errorPayload is json && errorPayload is map<json> {
            json messageField = errorPayload["message"];
            if messageField is string {
                errorMessage = messageField;
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
        log:printError("Error parsing article processing response", 'error = responsePayload);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Invalid response from processing service",
            error_code: "INVALID_RESPONSE",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Convert JSON response to typed response
    types:ArticleProcessingResponse|error typedResponse = responsePayload.cloneWithType(types:ArticleProcessingResponse);
    if typedResponse is error {
        log:printError("Error converting article processing response", 'error = typedResponse);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Invalid response format from processing service",
            error_code: "RESPONSE_FORMAT_ERROR",
            task_id: ()
        };
        return errorResponse;
    }
    
    return typedResponse;
}

// Forward auto processing request to Python service - Removed isolated due to HTTP client access
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
    
    // Forward request to Python service
    http:Response|error response = autoProcessingClient->post(endpoint, {}, 
        headers = {"Content-Type": "application/json"});
    
    if response is error {
        log:printError("Error calling auto processing service", 'error = response);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Auto processing service is unavailable",
            error_code: "SERVICE_UNAVAILABLE",
            task_id: ()
        };
        return errorResponse;
    }
    
    // Check HTTP status
    if response.statusCode != 200 {
        json|error errorPayload = response.getJsonPayload();
        string errorMessage = "Auto processing failed";
        
        if errorPayload is json && errorPayload is map<json> {
            json messageField = errorPayload["message"];
            if messageField is string {
                errorMessage = messageField;
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
    
    // Convert JSON response to typed response
    types:AutoProcessingResponse|error typedResponse = responsePayload.cloneWithType(types:AutoProcessingResponse);
    if typedResponse is error {
        log:printError("Error converting auto processing response", 'error = typedResponse);
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "Invalid response format from processing service",
            error_code: "RESPONSE_FORMAT_ERROR",
            task_id: ()
        };
        return errorResponse;
    }
    
    return typedResponse;
}

// Validate article processing request - Can remain isolated as it's pure function
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
    
    // Validate n_clusters
    if request.n_clusters < 1 || request.n_clusters > 50 {
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "n_clusters must be between 1 and 50",
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
    }
    
    return ();
}

// Validate auto processing query parameters - Can remain isolated as it's pure function
public isolated function validateAutoProcessingParams(types:AutoProcessingQueryParams queryParams) returns types:ClusterProcessingErrorResponse? {
    
    // Validate n_clusters
    if queryParams.n_clusters is int && (queryParams.n_clusters < 1 || queryParams.n_clusters > 50) {
        types:ClusterProcessingErrorResponse errorResponse = {
            success: false,
            message: "n_clusters must be between 1 and 50",
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

// Helper function to build query string - Can remain isolated as it's pure function
isolated function buildClusterQueryString(map<string> params) returns string {
    string[] pairs = [];
    foreach string key in params.keys() {
        string value = params.get(key);
        pairs.push(key + "=" + value);
    }
    return pairs.length() > 0 ? "?" + string:'join("&", ...pairs) : "";
}