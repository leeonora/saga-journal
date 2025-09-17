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


# Fake memory storage (in-memory)
# journal_db: List[JournalEntry] = []

# Update: Using SQLite for persistent (local) storage

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
    summary TEXT DEFAULT NULL       
);
""")
conn.commit() # save changes



@app.get("/")
def home():
    return {"message": "Welcome to Journal API"}


# Add new entry to the .db database
@app.post("/journal/")
async def add_entry(entry: JournalEntry):
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
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        entry.summary = "Could not generate summary."

    #journal_db.append(entry)
    # Insert the new entry into the database
    cursor.execute("INSERT INTO journal_entries (id, title, content, summary) VALUES (?, ?, ?, ?)", 
                   (entry.id, entry.title, entry.content, entry.summary))
    conn.commit()
    return {"message": "Entry added with summary", "entry": entry}

# Fetch all entries from the .db database
@app.get("/journal/")
def get_entries():
    cursor.execute("SELECT id, title, content, date, summary FROM journal_entries")
    rows = cursor.fetchall()
    entries = [{"id": row[0], "title": row[1], "content": row[2], "date": row[3], "summary": row[4]} for row in rows]
    conn.commit()
    return {"entries": entries}


# @app.get("/journal/")
# def get_entries():
#     return {"entries": journal_db}

# @app.put("/journal/{entry_id}")
# def update_entry(entry_id: str, updated_entry: JournalEntry):
#     for index, entry in enumerate(journal_db):
#         if entry.id == entry_id:
#             journal_db[index].title = updated_entry.title
#             journal_db[index].content = updated_entry.content
#             return {"message": f"Entry with id {entry_id} updated successfully", "entry": journal_db[index]}
#     raise HTTPException(status_code=404, detail="Entry not found")

@app.put("/journal/{entry_id}")
def update_entry(entry_id: str, updated_entry: JournalEntry):
    # Fetch the original entry from the database
    cursor.execute("SELECT content, summary FROM journal_entries WHERE id = ?", (entry_id,))
    original_entry_row = cursor.fetchone()

    if not original_entry_row:
        raise HTTPException(status_code=404, detail="Entry not found")

    original_content, original_summary = original_entry_row

    new_summary = original_summary
    # If the content has changed, generate a new summary
    if updated_entry.content != original_content:
        prompt_text = f"""Summarize this journal post in one short sentence, in the second person in past tense: "{updated_entry.content}"""
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

    # Update the database with the new content and summary
    cursor.execute(
        """
        UPDATE journal_entries
        SET title = ?, content = ?, summary = ?, date = ?
        WHERE id = ?
        """,
        (updated_entry.title, 
         updated_entry.content,
         new_summary,
         updated_entry.date if updated_entry.date else datetime.now().isoformat(), 
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
        "date": updated_entry.date if updated_entry.date else datetime.now().isoformat()
    }

    return {"entry": updated_entry_dict}


# @app.delete("/journal/{entry_id}")
# def delete_entry(entry_id: str):
#     global journal_db
#     initial_length = len(journal_db)
#     journal_db = [entry for entry in journal_db if entry.id != entry_id]
    
#     if len(journal_db) < initial_length:
#         return {"message": f"Entry with id {entry_id} deleted successfully"}
#     else:
#         raise HTTPException(status_code=404, detail="Entry not found")

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

@app.post("/generate-prompt")
async def generate_prompt(request: PromptRequest):
    system_message = "You are a helpful assistant that provides writing prompts."
    if request.promptType == 'journal':
        system_message = "You are an insightful assistant that provides journal prompts to encourage self-reflection."
    elif request.promptType == 'creative':
        system_message = "You are a creative assistant that provides imaginative prompts for creative writing."

    user_message = "Based on the following recent entries, generate a new writing prompt."
    if request.recentEntries:
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
            max_tokens=100
        )
        prompt = response.choices[0].message.content.strip()
        return {"prompt": prompt}
    except Exception as e:
        print(f"Error calling OpenAI API for prompt generation: {e}")
        raise HTTPException(status_code=500, detail="Could not generate prompt.")
