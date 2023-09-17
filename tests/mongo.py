import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['doggobot']

# Make unit_test by creating a new collection and inserting a document.
db['unit_test'].insert_one({'test': 'test'})

# Print all collections in the database.
collections = db.list_collection_names()
print(collections)

# Print values in the unit_test collection.
for collection in collections:
    print(db[collection].find_one())
    

# Get all collections in the database.
collections = db.list_collection_names()

# Delete all collections in the database.
for collection in collections:
    db[collection].drop()

