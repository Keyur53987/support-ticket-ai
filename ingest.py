import asyncio
from src.retrieval import ingest_documents

if __name__ == "__main__":
    print("Ingesting policy documents...")
    ingest_documents("data/knowledge_base")
    print("Ingestion complete!")
