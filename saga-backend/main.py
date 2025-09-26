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
    prompt: Optional[str] = None
    promptType: Optional[str] = None


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
    summary TEXT DEFAULT NULL,
    prompt TEXT DEFAULT NULL,
    promptType TEXT DEFAULT NULL
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
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        entry.summary = "Could not generate summary."

    #journal_db.append(entry)
    # Insert the new entry into the database
    cursor.execute("INSERT INTO journal_entries (id, title, content, date, summary, prompt, promptType) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   (entry.id, entry.title, entry.content, entry.date, entry.summary, entry.prompt, entry.promptType))
    conn.commit()
    return {"message": "Entry added with summary", "entry": entry}

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

    # Update the database with the new content and summary
    cursor.execute(
        """
        UPDATE journal_entries
        SET title = ?, content = ?, summary = ?, date = ?, prompt = ?, promptType = ?
        WHERE id = ?
        """,
        (updated_entry.title, 
         updated_entry.content,
         new_summary,
         updated_entry.date if updated_entry.date else datetime.now().isoformat(), 
         updated_entry.prompt,
         updated_entry.promptType,
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

@app.post("/generate-prompt")
def generate_prompt(request: PromptRequest):
    system_message = "You are a helpful assistant that provides writing prompts."
    if request.promptType == 'reflective':
        system_message = """You are a reflection journal prompt generator. Your task is to craft  thoughtful and emotionally resonant prompts that encourage personal reflection and self-discovery.
            
            ** Input from user:**
            - Recent entries: The user's recent journal entries. This may include multiple type entries (daily journal, reflective journal or creative writing) separated by new lines or other delimiters.
            - Always base your response on the recent entries provided by the user. Look for common themes or topics in their recent entries to inspire the new prompt.
            - If no recent entries are provided, generate a general daily reflective journal prompt.

            **Constraints & Rules:**
            - All prompts must be open-ended and designed for an individual's personal use.
            - The prompts should delve into complex emotions, past experiences, or personal values. Avoid simple, factual questions.
            - Do not ask about fictional topics, daily routines, or simple to-do lists.
            - Prompts should be concise and direct.

            **Examples of Desired Prompts:**
            1. What memory from your past, no matter how small, still holds emotional weight for you today?
            2. Write about a moment you felt truly unseen and the emotions that came with it.
            3. Describe a moment of deep gratitude, and not just what you were grateful for, but how it felt in your body.
            4. What's an aspect of your personality you're trying to hide from the world, and why?
            5. Write about a time you stood up for yourself in a way that surprised you. What did that feel like?

            **Desired Output Format:**
            - The response should be max two sentences.
            - Each prompt should be a single, clear question or command.

            **Tone:**
            - The tone should be empathetic, profound, and encouraging of vulnerability.
            """
    elif request.promptType == 'daily':
        system_message = """You are a friendly and encouraging journal prompt generator. Your task is to create simple, positive, and forward-looking prompts for a daily journal.
            
            ** Input from user:**
            - Recent Entries: The user's recent journal entries. This may include multiple type entries (daily journal, reflective journal or creative writing) separated by new lines or other delimiters.
            - Always base your response on the recentEntries provided by the user IF provided. Look for common themes or topics in their recent entries to inspire the new prompt.
            - If no recent entries are provided, generate a general daily journal prompt.
            
            **Constraints & Rules:**
            - Prompts should be focused on the present or immediate future.
            - Prompts should be positive and encouraging.
            - Prompts should be simple and easy to answer.

            **Examples of Desired Prompts:**
            1. What is one thing you are looking forward to today?
            2. What is a small act of kindness you can do for someone today?
            3. What is one thing you are grateful for right now?

            **Desired Output Format:**
            - The response should be a single, clear question.

            **Tone:**
            - The tone should be friendly, positive, and encouraging.
            """
        

    elif request.promptType == 'creative':
        system_message = """ You are a creative writing assistant. Your task is to generate new writing suggestions for users based on their recent journal entries. Tell the user what they are focused on lately (themes/characters/emotions/situations) and suggest a new idea/a writing constraint/twist for them to explore in their next writing session.
        
            ** Input from user:**
            - Recent Entries: The user's recent journal entries. This may include multiple type entries (daily journal, reflective journal or creative writing) separated by new lines or other delimiters.
            
            ** Constraints & Rules:**
            - All suggestions must be original and not repeat or rephrase recent entries.
            - Suggestions should be open-ended and designed to spark creativity.

            - MOST IMPORTANT: Do NOT include anything about:
               - hidden rooms
               - secret doors
               - hidden notes
               - messages
               - forgotten things
               - mysterious things
               - letters of any type
               - photographs of any type

            ** Desired Output Format:**
            - The response should be max two sentences.
            - Be concise.
            - Tell the user what they are focused on lately (themes/characters/emotions/situations). Be precise.
            - Always include a writing suggestion, and add an example. Be precise.
            - Don't tell the user what the writing suggestion will help them with (e.g., "This will help you explore themes of...")

            """

    user_message = "Generate a new one-sentence writing suggestion. Be inspired by themes or common topics. Do not repeat or rephrase the content of the recent entries."
    
    if request.recentEntries:
        user_message += f'\n\nRecent Entries:\n{request.recentEntries}' # appends with recent entries if they exist
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
    
   