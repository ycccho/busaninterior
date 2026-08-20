import urllib.request
import re
import json

urls = [
    "https://cleanbloomhq.pages.dev/gangnam-hospital.html",
    "https://cleanwavekr.pages.dev/gangnam-hospital.html",
    "https://cleanblushhq.pages.dev/sinsa-gangnam-hospital-regular.html",
    "https://cleanseoulkr.pages.dev/gangnam-hospital-regular.html"
]

results = []

for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
        
        # Extract title
        title_m = re.search(r'<title>(.*?)</title>', html, re.I)
        title = title_m.group(1) if title_m else ""
        
        # Extract meta description
        desc_m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.I)
        desc = desc_m.group(1) if desc_m else ""
        
        # Extract canonical
        canon_m = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']', html, re.I)
        canon = canon_m.group(1) if canon_m else ""
        
        # Extract schemas
        schemas = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', html, re.I | re.S)
        
        # Count links
        links = re.findall(r'href=["\'](.*?)["\']', html)
        internal_links = [l for l in links if not l.startswith('tel:') and not l.startswith('http') or url.split('/')[2] in l]
        tel_links = [l for l in links if l.startswith('tel:')]
        naver_form_links = [l for l in links if 'naver.me' in l or 'naver' in l]
        
        # Count total word count / char count
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        
        results.append({
            "url": url,
            "title": title,
            "desc": desc,
            "canonical": canon,
            "schema_count": len(schemas),
            "schemas": [s.strip() for s in schemas],
            "total_links": len(links),
            "internal_links_count": len(internal_links),
            "sample_internal_links": internal_links[:10],
            "tel_links": tel_links,
            "naver_form_links": naver_form_links,
            "html_length": len(html),
            "text_length": len(text),
            "headings": {
                "h1": re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.I | re.S),
                "h2": re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.I | re.S),
                "h3": re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.I | re.S),
            }
        })
    except Exception as e:
        results.append({"url": url, "error": str(e)})

with open("D:/busaninterior/competitor_analysis.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Saved analysis to competitor_analysis.json")
