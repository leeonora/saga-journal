import pytest
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


@pytest.fixture
def sample_text():
    return "This is a sample text for generating embeddings."

@pytest.fixture
def sample_embedding(sample_text):
    """Creates a real embedding to use in other tests"""
    return get_embedding(sample_text)

#
# tests, these are converted from tests performed during development (written by Benedicte) into Pytests with the help of Gemini.
# they test whether the embedding functions work as expected:
# ... because the embedding needs to be saved in .db as a BLOB and not numpy array directly. But it needs to be converted back when retrieved.
#  

def test_get_embedding_returns_valid_numpy_array(sample_text):
    """Test if the model returns a numpy array with the correct shape."""
    embedding = get_embedding(sample_text)
    
    # Check type
    assert isinstance(embedding, np.ndarray)
    
    # Check shape: 'all-MiniLM-L6-v2' produces 384-dimensional vectors
    assert embedding.shape == (384,)
    
    # Check content: Ensure it's not empty
    assert embedding.size > 0

def test_blob_conversion_roundtrip(sample_embedding):
    """Test that converting to blob and back restores the original array exactly."""
    # 1. Convert to Blob
    blob = embedding_to_blob(sample_embedding)
    
    # Check that it is actually bytes
    assert isinstance(blob, bytes)
    
    # 2. Convert back to Numpy
    restored_embedding = embedding_from_blob(blob)
    
    # 3. Assert Equality
    # We use numpy's built-in testing assertion which is safer for floats
    np.testing.assert_array_equal(sample_embedding, restored_embedding)

def test_blob_conversion_with_random_data():
    """
    Test the conversion logic isolated from the ML model.
    This ensures the blob logic works even if the model changes.
    """
    # Create a random numpy array resembling an embedding
    dummy_array = np.random.rand(384).astype(np.float32)
    
    blob = embedding_to_blob(dummy_array)
    restored = embedding_from_blob(blob)
    
    np.testing.assert_array_equal(dummy_array, restored)

def test_empty_string_behavior():
    """Edge case: Ensure an empty string doesn't crash the model."""
    text = ""
    embedding = get_embedding(text)
    assert embedding.shape == (384,)