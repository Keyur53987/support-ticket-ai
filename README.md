# Support Ticket AI

This is an AI-powered Support Ticket resolution system that uses Google's Gemini API and a Retrieval-Augmented Generation (RAG) approach to automatically suggest resolutions for incoming support tickets based on company policy documents.

## Features

- **Streamlit Frontend**: A clean user interface to register, log in, submit support tickets, and view ticket history.
- **FastAPI Backend**: A robust asynchronous REST API to handle user authentication, ticket creation, and fetching ticket history.
- **AI Decision Engine**: Integrates with the Gemini API to analyze tickets and provide an automated decision (action, reasoning, and confidence level) citing relevant policy sources.
- **Policy Ingestion**: Scripts to easily ingest policy documents into a vector database (Qdrant) for RAG support.
- **Local Database**: Uses SQLite for managing users, tickets, and AI decisions securely.

## Prerequisites

- Python 3.9+
- A Google Gemini API Key.

## Setup Instructions

1. **Install Dependencies**
   Install the necessary requirements for both the backend and frontend:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Create a `.env` file in the root directory (or update the existing one) with your API key:
   ```env
   GEMINI_API_KEY="your_actual_api_key_here"
   ```

3. **Ingest Policy Documents**
   Before running the application, make sure to ingest the knowledge base documents into the vector database. Run the following script:
   ```bash
   python ingest.py
   ```

4. **Run the Application**
   You can start both the FastAPI backend (running on port 8000) and the Streamlit frontend with a single command:
   ```bash
   python run.py
   ```
   This script will launch the API server and automatically open the Streamlit interface in your default web browser.

## Application Architecture

- `src/api.py`: FastAPI endpoints for authentication and ticket management.
- `src/decision.py`: The core AI generation logic using Gemini and retrieved policy context.
- `src/retrieval.py`: Functions to handle Qdrant vector database embedding and querying.
- `src/database.py`: SQLAlchemy database models and connection setup.
- `src/auth.py`: JWT-based authentication utility functions.
- `streamlit_app.py`: The frontend UI application.
- `run.py`: The main entrypoint to spin up the full stack.

## Testing

Run tests to evaluate the model using `tests/evaluate.py`.
