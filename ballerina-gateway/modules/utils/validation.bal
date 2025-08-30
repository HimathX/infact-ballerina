import ballerina_gateway.types;

// Validate parameters for getAllClusters function
public isolated function validateAllClustersParams(int? 'limit = (), int? skip = (), string? sortBy = (), int? sortOrder = ()) returns types:ErrorResponse? {
    // Validate limit
    if 'limit is int {
        if 'limit < 1 || 'limit > 100 {
            return {
                success: false,
                message: "Limit must be between 1 and 100",
                error_code: "INVALID_LIMIT"
            };
        }
    }
    
    // Validate skip
    if skip is int {
        if skip < 0 {
            return {
                success: false,
                message: "Skip must be non-negative",
                error_code: "INVALID_SKIP"
            };
        }
    }
    
    // Validate sortBy
    if sortBy is string {
        // Check for MongoDB reserved characters
        if sortBy.startsWith("$") {
            return {
                success: false,
                message: "Sort field cannot start with '$' character",
                error_code: "INVALID_SORT_FIELD_FORMAT"
            };
        }
        
        string[] validSortFields = ["created_at", "updated_at", "cluster_name", "articles_count"];
        boolean isValidSortField = false;
        foreach string validField in validSortFields {
            if sortBy == validField {
                isValidSortField = true;
                break;
            }
        }
        if !isValidSortField {
            return {
                success: false,
                message: "Invalid sort field. Valid options: " + validSortFields.toString(),
                error_code: "INVALID_SORT_FIELD"
            };
        }
    }
    
    // Validate sortOrder
    if sortOrder is int {
        if sortOrder != 1 && sortOrder != -1 {
            return {
                success: false,
                message: "Sort order must be 1 (ascending) or -1 (descending)",
                error_code: "INVALID_SORT_ORDER"
            };
        }
    }
    
    return ();
}

// Validate article sorting parameters
public isolated function validateArticleSortParams(string? sortBy = (), int? sortOrder = ()) returns types:ErrorResponse? {
    // Validate sortBy
    if sortBy is string {
        // Check for MongoDB reserved characters
        if sortBy.startsWith("$") {
            return {
                success: false,
                message: "Sort field cannot start with '$' character",
                error_code: "INVALID_SORT_FIELD_FORMAT"
            };
        }
        
        string[] validSortFields = ["published_at", "extracted_at", "title", "source"];
        boolean isValidSortField = false;
        foreach string validField in validSortFields {
            if sortBy == validField {
                isValidSortField = true;
                break;
            }
        }
        if !isValidSortField {
            return {
                success: false,
                message: "Invalid article sort field. Valid options: " + validSortFields.toString(),
                error_code: "INVALID_ARTICLE_SORT_FIELD"
            };
        }
    }
    
    // Validate sortOrder
    if sortOrder is int {
        if sortOrder != 1 && sortOrder != -1 {
            return {
                success: false,
                message: "Sort order must be 1 (ascending) or -1 (descending)",
                error_code: "INVALID_SORT_ORDER"
            };
        }
    }
    
    return ();
}

// Validate cluster ID format (MongoDB ObjectId)
public isolated function validateClusterId(string clusterId) returns types:ErrorResponse? {
    // Check if cluster ID is empty
    if clusterId.trim().length() == 0 {
        return {
            success: false,
            message: "Cluster ID cannot be empty",
            error_code: "EMPTY_CLUSTER_ID"
        };
    }
    
    // Check if cluster ID has valid MongoDB ObjectId length (24 characters)
    if clusterId.length() != 24 {
        return {
            success: false,
            message: "Invalid cluster ID format. Must be 24 characters long",
            error_code: "INVALID_CLUSTER_ID_LENGTH"
        };
    }
    
    // Check if cluster ID contains only valid hexadecimal characters
    string validChars = "0123456789abcdefABCDEF";
    foreach string:Char char in clusterId {
        boolean isValidChar = false;
        foreach string:Char validChar in validChars {
            if char == validChar {
                isValidChar = true;
                break;
            }
        }
        if !isValidChar {
            return {
                success: false,
                message: "Invalid cluster ID format. Must contain only hexadecimal characters",
                error_code: "INVALID_CLUSTER_ID_FORMAT"
            };
        }
    }
    
    return ();
}

// Validate cluster search request
public isolated function validateClusterSearchRequest(types:ClusterSearchRequest searchRequest) returns types:ErrorResponse? {
    // Validate query parameter
    if searchRequest.query.trim().length() == 0 {
        return {
            success: false,
            message: "Search query cannot be empty",
            error_code: "EMPTY_SEARCH_QUERY"
        };
    }
    
    // Validate query length
    if searchRequest.query.length() > 500 {
        return {
            success: false,
            message: "Search query too long. Maximum 500 characters allowed",
            error_code: "SEARCH_QUERY_TOO_LONG"
        };
    }
    
    // Validate limit if provided
    if searchRequest.'limit is int {
        int searchLimit = <int>searchRequest.'limit;
        if searchLimit < 1 || searchLimit > 100 {
            return {
                success: false,
                message: "Search limit must be between 1 and 100",
                error_code: "INVALID_SEARCH_LIMIT"
            };
        }
    }
    
    // Validate sources array if provided
    if searchRequest.sources is string[] {
        string[] sources = <string[]>searchRequest.sources;
        if sources.length() > 20 {
            return {
                success: false,
                message: "Too many sources specified. Maximum 20 sources allowed",
                error_code: "TOO_MANY_SOURCES"
            };
        }
        
        foreach string 'source in sources {
            if 'source.trim().length() == 0 {
                return {
                    success: false,
                    message: "Source names cannot be empty",
                    error_code: "EMPTY_SOURCE_NAME"
                };
            }
        }
    }
    
    // Validate keywords array if provided
    if searchRequest.keywords is string[] {
        string[] keywords = <string[]>searchRequest.keywords;
        if keywords.length() > 50 {
            return {
                success: false,
                message: "Too many keywords specified. Maximum 50 keywords allowed",
                error_code: "TOO_MANY_KEYWORDS"
            };
        }
        
        foreach string keyword in keywords {
            if keyword.trim().length() == 0 {
                return {
                    success: false,
                    message: "Keywords cannot be empty",
                    error_code: "EMPTY_KEYWORD"
                };
            }
        }
    }
    
    return ();
}

// Validate trending topics parameters
public isolated function validateTrendingTopicsParams(int? daysBack = (), int? minArticles = ()) returns types:ErrorResponse? {
    // Validate daysBack
    if daysBack is int {
        if daysBack < 1 || daysBack > 365 {
            return {
                success: false,
                message: "Days back must be between 1 and 365",
                error_code: "INVALID_DAYS_BACK"
            };
        }
    }
    
    // Validate minArticles
    if minArticles is int {
        if minArticles < 1 || minArticles > 100 {
            return {
                success: false,
                message: "Minimum articles must be between 1 and 100",
                error_code: "INVALID_MIN_ARTICLES"
            };
        }
    }
    
    return ();
}