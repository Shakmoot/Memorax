import datetime

def get_current_time():
    """Returns the current system time in a readable format."""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

# Test block: to check if our code works on our machine
if __name__ == "__main__":
    print("Testing the tool: The current time is", get_current_time())