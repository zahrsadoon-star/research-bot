import os
import requests
import xml.etree.ElementTree as ET
import random
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

SEARCH_KEYWORDS = [
    "photovoltaic battery storage optimization",
    "solar energy storage system sizing",
    "renewable energy optimization algorithm",
    "hybrid energy system optimization",
    "particle swarm optimization energy storage",
    "PV system sizing genetic algorithm",
    "battery energy storage renewable Iraq"
]

def fetch_from_arxiv():
    keyword = random.choice(SEARCH_KEYWORDS)
    print(f"Searching: {keyword}")
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{keyword}",
        "start": 0,
        "max_results": 10,
        "sortBy": "relevance"
    }
    response = requests.get(url, params=params, timeout=30)
    print(f"arXiv status: {response.status_code}")
    if response.status_code != 200:
        return None
    root = ET.fromstring(response.text)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entries = root.findall('atom:entry', ns)
    print(f"Found {len(entries)} entries")
    papers = []
    for entry in entries:
        title = entry.find('atom:title', ns)
        summary = entry.find('atom:summary', ns)
        link = entry.find('atom:id', ns)
        authors_els = entry.findall('atom:author', ns)
        published = entry.find('atom:published', ns)
        if title is None or summary is None:
            continue
        abstract = summary.text.strip()
        if len(abstract) < 100:
            continue
        authors = ", ".join([
            a.find('atom:name', ns).text
            for a in authors_els[:3]
            if a.find('atom:name', ns) is not None
        ])
        papers.append({
            "title": title.text.strip().replace('\n', ' '),
            "abstract": abstract,
            "authors": authors,
            "year": published.text[:4] if published is not None else "N/A",
            "url": link.text.strip() if link is not None else "N/A",
            "venue": "arXiv"
        })
    return random.choice(papers) if papers else None

def summarize_with_groq(paper):
    prompt = f"""أنت مساعد بحثي لطالب ماجستير في هندسة الطاقة الكهربائية متخصص في أنظمة PV-Battery والشبكات الذكية.

لخص هذا البحث بالعربية:

العنوان: {paper['title']}
الباحثون: {paper['authors']}
السنة: {paper['year']}

الملخص:
{paper['abstract']}

قدم:
1. 🎯 الهدف الرئيسي (2-3 جمل)
2. 🔧 المنهجية (2-3 جمل)
3. 📊 أهم النتائج (2-3 نقاط)
4. 💡 أهميته لمجال PV-Battery (جملة أو جملتين)

اكتب بعربية واضحة ومختصرة."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    print(f"Groq status: {response.status_code}")
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Groq error: {response.text}")
        return None

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload, timeout=15)
    print(f"Telegram status: {r.status_code}")
    return r.status_code == 200

def main():
    print(f"Bot started at {datetime.now()}")
    paper = fetch_from_arxiv()
    if not paper:
        send_telegram("⚠️ لم يتم العثور على أبحاث اليوم.")
        return
    print(f"Paper: {paper['title']}")
    summary = summarize_with_groq(paper)
    if not summary:
        send_telegram("⚠️ حدث خطأ في التلخيص. سيتم المحاولة مرة أخرى.")
        return
    message = f"""📚 *بحث جديد في مجالك*
━━━━━━━━━━━━━━━━━━━━
📄 *العنوان:*
{paper['title']}

👥 *الباحثون:* {paper['authors']}
📅 *السنة:* {paper['year']}
🏛️ *المصدر:* {paper['venue']}

━━━━━━━━━━━━━━━━━━━━
{summary}
━━━━━━━━━━━━━━━━━━━━
🔗 [رابط البحث الكامل]({paper['url']})

_✅ {datetime.now().strftime('%Y-%m-%d %H:%M')}_"""

    send_telegram(message)
    print("Done!")

if __name__ == "__main__":
    main()
