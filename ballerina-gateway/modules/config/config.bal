import ballerinax/mongodb;

// Configurable MongoDB connection settings
configurable string mongoUri = "mongodb+srv://himathnimpura:himathavenge@cluster0.bjaku.mongodb.net/User_Details?retryWrites=true&w=majority";
configurable string databaseName = "newsstore";

// MongoDB client instance
public final mongodb:Client mongoClient = check new ({
    connection: mongoUri
});

// Public function to get database name
public function getDatabaseName() returns string {
    return databaseName;
}

// Public function to get MongoDB client
public function getMongoClient() returns mongodb:Client {
    return mongoClient;
}

// Public function to get MongoDB database
public function getDatabase() returns mongodb:Database|error {
    mongodb:Database database = check mongoClient->getDatabase(databaseName);
    return database;
}

// Public function to get news collection
public isolated function getNewsCollection() returns mongodb:Collection|error {
    mongodb:Database database = check mongoClient->getDatabase(databaseName);
    mongodb:Collection newsCollection = check database->getCollection("news");
    return newsCollection;
}

// Public function to get clusters collection

public isolated function getClustersCollection() returns mongodb:Collection|error {
    mongodb:Database database = check mongoClient->getDatabase(databaseName);
    mongodb:Collection clustersCollection = check database->getCollection("clusters");
    return clustersCollection;
}