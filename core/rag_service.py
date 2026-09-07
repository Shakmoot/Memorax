import os
import chromadb
import pypdf
from core.orchestrator import AIAssistant

class StudentModeRAG:
    def __init__(self, ai_assistant=None):
        self.client = chromadb.PersistentClient(path="./local_vector_db")
        self.collection = self.client.get_or_create_collection(name="student_notes")
        self.assistant = ai_assistant

    def save_note(self, note_id, text_content):
        """Saves a single short note into the database."""
        self.collection.add(
            documents=[text_content],
            ids=[note_id]
        )
        print(f"[System] Note '{note_id}' saved successfully!")

    def ingest_pdf(self, pdf_path):
        """Reads a PDF, chops it into chunks with overlap, and saves them to ChromaDB."""
        if not os.path.exists(pdf_path):
            print(f"Error: Could not find the file {pdf_path}")
            return

        print(f"[System] Reading PDF: {pdf_path}...")
        
        # 1. Read all the text from the PDF
        full_text = ""
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    full_text += extracted + "\n"

        # 2. Chunk the text (1000 characters per chunk, 100 character overlap)
        print("[System] Chunking text to prevent token limit errors...")
        chunk_size = 1000
        overlap = 100
        
        chunks = []
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk = full_text[i:i + chunk_size]
            chunks.append(chunk)

        # 3. Save all chunks into the Vector Database efficiently
        print(f"[System] Saving {len(chunks)} chunks into the database...")
        
        documents = []
        ids = []
        for index, chunk_text in enumerate(chunks):
            documents.append(chunk_text)
            # Give each chunk a unique ID (e.g., sample_notes.pdf_chunk_0)
            ids.append(f"{os.path.basename(pdf_path)}_chunk_{index}")

        # Add them all at once!
        if documents:
            self.collection.add(documents=documents, ids=ids)
            print("[System] PDF ingested successfully!")
        else:
            print("[System] No text found in PDF to ingest.")

    def search_notes(self, user_question, max_results=3):
        """Searches the database for notes matching the question."""
        results = self.collection.query(
            query_texts=[user_question],
            n_results=max_results
        )
        
        # We grab the top chunks found and glue them together for the AI to read
        if results['documents'] and results['documents'][0]:
            found_documents = results['documents'][0]
            return "\n\n...[NEXT EXCERPT]...\n\n".join(found_documents)
        return ""

    def ask_student_question(self, user_question):
        """The RAG pipeline: Checks notes first; offers web search fallback if not found."""
        if not self.assistant:
            return "Error: AI Assistant is not connected."
            
        relevant_notes = self.search_notes(user_question)
        
        augmented_prompt = f"""
        You are an AI study assistant for a student wearing smart glasses.
        Answer the student's question based strictly on the provided notes below.
        
        CRITICAL INSTRUCTION:
        If the answer is NOT clearly contained in the notes, do NOT answer using outside knowledge. 
        Instead, say:
        "I couldn't find anything about this in your notes. Would you like me to search the web for you?"
        
        STUDENT'S NOTES:
        {relevant_notes}
        
        STUDENT'S QUESTION:
        {user_question}
        """
        
        return self.assistant.ask_question(augmented_prompt)

    def search_web_and_explain(self, user_question):
        """Fallback tool: Uses general web/AI knowledge when notes lack the answer."""
        if not self.assistant:
            return "Error: AI Assistant is not connected."
            
        web_prompt = f"Answer the following student question clearly and accurately using general knowledge:\n{user_question}"
        return self.assistant.ask_question(web_prompt)

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Starting Student Mode RAG...\n")
    
    brain = AIAssistant()
    rag = StudentModeRAG(ai_assistant=brain)
    
    # 1. Ingest the PDF! (Make sure sample_notes.pdf is inside the core folder)
    pdf_file = "core/sample_notes.pdf"
    rag.ingest_pdf(pdf_file)
    
    # 2. Ask a question about the PDF
    # (Change this string to a question that actually exists inside your PDF!)
    print("\n--- TESTING PDF KNOWLEDGE ---")
    question = "what is the advantage of multiple columns in a single page?" 
    print(f"Student: {question}")
    
    answer = rag.ask_student_question(question)
    print(f"AI Tutor: {answer}\n")