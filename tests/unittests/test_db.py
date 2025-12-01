import sqlite3
import numpy as np

# We need to test the database interactions:
# Not because we test SQLite, but because we need to ensure that the type of data is not lost:
# for instance, that Booleans remain Booleans, and that numpy arrays are properly stored as BLOBs and can be restored.
# the pytests are written with asssitance from Gemini.

# test booleans
def test_insert_and_retrieve_basic(db_connection):
    """Test that we can save and retrieve a standard entry."""
    cursor = db_connection.cursor()
    
    # Insert data
    cursor.execute("""
        INSERT INTO journal_entries (id, title, content, use_for_prompt_generation)
        VALUES (?, ?, ?, ?)
    """, ("uuid-1", "My Day", "Today was good.", False))
    db_connection.commit()
    
    # Retrieve data
    cursor.execute("SELECT title, content, use_for_prompt_generation FROM journal_entries WHERE id=?", ("uuid-1",))
    row = cursor.fetchone()
    
    assert row[0] == "My Day"
    assert row[1] == "Today was good."
    assert row[2] in [0, False] 

def test_default_values(db_connection):
    """Test that default values (True for prompt generation) are applied."""
    cursor = db_connection.cursor()
    
    # Insert without specifying 'use_for_prompt_generation'
    cursor.execute("""
        INSERT INTO journal_entries (id, title, content)
        VALUES (?, ?, ?)
    """, ("uuid-2", "Default Test", "Checking defaults"))
    db_connection.commit()
    
    cursor.execute("SELECT use_for_prompt_generation FROM journal_entries WHERE id=?", ("uuid-2",))
    row = cursor.fetchone()
    
    # Should default to TRUE (1)
    assert row[0] in [1, True]

# test blob storage
def test_blob_storage(db_connection):
    """Test storing the numpy embedding as a BLOB."""
    cursor = db_connection.cursor()
    
    # Create a dummy numpy array (simulation of your embedding)
    original_embedding = np.array([0.1, 0.5, -0.2], dtype=np.float32)
    # Convert to bytes
    embedding_bytes = original_embedding.tobytes()
    
    cursor.execute("""
        INSERT INTO journal_entries (id, title, content, summaryEmbedding)
        VALUES (?, ?, ?, ?)
    """, ("uuid-3", "Blob Test", "Testing Matrix", embedding_bytes))
    db_connection.commit()
    
    # Retrieve
    cursor.execute("SELECT summaryEmbedding FROM journal_entries WHERE id=?", ("uuid-3",))
    row = cursor.fetchone()
    retrieved_blob = row[0]
    
    # Convert back to numpy
    restored_embedding = np.frombuffer(retrieved_blob, dtype=np.float32)
    
    # Assert they are identical
    assert np.array_equal(original_embedding, restored_embedding)