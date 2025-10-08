from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def calc_similarity(query, doc):
    similarity = model.similarity(query, doc)
    return similarity 

# print(model.similarity_fn_name) # should print cosine, can be edited to other similarity functions