import os
import chromadb
import pdfplumber

class RAGDatabase:
    def __init__(self, db_path="./local_vector_db"):
        # Connect to the persistent ChromaDB storage
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="student_notes")

    def ingest_pdf(self, pdf_path):
        """Reads a PDF, chops it into chunks with overlap, and saves them to ChromaDB."""
        if not os.path.exists(pdf_path):
            print(f"[RAG ERROR] Could not find the file {pdf_path}")
            return False

        print(f"[RAG] Reading PDF using pdfplumber: {pdf_path}...")
        
        full_text = ""
        try:
            # pdfplumber correctly handles multi-column layouts
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        full_text += extracted + "\n"
        except Exception as e:
            print(f"[RAG ERROR] Failed to read PDF: {e}")
            return False

        print("[RAG] Chunking text to prevent token limit errors...")
        chunk_size = 1000
        overlap = 100
        
        chunks = []
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk = full_text[i:i + chunk_size]
            chunks.append(chunk)

        print(f"[RAG] Saving {len(chunks)} chunks into the database...")
        
        documents = []
        ids = []
        for index, chunk_text in enumerate(chunks):
            documents.append(chunk_text)
            ids.append(f"{os.path.basename(pdf_path)}_chunk_{index}")

        if documents:
            self.collection.add(documents=documents, ids=ids)
            print("[RAG] PDF ingested successfully!")
            return True
        else:
            print("[RAG] No text found in PDF to ingest.")
            return False

    def search_notes(self, query_text, max_results=3):
        """Searches the database for notes matching the question and returns them as a string."""
        print(f"[RAG] Searching notes for: '{query_text}'")
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=max_results
            )
            
            if results and results['documents'] and results['documents'][0]:
                found_documents = results['documents'][0]
                formatted_results = "\n\n--- NEXT EXCERPT ---\n\n".join(found_documents)
                return f"Here is the relevant information from the student's notes:\n\n{formatted_results}"
            
            return "No relevant information found in the student's notes."
        except Exception as e:
            print(f"[RAG ERROR] Search failed: {e}")
            return "Error occurred while searching the notes."

# --- TEST BLOCK ---
if __name__ == "__main__":
    # You can run this file directly to ingest a new PDF!
    db = RAGDatabase()
    
    test_pdf = "core/sample_notes.pdf" 
    if os.path.exists(test_pdf):
        db.ingest_pdf(test_pdf)
        print(db.search_notes("Summarize this document"))
    else:
        print(f"Please place a PDF at {test_pdf} to test ingestion.")