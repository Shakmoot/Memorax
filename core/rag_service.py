import chromadb

class StudentModeRAG:
    def __init__(self):
        # 1. Initialize a local Vector Database. 
        # This will create a folder called 'local_vector_db' on your PC to save notes permanently.
        self.client = chromadb.PersistentClient(path="./local_vector_db")
        
        # 2. Create or open a 'collection' (think of this like a table or a notebook)
        self.collection = self.client.get_or_create_collection(name="student_notes")

    def save_note(self, note_id, text_content):
        """Converts text into embeddings and saves it into the database."""
        self.collection.add(
            documents=[text_content],
            ids=[note_id]
        )
        print(f"[System] Note '{note_id}' saved successfully!")

    def search_notes(self, user_question, max_results=1):
        """Searches the database for notes that match the meaning of the user's question."""
        results = self.collection.query(
            query_texts=[user_question],
            n_results=max_results
        )
        
        # ChromaDB returns a complex dictionary. We just want the actual text documents it found.
        found_documents = results['documents'][0]
        return found_documents

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Starting Student Mode RAG Database...\n")
    
    rag = StudentModeRAG()
    
    # 1. Let's save some mock OCR text (as if we just scanned a textbook)
    print("Saving notes to the database...")
    rag.save_note(
        note_id="biology_page_1", 
        text_content="The mitochondria is an organelle known as the powerhouse of the cell. It generates most of the cell's supply of adenosine triphosphate (ATP), used as a source of chemical energy."
    )
    rag.save_note(
        note_id="history_page_1", 
        text_content="The Industrial Revolution transitioned human manufacturing processes from hand production methods to machines, primarily beginning in Great Britain in the 1760s."
    )
    
    # 2. Let's test the Semantic Search (Searching by meaning)
    print("\n--- TESTING SEARCH ---")
    
    # Notice we ask about "factories" and "UK", but those words are NOT in the history note!
    # The Vector Database should still find it because the *meaning* is the same.
    question1 = "Where did factories and machine manufacturing start?"
    print(f"Question: {question1}")
    answer1 = rag.search_notes(question1)
    print(f"Found Note: {answer1}\n")
    
    question2 = "What part of the cell makes energy?"
    print(f"Question: {question2}")
    answer2 = rag.search_notes(question2)
    print(f"Found Note: {answer2}\n")