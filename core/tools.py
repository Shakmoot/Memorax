from datetime import datetime
from database.memory_db import MemoryDatabase

# Initialize a global connection to the memory database
memory_db = MemoryDatabase()

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