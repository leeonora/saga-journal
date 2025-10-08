# Download: 
# pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
# pip install -U sentence-transformers
# https://www.sbert.net/ 
import numpy as np 
from sentence_transformers import SentenceTransformer

# Load pre-trained model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    # Generate embedding
    embedding = model.encode(text) # returns a numpy array
    return embedding

def embedding_to_blob(embedding):
    """ Convert numpy array to bytes for BLOB storage """ # Or JSON? 
    return embedding.tobytes()

def embedding_from_blob(blob):
    """ Convert bytes back to numpy array """
    return np.frombuffer(blob, dtype=np.float32)    


## UNIT TESTING -> convert to pytest later :)) 
if __name__ == "__main__":
    sample_text = "This is a sample text for generating embeddings."
    embedding = get_embedding(sample_text)
    embedding_blob = embedding_to_blob(embedding)
    restored_embedding = embedding_from_blob(embedding_blob)
    print("Original Embedding:", embedding)
    print("Restored Embedding:", restored_embedding)
    print("Are they equal?", np.array_equal(embedding, restored_embedding))
    # check what datatype the embedding is
    print(type(embedding)) #  <class 'numpy.ndarray'>,  sql cannot store as numpy array, need to convert to BLOB or list
    print(embedding.shape) # (384,) for 'all-MiniLM-L6-v2'