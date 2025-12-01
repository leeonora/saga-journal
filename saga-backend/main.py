from urllib import request
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

# import from other folders
from services.sbert.embeddings_sbert import get_embedding, embedding_to_blob, embedding_from_blob  # the embedding function for db
from services.openAI.system_messages import reflective_mode, daily_mode, creative_mode

# load env variables
load_dotenv()

# init openai client
client = openai.OpenAI()

# init FastAPI app
app = FastAPI()
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

# ensure correct data types w. pydantic
class JournalEntry(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    date: Optional[str] = None
    summary: Optional[str] = None
    prompt: Optional[str] = None
    promptType: Optional[str] = None
    summaryEmbedding: Optional[bytes] = None  # Store embedding as bytes
    use_for_prompt_generation: Optional[bool] = True


# create connection and cursor
conn = sqlite3.connect('journal.db', check_same_thread=False) # the connection between the app and the db
cursor = conn.cursor() # the object that executes SQL commands (translator)

# create table if it doesn't exist (only runs once, even when restarting the app)
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
conn.commit() # save changes



@app.get("/") # home route
def home():
    return {"message": "Welcome to Journal API"}


# POST: add new entry to the .db database
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

        # generate embedding for the summary
        embedding = get_embedding(entry.summary)
        #entry.summaryEmbedding = embedding.tobytes() # sqllite does not support numpy.ndarray. Convert to bytes for storage
        entry.summaryEmbedding = embedding_to_blob(embedding) # alternative way to convert to blob
    
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        entry.summary = "Could not generate summary."

    
    # insert the new entry into the database
    cursor.execute("INSERT INTO journal_entries (id, title, content, date, summary, prompt, promptType, summaryEmbedding, use_for_prompt_generation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                   (entry.id, entry.title, entry.content, entry.date, entry.summary, entry.prompt, entry.promptType, entry.summaryEmbedding, entry.use_for_prompt_generation))
    conn.commit()

    # return entry without embedding (internal only)
    entry_dict = entry.model_dump()
    entry_dict.pop("summaryEmbedding", None)

    return {"message": "Entry added with summary", "entry": entry_dict}

#GET: fetch all entries from the .db database
@app.get("/journal/")
def get_entries(search: Optional[str] = None):
    if search:
        cursor.execute("SELECT id, title, content, date, summary, prompt, promptType, use_for_prompt_generation FROM journal_entries WHERE title LIKE ? OR content LIKE ?", (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT id, title, content, date, summary, prompt, promptType, use_for_prompt_generation FROM journal_entries")
    rows = cursor.fetchall()
    entries = [{"id": row[0], "title": row[1], "content": row[2], "date": row[3], "summary": row[4], "prompt": row[5], "promptType": row[6], "use_for_prompt_generation": row[7]} for row in rows]
    conn.commit()
    return {"entries": entries}


# PUT: update an existing entry in the .db database
@app.put("/journal/{entry_id}")
def update_entry(entry_id: str, updated_entry: JournalEntry):
    # fetch the original entry from the database
    cursor.execute("SELECT content, summary, prompt, promptType FROM journal_entries WHERE id = ?", (entry_id,))
    original_entry_row = cursor.fetchone()

    if not original_entry_row:
        raise HTTPException(status_code=404, detail="Entry not found")

    original_content, original_summary, original_prompt, original_promptType = original_entry_row

    new_summary = original_summary
    # if the content has changed, generate a new summary
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

    # update the database with the new content and summary
    cursor.execute(
        """
        UPDATE journal_entries
        SET title = ?, content = ?, summary = ?, date = ?, prompt = ?, promptType = ?, summaryEmbedding = ?, use_for_prompt_generation = ?
        WHERE id = ?
        """,
        (updated_entry.title,
         updated_entry.content,
         new_summary,
         updated_entry.date if updated_entry.date else datetime.now().isoformat(),
         updated_entry.prompt,
         updated_entry.promptType,
         new_embedding,
         updated_entry.use_for_prompt_generation,
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
        "promptType": updated_entry.promptType,
        "use_for_prompt_generation": updated_entry.use_for_prompt_generation
    }

    return {"entry": updated_entry_dict}



# DELETE: delete an entry from the .db database
@app.delete("/journal/{entry_id}")
def delete_entry(entry_id: str):
    cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": f"Entry with id {entry_id} deleted successfully"}

class PromptRequest(BaseModel):
    promptType: str
    recentEntries: List[JournalEntry]
    customPrompt: Optional[str] = None

# POST II: generate a writing prompt based on query (RAG)
@app.post("/generate-prompt")
def generate_prompt(request: PromptRequest):
    # ----- SYSTEM MESSAGE -----
    if request.promptType == "reflective":
        system_message = reflective_mode
    elif request.promptType == "daily":
        system_message = daily_mode
    elif request.promptType == "creative":
        system_message = creative_mode
    else:
        system_message = "You are a helpful assistant that provides writing prompts."

    # ----- USER MESSAGE BASE -----
    if request.customPrompt:
        user_message = request.customPrompt
    else:
        user_message = (
            "Generate a new one-sentence writing suggestion. "
            "Be inspired by themes or common topics. "
            "Do not repeat or rephrase the content of the recent entries."
        )

    # ----- OPTIONAL RAG FOR CUSTOM PROMPT -----
    similar_contents_text = ""
    if request.customPrompt:
        query_embedding = get_embedding(user_message)

        cursor.execute("""
            SELECT id, summaryEmbedding
            FROM journal_entries
            WHERE use_for_prompt_generation = 1
        """)

        rows = cursor.fetchall()

        # keep ids and embeddings aligned (only rows with an embedding)
        entries_with_emb = [(row[0], row[1]) for row in rows if row[1] is not None]
        entry_ids = [r[0] for r in entries_with_emb]
        summary_embeddings = [embedding_from_blob(r[1]) for r in entries_with_emb]

        if summary_embeddings:
            similarities = cosine_similarity(
                query_embedding.reshape(1, -1), summary_embeddings
            )[0]
            similar_entries = sorted(
                zip(entry_ids, similarities), key=lambda item: item[1], reverse=True
            )
            top_similar_entries = similar_entries[:5]

            cursor.execute(
                "SELECT content FROM journal_entries WHERE id IN ({seq})".format(
                    seq=",".join(["?"] * len(top_similar_entries))
                ),
                tuple([entry[0] for entry in top_similar_entries]),
            )
            similar_contents = cursor.fetchall()
            similar_contents_text = "\n".join([content[0] for content in similar_contents])

    # ----- ATTACH CONTEXT FROM ENTRIES -----
    if request.recentEntries:
        # only include entries marked for prompt generation
        filtered_recent_entries = [
            e for e in request.recentEntries 
            if e.use_for_prompt_generation is not False  # treat None/True as allowed
        ]

        if filtered_recent_entries:
            recent_entries_text = "\n\n".join(e.content for e in filtered_recent_entries)

            if request.customPrompt and similar_contents_text:
                user_message += (
                    f"\n\nRecent entries (similar to your request):\n{similar_contents_text}"
                )
            else:
                user_message += f"\n\nRecent entries:\n{recent_entries_text}"


    # ----- CALL OPENAI -----
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=60,
        )
        prompt = response.choices[0].message.content.strip()
        return {"prompt": prompt}

    except Exception as e:
        print(f"Error calling OpenAI API for prompt generation: {e}")
        raise HTTPException(status_code=500, detail="Could not generate prompt.")
