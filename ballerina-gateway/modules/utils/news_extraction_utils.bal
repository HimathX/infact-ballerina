import ballerina/io;
import ballerina/http;
import ballerina/time;
import ballerina_gateway.config;
import ballerina_gateway.types;

// Configurable News API settings
configurable string newsApiKey = "72b8758ce89d4c7e8c6ae949aca9224b";

// HTTP client for News API
http:Client newsHttpClient = check new ("https://newsapi.org/v2");

// HTTP client for RSS extraction service with increased timeout
http:Client rssExtractionClient = check new ("http://127.0.0.1:8091", {
    timeout: 300.0  // 5 minutes timeout for RSS extraction
});

// Public function to get RSS extraction client
public function getRssExtractionClient() returns http:Client {
    return rssExtractionClient;
}

// Process RSS extracted articles with duplicate checking
public function processRssExtractedArticles(json[] articleArray) returns types:ManualFeedResponse|error {
    string[] insertedTitles = [];
    string[] skippedTitles = [];
    types:NewsArticle[] articlesToInsert = [];
    
    time:Utc currentTime = time:utcNow();
    string currentTimeString = time:utcToString(currentTime);
    
    foreach json articleJson in articleArray {
        types:RssExtractedArticle rssArticle = check articleJson.cloneWithType(types:RssExtractedArticle);
        
        // Create NewsArticle with extracted_at timestamp
        types:NewsArticle newsArticle = {
            title: rssArticle.title,
            content: rssArticle.content,
            'source: rssArticle.'source,
            url: rssArticle.url,
            image_url: rssArticle.image_url,
            published_at: rssArticle.published_at,
            extracted_at: currentTimeString
        };
        
        // Check for duplicates by title OR url
        boolean isDuplicate = check checkArticleDuplicate(newsArticle);
        
        if isDuplicate {
            string titleToAdd = newsArticle.title ?: "Untitled";
            skippedTitles.push(titleToAdd);
        } else {
            string titleToAdd = newsArticle.title ?: "Untitled";
            insertedTitles.push(titleToAdd);
            articlesToInsert.push(newsArticle);
        }
    }
    
    // Insert non-duplicate articles
    if articlesToInsert.length() > 0 {
        check (check config:getNewsCollection())->insertMany(articlesToInsert);
        io:println("Inserted " + articlesToInsert.length().toString() + " RSS extracted articles");
    }
    
    return {
        status: "success",
        inserted_titles: insertedTitles,
        skipped_titles: skippedTitles,
        inserted_count: insertedTitles.length(),
        skipped_count: skippedTitles.length(),
        total_count: articleArray.length()
    };
}

// Process manual feed articles with duplicate checking
public function processManualFeedArticles(json[] articleArray) returns types:ManualFeedResponse|error {
    string[] insertedTitles = [];
    string[] skippedTitles = [];
    types:NewsArticle[] articlesToInsert = [];
    
    time:Utc currentTime = time:utcNow();
    string currentTimeString = time:utcToString(currentTime);
    
    foreach json articleJson in articleArray {
        types:InputArticle inputArticle = check articleJson.cloneWithType(types:InputArticle);
        
        // Create NewsArticle with extracted_at timestamp
        types:NewsArticle newsArticle = {
            title: inputArticle.title,
            content: inputArticle.content,
            'source: inputArticle.'source,
            url: inputArticle.url,
            image_url: inputArticle.image_url,
            published_at: inputArticle.published_at,
            extracted_at: currentTimeString
        };
        
        // Check for duplicates by title OR url
        boolean isDuplicate = check checkArticleDuplicate(newsArticle);
        
        if isDuplicate {
            string titleToAdd = newsArticle.title ?: "Untitled";
            skippedTitles.push(titleToAdd);
        } else {
            string titleToAdd = newsArticle.title ?: "Untitled";
            insertedTitles.push(titleToAdd);
            articlesToInsert.push(newsArticle);
        }
    }
    
    // Insert non-duplicate articles
    if articlesToInsert.length() > 0 {
        check (check config:getNewsCollection())->insertMany(articlesToInsert);
        io:println("Inserted " + articlesToInsert.length().toString() + " new articles");
    }
    
    return {
        status: "success",
        inserted_titles: insertedTitles,
        skipped_titles: skippedTitles,
        inserted_count: insertedTitles.length(),
        skipped_count: skippedTitles.length(),
        total_count: articleArray.length()
    };
}

// Call RSS extraction service with proper error handling
public function callRssExtractionService(json requestBody) returns json|error {
    http:Client rssClient = getRssExtractionClient();
    
    // Try to call the RSS extraction service
    json|error extractionResponse = rssClient->post("/extract", requestBody, headers = {"Content-Type": "application/json"});
    
    if extractionResponse is error {
        io:println("Error calling RSS extraction service: " + extractionResponse.message());
        return error("RSS extraction service is unavailable. Please ensure the service is running on http://127.0.0.1:8091");
    }
    
    return extractionResponse;
}

// Check if article is duplicate by title OR url
function checkArticleDuplicate(types:NewsArticle article) returns boolean|error {
    map<json> query = {};
    json[] orConditions = [];
    
    // Add title condition if title exists
    if article.title is string && article.title != "" {
        orConditions.push({"title": article.title});
    }
    
    // Add url condition if url exists
    if article.url is string && article.url != "" {
        orConditions.push({"url": article.url});
    }
    
    // If no title or url, consider it not a duplicate
    if orConditions.length() == 0 {
        return false;
    }
    
    query["$or"] = orConditions;
    
    int count = check (check config:getNewsCollection())->countDocuments(filter = query);
    return count > 0;
}

// Helper function to extract string field from JSON payload
public function extractStringField(json? payload, string fieldName) returns string? {
    if payload is map<json> {
        json fieldValue = payload[fieldName];
        return fieldValue is string ? fieldValue : ();
    }
    return ();
}

// Helper function to extract int field from JSON payload
public function extractIntField(json? payload, string fieldName) returns int? {
    if payload is map<json> {
        json fieldValue = payload[fieldName];
        return fieldValue is int ? fieldValue : ();
    }
    return ();
}

// Helper function to extract boolean field from JSON payload
public function extractBooleanField(json? payload, string fieldName) returns boolean? {
    if payload is map<json> {
        json fieldValue = payload[fieldName];
        return fieldValue is boolean ? fieldValue : ();
    }
    return ();
}

// Helper function to build query string
function buildQueryString(map<string> params) returns string {
    string[] pairs = [];
    foreach string key in params.keys() {
        pairs.push(key + "=" + params.get(key));
    }
    return pairs.length() > 0 ? "?" + string:'join("&", ...pairs) : "";
}

// Helper function to extract string from JSON field
function getStringFromJson(json jsonField) returns string? {
    return jsonField is string ? jsonField : ();
}

// Helper function to normalize date to ISO 8601 format
function normalizeDate(string? dateString) returns string? {
    if dateString is () {
        return ();
    }
    
    // Try to parse the date string and convert to ISO 8601 format
    time:Utc|error parsedTime = time:utcFromString(dateString);
    if parsedTime is time:Utc {
        return time:utcToString(parsedTime);
    }
    
    // If parsing fails, return the original string
    return dateString;
}

// Helper function to convert JSON article to NewsArticle record with required structure
function jsonToNewsArticle(json articleJson) returns types:NewsArticle|error {
    // Extract source information
    json sourceField = check articleJson.'source;
    string? sourceName = ();
    
    if sourceField is map<json> {
        sourceName = getStringFromJson(sourceField["name"]);
    }

    // Extract and normalize all required fields
    string? title = getStringFromJson(check articleJson.title);
    string? content = getStringFromJson(check articleJson.content);
    string? description = getStringFromJson(check articleJson.description);
    string? url = getStringFromJson(check articleJson.url);
    string? imageUrl = getStringFromJson(check articleJson.urlToImage);
    string? publishedAt = getStringFromJson(check articleJson.publishedAt);

    // Use description as content if content is null or empty
    string? finalContent = content;
    if finalContent is () || finalContent.trim() == "" {
        finalContent = description;
    }

    // Normalize the published date to ISO 8601 format
    string? normalizedDate = normalizeDate(publishedAt);

    // Get current time for extracted_at
    time:Utc currentTime = time:utcNow();
    string extractedAtTime = time:utcToString(currentTime);

    // Return the transformed NewsArticle with required structure
    return {
        title: title,
        content: finalContent,
        'source: sourceName,
        published_at: normalizedDate,
        url: url,
        image_url: imageUrl,
        extracted_at: extractedAtTime
    };
}

// Fetch articles from News API and store in MongoDB, return the fetched articles
public function fetchAndStoreArticles(string? query = (), int pageSize = 20) returns types:NewsArticle[]|error {
    map<string> queryParams = {"apiKey": newsApiKey, "pageSize": pageSize.toString(), "page": "1"};
    
    if query is string {
        queryParams["q"] = query;
    }

    string queryString = buildQueryString(queryParams);
    json response = check newsHttpClient->get("/everything" + queryString);

    // Check for API error
    json statusField = check response.status;
    if statusField is string && statusField == "error" {
        json messageField = check response.message;
        string errorMessage = messageField is string ? messageField : "Unknown error";
        return error(errorMessage);
    }

    json[] articles = check (check response.articles).ensureType();
    if articles.length() == 0 {
        io:println("No articles found");
        return [];
    }

    // Convert and store articles with required structure
    types:NewsArticle[] newsArticles = [];
    foreach json article in articles {
        newsArticles.push(check jsonToNewsArticle(article));
    }

    check (check config:getNewsCollection())->insertMany(newsArticles);
    io:println("Stored " + newsArticles.length().toString() + " articles");
    
    // Return the fetched articles
    return newsArticles;
}

// Get all news articles from MongoDB
public function getAllNewsArticles() returns types:NewsArticle[]|error {
    stream<types:NewsArticle, error?> newsStream = check (check config:getNewsCollection())->find(targetType = types:NewsArticle);
    types:NewsArticle[] articles = check from types:NewsArticle article in newsStream select article;
    check newsStream.close();
    return articles;
}

// Count news articles
public function countNewsArticles() returns int|error {
    return check (check config:getNewsCollection())->countDocuments();
}