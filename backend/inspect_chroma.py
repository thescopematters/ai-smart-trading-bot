
import chromadb
from chromadb.utils import embedding_functions
import os

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "crypto_knowledge"

def inspect_chroma():
    if not os.path.exists(CHROMA_DB_PATH):
        print(f"Error: ChromaDB path '{CHROMA_DB_PATH}' not found.")
        return

    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        embed_fn = embedding_functions.DefaultEmbeddingFunction()
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embed_fn)
        
        count = collection.count()
        print(f"\n--- ChromaDB Inspection ---")
        print(f"Total Chunks Indexed: {count}")
        
        if count == 0:
            print("The collection is empty.")
            return

        # Get all metadatas to see unique sources
        results = collection.get(include=['metadatas', 'documents'])
        
        sources = {}
        for i, meta in enumerate(results['metadatas']):
            src = meta.get('source', 'unknown')
            if src not in sources:
                sources[src] = {
                    'chunks': 0,
                    'preview': results['documents'][i][:100].replace('\n', ' ') + "..."
                }
            sources[src]['chunks'] += 1
        
        print(f"\nIndexed Files ({len(sources)} total):")
        print(f"{'Filename':<40} | {'Chunks':<8} | {'Content Preview'}")
        print("-" * 100)
        for name, info in sources.items():
            print(f"{name:<40} | {info['chunks']:<8} | {info['preview']}")
            
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")

if __name__ == "__main__":
    inspect_chroma()
