import ballerina/time;
import ballerinax/mongodb;
import ballerina_gateway.config;
import ballerina_gateway.types;
import ballerina/log;

// Get clusters collection with better error handling
isolated function getClustersCollection() returns mongodb:Collection|error {
    do {
        mongodb:Collection clustersCollection = check config:getClustersCollection();
        return clustersCollection;
    } on fail error e {
        return error("Failed to get clusters collection: " + e.message());
    }
}

// Get news collection with better error handling
isolated function getNewsCollection() returns mongodb:Collection|error {
    do {
        mongodb:Collection newsCollection = check config:getNewsCollection();
        return newsCollection;
    } on fail error e {
        return error("Failed to get news collection: " + e.message());
    }
}

// Validate and sanitize field names for MongoDB
isolated function validateAndSanitizeFieldName(string fieldName) returns string|error {
    // Check if field name starts with '$'
    if fieldName.startsWith("$") {
        return error("Field name cannot start with '$': " + fieldName);
    }
    
    // List of valid field names for sorting
    string[] validFields = ["created_at", "updated_at", "cluster_name", "articles_count"];
    boolean isValid = false;
    foreach string validField in validFields {
        if fieldName == validField {
            isValid = true;
            break;
        }
    }
    
    if !isValid {
        return error("Invalid field name for sorting: " + fieldName);
    }
    
    return fieldName;
}

// Validate and sanitize article field names for MongoDB
isolated function validateAndSanitizeArticleFieldName(string fieldName) returns string|error {
    // Check if field name starts with '$'
    if fieldName.startsWith("$") {
        return error("Field name cannot start with '$': " + fieldName);
    }
    
    // List of valid field names for article sorting
    string[] validFields = ["published_at", "extracted_at", "title", "source"];
    boolean isValid = false;
    foreach string validField in validFields {
        if fieldName == validField {
            isValid = true;
            break;
        }
    }
    
    if !isValid {
        return error("Invalid article sort field: " + fieldName);
    }
    
    return fieldName;
}

// Extract string from MongoDB ObjectId json structure
isolated function extractObjectIdString(json objectIdJson) returns string {
    if objectIdJson is map<json> {
        json oidValue = objectIdJson["$oid"];
        if oidValue is string {
            return oidValue;
        }
    }
    return objectIdJson.toString();
}

// Extract string from MongoDB Date json structure
isolated function extractDateString(json? dateJson) returns string? {
    if dateJson is map<json> {
        json dateValue = dateJson["$date"];
        if dateValue is string {
            return dateValue;
        }
    }
    return ();
}

// Convert json array of ObjectIds to string array
isolated function convertJsonObjectIdArrayToStringArray(json[]? objectIdArray) returns string[]? {
    if objectIdArray is json[] {
        string[] stringArray = [];
        foreach json objectId in objectIdArray {
            string objectIdString = extractObjectIdString(objectId);
            stringArray.push(objectIdString);
        }
        return stringArray;
    }
    return ();
}

// Convert MongoDB cluster to API cluster format
isolated function convertMongoClusterToCluster(types:MongoCluster mongoCluster) returns types:Cluster {
    // Extract ObjectId string from MongoDB _id structure
    string clusterId = extractObjectIdString(mongoCluster._id);
    
    // Convert MongoDB date objects to strings
    string? createdAtString = extractDateString(mongoCluster.created_at);
    string? updatedAtString = extractDateString(mongoCluster.updated_at);
    
    // Convert article_ids from json ObjectId array to string array
    string[]? articleIds = convertJsonObjectIdArrayToStringArray(mongoCluster.article_ids);
    
    return {
        _id: clusterId,
        cluster_name: mongoCluster.cluster_name,
        facts: mongoCluster.facts,
        musings: mongoCluster.musings,
        keywords: mongoCluster.keywords,
        sources: mongoCluster.sources,
        article_urls: mongoCluster.article_urls,
        article_ids: articleIds,
        generated_article: mongoCluster.generated_article,
        factual_summary: mongoCluster.factual_summary,
        contextual_analysis: mongoCluster.contextual_analysis,
        context: mongoCluster.context,
        background: mongoCluster.background,
        image_url: mongoCluster.image_url,
        articles_count: mongoCluster.articles_count,
        source_counts: mongoCluster.source_counts,
        similarity_scores: mongoCluster.similarity_scores,
        embedding: mongoCluster.embedding,
        created_at: createdAtString,
        updated_at: updatedAtString
    };
}

// Create sort document safely
isolated function createSortDocument(string sortBy, int sortOrder) returns map<json>|error {
    string validatedField = check validateAndSanitizeFieldName(sortBy);
    
    // Create sort document based on field name
    map<json> sortDoc = {};
    if validatedField == "created_at" {
        sortDoc["created_at"] = sortOrder;
    } else if validatedField == "updated_at" {
        sortDoc["updated_at"] = sortOrder;
    } else if validatedField == "cluster_name" {
        sortDoc["cluster_name"] = sortOrder;
    } else if validatedField == "articles_count" {
        sortDoc["articles_count"] = sortOrder;
    } else {
        return error("Unsupported sort field: " + validatedField);
    }
    
    return sortDoc;
}

// Create article sort document safely
isolated function createArticleSortDocument(string sortBy, int sortOrder) returns map<json>|error {
    string validatedField = check validateAndSanitizeArticleFieldName(sortBy);
    
    // Create sort document based on field name
    map<json> sortDoc = {};
    if validatedField == "published_at" {
        sortDoc["published_at"] = sortOrder;
    } else if validatedField == "extracted_at" {
        sortDoc["extracted_at"] = sortOrder;
    } else if validatedField == "title" {
        sortDoc["title"] = sortOrder;
    } else if validatedField == "source" {
        sortDoc["source"] = sortOrder;
    } else {
        return error("Unsupported article sort field: " + validatedField);
    }
    
    return sortDoc;
}

// Create MongoDB ObjectId query document
isolated function createObjectIdQuery(string clusterId) returns map<json> {
    return {
        "_id": {
            "$oid": clusterId
        }
    };
}

// Create MongoDB query for multiple ObjectIds - Enhanced with debugging
isolated function createMultipleObjectIdQuery(string[] objectIds) returns map<json> {
    json[] objectIdQueries = [];
    foreach string objectId in objectIds {
        // Create proper ObjectId structure for each ID
        map<json> objectIdMap = {
            "$oid": objectId
        };
        objectIdQueries.push(objectIdMap);
    }
    
    return {
        "_id": {
            "$in": objectIdQueries
        }
    };
}

// Create alternative query for articles using simple string IDs
isolated function createSimpleStringIdQuery(string[] objectIds) returns map<json> {
    return {
        "_id": {
            "$in": objectIds
        }
    };
}

// Create search query for MongoDB
isolated function createSearchQuery(types:ClusterSearchRequest searchRequest) returns map<json> {
    string searchQuery = searchRequest.query;
    
    // Create regex pattern for case-insensitive search
    map<json> regexPattern = {
        "$regex": searchQuery,
        "$options": "i"
    };
    
    // Build OR query to search across multiple fields
    json[] orConditions = [];
    
    // Search in cluster_name
    orConditions.push({"cluster_name": regexPattern});
    
    // Search in generated_article
    orConditions.push({"generated_article": regexPattern});
    
    // Search in factual_summary
    orConditions.push({"factual_summary": regexPattern});
    
    // Search in contextual_analysis
    orConditions.push({"contextual_analysis": regexPattern});
    
    // Search in context
    orConditions.push({"context": regexPattern});
    
    // Search in background
    orConditions.push({"background": regexPattern});
    
    // Search in facts array
    orConditions.push({"facts": regexPattern});
    
    // Search in musings array
    orConditions.push({"musings": regexPattern});
    
    // Search in keywords array
    orConditions.push({"keywords": regexPattern});
    
    map<json> query = {"$or": orConditions};
    
    // Add source filter if provided
    if searchRequest.sources is string[] {
        string[] sources = <string[]>searchRequest.sources;
        if sources.length() > 0 {
            query["sources"] = {"$in": sources};
        }
    }
    
    // Add keyword filter if provided
    if searchRequest.keywords is string[] {
        string[] keywords = <string[]>searchRequest.keywords;
        if keywords.length() > 0 {
            query["keywords"] = {"$in": keywords};
        }
    }
    
    return query;
}

// Create date range query for trending topics analysis
isolated function createDateRangeQuery(int daysBack) returns map<json>|error {
    // Calculate the date threshold
    time:Utc currentTime = time:utcNow();
    time:Seconds secondsBack = <time:Seconds>(daysBack * 24 * 60 * 60);
    time:Utc thresholdTime = time:utcAddSeconds(currentTime, -secondsBack);
    
    // Convert to ISO string format for MongoDB
    string thresholdDateString = time:utcToString(thresholdTime);
    
    return {
        "created_at": {
            "$gte": {
                "$date": thresholdDateString
            }
        }
    };
}

// Create query for clusters with minimum article count
isolated function createMinArticlesQuery(int minArticles) returns map<json> {
    return {
        "articles_count": {
            "$gte": minArticles
        }
    };
}

// Create combined query for date range and minimum articles
isolated function createCombinedQuery(int? daysBack, int minArticles) returns map<json>|error {
    json[] andConditions = [];
    
    // Add minimum articles condition
    andConditions.push(createMinArticlesQuery(minArticles));
    
    // Add date range condition if specified
    if daysBack is int {
        map<json> dateRangeQuery = check createDateRangeQuery(daysBack);
        andConditions.push(dateRangeQuery);
    }
    
    if andConditions.length() == 1 {
        return <map<json>>andConditions[0];
    } else {
        return {
            "$and": andConditions
        };
    }
}

// Get all clusters with pagination and sorting
public isolated function getAllClusters(int 'limit = 20, int skip = 0, string sortBy = "created_at", int sortOrder = -1) returns types:ClusterListResponse|error {
    do {
        mongodb:Collection clustersCollection = check getClustersCollection();
        
        // Get total count with error handling
        int totalCount = 0;
        do {
            totalCount = check clustersCollection->countDocuments();
        } on fail error e {
            return error("Failed to count documents: " + e.message());
        }
        
        // Create sort document safely
        map<json> sortDoc = check createSortDocument(sortBy, sortOrder);

        // Create FindOptions with sort, limit, and skip
        mongodb:FindOptions findOptions = {
            sort: sortDoc,
            'limit: 'limit,
            skip: skip
        };
        
        // Find clusters with pagination using MongoCluster type
        stream<types:MongoCluster, error?> mongoClusterStream = check clustersCollection->find(
            targetType = types:MongoCluster,
            findOptions = findOptions
        );
        
        // Convert stream to array with error handling
        types:Cluster[] clusters = [];
        do {
            record {| types:MongoCluster value; |}? streamResult = check mongoClusterStream.next();
            while streamResult is record {| types:MongoCluster value; |} {
                types:Cluster convertedCluster = convertMongoClusterToCluster(streamResult.value);
                clusters.push(convertedCluster);
                streamResult = check mongoClusterStream.next();
            }
            check mongoClusterStream.close();
        } on fail error e {
            check mongoClusterStream.close();
            return error("Failed to process cluster stream: " + e.message());
        }
        
        time:Utc currentTime = time:utcNow();
        return {
            success: true,
            clusters: clusters,
            total_count: totalCount,
            timestamp: time:utcToString(currentTime)
        };
    } on fail error e {
        return error("Failed to get all clusters: " + e.message());
    }
}

// Get specific cluster by ID
public isolated function getClusterById(string clusterId) returns types:SingleClusterResponse|error {
    do {
        mongodb:Collection clustersCollection = check getClustersCollection();
        
        // Create query document for ObjectId
        map<json> query = createObjectIdQuery(clusterId);
        
        // Find the specific cluster
        types:MongoCluster? mongoCluster = check clustersCollection->findOne(
            filter = query,
            targetType = types:MongoCluster
        );
        
        if mongoCluster is () {
            return error("Cluster not found with ID: " + clusterId);
        }
        
        // Convert MongoDB cluster to API cluster format
        types:Cluster cluster = convertMongoClusterToCluster(mongoCluster);
        
        time:Utc currentTime = time:utcNow();
        return {
            success: true,
            cluster: cluster,
            timestamp: time:utcToString(currentTime)
        };
    } on fail error e {
        return error("Failed to get cluster by ID: " + e.message());
    }
}

// Get articles belonging to a specific cluster - Enhanced with proper debugging
public isolated function getClusterArticles(string clusterId, string sortBy = "published_at", int sortOrder = -1) returns types:ClusterArticlesResponse|error {
    do {
        mongodb:Collection clustersCollection = check getClustersCollection();
        mongodb:Collection newsCollection = check getNewsCollection();
        
        // First, get the cluster to retrieve article IDs
        map<json> clusterQuery = createObjectIdQuery(clusterId);
        types:MongoCluster? mongoCluster = check clustersCollection->findOne(
            filter = clusterQuery,
            targetType = types:MongoCluster
        );
        
        if mongoCluster is () {
            return error("Cluster not found with ID: " + clusterId);
        }
        
        // Log cluster information for debugging
        log:printInfo("Found cluster", cluster_id = clusterId, cluster_name = mongoCluster.cluster_name);
        
        // Extract article IDs from the cluster
        string[]? articleIds = convertJsonObjectIdArrayToStringArray(mongoCluster.article_ids);
        
        // Log article IDs for debugging
        if articleIds is string[] {
            log:printInfo("Extracted article IDs", article_count = articleIds.length(), article_ids = articleIds.toString());
        } else {
            log:printInfo("No article IDs found in cluster", cluster_id = clusterId);
        }
        
        if articleIds is () || articleIds.length() == 0 {
            // Return empty response if no articles in cluster
            time:Utc currentTime = time:utcNow();
            return {
                success: true,
                cluster_id: clusterId,
                articles: [],
                total_articles: 0,
                timestamp: time:utcToString(currentTime)
            };
        }
        
        // Test: Check if any articles exist in news collection at all
        int totalNewsCount = check newsCollection->countDocuments();
        log:printInfo("Total articles in news collection", total_count = totalNewsCount);
        
        // Test: Try to find one specific article by ID using ObjectId format
        string firstArticleId = articleIds[0];
        map<json> singleArticleQuery = createObjectIdQuery(firstArticleId);
        log:printInfo("Testing single article query with ObjectId format", article_id = firstArticleId, query = singleArticleQuery.toString());
        
        types:NewsArticle? singleArticleResult = check newsCollection->findOne(
            filter = singleArticleQuery,
            targetType = types:NewsArticle
        );
        
        if singleArticleResult is types:NewsArticle {
            log:printInfo("Single article found with ObjectId format", article_found = true);
        } else {
            log:printInfo("Single article NOT found with ObjectId format", article_found = false);
            
            // Try alternative query format - simple string ID
            map<json> alternativeQuery = {
                "_id": firstArticleId
            };
            log:printInfo("Trying alternative query format with simple string", query = alternativeQuery.toString());
            
            types:NewsArticle? alternativeResult = check newsCollection->findOne(
                filter = alternativeQuery,
                targetType = types:NewsArticle
            );
            
            if alternativeResult is types:NewsArticle {
                log:printInfo("Alternative query worked with simple string", found = true);
                // Use simple string format for the main query
                map<json> articlesQuery = createSimpleStringIdQuery(articleIds);
                log:printInfo("Using simple string ID query for all articles", query = articlesQuery.toString());
                
                // Create sort document for articles
                map<json> articleSortDoc = check createArticleSortDocument(sortBy, sortOrder);
                
                // Create FindOptions with sort
                mongodb:FindOptions findOptions = {
                    sort: articleSortDoc
                };
                
                // Find articles using simple string IDs
                stream<types:NewsArticle, error?> newsArticleStream = check newsCollection->find(
                    filter = articlesQuery,
                    targetType = types:NewsArticle,
                    findOptions = findOptions
                );
                
                // Convert stream to array
                types:NewsArticle[] articles = [];
                do {
                    record {| types:NewsArticle value; |}? streamResult = check newsArticleStream.next();
                    while streamResult is record {| types:NewsArticle value; |} {
                        articles.push(streamResult.value);
                        streamResult = check newsArticleStream.next();
                    }
                    check newsArticleStream.close();
                } on fail error e {
                    check newsArticleStream.close();
                    return error("Failed to process articles stream: " + e.message());
                }
                
                log:printInfo("Articles found with simple string query", articles_found = articles.length(), expected_count = articleIds.length());
                
                time:Utc currentTime = time:utcNow();
                return {
                    success: true,
                    cluster_id: clusterId,
                    articles: articles,
                    total_articles: articles.length(),
                    timestamp: time:utcToString(currentTime)
                };
            } else {
                log:printInfo("Alternative query also failed", found = false);
            }
        }
        
        // If ObjectId format worked, use it for the main query
        map<json> articlesQuery = createMultipleObjectIdQuery(articleIds);
        log:printInfo("Using ObjectId format query for all articles", query = articlesQuery.toString());
        
        // Create sort document for articles
        map<json> articleSortDoc = check createArticleSortDocument(sortBy, sortOrder);
        
        // Create FindOptions with sort
        mongodb:FindOptions findOptions = {
            sort: articleSortDoc
        };
        
        // Find articles matching the IDs
        stream<types:NewsArticle, error?> newsArticleStream = check newsCollection->find(
            filter = articlesQuery,
            targetType = types:NewsArticle,
            findOptions = findOptions
        );
        
        // Convert stream to array with error handling
        types:NewsArticle[] articles = [];
        do {
            record {| types:NewsArticle value; |}? streamResult = check newsArticleStream.next();
            while streamResult is record {| types:NewsArticle value; |} {
                articles.push(streamResult.value);
                streamResult = check newsArticleStream.next();
            }
            check newsArticleStream.close();
        } on fail error e {
            check newsArticleStream.close();
            return error("Failed to process articles stream: " + e.message());
        }
        
        // Log final results
        log:printInfo("Articles found", articles_found = articles.length(), expected_count = articleIds.length());
        
        time:Utc currentTime = time:utcNow();
        return {
            success: true,
            cluster_id: clusterId,
            articles: articles,
            total_articles: articles.length(),
            timestamp: time:utcToString(currentTime)
        };
    } on fail error e {
        return error("Failed to get cluster articles: " + e.message());
    }
}

// Search clusters based on query
public isolated function searchClusters(types:ClusterSearchRequest searchRequest) returns types:ClusterSearchResponse|error {
    do {
        mongodb:Collection clustersCollection = check getClustersCollection();
        
        // Create search query
        map<json> searchQuery = createSearchQuery(searchRequest);
        
        // Set default limit if not provided
        int searchLimit = searchRequest.'limit ?: 20;
        
        // Create FindOptions with limit and sort by relevance (created_at desc)
        mongodb:FindOptions findOptions = {
            'limit: searchLimit,
            sort: {"created_at": -1}
        };
        
        // Find clusters matching the search query
        stream<types:MongoCluster, error?> mongoClusterStream = check clustersCollection->find(
            filter = searchQuery,
            targetType = types:MongoCluster,
            findOptions = findOptions
        );
        
        // Convert stream to array with error handling
        types:Cluster[] clusters = [];
        do {
            record {| types:MongoCluster value; |}? streamResult = check mongoClusterStream.next();
            while streamResult is record {| types:MongoCluster value; |} {
                types:Cluster convertedCluster = convertMongoClusterToCluster(streamResult.value);
                clusters.push(convertedCluster);
                streamResult = check mongoClusterStream.next();
            }
            check mongoClusterStream.close();
        } on fail error e {
            check mongoClusterStream.close();
            return error("Failed to process search results: " + e.message());
        }
        
        time:Utc currentTime = time:utcNow();
        return {
            success: true,
            clusters: clusters,
            total_results: clusters.length(),
            search_query: searchRequest.query,
            timestamp: time:utcToString(currentTime)
        };
    } on fail error e {
        return error("Failed to search clusters: " + e.message());
    }
}

// Get trending topics based on cluster analysis
public isolated function getTrendingTopics(int daysBack = 7, int minArticles = 3) returns types:TrendingTopicsResponse|error {
    do {
        mongodb:Collection clustersCollection = check getClustersCollection();
        
        // Create date range query for recent clusters
        map<json> dateRangeQuery = check createDateRangeQuery(daysBack);
        
        // Find clusters within the specified time range
        stream<types:MongoCluster, error?> mongoClusterStream = check clustersCollection->find(
            filter = dateRangeQuery,
            targetType = types:MongoCluster
        );
        
        // Process clusters to extract trending topics
        map<types:TopicAnalysis> topicAnalysisMap = {};
        
        do {
            record {| types:MongoCluster value; |}? streamResult = check mongoClusterStream.next();
            while streamResult is record {| types:MongoCluster value; |} {
                types:MongoCluster cluster = streamResult.value;
                
                // Process keywords from this cluster
                foreach string keyword in cluster.keywords {
                    string normalizedKeyword = keyword.toLowerAscii().trim();
                    
                    if topicAnalysisMap.hasKey(normalizedKeyword) {
                        types:TopicAnalysis existingAnalysis = topicAnalysisMap.get(normalizedKeyword);
                        existingAnalysis.cluster_count += 1;
                        existingAnalysis.article_count += cluster.articles_count;
                        
                        // Add sources
                        foreach string 'source in cluster.sources {
                            boolean sourceExists = false;
                            foreach string existingSource in existingAnalysis.sources {
                                if existingSource == 'source {
                                    sourceExists = true;
                                    break;
                                }
                            }
                            if !sourceExists {
                                existingAnalysis.sources.push('source);
                            }
                        }
                        
                        // Add related keywords
                        foreach string relatedKeyword in cluster.keywords {
                            if relatedKeyword != keyword {
                                boolean keywordExists = false;
                                foreach string existingKeyword in existingAnalysis.keywords {
                                    if existingKeyword == relatedKeyword {
                                        keywordExists = true;
                                        break;
                                    }
                                }
                                if !keywordExists {
                                    existingAnalysis.keywords.push(relatedKeyword);
                                }
                            }
                        }
                        
                        topicAnalysisMap[normalizedKeyword] = existingAnalysis;
                    } else {
                        types:TopicAnalysis newAnalysis = {
                            topic: normalizedKeyword,
                            keywords: cluster.keywords.clone(),
                            cluster_count: 1,
                            article_count: cluster.articles_count,
                            sources: cluster.sources.clone(),
                            trend_score: 0.0,
                            trend_direction: "stable"
                        };
                        topicAnalysisMap[normalizedKeyword] = newAnalysis;
                    }
                }
                
                streamResult = check mongoClusterStream.next();
            }
            check mongoClusterStream.close();
        } on fail error e {
            check mongoClusterStream.close();
            return error("Failed to process trending topics stream: " + e.message());
        }
        
        // Filter topics by minimum articles threshold and calculate trend scores
        types:TrendingTopic[] trendingTopics = [];
        
        foreach string topicKey in topicAnalysisMap.keys() {
            types:TopicAnalysis analysis = topicAnalysisMap.get(topicKey);
            
            if analysis.article_count >= minArticles {
                // Calculate trend score based on cluster count, article count, and recency
                decimal clusterWeight = <decimal>analysis.cluster_count * 2.0;
                decimal articleWeight = <decimal>analysis.article_count * 1.0;
                decimal sourceWeight = <decimal>analysis.sources.length() * 0.5;
                decimal trendScore = clusterWeight + articleWeight + sourceWeight;
                
                // Determine trend direction based on cluster frequency
                string trendDirection = "stable";
                if analysis.cluster_count >= 5 {
                    trendDirection = "rising";
                } else if analysis.cluster_count >= 3 {
                    trendDirection = "emerging";
                }
                
                types:TrendingTopic trendingTopic = {
                    topic: analysis.topic,
                    keywords: analysis.keywords,
                    cluster_count: analysis.cluster_count,
                    article_count: analysis.article_count,
                    sources: analysis.sources,
                    trend_score: trendScore,
                    trend_direction: trendDirection
                };
                
                trendingTopics.push(trendingTopic);
            }
        }
        
        // Sort trending topics by trend score (descending)
        types:TrendingTopic[] sortedTrendingTopics = [];
        foreach types:TrendingTopic topic in trendingTopics {
            boolean inserted = false;
            int insertIndex = 0;
            
            foreach int i in 0 ..< sortedTrendingTopics.length() {
                if topic.trend_score > sortedTrendingTopics[i].trend_score {
                    insertIndex = i;
                    inserted = true;
                    break;
                }
            }
            
            if inserted {
                // Insert at the found position
                types:TrendingTopic[] beforeInsert = sortedTrendingTopics.slice(0, insertIndex);
                types:TrendingTopic[] afterInsert = sortedTrendingTopics.slice(insertIndex);
                sortedTrendingTopics = [...beforeInsert, topic, ...afterInsert];
            } else {
                // Add to the end
                sortedTrendingTopics.push(topic);
            }
        }
        
        // Limit to top 20 trending topics
        if sortedTrendingTopics.length() > 20 {
            sortedTrendingTopics = sortedTrendingTopics.slice(0, 20);
        }
        
        time:Utc currentTime = time:utcNow();
        string analysisPeriod = string `Last ${daysBack} days`;
        
        return {
            success: true,
            trending_topics: sortedTrendingTopics,
            analysis_period: analysisPeriod,
            timestamp: time:utcToString(currentTime)
        };
    } on fail error e {
        return error("Failed to get trending topics: " + e.message());
    }
}

// Get top clusters by article count
public isolated function getTopClustersByArticleCount(int? daysBack = (), int minArticles = 1) returns types:TopClustersResponse|error {
    do {
        mongodb:Collection clustersCollection = check getClustersCollection();
        
        // Create combined query for date range and minimum articles
        map<json> query = check createCombinedQuery(daysBack, minArticles);
        
        // Create sort document to sort by articles_count in descending order
        map<json> sortDoc = {"articles_count": -1};
        
        // Create FindOptions with sort and limit to top 50 clusters
        mongodb:FindOptions findOptions = {
            sort: sortDoc,
            'limit: 50
        };
        
        // Find clusters matching the criteria
        stream<types:MongoCluster, error?> mongoClusterStream = check clustersCollection->find(
            filter = query,
            targetType = types:MongoCluster,
            findOptions = findOptions
        );
        
        // Convert stream to array with error handling
        types:Cluster[] clusters = [];
        do {
            record {| types:MongoCluster value; |}? streamResult = check mongoClusterStream.next();
            while streamResult is record {| types:MongoCluster value; |} {
                types:Cluster convertedCluster = convertMongoClusterToCluster(streamResult.value);
                clusters.push(convertedCluster);
                streamResult = check mongoClusterStream.next();
            }
            check mongoClusterStream.close();
        } on fail error e {
            check mongoClusterStream.close();
            return error("Failed to process top clusters stream: " + e.message());
        }
        
        time:Utc currentTime = time:utcNow();
        string analysisPeriod = daysBack is int ? string `Last ${daysBack} days` : "All time";
        
        return {
            success: true,
            clusters: clusters,
            total_clusters: clusters.length(),
            analysis_period: analysisPeriod,
            min_articles_threshold: minArticles,
            timestamp: time:utcToString(currentTime)
        };
    } on fail error e {
        return error("Failed to get top clusters by article count: " + e.message());
    }
}

// Get weekly digest of all clusters from the last 7 days
public isolated function getWeeklyDigest() returns types:WeeklyDigestResponse|error {
    do {
        mongodb:Collection clustersCollection = check getClustersCollection();
        
        // Create date range query for last 7 days
        map<json> dateRangeQuery = check createDateRangeQuery(7);
        
        // Create sort document to sort by created_at descending (most recent first)
        map<json> sortDoc = {"created_at": -1};
        
        // Create FindOptions with sort
        mongodb:FindOptions findOptions = {
            sort: sortDoc
        };
        
        // Find clusters from the last 7 days
        stream<types:MongoCluster, error?> mongoClusterStream = check clustersCollection->find(
            filter = dateRangeQuery,
            targetType = types:MongoCluster,
            findOptions = findOptions
        );
        
        // Process clusters and collect statistics
        types:Cluster[] clusters = [];
        int totalArticles = 0;
        int totalFacts = 0;
        int totalMusings = 0;
        map<int> sourceCountMap = {};
        map<int> keywordCountMap = {};
        
        do {
            record {| types:MongoCluster value; |}? streamResult = check mongoClusterStream.next();
            while streamResult is record {| types:MongoCluster value; |} {
                types:MongoCluster mongoCluster = streamResult.value;
                types:Cluster convertedCluster = convertMongoClusterToCluster(mongoCluster);
                clusters.push(convertedCluster);
                
                // Accumulate statistics
                totalArticles += mongoCluster.articles_count;
                totalFacts += mongoCluster.facts.length();
                totalMusings += mongoCluster.musings.length();
                
                // Count sources
                foreach string 'source in mongoCluster.sources {
                    if sourceCountMap.hasKey('source) {
                        int currentCount = sourceCountMap.get('source);
                        sourceCountMap['source] = currentCount + 1;
                    } else {
                        sourceCountMap['source] = 1;
                    }
                }
                
                // Count keywords
                foreach string keyword in mongoCluster.keywords {
                    string normalizedKeyword = keyword.toLowerAscii().trim();
                    if keywordCountMap.hasKey(normalizedKeyword) {
                        int currentCount = keywordCountMap.get(normalizedKeyword);
                        keywordCountMap[normalizedKeyword] = currentCount + 1;
                    } else {
                        keywordCountMap[normalizedKeyword] = 1;
                    }
                }
                
                streamResult = check mongoClusterStream.next();
            }
            check mongoClusterStream.close();
        } on fail error e {
            check mongoClusterStream.close();
            return error("Failed to process weekly digest stream: " + e.message());
        }
        
        // Calculate statistics
        int totalClusters = clusters.length();
        int avgArticlesPerCluster = totalClusters > 0 ? totalArticles / totalClusters : 0;
        int uniqueSources = sourceCountMap.keys().length();
        decimal avgClusterSize = totalClusters > 0 ? <decimal>totalArticles / <decimal>totalClusters : 0.0;
        
        // Find most active source
        string mostActiveSource = "";
        int maxSourceCount = 0;
        foreach string sourceKey in sourceCountMap.keys() {
            int sourceCount = sourceCountMap.get(sourceKey);
            if sourceCount > maxSourceCount {
                maxSourceCount = sourceCount;
                mostActiveSource = sourceKey;
            }
        }
        
        // Find most covered topic
        string mostCoveredTopic = "";
        int maxKeywordCount = 0;
        foreach string keywordKey in keywordCountMap.keys() {
            int keywordCount = keywordCountMap.get(keywordKey);
            if keywordCount > maxKeywordCount {
                maxKeywordCount = keywordCount;
                mostCoveredTopic = keywordKey;
            }
        }
        
        // Get top 10 keywords
        string[] topKeywords = [];
        string[] sortedKeywords = keywordCountMap.keys();
        // Simple sorting by count (descending)
        foreach int i in 0 ..< sortedKeywords.length() {
            foreach int j in i + 1 ..< sortedKeywords.length() {
                string keywordI = sortedKeywords[i];
                string keywordJ = sortedKeywords[j];
                int countI = keywordCountMap.get(keywordI);
                int countJ = keywordCountMap.get(keywordJ);
                if countJ > countI {
                    sortedKeywords[i] = keywordJ;
                    sortedKeywords[j] = keywordI;
                }
            }
        }
        
        int keywordLimit = sortedKeywords.length() < 10 ? sortedKeywords.length() : 10;
        foreach int i in 0 ..< keywordLimit {
            topKeywords.push(sortedKeywords[i]);
        }
        
        // Get top 10 sources
        string[] topSources = [];
        string[] sortedSources = sourceCountMap.keys();
        // Simple sorting by count (descending)
        foreach int i in 0 ..< sortedSources.length() {
            foreach int j in i + 1 ..< sortedSources.length() {
                string sourceI = sortedSources[i];
                string sourceJ = sortedSources[j];
                int countI = sourceCountMap.get(sourceI);
                int countJ = sourceCountMap.get(sourceJ);
                if countJ > countI {
                    sortedSources[i] = sourceJ;
                    sortedSources[j] = sourceI;
                }
            }
        }
        
        int sourceLimit = sortedSources.length() < 10 ? sortedSources.length() : 10;
        foreach int i in 0 ..< sourceLimit {
            topSources.push(sortedSources[i]);
        }
        
        // Create digest statistics
        types:WeeklyDigestStats stats = {
            avg_articles_per_cluster: avgArticlesPerCluster,
            total_facts: totalFacts,
            total_musings: totalMusings,
            unique_sources: uniqueSources,
            most_active_source: mostActiveSource,
            most_covered_topic: mostCoveredTopic,
            avg_cluster_size: avgClusterSize
        };
        
        // Generate summary
        string summary = string `Weekly digest covering ${totalClusters} clusters with ${totalArticles} articles from ${uniqueSources} unique sources. Most active source: ${mostActiveSource}. Most covered topic: ${mostCoveredTopic}.`;
        
        // Create digest data
        types:WeeklyDigestData digestData = {
            total_clusters: totalClusters,
            total_articles: totalArticles,
            clusters: clusters,
            stats: stats,
            top_keywords: topKeywords,
            top_sources: topSources,
            summary: summary
        };
        
        time:Utc currentTime = time:utcNow();
        return {
            success: true,
            digest_period: "Last 7 days",
            digest: digestData,
            timestamp: time:utcToString(currentTime)
        };
    } on fail error e {
        return error("Failed to get weekly digest: " + e.message());
    }
}