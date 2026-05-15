# Reads documents (PDF / TXT / MD)
# Breaks them into chunks
# Converts chunks → vectors (embeddings)
# Stores them in ChromaDB
# Searches them when a question is asked
# Returns relevant text to the AI

import os
import json
import chromadb
import traceback
import boto3
import tempfile
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from sqlalchemy.orm import Session
from database import Document, DocumentStatus, SessionLocal

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "crypto_knowledge"
DATA_FOLDER = "./data"

# S3 Config
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

# Global client/collection reference
_collection = None

def initialize_rag():
    """Initializes ChromaDB (Latest) and ingests any new files."""
    global _collection
    
    print("Initializing RAG Service (ChromaDB Latest)...")
    
    try:
        # 1. Setup Client (Persistent)
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # 2. Setup Embedding Function (Default is all-MiniLM-L6-v2)
        embed_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # 3. Get/Create Collection
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME, 
            embedding_function=embed_fn
        )
        # If collection exists → load it
        # If not → create it
        
        print(f"RAG: Collection '{COLLECTION_NAME}' loaded. Count: {_collection.count()}")
        
        # 4. Ingest Data Folder
        if os.path.exists(DATA_FOLDER):
            _ingest_folder(DATA_FOLDER)
        else:
            os.makedirs(DATA_FOLDER, exist_ok=True)

        # This scans and ingests all documents inside ./data.

    except Exception as e:
        print(f"RAG Initialization Failed: {e}")
        traceback.print_exc()

def ingest_file(file_path: str = None, s3_key: str = None):
    """Ingests a file from local path OR S3 into the vector database."""
    global _collection
    if _collection is None:
        initialize_rag()
    
    filename = s3_key if s3_key else os.path.basename(file_path)
    temp_local_path = None
    
    try:
        if s3_key and S3_BUCKET:
            # Download from S3 to temp file
            s3 = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=AWS_REGION
            )
            suffix = os.path.splitext(s3_key)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                print(f"RAG: Downloading {s3_key} from S3...")
                s3.download_fileobj(S3_BUCKET, s3_key, tmp)
                temp_local_path = tmp.name
            target_path = temp_local_path
        else:
            target_path = file_path

        if not target_path or not os.path.exists(target_path):
            return False

        text = ""
        if filename.lower().endswith(".pdf"):
            text = _read_pdf(target_path)
        elif filename.lower().endswith((".txt", ".md")):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                pass
        
        if text:
            # Check if this source exists in Chroma
            existing = _collection.get(where={"source": filename})
            if existing and len(existing['ids']) > 0:
                print(f"RAG: {filename} already exists in vector DB. Skipping.")
                return True

            _add_text_to_db(filename, text)
            return True
            
    except Exception as e:
        print(f"RAG Ingestion Error ({filename}): {e}")
        return False
    finally:
        # Cleanup temp file
        if temp_local_path and os.path.exists(temp_local_path):
            os.remove(temp_local_path)
            
    return False

def _ingest_folder(folder_path):
    """Scans and ingests all documents inside a folder."""
    # Loops through files
    # Reads text from each file
    # Avoids re-indexing duplicates
    # Sends text for chunking + storage
    
    print(f"RAG: Scanning {folder_path}...")
    
    files_processed = 0
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        text = ""
        if filename.endswith(".pdf"):
            text = _read_pdf(file_path)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                pass
        
        if text:
            # Check if this source exists
            existing = _collection.get(where={"source": filename})
            if existing and len(existing['ids']) > 0:
                continue

            # ❌ Re-embedding the same document again
            # ✔ Uses metadata (source) to detect duplicates

            _add_text_to_db(filename, text)
            files_processed += 1
            
    if files_processed > 0:
        print(f"RAG: Ingested {files_processed} new files.")

def _read_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
        return text
    except Exception as e:
        print(f"RAG: Error reading PDF {path}: {e}")
        return ""

def _add_text_to_db(source_name, text):
    # Recursive Character Splitter logic
    # Splits by double newline, then single newline, then space
    separators = ["\n\n", "\n", " ", ""]
    chunk_size = 1000
    overlap = 100

    def split_text(text, separators, chunk_size, overlap):
        if not separators:
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]
        
        sep = separators[0]
        splits = text.split(sep)
        final_chunks = []
        current_chunk = ""
        
        for s in splits:
            if len(current_chunk) + len(s) + len(sep) <= chunk_size:
                current_chunk += (sep if current_chunk else "") + s
            else:
                if current_chunk:
                    final_chunks.append(current_chunk)
                
                # If a single split is still too big, go to next separator
                if len(s) > chunk_size:
                    final_chunks.extend(split_text(s, separators[1:], chunk_size, overlap))
                    current_chunk = ""
                else:
                    current_chunk = s
        
        if current_chunk:
            final_chunks.append(current_chunk)
        return final_chunks

    chunks = split_text(text, separators, chunk_size, overlap)
    metadatas = [{"source": source_name} for _ in chunks]
    ids = [f"{source_name}_{i}" for i in range(len(chunks))]
    
    if chunks:
        _collection.add(documents=chunks, metadatas=metadatas, ids=ids)
        print(f"RAG: Indexed {source_name} ({len(chunks)} smart chunks)")

def get_sync_status():
    """Calculates synchronization status based on DB Document tracking."""
    # Lead Engineer Refactor: Use DB as source of truth instead of local filesystem
    db = SessionLocal()
    try:
        total_docs = db.query(Document).count()
        indexed_docs = db.query(Document).filter(Document.status == DocumentStatus.PROCESSED).count()
        
        percent = int((indexed_docs / total_docs) * 100) if total_docs > 0 else 100
        return {
            "percent": percent,
            "total_files": total_docs,
            "indexed_files": indexed_docs
        }
    except Exception as e:
        print(f"RAG: Error getting sync status: {e}")
        return {"percent": 0, "total_files": 0, "indexed_files": 0}
    finally:
        db.close()

def search_knowledge_base(query: str, n_results: int = 3) -> str:
    """Searches the vector DB for relevant context."""
    if _collection is None:
        initialize_rag()
    
    if _collection is None:
        return "Knowledge base unavailable."

    if _collection.count() == 0:
        return "No documents found in knowledge base."

    # Behind the scenes:
    # Query → embeddings
    # Cosine similarity search
    # Returns top N results/Top-K closest chunks returned
    
    results = _collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    if not results or not results['documents']:
         return "No relevant info found."

    docs = results['documents'][0]
    metas = results['metadatas'][0]
    
    context_data = []
    for i, doc in enumerate(docs):
        source = metas[i].get('source', 'unknown')
        context_data.append({"source": source, "content": doc})

    return json.dumps(context_data, indent=2)

def delete_document(filename: str):
    """Removes a document's embeddings from the vector store."""
    global _collection
    if _collection is None:
        initialize_rag()
    
    if _collection:
        try:
            _collection.delete(where={"source": filename})
            print(f"RAG: Deleted vectors for {filename}")
            return True
        except Exception as e:
            print(f"RAG Delete Error: {e}")
            return False
    return False
