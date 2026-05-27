import httpx
import math
import ast
import operator
import re

async def get_weather(city: str) -> str:
    """Gets the current weather and temperature for a given city in real time.

    Args:
        city: The city name, e.g. "Madrid", "New York", "Paris".
    """
    try:
        async with httpx.AsyncClient() as client:
            # We use the clean wttr.in API
            response = await client.get(f"https://wttr.in/{city}?format=3", timeout=10.0)
            if response.status_code == 200:
                return response.text.strip()
            else:
                return f"Could not fetch weather for {city}. HTTP status: {response.status_code}"
    except Exception as e:
        return f"Error retrieving weather for {city}: {str(e)}"

async def search_github_repos(query: str, language: str = None) -> str:
    """Searches popular GitHub repositories matching a query and optional programming language.

    Args:
        query: The search term or keyword, e.g. "fastapi", "machine-learning".
        language: Optional programming language filter, e.g. "python", "javascript", "go".
    """
    try:
        url = "https://api.github.com/search/repositories"
        q = query
        if language:
            q += f" language:{language}"
        params = {
            "q": q,
            "sort": "stars",
            "order": "desc",
            "per_page": 3
        }
        headers = {
            "User-Agent": "Antigravity-Agent/1.0"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                if not items:
                    return f"No GitHub repositories found matching query: '{query}'"
                
                result = [f"### Top GitHub Repositories for '{query}'"]
                for i, item in enumerate(items, 1):
                    name = item.get("full_name")
                    stars = item.get("stargazers_count")
                    desc = item.get("description") or "No description provided."
                    html_url = item.get("html_url")
                    result.append(f"{i}. **[{name}]({html_url})** - ⭐ {stars} stars\n   _{desc}_")
                return "\n".join(result)
            else:
                return f"Failed to query GitHub API. Status code: {response.status_code}"
    except Exception as e:
        return f"Error searching GitHub: {str(e)}"

async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Converts a monetary amount from one currency to another using real-time or standard rates.

    Args:
        amount: The quantity of money to convert.
        from_currency: The 3-letter currency code to convert from, e.g. "USD", "EUR", "MXN", "JPY".
        to_currency: The 3-letter currency code to convert to, e.g. "USD", "EUR", "MXN", "JPY".
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # Fallback rates in case the API fails
    fallback_rates = {
        "USD": {"EUR": 0.92, "MXN": 16.70, "GBP": 0.79, "JPY": 155.0, "USD": 1.0},
        "EUR": {"USD": 1.09, "MXN": 18.15, "GBP": 0.86, "JPY": 168.0, "EUR": 1.0},
        "MXN": {"USD": 0.060, "EUR": 0.055, "GBP": 0.047, "JPY": 9.28, "MXN": 1.0},
        "GBP": {"USD": 1.27, "EUR": 1.16, "MXN": 21.10, "JPY": 196.0, "GBP": 1.0},
        "JPY": {"USD": 0.0065, "EUR": 0.0060, "MXN": 0.11, "GBP": 0.0051, "JPY": 1.0}
    }
    
    rate = None
    source = "Real-time API"
    
    try:
        url = f"https://open.er-api.com/v6/latest/{from_currency}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                if to_currency in rates:
                    rate = rates[to_currency]
    except Exception:
        # Fail silently and use fallback
        pass
    
    if rate is None:
        source = "Offline Fallback Database"
        # Check fallback rates
        if from_currency in fallback_rates and to_currency in fallback_rates[from_currency]:
            rate = fallback_rates[from_currency][to_currency]
        elif to_currency in fallback_rates and from_currency in fallback_rates[to_currency]:
            # Inverse rate
            rate = 1.0 / fallback_rates[to_currency][from_currency]
        else:
            # Generic approximation using USD as a bridge
            rate_to_usd = 1.0
            usd_to_target = 1.0
            
            # Find from -> USD
            if from_currency in fallback_rates:
                rate_to_usd = fallback_rates[from_currency].get("USD", 1.0)
            elif from_currency != "USD":
                # Try to find USD -> from and invert it
                for base, targets in fallback_rates.items():
                    if base == "USD" and from_currency in targets:
                        rate_to_usd = 1.0 / targets[from_currency]
                        break
            
            # Find USD -> to
            if "USD" in fallback_rates and to_currency in fallback_rates["USD"]:
                usd_to_target = fallback_rates["USD"][to_currency]
            elif to_currency != "USD":
                for base, targets in fallback_rates.items():
                    if base == to_currency and "USD" in targets:
                        usd_to_target = 1.0 / targets["USD"]
                        break
            
            rate = rate_to_usd * usd_to_target
    
    converted_amount = amount * rate
    return (
        f"💵 **Currency Conversion ({source})**:\n"
        f"- Input: {amount:,.2f} {from_currency}\n"
        f"- Output: **{converted_amount:,.2f} {to_currency}**\n"
        f"- Exchange Rate: 1 {from_currency} = {rate:.4f} {to_currency}"
    )

# Safe operators map for math evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe math functions
SAFE_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pi": math.pi,
    "e": math.e,
    "pow": pow,
    "abs": abs,
    "round": round,
}

def _safe_eval_node(node):
    if isinstance(node, ast.Num):  # Python < 3.8
        return node.n
    elif isinstance(node, ast.Constant):  # Python >= 3.8
        return node.value
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise TypeError(f"Operator {op_type.__name__} is not allowed.")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        return SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise TypeError(f"Operator {op_type.__name__} is not allowed.")
        operand = _safe_eval_node(node.operand)
        return SAFE_OPERATORS[op_type](operand)
    elif isinstance(node, ast.Name):
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        raise NameError(f"Name '{node.id}' is not allowed.")
    elif isinstance(node, ast.Call):
        func = _safe_eval_node(node.func)
        args = [_safe_eval_node(arg) for arg in node.args]
        if not callable(func):
            raise TypeError("Attempted to call a non-callable object.")
        return func(*args)
    else:
        raise TypeError(f"Unsupported expression element: {type(node).__name__}")

def safe_math_eval(expr_str: str) -> float:
    # Basic clean and exponent replacement
    expr_str = expr_str.replace("^", "**").strip()
    tree = ast.parse(expr_str, mode="eval")
    return _safe_eval_node(tree.body)

async def calculate_expression(expression: str) -> str:
    """Safely evaluates a mathematical expression containing arithmetic operations and functions like sin, cos, tan, log, sqrt, etc.

    Args:
        expression: The mathematical string expression to solve, e.g. "sqrt(25) + 3 * log10(100) - 2^3".
    """
    try:
        result = safe_math_eval(expression)
        return (
            f"🔢 **Math Calculator Output**:\n"
            f"- Expression: `{expression}`\n"
            f"- Evaluated Result: **{result}**"
        )
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}"

async def analyze_text(text: str) -> str:
    """Analyzes a text block and returns metrics like word/char counts, reading time, keyword density, and readability estimates.

    Args:
        text: The block of text or article to analyze.
    """
    if not text or not text.strip():
        return "Text is empty."
        
    char_count = len(text)
    char_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\r", ""))
    
    # Split into words and sentences
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = len(words)
    
    # Split by punctuation for sentence approximation
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences) or 1
    
    # Estimated reading time (average 200 words per minute)
    reading_time_seconds = int((word_count / 200) * 60)
    reading_time_str = (
        f"{reading_time_seconds} seconds" if reading_time_seconds < 60
        else f"{reading_time_seconds // 60} min {reading_time_seconds % 60} sec"
    )
    
    # Average word length
    avg_word_len = sum(len(w) for w in words) / word_count if word_count > 0 else 0
    
    # Syllable approximation (simple heuristic for readability scoring)
    def count_syllables(word):
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        if len(word) == 0:
            return 0
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count = 1
        return count
    
    total_syllables = sum(count_syllables(w) for w in words)
    
    # Flesch Readability Score estimate
    if word_count > 0:
        flesch_score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (total_syllables / word_count)
        if flesch_score > 90:
            readability_level = "Very Easy (5th grade level)"
        elif flesch_score > 80:
            readability_level = "Easy (6th grade level)"
        elif flesch_score > 70:
            readability_level = "Fairly Easy (7th grade level)"
        elif flesch_score > 60:
            readability_level = "Standard (8th-9th grade level)"
        elif flesch_score > 50:
            readability_level = "Fairly Difficult (High School level)"
        elif flesch_score > 30:
            readability_level = "Difficult (College level)"
        else:
            readability_level = "Very Confusing (College Graduate level)"
    else:
        flesch_score = 0
        readability_level = "N/A"
    
    # Top keywords (excluding common English stop words)
    stop_words = {
        "the", "a", "an", "and", "or", "but", "if", "because", "as", "what", "which", "this",
        "that", "these", "those", "is", "are", "was", "were", "be", "been", "being", "have",
        "has", "had", "do", "does", "did", "to", "for", "with", "about", "against", "between",
        "into", "through", "during", "before", "after", "above", "below", "of", "at", "by", "on",
        "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
        "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        "s", "t", "can", "will", "just", "don", "should", "now", "i", "me", "my", "myself", "we",
        "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him",
        "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them",
        "their", "theirs", "themselves"
    }
    
    filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
    word_freq = {}
    for w in filtered_words:
        word_freq[w] = word_freq.get(w, 0) + 1
    
    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    keywords_str = ", ".join(f"'{k}' ({v} times)" for k, v in top_keywords) if top_keywords else "None"
    
    return (
        f"📊 **Text Analytics Dashboard**:\n"
        f"- **Basic Stats**:\n"
        f"  - Characters: {char_count:,} (without spaces: {char_no_spaces:,})\n"
        f"  - Words: {word_count:,}\n"
        f"  - Sentences: {sentence_count:,}\n"
        f"  - Average Word Length: {avg_word_len:.2f} chars\n"
        f"- **Performance & Complexity**:\n"
        f"  - Estimated Reading Time: **{reading_time_str}**\n"
        f"  - Readability Score (Flesch): **{flesch_score:.2f}** -> _{readability_level}_\n"
        f"- **Top Keywords**: {keywords_str}"
    )
