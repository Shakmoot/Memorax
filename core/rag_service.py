import chromadb
from core.orchestrator import AIAssistant

class StudentModeRAG:
    def __init__(self, ai_assistant=None):
        self.client = chromadb.PersistentClient(path="./local_vector_db")
        self.collection = self.client.get_or_create_collection(name="student_notes")
        self.assistant = ai_assistant

    def save_note(self, note_id, text_content):
        """Converts text into embeddings and saves it into the database."""
        self.collection.add(
            documents=[text_content],
            ids=[note_id]
        )
        print(f"[System] Note '{note_id}' saved successfully!")

    def search_notes(self, user_question, max_results=2):
        """Searches the database for notes matching the question."""
        results = self.collection.query(
            query_texts=[user_question],
            n_results=max_results
        )
        
        found_documents = results['documents'][0]
        return "\n".join(found_documents)

    def ask_student_question(self, user_question):
        """The RAG pipeline: Checks notes first; offers web search fallback if not found."""
        if not self.assistant:
            return "Error: AI Assistant is not connected."
            
        # 1. RETRIEVE
        relevant_notes = self.search_notes(user_question)
        
        # 2. AUGMENT
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
        
        # 3. GENERATE
        return self.assistant.ask_question(augmented_prompt)

    def search_web_and_explain(self, user_question):
        """Fallback tool: Uses general web/AI knowledge when notes lack the answer."""
        if not self.assistant:
            return "Error: AI Assistant is not connected."
            
        web_prompt = f"""
        Answer the following student question clearly and accurately using general knowledge:
        {user_question}
        """
        return self.assistant.ask_question(web_prompt)

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Starting Student Mode RAG...\n")
    
    brain = AIAssistant()
    rag = StudentModeRAG(ai_assistant=brain)
    
    # 1. Question in notes
    print("--- TEST 1: Question in Notes ---")
    q1 = "What part of the cell makes energy?"
    print(f"Student: {q1}")
    a1 = rag.ask_student_question(q1)
    print(f"AI Tutor: {a1}\n")
    
    # 2. Question NOT in notes
    print("--- TEST 2: Question NOT in Notes ---")
    q2 = "Who was the first president of the United States?"
    print(f"Student: {q2}")
    a2 = rag.ask_student_question(q2)
    print(f"AI Tutor: {a2}\n")
    
    # 3. User approves web search
    if "search the web" in a2.lower():
        print("Student: Yes, please search.")
        web_answer = rag.search_web_and_explain(q2)
        print(f"AI (Web Search): {web_answer}\n")