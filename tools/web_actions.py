import math
import re
import urllib.parse
import webbrowser
import requests

def search_web(query: str) -> str:
    """
    Performs a Google web search in the default browser for the given query.
    """
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    webbrowser.open(url)
    return f"Opened Google search for: '{query}'"

def play_youtube(query: str) -> str:
    """
    Searches YouTube and directly opens and plays the top matching video.
    """
    import urllib.request
    clean_q = re.sub(r'^(play|on youtube|play song|song|video|youtube)\s*', '', query, flags=re.IGNORECASE).strip()
    clean_q = clean_q or "trending music"
    encoded_query = urllib.parse.quote_plus(clean_q)
    try:
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=4).read().decode('utf-8')
        video_ids = re.findall(r"watch\?v=(\S{11})", html)
        if video_ids:
            direct_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            webbrowser.open(direct_url)
            return f"Playing {clean_q} directly on YouTube for you Boss."
    except Exception:
        pass
        
    fallback_url = f"https://www.youtube.com/results?search_query={encoded_query}"
    webbrowser.open(fallback_url)
    return f"Playing {clean_q} on YouTube for you Boss."

def open_url(url: str) -> str:
    """
    Opens the specified web URL in the browser.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url} in browser."

def solve_math_expression(text: str) -> str:
    """
    Evaluates spoken math problems (e.g., '2 + 2', '15 * 8', '100 / 4', '50 plus 25').
    """
    try:
        t = text.lower()
        t = re.sub(r'^(what is|calculate|solve|tell me|how much is)\s*', '', t)
        t = t.replace('plus', '+').replace('minus', '-').replace('multiplied by', '*')
        t = t.replace('times', '*').replace('divided by', '/').replace('into', '*').replace('x', '*')
        t = t.replace('కూడిక', '+').replace('తీసివేత', '-').replace('గుణకారం', '*')
        t = t.replace('जोड़', '+').replace('घटाव', '-').replace('गुणा', '*')
        t = t.strip(' ?=')
        
        # Check if contains arithmetic
        if re.search(r'[\d\+\-\*\/\.\(\)\^ ]+', t):
            clean_expr = re.findall(r'[\d\+\-\*\/\.\(\)\^ ]+', t)[0].strip()
            # Safety check on characters
            if not re.match(r'^[0-9\+\-\*\/\.\(\)\^ ]+$', clean_expr):
                return None
            clean_expr = clean_expr.replace('^', '**')
            ans = eval(clean_expr, {"__builtins__": None}, {"math": math})
            if isinstance(ans, float) and ans.is_integer():
                ans = int(ans)
            return f"{clean_expr.replace('**', '^')} equals {ans}."
    except Exception:
        pass
    return None

def fetch_instant_knowledge(query: str) -> str:
    """
    Searches online knowledge databases (Wikipedia API) and returns a concise, factual spoken summary.
    """
    clean_q = re.sub(r'^(who is|what is|where is|tell me about|explain|meaning of|capital of|when was)\s*', '', query, flags=re.IGNORECASE).strip(' ?.')
    if not clean_q or len(clean_q) < 2:
        return None

    try:
        # Search Wikipedia
        s_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_q)}&format=json"
        s_res = requests.get(s_url, headers={"User-Agent": "JarvisAssistant/2.0"}, timeout=5).json()
        items = s_res.get("query", {}).get("search", [])
        if items:
            title = items[0]["title"]
            sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
            sum_res = requests.get(sum_url, headers={"User-Agent": "JarvisAssistant/2.0"}, timeout=5).json()
            extract = sum_res.get("extract")
            if extract:
                # Get the first 1-2 concise sentences
                sentences = re.split(r'(?<=[.!?])\s+', extract)
                short_summary = " ".join(sentences[:2])
                return short_summary
    except Exception:
        pass
    return None
