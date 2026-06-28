import os
import requests
import google.generativeai as genai
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

SEARCH_KEYWORDS = [
    "PV battery sizing optimization",
    "hybrid optimization renewable energy Iraq",
    "HOMER Pro photovoltaic battery",
    "genetic algorithm particle swarm energy storage"
]

def fetch_papers():
    import random
    keyword = random.choice(SEARCH_KEYWORDS)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": keyword,
        "limit": 3,
        "fields": "title,abstract,authors,year,url,venue",
        "sort": "relevance"
    }
    response = requests.get(url, params=params, timeout=15)
    if response.status_code == 200:
        data = response.json()
        papers = data.get("data", [])
        papers = [p for p in papers if p.get("abstract")]
        return papers[:1] if papers else []
    return []

def summarize_with_gemini(paper):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    title = paper.get("title", "No title")
    abstract = paper.get("abstract", "No abstract")
    authors = ", ".join([a.get("name", "") for a in paper.get("authors", [])[:3]])
    year = paper.get("year", "N/A")
    venue = paper.get("venue", "N/A")
    url = paper.get("url", "N/A")
    prompt = f"""
You are a research assistant for an electrical engineering Master's student specializing in 
renewable energy systems, PV-battery optimization, and smart grids.

Summarize this research paper in Arabic in a clear, structured way:

Title: {title}
Authors: {authors}
Year: {year}
Journal/Conference: {venue}

Abstract:
{abstract}

Please provide:
1. 🎯 الهدف الرئيسي للبحث (2-3 جمل)
2. 🔧 المنهجية المستخدمة (2-3 جمل)
3. 📊 أهم النتائج (2-3 نقاط)
4. 💡 ليش مهم لمجال الطاقة المتجددة وأنظمة PV-Battery (جملة أو جملتين)

Keep it concise and practical. Write in clear Arabic.
"""
    response = model.generate_content(prompt)
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "url": url,
        "summary": response.text
    }

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload, timeout=15)
    return response.status_code == 200

def main():
    print(f"Starting research bot at {datetime.now()}")
    papers = fetch_papers()
    if not papers:
        send_telegram_message("⚠️ لم يتم العثور على أبحاث جديدة اليوم.")
        return
    paper = papers[0]
    result = summarize_with_gemini(paper)
    message = f"""📚 *بحث جديد في مجالك*
━━━━━━━━━━━━━━━━━━━━
📄 *العنوان:*
{result['title']}

👥 *الباحثون:* {result['authors']}
📅 *السنة:* {result['year']}
🏛️ *المصدر:* {result['venue']}

━━━━━━━━━━━━━━━━━━━━
{result['summary']}
━━━━━━━━━━━━━━━━━━━━
🔗 [رابط البحث الكامل]({result['url']})

_تم الإرسال تلقائياً - {datetime.now().strftime('%Y-%m-%d %H:%M')}_"""
    success = send_telegram_message(message)
    if success:
        print("Message sent successfully!")
    else:
        print("Failed to send message")

if __name__ == "__main__":
    main()
