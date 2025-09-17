# Project Overview

This is a web-based journaling application called "Saga Journal". It consists of a frontend built with Next.js and a backend API built with Python and FastAPI. The application allows users to create, view, edit, and delete journal entries. It also leverages the OpenAI API to automatically generate summaries for new entries and to provide writing prompts.

## Backend (saga-backend)

*   **Framework:** FastAPI
*   **Language:** Python
*   **Database:** SQLite
*   **Key Libraries:**
    *   `fastapi`: For building the API.
    *   `uvicorn`: For running the API server.
    *   `pydantic`: For data validation.
    *   `openai`: For interacting with the OpenAI API.
    *   `sqlite3`: For the database.
*   **API:** The backend provides a RESTful API for managing journal entries.

## Frontend (saga-frontend)

*   **Framework:** Next.js
*   **Language:** TypeScript
*   **UI:** React, with components from Radix UI and lucide-react.
*   **Styling:** Tailwind CSS
*   **Key Libraries:**
    *   `next`: The React framework.
    *   `react`: For building the user interface.
    *   `@radix-ui/react-*`: For accessible UI components.
    *   `lucide-react`: For icons.
    *   `genkit`: For AI-powered features.
    *   `tailwindcss`: For styling.

# Building and Running

## Backend

1.  **Navigate to the backend directory:**
    ```bash
    cd saga-backend
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the development server:**
    ```bash
    uvicorn main:app --reload
    ```
    The backend API will be available at `http://127.0.0.1:8000`.

## Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd saga-frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Run the development server:**
    ```bash
    npm run dev
    ```
    The frontend application will be available at `http://localhost:9002`.

# Development Conventions

*   **Backend:** The backend follows standard FastAPI conventions. It uses Pydantic for data modeling and validation.
*   **Frontend:** The frontend is a standard Next.js application with TypeScript. It uses a component-based architecture, with components organized in the `src/components` directory. The `useJournal` hook encapsulates the logic for interacting with the backend API.
*   **API Interaction:** The frontend communicates with the backend via a REST API.
*   **AI Integration:** The application uses the OpenAI API for generating summaries and prompts. The `genkit` library is also included in the frontend, suggesting that there may be plans to expand the AI-powered features.
