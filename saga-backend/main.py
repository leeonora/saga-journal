from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

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

class JournalEntry(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    date: Optional[str] = None
    summary: Optional[str] = None

# Fake in-memory DB (resets if you restart)
journal_db: List[JournalEntry] = []

@app.get("/")
def home():
    return {"message": "Welcome to Journal API"}

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

    journal_db.append(entry)
    return {"message": "Entry added with summary", "entry": entry}

@app.get("/journal/")
def get_entries():
    return {"entries": journal_db}

@app.put("/journal/{entry_id}")
def update_entry(entry_id: str, updated_entry: JournalEntry):
    for index, entry in enumerate(journal_db):
        if entry.id == entry_id:
            journal_db[index].title = updated_entry.title
            journal_db[index].content = updated_entry.content
            return {"message": f"Entry with id {entry_id} updated successfully", "entry": journal_db[index]}
    raise HTTPException(status_code=404, detail="Entry not found")

@app.delete("/journal/{entry_id}")
def delete_entry(entry_id: str):
    global journal_db
    initial_length = len(journal_db)
    journal_db = [entry for entry in journal_db if entry.id != entry_id]
    
    if len(journal_db) < initial_length:
        return {"message": f"Entry with id {entry_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Entry not found")

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
