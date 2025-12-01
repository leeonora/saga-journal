import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import cdist
from datetime import datetime

# - this should be loaded from embeddings_sbert.py
import numpy as np 
from sentence_transformers import SentenceTransformer

# cross encoder 
from sentence_transformers import CrossEncoder

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

# For testing run-time

import time

def timed(fn):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        end = time.perf_counter()
        print(f"[RUNTIME] {fn.__name__}: {(end - start):.4f} seconds\n")
        return result
    return wrapper




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


# BENCHMARKING 
# a mock query which clearly matches some of the summaries, and none of the others

mock_query = "I'm sad today and I don't know why."

mock_summaries = [
    # Relevant
    "You wrote about feeling lonely and uncertain about your future.",
    "You reflected on a tough week and mentioned struggling with motivation.",
    "You described a day when everything felt overwhelming and you couldn’t shake the sadness.",
    "You journaled about missing your friends and feeling emotionally exhausted.",
    "You wrote that you’ve been having trouble finding joy in things you used to love.",
    # Non-relevant
    "You wrote about a character named Susanne, who lives alone.",
    "You wrote a journal entry about moving out of your first apartment, which is a mixed experience for you.",
    "You described a road trip you took with your cousin through the mountains.",
    "You journaled about starting a new job and meeting your coworkers.",
    "You wrote a reflection about learning to cook a new recipe.",
    "You mentioned how excited you are for your upcoming vacation.",
    "You described finishing a big project and feeling proud of yourself.",
    "You wrote about going for a long run and enjoying the fresh air.",
    "You journaled about reading a book that inspired you about feeling alright.",
    "You wrote about adopting a cat and how playful it is."
]

labels = [1]*5 + [0]*10 # 5 relevant, 10 non-relevant

# query embedding
query_embedding = get_embedding(mock_query).reshape(1, -1)
    
# summary embeddings
summary_embeddings = np.array([get_embedding(summary) for summary in mock_summaries])

@timed
def test_cosine_similarity_benchmark():

    # query embedding
    #query_embedding = get_embedding(mock_query).reshape(1, -1)
    
    # summary embeddings
    #summary_embeddings = np.array([get_embedding(summary) for summary in mock_summaries])

    # compute similarities
    similarities = cosine_similarity(query_embedding, summary_embeddings)

    # rank summaries by similarity
    ranked_indices = np.argsort(similarities[0])[::-1]  # descending order
    ranked_labels = [labels[i] for i in ranked_indices]

    # Calculate precision at k (k=5)
    k = 5
    top_k_labels = ranked_labels[:k]
    precision_at_k = sum(top_k_labels) / k

    # print("Ranked indices:", ranked_indices)
    # print the mock summary corresponding to the top ranked index
    # print("Top ranked summary:", mock_summaries[ranked_indices[0]])

    #print("\nTop 5 ranked summaries:")
    #for i in ranked_indices[:5]:
    #    print(f"Index {i}: label={labels[i]}, score={similarities[0][i]:.4f}")
    #    print(f" → {mock_summaries[i]}\n")


    #print("Ranked labels:", ranked_labels)
    #print(f"Precision at {k}: {precision_at_k}")
    return similarities

# def test_manhattan_distance_benchmark():

#     # query embedding
#     #query_embedding = get_embedding(mock_query).reshape(1, -1)
    
#     # summary embeddings
#     #summary_embeddings = np.array([get_embedding(summary) for summary in mock_summaries])

#     # compute Manhattan (L1) distances
#     distances = cdist(query_embedding, summary_embeddings, metric='cityblock')[0]

#     # convert distances to similarities (invert — smaller distance = higher similarity)
#     similarities = 1 / (1 + distances)

#     # rank summaries by similarity
#     ranked_indices = np.argsort(similarities)[::-1]  # descending
#     ranked_labels = [labels[i] for i in ranked_indices]

#     # Calculate precision at k (k=5)
#     k = 5
#     top_k_labels = ranked_labels[:k]
#     precision_at_k = sum(top_k_labels) / k

#     print("Ranked indices:", ranked_indices)
#     print("Top ranked summary:", mock_summaries[ranked_indices[0]])

#     print("\nTop 5 ranked summaries:")
#     for i in ranked_indices[:5]:
#         print(f"Index {i}: label={labels[i]}, score={similarities[i]:.4f}")
#         print(f" → {mock_summaries[i]}\n")

#     print("Ranked labels:", ranked_labels)
#     print(f"Precision at {k}: {precision_at_k:.3f}")

## Hybrid search 


def calc_datetime_score(entry_date_str):
    """ Calculate a recency score based on the date string in ISO format. """
    entry_date = datetime.fromisoformat(entry_date_str)
    current_date = datetime.now()
    delta_days = (current_date - entry_date).days
    # Simple scoring: more recent dates get higher scores
    return 1 / (1 + delta_days)  #  inverse of days since entry
 
def hybrid_similarity(semantic_scores, datetime_scores, alpha=0.7):
    """
    Combines semantic similarity with datetime score.
    alpha: weight for semantic similarity
    1 - alpha: weight for datetime
    """
    semantic_scores = np.array(semantic_scores)
    datetime_scores = np.array(datetime_scores)

    # Optional: normalize datetime scores to [0, 1]
    datetime_scores_norm = datetime_scores / (np.max(datetime_scores) + 1e-8)

    return alpha * semantic_scores + (1 - alpha) * datetime_scores_norm
 
@timed
def test_hybrid_search_with_datetime_benchmark(semantic_scores = test_cosine_similarity_benchmark()):

    
    summary_dates = [
        "2025-11-05", "2025-11-01", "2025-10-25", "2025-11-04", "2025-10-20",
        "2025-09-15", "2025-08-01", "2025-07-22", "2025-06-30", "2025-05-01",
        "2025-04-15", "2025-03-01", "2025-02-20", "2025-01-10", "2024-12-25"
    ]

    similarities = cosine_similarity(query_embedding, summary_embeddings)
    semantic_scores = np.array(similarities).flatten()

    datetime_scores = np.array([calc_datetime_score(date_str) for date_str in summary_dates])

    hybrid_scores = hybrid_similarity(semantic_scores, datetime_scores, alpha=0.7)

    ranked_indices = np.argsort(hybrid_scores)[::-1]
    ranked_labels = [labels[i] for i in ranked_indices]

    # Step 5: Evaluate precision@k
    k = 5
    top_k_labels = ranked_labels[:k]
    precision_at_k = sum(top_k_labels) / k

    #print("HYBRID SEARCH WITH DATETIME SCORES\n")
    #print("Ranked indices:", ranked_indices)
    #print("Top ranked summary:", mock_summaries[ranked_indices[0]])

    #print("\nTop 5 ranked summaries with datetime hybrid:")
    #for i in ranked_indices[:5]:
    #    print(f"Index {i}: label={labels[i]}, score={hybrid_scores[i]:.4f}")
    #    print(f" → {mock_summaries[i]}\n")

    # print(f"Precision at {k}: {precision_at_k:.3f}")

model_cross = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
#https://sbert.net/docs/cross_encoder/usage/usage.html
@timed
def test_crossencoder_hybrid_search_benchmark():

    # compute similarities
    similarities = cosine_similarity(query_embedding, summary_embeddings)

    # rank summaries by similarity
    ranked_indices = np.argsort(similarities[0])[::-1]  # descending order
    ranked_labels = [labels[i] for i in ranked_indices]

    # Calculate precision at k (k=10)
    k = 10
    top_k_labels = ranked_labels[:k]
    precision_at_k = sum(top_k_labels) / k

    # print("Ranked indices:", ranked_indices)
    # print the mock summary corresponding to the top ranked index0.8
    # print("Top ranked summary:", mock_summaries[ranked_indices[0]])

    # Now use cross-encoder to re-rank top 10
    top_indices = ranked_indices[:k]
    top_summaries = [mock_summaries[i] for i in top_indices]

    ranks = model_cross.rank(mock_query, top_summaries)
    # print("\nTop 10 ranked summaries after Cross-Encoder re-ranking:")

    reranked_indices = [top_indices[r['corpus_id']] for r in ranks]
    reranked_labels = [labels[i] for i in reranked_indices]
    precision_at_k = sum(reranked_labels[:5]) / 5

    # print("\nTop 10 ranked summaries after Cross-Encoder re-ranking:\n")
    
    #for r in ranks:
    #    idx = top_indices[r['corpus_id']]
    #    print(f"{r['score']:.4f}\t label={labels[idx]}\t → {mock_summaries[idx]}")
    #
    #print(f"\nPrecision@{k} after CrossEncoder reranking: {precision_at_k:.3f}")    



# Gives better precision at k than pure cosine similarity !! 
# But higher computational cost due to cross-encoder
# Gives 


if __name__ == "__main__":
    test_cosine_similarity_benchmark()
    #test_manhattan_distance_benchmark()
    test_hybrid_search_with_datetime_benchmark()
    test_crossencoder_hybrid_search_benchmark()

    



