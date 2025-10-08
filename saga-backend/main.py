from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
import sqlite3
from sklearn.metrics.pairwise import cosine_similarity
# Import from other folders
from services.sbert.embeddings_sbert import get_embedding, embedding_to_blob, embedding_from_blob  # Import the embedding function
from services.openAI.system_messages import reflective_mode, daily_mode, creative_mode

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = openai.OpenAI()

app = FastAPI()

# Allow locally hosted api to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
          # Allows requests from your local machine
    ],
    allow_credentials=True,
    allow_methods=[
        "*"
    ],
    allow_headers=[
        "*"
    ],
)

# Pydantic model for journal entry, ensure correct data types
class JournalEntry(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    date: Optional[str] = None
    summary: Optional[str] = None
    prompt: Optional[str] = None
    promptType: Optional[str] = None
    summaryEmbedding: Optional[bytes] = None  # Store embedding as bytes


# Create connection and cursor
conn = sqlite3.connect('journal.db', check_same_thread=False) # the connection between the app and the db
cursor = conn.cursor() # the object that executes SQL commands (translator)

# Create table if it doesn't exist (only runs once, even when you restart the app)
cursor.execute("""
CREATE TABLE IF NOT EXISTS journal_entries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    summary TEXT DEFAULT NULL,
    prompt TEXT DEFAULT NULL,
    promptType TEXT DEFAULT NULL,
    summaryEmbedding BLOB
);
""")
conn.commit() # save changes



@app.get("/")
def home():
    return {"message": "Welcome to Journal API"}


# Add new entry to the .db database
@app.post("/journal/")
def add_entry(entry: JournalEntry):
    entry.id = str(uuid.uuid4())
    if not entry.date:
        entry.date = datetime.now().isoformat()

    prompt_text = f"Summarize this journal post in one short sentence, in the second person in past tense: \"{entry.content}\""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You summarize journal entries in a single sentence."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=60
        )
        summary_text = response.choices[0].message.content.strip()
        entry.summary = summary_text

        # Generate embedding for the summary
        embedding = get_embedding(entry.summary)
        #entry.summaryEmbedding = embedding.tobytes() # sqllite does not support numpy.ndarray. Convert to bytes for storage
        entry.summaryEmbedding = embedding_to_blob(embedding) # alternative way to convert to blob
    
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        entry.summary = "Could not generate summary."

    
    # Insert the new entry into the database
    cursor.execute("INSERT INTO journal_entries (id, title, content, date, summary, prompt, promptType, summaryEmbedding) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                   (entry.id, entry.title, entry.content, entry.date, entry.summary, entry.prompt, entry.promptType, entry.summaryEmbedding))
    conn.commit()

    # Return entry without embedding (internal only)
    entry_dict = entry.model_dump()
    entry_dict.pop("summaryEmbedding", None)

    return {"message": "Entry added with summary", "entry": entry_dict}

# Fetch all entries from the .db database
@app.get("/journal/")
def get_entries():
    cursor.execute("SELECT id, title, content, date, summary, prompt, promptType FROM journal_entries")
    rows = cursor.fetchall()
    entries = [{"id": row[0], "title": row[1], "content": row[2], "date": row[3], "summary": row[4], "prompt": row[5], "promptType": row[6]} for row in rows]
    conn.commit()
    return {"entries": entries}


@app.put("/journal/{entry_id}")
def update_entry(entry_id: str, updated_entry: JournalEntry):
    # Fetch the original entry from the database
    cursor.execute("SELECT content, summary, prompt, promptType FROM journal_entries WHERE id = ?", (entry_id,))
    original_entry_row = cursor.fetchone()

    if not original_entry_row:
        raise HTTPException(status_code=404, detail="Entry not found")

    original_content, original_summary, original_prompt, original_promptType = original_entry_row

    new_summary = original_summary
    # If the content has changed, generate a new summary
    if updated_entry.content != original_content:
        prompt_text = f"""Summarize this journal post in one short sentence, in the second person in past tense: \"{updated_entry.content}\""""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You summarize journal entries in a single sentence."},
                    {"role": "user", "content": prompt_text}
                ],
                max_tokens=60
            )
            new_summary = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            new_summary = "Could not generate summary."

    new_embedding = None
    if new_summary != original_summary:
        embedding = get_embedding(new_summary)
        new_embedding = embedding.tobytes()

    # Update the database with the new content and summary
    cursor.execute(
        """
        UPDATE journal_entries
        SET title = ?, content = ?, summary = ?, date = ?, prompt = ?, promptType = ?, summaryEmbedding = ?
        WHERE id = ?
        """,
        (updated_entry.title,
         updated_entry.content,
         new_summary,
         updated_entry.date if updated_entry.date else datetime.now().isoformat(),
         updated_entry.prompt,
         updated_entry.promptType,
         new_embedding,
         entry_id)
    )
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    updated_entry_dict = {
        "id": entry_id,
        "title": updated_entry.title,
        "content": updated_entry.content,
        "summary": new_summary,
        "date": updated_entry.date if updated_entry.date else datetime.now().isoformat(),
        "prompt": updated_entry.prompt,
        "promptType": updated_entry.promptType
    }

    return {"entry": updated_entry_dict}




@app.delete("/journal/{entry_id}")
def delete_entry(entry_id: str):
    cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": f"Entry with id {entry_id} deleted successfully"}

class PromptRequest(BaseModel):
    promptType: str
    recentEntries: str
    customPrompt: Optional[str] = None

@app.post("/generate-prompt")
def generate_prompt(request: PromptRequest):
    
    
    ### User message construction
    if request.customPrompt:
        user_message = request.customPrompt

        #################  RAG - retrieve similar entries based on embedding similarity #########################
        
        query_embedding = get_embedding(user_message) # get embedding for the custom prompt

        # fetch all journal entry embeddings from db
        cursor.execute("SELECT id, summaryEmbedding FROM journal_entries")
        rows = cursor.fetchall()

        entry_ids = [row[0] for row in rows]
        summary_embeddings = [embedding_from_blob(row[1]) for row in rows if row[1] is not None]

        if summary_embeddings:
            similarities = cosine_similarity(query_embedding.reshape(1, -1), summary_embeddings)[0] # Edit here for other similarity measures

            # Get top 5 most similar entries
            similar_entries = sorted(zip(entry_ids, similarities), key=lambda item: item[1], reverse=True)
            top_similar_entries = similar_entries[:5]

            # fetch the content of the top similar entries
            cursor.execute("SELECT content FROM journal_entries WHERE id IN ({seq})".format(
                seq=','.join(['?']*len(top_similar_entries))
            ), tuple([entry[0] for entry in top_similar_entries]))
            similar_contents = cursor.fetchall()

            similar_contents_text = "\n".join([content[0] for content in similar_contents])
        
        #################################################### - ####################################################

    else:
        user_message = "Generate a new one-sentence writing suggestion. Be inspired by themes or common topics. Do not repeat or rephrase the content of the recent entries."   
    

    ### System message construction 
    if request.promptType == 'reflective':
        system_message = reflective_mode
    elif request.promptType == 'daily':
        system_message = daily_mode
    elif request.promptType == 'creative':
        system_message = creative_mode
    else:
        system_message = "You are a helpful assistant that provides writing prompts."


    ### Append recent entries if available, and if no custom prompt is provided

    if request.recentEntries:
        if request.customPrompt and summary_embeddings: # custom prompt with RAG 
            user_message += f'\n\nRecent Entries:\n{similar_contents_text}'
        else:
            user_message += f'\n\nRecent Entries:\n{request.recentEntries}'
    else:
        user_message = "Generate a writing prompt."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=60
        )
        prompt = response.choices[0].message.content.strip()
        return {"prompt": prompt}
    
    except Exception as e:
        print(f"Error calling OpenAI API for prompt generation: {e}")
        raise HTTPException(status_code=500, detail="Could not generate prompt.")
    
   