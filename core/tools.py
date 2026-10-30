from datetime import datetime
from database.memory_db import MemoryDatabase
from database.rag_db import RAGDatabase
from core.reminder_service import ReminderService
import requests
import os
import re
import time

# Initialize global connections to your databases and services
memory_db = MemoryDatabase()
rag_db = RAGDatabase()
reminder_service = ReminderService()

# ---------------------------------------------------------------------------
# Search helpers: reusable client, cache, and recency detection
# ---------------------------------------------------------------------------
_tavily_client = None
_search_cache = {}          # {normalized_query: (timestamp, result_string)}
CACHE_TTL_SECONDS = 300     # 5 minutes: fresh enough, avoids repeat calls
TAVILY_TIMEOUT = 8          # seconds

_NEWS_WORDS = {
    "news", "latest", "today", "breaking", "election", "elections", "minister",
    "president", "prime", "score", "scores", "match", "headline", "headlines",
    "announced", "recent", "yesterday", "tonight", "live", "result", "results",
}
_RECENCY_WORDS = _NEWS_WORDS | {
    "price", "prices", "current", "currently", "now", "new", "weather",
    "rate", "stock", "update", "updates", "this week", "this month",
}


def _get_tavily_client():
    """Creates the Tavily client once and reuses it."""
    global _tavily_client
    if _tavily_client is None:
        from tavily import TavilyClient
        _tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _tavily_client


def _words(query: str) -> set:
    return set(re.findall(r"[a-z]+", query.lower()))


def _is_news_query(query: str) -> bool:
    return bool(_words(query) & _NEWS_WORDS)


def _needs_recency(query: str) -> bool:
    q = query.lower()
    return bool(_words(query) & _RECENCY_WORDS) or "this week" in q or "this month" in q


def get_current_time() -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")


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
    Searches the internet for real-time, up-to-date information.
    Use this tool whenever the user asks about current events, news, prices,
    recent developments, office holders, sports results, or anything that might
    have changed recently. ALWAYS call it again for a new question, even if a
    similar question was answered earlier in the conversation.

    DO NOT use this for questions answerable from memory (e.g., "where are my keys?")
    or questions about the user's personal notes/documents.

    Args:
        query: A short, specific search query WITHOUT guessing a year unless the
            user gave one (e.g., "petrol price Kochi today", "India prime minister").
    """
    t0 = time.time()
    now = datetime.now()
    print(f"[TOOLS] ⏱ Search START for: {query}")

    # Add the current year to time-sensitive queries so engines don't return old pages
    search_query = query.strip()
    if _needs_recency(search_query) and not re.search(r"\b20\d{2}\b", search_query):
        search_query = f"{search_query} {now.year}"

    # Short-lived cache: repeated questions return instantly
    cache_key = search_query.lower()
    cached = _search_cache.get(cache_key)
    if cached and (time.time() - cached[0]) < CACHE_TTL_SECONDS:
        print(f"[TOOLS] ⚡ Cache hit ({time.time() - t0:.2f}s)")
        return cached[1]

    if not os.getenv("TAVILY_API_KEY"):
        print("[TOOLS] ⚠️ TAVILY_API_KEY not set. Falling back to Wikipedia.")
        return _wikipedia_search(query)

    try:
        client = _get_tavily_client()

        kwargs = dict(
            query=search_query,
            max_results=3,
            search_depth="basic",
            include_answer=True,      # FIX: without this, "answer" was always empty
            timeout=TAVILY_TIMEOUT,
        )
        if _is_news_query(search_query):
            kwargs["topic"] = "news"
            kwargs["days"] = 7        # only the last week for news
        elif _needs_recency(search_query):
            kwargs["time_range"] = "month"

        response = client.search(**kwargs)

        parts = []
        if response.get("answer"):
            parts.append(f"Direct Answer: {response['answer']}")

        for item in response.get("results", [])[:3]:
            title = item.get("title", "")
            content = item.get("content", "")[:300]
            published = item.get("published_date", "")
            if title and content:
                date_note = f" (published {published})" if published else ""
                parts.append(f"{title}{date_note}: {content}")

        print(f"[TOOLS] ✅ Tavily search took {time.time() - t0:.1f}s")

        if parts:
            result = (
                f"Search Results (retrieved {now.strftime('%Y-%m-%d %H:%M')}):\n"
                + "\n\n".join(parts)
                + "\n\nSYSTEM INSTRUCTION: Use these results to give a short, spoken, "
                  "up-to-date answer. Prefer the most recent information. "
                  "Do not read out URLs."
            )
            _search_cache[cache_key] = (time.time(), result)
            return result

        return "The search returned no results. Try rephrasing your question."

    except Exception as e:
        print(f"[TOOLS] ⚠️ Tavily failed after {time.time() - t0:.1f}s: {e}. Falling back to Wikipedia.")
        return _wikipedia_search(query)


_wiki_session = requests.Session()
_wiki_session.headers.update({
    "User-Agent": "MemoraxSmartGlasses/1.0 (StudentProject) PythonRequests"
})


def _wikipedia_search(query: str) -> str:
    """Internal fallback: searches Wikipedia if Tavily is unavailable.
    NOTE: Wikipedia can be out of date for current events."""
    print(f"[TOOLS] 📖 Wikipedia fallback for: {query}")
    t0 = time.time()

    try:
        search_response = _wiki_session.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query,
                    "utf8": "", "format": "json", "srlimit": 1},
            timeout=4,
        ).json()

        search_results = search_response.get("query", {}).get("search", [])
        if not search_results:
            return "No information found for that query."

        best_title = search_results[0]["title"]

        summary_response = _wiki_session.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "prop": "extracts", "exsentences": 3,
                    "exlimit": 1, "titles": best_title, "explaintext": 1,
                    "format": "json"},
            timeout=4,
        ).json()

        pages = summary_response.get("query", {}).get("pages", {})
        for page_id in pages:
            extract = pages[page_id].get("extract", "")
            if extract:
                print(f"[TOOLS] ✅ Wikipedia found '{best_title}' in {time.time() - t0:.1f}s")
                return (
                    f"Facts from Wikipedia:\n{extract}\n\n"
                    f"SYSTEM INSTRUCTION: Use these facts to give a short spoken answer. "
                    f"Wikipedia may be outdated for current events, so if the question is "
                    f"about something recent, mention that live search is unavailable and "
                    f"the information may not be the latest."
                )

        return "Could not extract facts from Wikipedia."

    except Exception as e:
        print(f"[TOOLS] ⚠️ Wikipedia also failed after {time.time() - t0:.1f}s: {e}")
        return "Could not retrieve information at this time."