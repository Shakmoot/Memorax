from datetime import datetime
from database.memory_db import MemoryDatabase
from database.rag_db import RAGDatabase
from core.reminder_service import ReminderService
from ddgs import DDGS

# Initialize global connections to your databases and services
memory_db = MemoryDatabase()
rag_db = RAGDatabase()
reminder_service = ReminderService()

def get_current_time() -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_memory(description: str, object_name: str = "", location: str = "") -> str:
    """
    Saves a memory or object location to the database.
    Use this when the user explicitly asks you to remember something or where they put an item.
    
    Args:
        description: A general description of what to remember.
        object_name: If the user is asking to remember a specific object (e.g., 'keys'), the name of the object.
        location: Where the object is located (e.g., 'on the coffee table').
    """
    if object_name and location:
        memory_db.update_object_location(object_name, location)
        return f"Successfully saved location of {object_name} at {location}."
    else:
        memory_db.record_memory(description)
        return "General memory saved successfully."

def find_object(object_name: str) -> str:
    """
    Searches the memory database for the last known location of an object.
    Use this when the user asks 'Where are my keys?' or similar questions.
    
    Args:
        object_name: The name of the object to search for (e.g., 'keys', 'wallet').
    """
    result = memory_db.find_object(object_name)
    if result:
        return f"I last saw the {result['name']} at {result['location']} on {result['last_seen']}."
    return f"I do not have a memory of where the {object_name} is."

def search_notes(query: str) -> str:
    """
    Searches the user's uploaded study notes (PDFs) for information.
    
    CRITICAL INSTRUCTION: ONLY use this tool if the user EXPLICITLY asks you to search their "notes", "pdf", "document", "upload", or specifically asks about their study materials. 
    DO NOT use this tool for general knowledge questions, casual conversation, or if the user is just asking a standard question (e.g. "What is the capital of France?"). Answer general questions directly from your own knowledge.
    
    Args:
        query: The specific question or topic to search for in the notes (e.g., "What is mitochondria?", "Summarize chapter 3").
    """
    return rag_db.search_notes(query)

def set_reminder(minutes: float, reminder_message: str) -> str:
    """
    Sets a proactive reminder for the user in the background.
    Use this tool when the user explicitly asks you to remind them to do something later.
    
    Args:
        minutes: The number of minutes from now to trigger the reminder. This can be a decimal (e.g., 0.5 for 30 seconds).
        reminder_message: The exact message you should speak when the reminder triggers.
    """
    delay_seconds = minutes * 60
    reminder_service.add_reminder(delay_seconds, reminder_message)
    return f"Reminder set successfully for {minutes} minutes from now."


def live_internet_search(query: str) -> str:
    """
    Searches the live internet for current events, real-world facts, news, and politicians.
    Use this tool whenever the user asks for up-to-date factual information.
    
    Args:
        query: The search query to look up (e.g., 'Who is the CM of Kerala 2026?').
    """
    print(f"[TOOLS] Searching the live internet for: {query}")
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No recent information found on the internet."
            
        formatted_results = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return f"Here is the latest live information from the internet:\n{formatted_results}"
    except Exception as e:
        return f"Internet search failed: {e}"