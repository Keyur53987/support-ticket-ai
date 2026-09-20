import os
import uuid
import json
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
try:
    from sentence_transformers import CrossEncoder
except Exception as e:
    print(f"Warning: sentence_transformers import failed: {e}")
    CrossEncoder = None


from dotenv import load_dotenv

# Initialize Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Qdrant Client (local disk storage)
qdrant_client = QdrantClient(path="./qdrant_data")
COLLECTION_NAME = "policies"

# Ensure collection exists
try:
    qdrant_client.get_collection(COLLECTION_NAME)
except Exception:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )

# Load CrossEncoder for re-ranking
try:
    if CrossEncoder:
        cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    else:
        cross_encoder = None
except Exception as e:
    print(f"Warning: Could not load CrossEncoder. Re-ranking will be disabled. Error: {e}")
    cross_encoder = None

def get_embedding(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/gemini-embedding-2",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def ingest_documents(directory: str):
    points = []
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = chunk_text(content)
            for i, chunk in enumerate(chunks):
                vector = get_embedding(chunk)
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={"source": filename, "text": chunk, "chunk_index": i}
                    )
                )
    
    if points:
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Ingested {len(points)} chunks into Qdrant.")

def query_expansion(ticket_message: str) -> list[str]:
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Given the following customer support ticket, generate 2 alternative search queries that would help retrieve the most relevant policy documents. Return ONLY a JSON list of strings.\n\nTicket: {ticket_message}"
    response = model.generate_content(prompt)
    try:
        queries = json.loads(response.text.strip().removeprefix('```json').removesuffix('```'))
        if not isinstance(queries, list):
            queries = []
    except:
        queries = []
    return [ticket_message] + queries

def retrieve_and_rerank(ticket_message: str, top_k: int = 3) -> list[dict]:
    # 1. Query Expansion
    expanded_queries = query_expansion(ticket_message)
    
    # 2. Vector Search (Retrieval)
    all_hits = []
    for query in expanded_queries:
        query_vector = get_embedding(query)
        hits = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=5
        )
        all_hits.extend(hits)
        
    # Deduplicate hits by payload text
    unique_hits = {}
    for hit in all_hits:
        if hit.payload['text'] not in unique_hits:
            unique_hits[hit.payload['text']] = hit
            
    hit_list = list(unique_hits.values())
    if not hit_list:
        return []

    # 3. Re-ranking
    if cross_encoder:
        pairs = [[ticket_message, hit.payload['text']] for hit in hit_list]
        scores = cross_encoder.predict(pairs)
        
        for i, hit in enumerate(hit_list):
            hit.score = scores[i]
            
        # Sort by cross-encoder score descending
        hit_list.sort(key=lambda x: x.score, reverse=True)
    
    # Return top_k
    top_hits = hit_list[:top_k]
    return [{"source": hit.payload["source"], "text": hit.payload["text"]} for hit in top_hits]
