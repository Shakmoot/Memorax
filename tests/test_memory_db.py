from database.memory_db import MemoryDatabase

def run_test():
    print("[TEST] Initializing Memory Database...")
    db = MemoryDatabase(db_path="test_glasses.db")
    
    # 1. Test recording a general memory
    mem_id = db.record_memory("Looked at textbook page covering network protocols.", tag="study")
    print(f"[TEST] Inserted general memory with ID: {mem_id}")

    # 2. Test saving an object's location
    print("[TEST] Saving location for 'car keys'...")
    db.update_object_location("car keys", "desk beside laptop", image_path="latest_capture.jpg")

    # 3. Test querying the object
    result = db.find_object("keys")
    print(f"[TEST] Search query 'keys' returned: {result}")
    
    assert result is not None, "Object was not found!"
    assert result["location"] == "desk beside laptop"
    print("[TEST] Database verification passed successfully!")

if __name__ == "__main__":
    run_test()