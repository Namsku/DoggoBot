import asyncio
import motor.motor_asyncio as motor

# Define the MongoDB connection URL
mongodb_url = "mongodb://localhost:27017"  # Replace with your MongoDB server URL

# Initialize the MongoClient
client = motor.AsyncIOMotorClient(mongodb_url)

# Select the database
database = client["doggobot"]

# Select the collection
collection = database["unit_test"]

# Insert a document into the collection
async def insert_document(document):
    try:
        result = await collection.insert_one(document)
        print("Document {0} inserted successfully.".format(document))
    except Exception as e:
        print("Document {0} not inserted. An exception occurred: {1}".format(document, e))

# Insert multiple documents into the collection
async def insert_multiple_documents(documents):
    try:
        result = await collection.insert_many(documents)
        print("Documents {0} inserted successfully.".format(documents))
    except Exception as e:
        print("Documents {0} not inserted. An exception occurred: {1}".format(documents, e))

# Find a single document from the collection
async def find_document(document):
    try:
        result = await collection.find_one(document)
        print("Found document {0}.".format(document))
    except Exception as e:
        print("Document {0} not found. An exception occurred: {1}".format(document, e))

# Find multiple documents from the collection
async def find_multiple_documents(documents):
    try:
        result = await collection.find(documents)
        print("Found documents {0}.".format(documents))
    except Exception as e:
        print("Documents {0} not found. An exception occurred: {1}".format(documents, e))

# Update a single document in the collection
async def update_document(document, update):
    try:
        result = await collection.update_one(document, update)
        print("Updated document {0}.".format(document))
    except Exception as e:
        print("Document {0} not updated. An exception occurred: {1}".format(document, e))

# Update multiple documents in the collection
async def update_multiple_documents(documents, update):
    try:
        result = await collection.update_many(documents, update)
        print("Updated documents {0}.".format(documents))
    except Exception as e:
        print("Documents {0} not updated. An exception occurred: {1}".format(documents, e))

# Delete a single document from the collection
async def delete_document(document):
    try:
        result = await collection.delete_one(document)
        print("Deleted document {0}.".format(document))
    except Exception as e:
        print("Document {0} not deleted. An exception occurred: {1}".format(document, e))

# Delete multiple documents from the collection
async def delete_multiple_documents(documents):
    try:
        result = await collection.delete_many(documents)
        print("Deleted documents {0}.".format(documents))
    except Exception as e:
        print("Documents {0} not deleted. An exception occurred: {1}".format(documents, e))

# Delete all documents from the collection
async def delete_all_documents():
    try:
        result = await collection.delete_many({})
        print("Deleted all documents.")
    except Exception as e:
        print("Documents not deleted. An exception occurred: {0}".format(e))

# Drop the collection
async def drop_collection():
    try:
        result = await collection.drop()
        print("Dropped collection.")
    except Exception as e:
        print("Collection not dropped. An exception occurred: {0}".format(e))

# Run the functions
async def main():
    await insert_document({"1": "1"})
    await insert_multiple_documents([{"2": "2"}, {"3": "3"}])
    await find_document({"1": "1"})
    await find_multiple_documents([{"1": "1"}, {"2": "2"}])
    await update_document({"3": "3"}, {"$set": {"4": "4"}})
    await update_multiple_documents([{"1": "1"}, {"2": "2"}], {"$set": {"4": "4"}})
    await delete_document({"test": "test"})
    await delete_all_documents()
    await drop_collection()

if __name__ == "__main__":
    """
    The main entry point for the bot.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    print("Starting tests...")
    # Run the main function
    asyncio.run(main())
