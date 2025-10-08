import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# - this should be loaded from embeddings_sbert.py
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

# -----------------------------------------------------------


# Here we should also consider making tests for other similarity functions if we add them later
# Benchmark the different similarity methods with a standard known set of embeddings 


def test_cosine_similarity_with_reshaping():

    # Generate random embeddings for testing
    query_prompt = "I want to write about my bestie Emilie."
    query_prompt_embedding = get_embedding(query_prompt)

    # Simulate summary embeddings
    summary_prompts = [
        "Write about your best friend.",
        "Describe a memorable experience with a close friend.",
        "What qualities do you value most in a friendship?",
        "How has your friendship with Emilie influenced your life?",
        "Share a funny story involving you and your bestie."
    ]
    summary_embeddings = [get_embedding(prompt) for prompt in summary_prompts]


    # Reshape the query_embedding and convert summary_embeddings to a 2D array
    query_embedding_2d = query_prompt_embedding.reshape(1, -1)
    summary_embeddings_2d = np.array(summary_embeddings)

    # This should work without errors
    similarities = cosine_similarity(query_embedding_2d, summary_embeddings_2d)
    assert similarities.shape == (1, 5)