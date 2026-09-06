import os
import math
import re
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from config import DOCS_DIR, DB_DIR, GEMINI_API_KEY

# Document reading libraries
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

class FastEmbeddingFunction(EmbeddingFunction):
    """
    Lightweight, deterministic feature-hashing embedding function.
    Runs 100% locally and instantly without downloading multi-megabyte external weights.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def name(self) -> str:
        return "fast_feature_hash"

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            tokens = re.findall(r'\w+', text.lower())
            vec = [0.0] * self.dim
            for token in tokens:
                # Hash token into dimension index
                idx = hash(token) % self.dim
                vec[idx] += 1.0
            # L2 normalize
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings

class RAGEngine:
    def __init__(self, persist_directory: Path = DB_DIR):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        
        # Use fast offline embedding function for instant responses and offline reliability
        self.embedding_fn = FastEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="personal_knowledge_v1",
            embedding_function=self.embedding_fn
        )

    def extract_text_from_file(self, file_path: Path) -> str:
        """Extracts text content from TXT, MD, PDF, or DOCX files."""
        ext = file_path.suffix.lower()
        if ext in [".txt", ".md", ".py", ".json", ".csv", ".log"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == ".pdf" and PdfReader:
            try:
                reader = PdfReader(str(file_path))
                text = []
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
                return "\n".join(text)
            except Exception as e:
                print(f"Error reading PDF {file_path.name}: {e}")
                return ""
        elif ext in [".docx", ".doc"] and docx:
            try:
                doc = docx.Document(str(file_path))
                return "\n".join([p.text for p in doc.paragraphs if p.text])
            except Exception as e:
                print(f"Error reading DOCX {file_path.name}: {e}")
                return ""
        return ""

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
        """Text chunking with overlap."""
        words = text.split()
        if not words:
            return []
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += (chunk_size - overlap)
        return chunks

    def ingest_documents(self, docs_directory: Path = DOCS_DIR) -> str:
        """
        Scans docs_directory, parses all files, chunks them, and stores in ChromaDB.
        """
        indexed_files = 0
        total_chunks = 0
        
        for file_path in docs_directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [".txt", ".md", ".pdf", ".docx", ".doc"]:
                content = self.extract_text_from_file(file_path)
                if not content.strip():
                    continue
                
                chunks = self.chunk_text(content)
                if not chunks:
                    continue
                
                # Create IDs and Metadatas
                clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', file_path.name)
                ids = [f"{clean_name}_{i}" for i in range(len(chunks))]
                metadatas = [{"source": file_path.name, "chunk_index": i} for i in range(len(chunks))]
                
                # Upsert into ChromaDB
                self.collection.upsert(
                    ids=ids,
                    documents=chunks,
                    metadatas=metadatas
                )
                indexed_files += 1
                total_chunks += len(chunks)
                
        return f"Ingestion complete: Indexed {indexed_files} file(s) into {total_chunks} vector chunks."

    def query(self, query_text: str, n_results: int = 3) -> str:
        """
        Queries the vector store for semantic context relevant to query_text.
        """
        count = self.collection.count()
        if count == 0:
            return "No documents found in knowledge base. Place documents in data/documents folder and run ingestion."
        
        actual_results = min(n_results, count)
        results = self.collection.query(
            query_texts=[query_text],
            n_results=actual_results
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        if not documents:
            return "No relevant information found in knowledge base."
            
        context_parts = []
        for doc, meta in zip(documents, metadatas):
            src = meta.get("source", "unknown")
            context_parts.append(f"[Source: {src}]\n{doc}")
            
        return "\n\n---\n\n".join(context_parts)

# Singleton helper
_rag_instance = None

def get_rag_engine() -> RAGEngine:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance

def query_personal_knowledge(query: str) -> str:
    """
    Searches your personal documents, notes, and local knowledge base for relevant information.
    """
    engine = get_rag_engine()
    return engine.query(query)

def ingest_local_documents() -> str:
    """
    Scans the data/documents directory and updates the vector database.
    """
    engine = get_rag_engine()
    return engine.ingest_documents()
