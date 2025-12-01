import pytest
import sqlite3

# fake memory for test_db unittests.

@pytest.fixture
def db_connection():
    """
    Creates an in-memory database for testing. 
    It creates the table, yields the connection to the test, 
    and closes it afterwards.
    """
    # Use :memory: for a temporary RAM-only database
    conn = sqlite3.connect(":memory:") 
    cursor = conn.cursor()
    
    # Re-create your EXACT table schema here
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS journal_entries (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        summary TEXT DEFAULT NULL,
        prompt TEXT DEFAULT NULL,
        promptType TEXT DEFAULT NULL,
        summaryEmbedding BLOB,
        use_for_prompt_generation BOOLEAN DEFAULT TRUE
    );
    """)
    conn.commit()
    
    yield conn  # Pass connection to the test
    
    conn.close() # Cleanup after test is done