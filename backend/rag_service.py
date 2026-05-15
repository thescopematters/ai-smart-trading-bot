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
        
        print(f"RAG: Collection '{COLLECTION_NAME}' loaded. Count: {_collection.count()}")
        
        # 4. Ingest Data Folder
        if os.path.exists(DATA_FOLDER):
            _ingest_folder(DATA_FOLDER)
        else:
            os.makedirs(DATA_FOLDER, exist_ok=True)

    except Exception as e:
        print(f"RAG Initialization Failed: {e}")
        traceback.print_exc()

def ingest_file(file_path: str):
    """Ingests a single local file into the vector database."""
    global _collection
    if _collection is None:
        initialize_rag()
    
    filename = os.path.basename(file_path)
    
    text = ""
    if filename.lower().endswith(".pdf"):
        text = _read_pdf(file_path)
    elif filename.lower().endswith((".txt", ".md")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            pass
    
    if text:
        # Check if this source exists
        existing = _collection.get(where={"source": filename})
        if existing and len(existing['ids']) > 0:
            print(f"RAG: {filename} already exists in vector DB. Skipping.")
            return True

        _add_text_to_db(filename, text)
        return True
    return False

def _ingest_folder(folder_path):
    """Scans and ingests all documents inside a folder."""
    print(f"RAG: Scanning {folder_path}...")
    files_processed = 0
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isdir(file_path): continue
        
        text = ""
        if filename.lower().endswith(".pdf"):
            text = _read_pdf(file_path)
        elif filename.lower().endswith((".txt", ".md")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                pass
        
        if text:
            existing = _collection.get(where={"source": filename})
            if existing and len(existing['ids']) > 0:
                continue

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
    """Calculates the percentage of files in ./data that are indexed."""
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
