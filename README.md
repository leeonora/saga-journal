## Getting Started

This guide will help you get the project up and running on your local machine. The project is split into two parts: a backend API and a frontend application.

#### Prerequisites

Python 3.x: Required for the backend.

pip: Python's package installer.

Node.js: Required for the frontend. You can download the installer here: https://nodejs.org/en/download/current

npm: The Node.js package manager, which is installed with Node.js.

## Running with Make

A `Makefile` is provided to simplify the development workflow.

### Commands

*   `make install`: Install all dependencies for both the frontend and backend.
*   `make run`: Start both the backend and frontend servers. The frontend will open automatically in Firefox.
*   `make run-backend`: Start only the backend server.
*   `make run-frontend`: Start only the frontend server. The frontend will open automatically in Firefox.
*   `make stop`: Stop the backend server when it's running in the background (i.e., after using `make run`).

## Backend

The backend is built with Python and uses Uvicorn to run the API.

#### Installation

Navigate to the backend directory:

`cd saga-backend`

Install the required Python packages from the requirements.txt file:

`pip install -r requirements.txt`

#### Running the API

To start the API server, run the following command:

`uvicorn main:app --reload`

The --reload flag will automatically restart the server whenever you make changes to your code. The API will be available at http://127.0.0.1:8000 (or http://localhost:8000).

## Frontend

The frontend is a Node.js application.

#### Installation

Navigate to the frontend directory:

`cd saga-frontend`

Install all the Node.js dependencies:

`npm install`

#### Running the Application

To start the development server, use the following command:

`npm run dev`

The application will be accessible in your web browser at http://localhost:9002.