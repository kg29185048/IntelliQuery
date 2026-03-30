# database/schema_extractor.py

def extract_full_schema(db, sample_size=5):
    schema = {}

    for collection_name in db.list_collection_names():
        samples = list(db[collection_name].find().limit(sample_size))

        fields = set()
        for doc in samples:
            for key in doc.keys():
                fields.add(key)

        schema[collection_name] = list(fields)

    return schema