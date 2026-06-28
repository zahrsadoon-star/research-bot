import os
import requests
import google.generativeai as genai
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

SEARCH_KEYWORDS = [
    "PV battery sizing optimization",
    "hybrid optimization renewable energy",
    "photovoltaic battery storage",
    "genetic algorithm particle swarm optimization energy",
    "solar energy storage system",
    "renewable energy Iraq",
    "HOMER energy system optimization"
]

def fetch_from_semantic_scholar(keyword):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": keyword,
        "limit": 5,
        "fields": "title,abstract,authors,year,url,venue",
    }
    try:
        response = requests.get(url, params=params, timeout=20)
        if response.status_code == 200:
            papers = response.json().get("data", [])
            return [p for p in papers if p.get("abstract") and len(p.get("abstract","")) > 100]
    except:
        pass
    return []

def fetch_from_arxiv(keyword):
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{keyword}",
        "start": 0,
        "max_results": 5,
        "sortBy": "relevance"
    }
    try:
        response = requests.get(url, params=params, timeout=20)
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            papers = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                link = entry.find('atom:id', ns)
                authors_list = entry.findall('atom:author', ns)
                published = entry.find('atom:published', ns)
                
                if title is not None and summary is not None:
                    authors = ", ".join([
                        a.find('atom:name', ns).text 
                        for a in authors_list[:3] 
                        if a.find('atom:name', ns) is not None
                    ])
                    papers.append({
                        "title": title.text.strip(),
                        "abstract": summary.text.strip(),
                        "authors": [{"name": n} for n in authors.split(", ")],
                        "year": published.text[:4] if published is not None else "N/A",
                        "url": link.text.strip() if link is not None else "N/A",
                        "venue": "arXiv"
                    })
            return papers
    except:
        pass
    return []

def fetch_paper():
    import random
    random.shuffle(SEARCH_KEYWORDS)
    
    for keyword in SEARCH_KEYWORDS:
        # Try Semantic Scholar first
        papers = fetch_from_semantic_scholar(keyword)
        if papers:
            return random.choice(papers)
        # Try arXiv as backup
        papers = fetch_from_arxiv(keyword)
        if papers:
            return random.choice(papers)
    return None

def summarize_with_gemini(paper):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    title = paper.get("title", "No title")
    abstract = paper.get("abstract", "No abstract")
    authors_raw = paper.get("authors", [])
    if authors_raw and isinstance(authors_raw[0], dict):
        authors = ", ".join([a.get("name", "") for a in authors_raw[:3]])
    else:
        authors = str(authors_raw)
    year = paper.get("year", "N/A")
    venue = paper.get("venue", "N/A")
    url = paper.get("url", "N/A")

    prompt = f"""أنت مساعد بحثي لطالب ماجستير في هندسة الطاقة الكهربائية متخصص في أنظمة PV-Battery والشبكات الذكية.

لخص هذا البحث بالعربية بشكل واضح ومنظم:

العنوان: {title}
الباحثون: {authors}
السنة: {year}
المصدر: {venue}

الملخص:
{abstract}

قدم:
1. 🎯 الهدف الرئيسي (2-3 جمل)
2. 🔧 المنهجية (2-3 جمل)
3. 📊 أهم النتائج (2-3 نقاط)
4. 💡 أهميته لمجال PV-Battery (جملة أو جملتين)

اكتب بعربية واضحة ومختصرة."""

    response = model.generate_content(prompt)
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "url": url,
        "summary": response.text
    }

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload, timeout=15)
    return r.status_code == 200

def main():
    print(f"Bot started at {datetime.now()}")
    paper = fetch_paper()
    
    if not paper:
        send_telegram("⚠️ لم يتم العثور على أبحاث اليوم. سيتم المحاولة مرة أخرى.")
        return

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

_تم الإرسال تلقائياً ✅ {datetime.now().strftime('%Y-%m-%d %H:%M')}_"""

    if send_telegram(message):
        print("✅ Message sent!")
    else:
        print("❌ Failed to send")

if __name__ == "__main__":
    main()
