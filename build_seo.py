import os
import sys
import json
import math
import re
from datetime import datetime, timezone

# ==============================================================================
# HOMPAGE_KEYWORD SEO 자동화 빌더 (busaninterior.kr 전용)
# 검색엔진(네이버 Yeti, 구글 Googlebot) 가이드라인 100% 준수
# 정적 HTML 20,580개 일괄 빌더 + Cloudflare Pages 엣지 렌더러 동시 지원
# ==============================================================================

SITE_URL = "https://busaninterior.kr"
BRAND_NAME = "부산 병원 인테리어 전문 업체"
RECOMMENDED_PARTNER = "인디컴퍼니"
PARTNER_URL = "https://inde.co.kr"
RAW_KEYWORD_FILE = os.path.join(os.path.dirname(__file__), "키워드작업", "keyword_combination.txt")
OUTPUT_DIR = os.path.dirname(__file__)

# 지역 매핑 목록 (긴 단어 우선)
REGIONS = [
    "부산 중구", "부산 서구", "부산 동구", "부산 영도구", "부산 부산진구", "부산 동래구",
    "부산 남구", "부산 북구", "부산 해운대구", "부산 사하구", "부산 금정구", "부산 강서구",
    "부산 연제구", "부산 수영구", "부산 사상구", "부산 기장군", "부산진구", "해운대구", "수영구",
    "동래구", "금정구", "강서구", "연제구", "사하구", "사상구", "부산",
    "울산 중구", "울산 남구", "울산 동구", "울산 북구", "울산 울주군", "울산",
    "경남 진주", "경남 통영", "경남 사천", "경남 김해", "경남 밀양", "경남 거제", "경남 양산", "경남 창원", "경남",
    "명지신도시", "명지", "에코델타시티", "센텀시티", "센텀", "해운대", "기장", "서면", "광안리", "남포동",
    "사상", "덕천", "화명", "동래", "진주", "창원", "김해", "밀양", "거제도", "거제", "양산", "통영", "사천",
    "신논현", "논현", "압구정", "청담", "강남"
]

def parse_keyword(kw: str):
    kw = kw.strip()
    if not kw:
        return None
    
    found_region = "부산 및 전국"
    cleaned_kw = kw
    for r in REGIONS:
        if kw.startswith(r + " ") or kw == r:
            found_region = r
            cleaned_kw = kw[len(r):].strip()
            break
            
    action = "인테리어"
    if "리모델링" in cleaned_kw:
        action = "리모델링"
        
    suffix = "전문 업체"
    if "전문 회사" in cleaned_kw or "회사" in cleaned_kw:
        suffix = "전문 회사"
    elif "전문 업체" in cleaned_kw or "전문업체" in cleaned_kw:
        suffix = "전문 업체"
    elif "추천" in cleaned_kw:
        suffix = "추천"
        
    category = cleaned_kw
    for remove_term in ["인테리어 전문 업체", "인테리어 전문 회사", "인테리어 회사", "리모델링 전문 업체", "리모델링 전문 회사", "리모델링 회사", "인테리어", "리모델링", "전문 업체", "전문 회사", "추천"]:
        category = category.replace(remove_term, "").strip()
    if not category:
        category = "병원/의원"
        
    return {
        "raw_keyword": kw,
        "region": found_region,
        "category": category,
        "action": action,
        "suffix": suffix
    }

def generate_seo_dataset(raw_keywords):
    dataset = []
    seen = set()
    id_counter = 1
    
    for raw in raw_keywords:
        raw = raw.strip()
        if not raw or raw in seen:
            continue
        seen.add(raw)
        
        parsed = parse_keyword(raw)
        if not parsed:
            continue
            
        page_id = id_counter
        id_counter += 1
        
        region = parsed["region"]
        category = parsed["category"]
        action = parsed["action"]
        
        title = f"{raw} 견적 및 시공 추천 | {BRAND_NAME}"
        
        if region != "부산 및 전국":
            desc = f"{region} 지역 {category} {action} 전문! 의료법 인허가 기준 동선 설계, 3D 도면 무료 제공 및 합리적인 평당 공사 비용 비교 견적 상담."
        else:
            desc = f"부산 및 전국 {category} {action} 전문 비교 견적! 의료 공간 최적화 설계, 실내건축공사업 면허 보유 업체의 신뢰할 수 있는 시공."
            
        canonical = f"{SITE_URL.rstrip('/')}/{page_id}/"
        
        schema_json = {
            "@context": "https://schema.org",
            "@type": "HomeAndConstructionBusiness",
            "name": f"{raw} - {BRAND_NAME}",
            "description": desc,
            "url": canonical,
            "telephone": "1588-0000",
            "priceRange": "$$",
            "areaServed": {
                "@type": "AdministrativeArea",
                "name": region if region != "부산 및 전국" else "부산광역시"
            },
            "serviceType": f"{category} {action}",
            "provider": {
                "@type": "Organization",
                "name": BRAND_NAME,
                "url": SITE_URL
            }
        }
        
        item = {
            "id": page_id,
            "keyword": raw,
            "region": region,
            "category": category,
            "action": action,
            "title": title,
            "description": desc,
            "url": canonical,
            "schema_json": schema_json
        }
        dataset.append(item)
        
    return dataset

def generate_sitemaps(dataset, output_dir):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # 주요 메인 및 포트폴리오 페이지
    xml_content.append(f'  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>')
    xml_content.append(f'  <url><loc>{SITE_URL}/portfolio-derma.html</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>')
    xml_content.append(f'  <url><loc>{SITE_URL}/portfolio-eye-internal.html</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>')
    xml_content.append(f'  <url><loc>{SITE_URL}/portfolio-dental.html</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>')
    
    # HTML 사이트맵 페이지 (1~42)
    total_pages = max(1, math.ceil(len(dataset) / 500))
    for p in range(1, total_pages + 1):
        p_url = f"{SITE_URL}/sitemap/" if p == 1 else f"{SITE_URL}/sitemap/page/{p}/"
        xml_content.append(f'  <url><loc>{p_url}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')
        
    # 20,580개 키워드 랜딩 페이지
    for item in dataset:
        loc = item["url"]
        xml_content.append(f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>')
        
    xml_content.append('</urlset>')
    
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_content))
        
    print(f"Generated: {sitemap_path} ({len(xml_content) - 2} URLs included)")
    
    # robots.txt 최신화
    robots_path = os.path.join(output_dir, "robots.txt")
    robots_content = f"""User-agent: *
Allow: /
Disallow:

Sitemap: {SITE_URL}/sitemap.xml
"""
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(robots_content)
    print(f"Updated: {robots_path}")

def generate_html_sitemaps(dataset, output_dir):
    PAGE_SIZE = 500
    total_items = len(dataset)
    total_pages = max(1, math.ceil(total_items / PAGE_SIZE))
    
    sitemap_base_dir = os.path.join(output_dir, "sitemap")
    os.makedirs(sitemap_base_dir, exist_ok=True)
    os.makedirs(os.path.join(sitemap_base_dir, "page"), exist_ok=True)
    
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * PAGE_SIZE
        end_idx = min(total_items, page_num * PAGE_SIZE)
        page_items = dataset[start_idx:end_idx]
        
        # 페이지네이션 링크 생성
        pagination_html = []
        pagination_html.append('<nav class="sitemap-pagination" aria-label="사이트맵 페이지 네비게이션">')
        if page_num > 1:
            prev_url = f"{SITE_URL}/sitemap/page/{page_num - 1}/" if page_num > 2 else f"{SITE_URL}/sitemap/"
            pagination_html.append(f'<a href="{prev_url}" class="page-btn prev">&laquo; 이전</a>')
            
        for p in range(1, total_pages + 1):
            p_url = f"{SITE_URL}/sitemap/page/{p}/" if p > 1 else f"{SITE_URL}/sitemap/"
            active_class = "active" if p == page_num else ""
            aria_current = ' aria-current="page"' if p == page_num else ''
            pagination_html.append(f'<a href="{p_url}" class="page-num {active_class}"{aria_current}>{p}</a>')
            
        if page_num < total_pages:
            next_url = f"{SITE_URL}/sitemap/page/{page_num + 1}/"
            pagination_html.append(f'<a href="{next_url}" class="page-btn next">다음 &raquo;</a>')
        pagination_html.append('</nav>')
        pagination_str = "".join(pagination_html)
        
        # 키워드 그리드 링크 목록 생성
        list_items = []
        for item in page_items:
            list_items.append(f'<li><a href="{item["url"]}" title="{item["keyword"]}">• {item["keyword"]}</a></li>')
        list_str = "\n".join(list_items)
        
        canonical_url = f"{SITE_URL}/sitemap/page/{page_num}/" if page_num > 1 else f"{SITE_URL}/sitemap/"
        
        html_doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>부산 병원 인테리어 전체 사이트맵 {page_num}페이지 | {BRAND_NAME}</title>
  <meta name="description" content="{BRAND_NAME} 진료과목 및 지역별 인테리어 포트폴리오 전체 사이트맵 {page_num}페이지 목록입니다.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical_url}">
  
  <!-- Pretendard Web Font CDN -->
  <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
  
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
    header.site-header {{ text-align: center; margin-bottom: 24px; }}
    h1 {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
    p.subtitle {{ font-size: 13px; color: #64748b; }}
    .sitemap-grid {{ list-style: none; display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 8px; margin: 24px 0; }}
    .sitemap-grid li a {{ display: block; padding: 8px 12px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; text-decoration: none; color: #334155; font-size: 13px; transition: all 0.2s ease; }}
    .sitemap-grid li a:hover {{ background: #fff7ed; border-color: #dd5828; color: #dd5828; transform: translateY(-1px); }}
    .sitemap-pagination {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin: 24px 0; }}
    .sitemap-pagination a {{ padding: 5px 10px; border: 1px solid #cbd5e1; border-radius: 4px; text-decoration: none; color: #334155; font-size: 12.5px; background: #ffffff; transition: all 0.15s; }}
    .sitemap-pagination a.active {{ background: #dd5828; color: #ffffff; border-color: #dd5828; font-weight: bold; }}
    .sitemap-pagination a:hover:not(.active) {{ background: #f1f5f9; }}
    .nav-links {{ display: flex; justify-content: center; gap: 16px; margin-top: 30px; font-size: 13px; }}
    .nav-links a {{ color: #dd5828; text-decoration: none; font-weight: 600; }}
    .nav-links a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="container">
    <header class="site-header">
      <h1>부산 병원 인테리어 전체 사이트맵 (페이지 {page_num} / {total_pages})</h1>
      <p class="subtitle">진료과목별(내과·치과·피부과·안과·성형외과 등) 및 지역별 인테리어/리모델링 전문 포트폴리오 바로가기</p>
    </header>
    
    {pagination_str}
    
    <ul class="sitemap-grid">
      {list_str}
    </ul>
    
    {pagination_str}
    
    <div class="nav-links">
      <a href="{SITE_URL}/">← 메인 페이지로 이동</a>
      <a href="{PARTNER_URL}" target="_blank" rel="noopener noreferrer">추천업체 인디컴퍼니 바로가기 →</a>
    </div>
  </div>
</body>
</html>
"""
        if page_num == 1:
            with open(os.path.join(sitemap_base_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_doc)
                
        page_dir = os.path.join(sitemap_base_dir, "page", str(page_num))
        os.makedirs(page_dir, exist_ok=True)
        with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_doc)
            
    print(f"Generated: {total_pages} HTML sitemap pages in {sitemap_base_dir}")

def update_index_and_base_html(total_pages):
    index_file = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 사이트맵 1~N 네비게이션 섹션 생성
    sitemap_buttons = []
    for p in range(1, total_pages + 1):
        s_url = f"{SITE_URL}/sitemap/" if p == 1 else f"{SITE_URL}/sitemap/page/{p}/"
        sitemap_buttons.append(
            f'<a href="{s_url}" title="사이트맵 {p}페이지 바로가기" class="px-2.5 py-1 bg-white hover:bg-[#dd5828] hover:text-white border border-gray-200 rounded text-xs text-gray-600 transition-all font-medium">{p}</a>'
        )
    sitemap_buttons_str = "\n        ".join(sitemap_buttons)

    sitemap_section = f"""  <!-- 전체 사이트맵 네비게이션 (검색엔진 크롤링 최적화 허브) -->
  <section class="max-w-7xl mx-auto px-6 py-10 border-t border-gray-200" id="sitemap-hub">
    <div class="bg-gray-50 border border-gray-200/80 rounded-xl p-6 text-center shadow-sm">
      <div class="flex items-center justify-center gap-2 mb-3">
        <span class="w-2 h-2 rounded-full bg-[#dd5828]"></span>
        <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">전체 진료과목 &amp; 지역별 서비스 사이트맵</h3>
      </div>
      <p class="text-[11px] text-gray-500 mb-4">원하시는 지역과 병원 진료과목의 맞춤 인테리어 포트폴리오 및 견적 정보를 바로 확인하실 수 있습니다.</p>
      <div class="flex flex-wrap justify-center gap-1.5">
        {sitemap_buttons_str}
      </div>
    </div>
  </section>
"""

    # 기존 sitemap-hub 섹션이 있다면 교체, 없다면 <!-- Footer Section --> 또는 <footer 앞에 삽입
    if 'id="sitemap-hub"' in html:
        html = re.sub(r'<!-- 전체 사이트맵 네비게이션[\s\S]*?</section>\n?', sitemap_section, html)
    elif '<!-- Footer Section -->' in html:
        html = html.replace('<!-- Footer Section -->', f'{sitemap_section}\n  <!-- Footer Section -->')
    else:
        html = html.replace('<footer', f'{sitemap_section}\n  <footer')

    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated index.html with sitemap navigation hub.")

    # busaninterior_base.html 생성
    base_file = os.path.join(OUTPUT_DIR, "busaninterior_base.html")
    with open(base_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Created/Updated busaninterior_base.html template.")
    return html

def generate_static_pages(dataset, base_html, output_dir):
    print(f"Generating all {len(dataset)} static keyword HTML pages...")
    for item in dataset:
        page_id = item["id"]
        page_dir = os.path.join(output_dir, str(page_id))
        os.makedirs(page_dir, exist_ok=True)

        html = base_html

        # 1. Title & 메타태그 치환
        html = re.sub(r'<title>.*?</title>', f'<title>{item["title"]}</title>', html, flags=re.I)
        html = re.sub(r'<meta name="description" content=".*?" />', f'<meta name="description" content="{item["description"]}" />\n  <link rel="canonical" href="{item["url"]}" />', html, flags=re.I)
        html = re.sub(r'<meta property="og:title" content=".*?" />', f'<meta property="og:title" content="{item["title"]}" />', html, flags=re.I)
        html = re.sub(r'<meta property="og:description" content=".*?" />', f'<meta property="og:description" content="{item["description"]}" />\n  <meta property="og:url" content="{item["url"]}" />', html, flags=re.I)

        # 2. Schema.org JSON-LD 주입
        schema_script = f"""  <script type="application/ld+json">
  {json.dumps(item["schema_json"], ensure_ascii=False)}
  </script>
</head>"""
        html = html.replace('</head>', schema_script)

        # 3. 헤더 로고 서브 텍스트 치환
        html = html.replace('메디컬 공간 디자인</span>', f'{item["keyword"]}</span>')

        # 4. 히어로 H1 타이틀 치환
        html = html.replace('<span class="text-primary">부산 병원 공간 디자인</span>', f'<span class="text-primary">{item["keyword"]}</span>')

        with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)

    print(f"Successfully generated all {len(dataset)} static pages in {output_dir}")

def create_cloudflare_edge_function(total_pages):
    functions_dir = os.path.join(OUTPUT_DIR, "functions")
    os.makedirs(functions_dir, exist_ok=True)
    
    function_code = f"""/**
 * Cloudflare Pages Functions / Workers용 동적 SEO 엣지 렌더러
 * 대상 사이트: busaninterior.kr
 * 경로: functions/[id].js 및 functions/[id]/index.js
 */

export async function onRequest(context) {{
  const {{ request, params }} = context;
  const url = new URL(request.url);
  const idStr = params.id;
  const pageId = parseInt(idStr, 10);

  if (isNaN(pageId) || pageId < 1 || pageId > 25000) {{
    return new Response('Page Not Found', {{ status: 404 }});
  }}

  // 1. 키워드 DB 조회
  const dataResponse = await fetch(new URL('/seo_keywords.json', url.origin));
  if (!dataResponse.ok) {{
    return new Response('Keywords DB not loaded', {{ status: 500 }});
  }}
  const keywords = await dataResponse.json();
  const item = keywords.find(k => k.id === pageId);

  if (!item) {{
    return new Response('Page Not Found', {{ status: 404 }});
  }}

  // 2. busaninterior 베이스 HTML 로드
  const baseResponse = await fetch(new URL('/busaninterior_base.html', url.origin));
  if (!baseResponse.ok) {{
    return new Response('Base HTML not loaded', {{ status: 500 }});
  }}
  let html = await baseResponse.text();

  // 3. Title & 메타태그 치환 (White-hat SEO 표준)
  html = html.replace(
    /<title>.*?<\\/title>/i,
    `<title>${{item.title}}</title>`
  );
  html = html.replace(
    /<meta name="description" content=".*?" \\/>/i,
    `<meta name="description" content="${{item.description}}" />\\n  <link rel="canonical" href="${{item.url}}" />`
  );
  html = html.replace(
    /<meta property="og:title" content=".*?" \\/>/i,
    `<meta property="og:title" content="${{item.title}}" />`
  );
  html = html.replace(
    /<meta property="og:description" content=".*?" \\/>/i,
    `<meta property="og:description" content="${{item.description}}" />\\n  <meta property="og:url" content="${{item.url}}" />`
  );

  // 4. Schema.org JSON-LD 구조화 데이터 주입
  const schemaScript = `
  <!-- 동적 Schema.org 구조화 데이터 -->
  <script type="application/ld+json">
  ${{JSON.stringify(item.schema_json)}}
  </script>
</head>`;
  html = html.replace('</head>', schemaScript);

  // 5. 헤더 상단 로고 옆 서브 텍스트 치환
  html = html.replace(
    '메디컬 공간 디자인</span>',
    `${{item.keyword}}</span>`
  );

  // 6. 히어로 H1 메인 타이틀 치환
  html = html.replace(
    '<span class="text-primary">부산 병원 공간 디자인</span>',
    `<span class="text-primary">${{item.keyword}}</span>`
  );

  return new Response(html, {{
    headers: {{
      'content-type': 'text/html;charset=UTF-8',
      'cache-control': 'public, max-age=86400, s-maxage=604800'
    }}
  }});
}}
"""
    # 1) functions/[id].js
    function_file = os.path.join(functions_dir, "[id].js")
    with open(function_file, "w", encoding="utf-8") as f:
        f.write(function_code)
    print(f"Created: {function_file}")

    # 2) functions/[id]/index.js (Trailing slash 지원)
    id_dir = os.path.join(functions_dir, "[id]")
    os.makedirs(id_dir, exist_ok=True)
    function_index_file = os.path.join(id_dir, "index.js")
    with open(function_index_file, "w", encoding="utf-8") as f:
        f.write(function_code)
    print(f"Created: {function_index_file}")

def main():
    print("=== HOMPAGE_KEYWORD SEO 자동화 빌드 시작 ===")
    print(f"대상 사이트: {SITE_URL}")
    print(f"브랜드: {BRAND_NAME}")
    
    if not os.path.exists(RAW_KEYWORD_FILE):
        print(f"Error: {RAW_KEYWORD_FILE} not found.")
        sys.exit(1)
        
    with open(RAW_KEYWORD_FILE, "r", encoding="utf-8-sig") as f:
        raw_keywords = [line.strip() for line in f if line.strip()]
        
    print(f"원천 키워드 수: {len(raw_keywords)}개")
    
    # 1. SEO 데이터셋 생성
    dataset = generate_seo_dataset(raw_keywords)
    print(f"파싱 완료된 고유 키워드 수: {len(dataset)}개")
    
    # 2. JSON 데이터 저장
    json_path = os.path.join(OUTPUT_DIR, "seo_keywords.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Saved: {json_path}")
    
    # 3. 사이트맵 페이지 수
    total_pages = max(1, math.ceil(len(dataset) / 500))
    
    # 4. index.html 및 busaninterior_base.html 갱신
    base_html = update_index_and_base_html(total_pages)
    
    # 5. sitemap.xml 및 robots.txt 생성
    generate_sitemaps(dataset, OUTPUT_DIR)
    
    # 6. HTML 사이트맵(1~42페이지) 생성
    generate_html_sitemaps(dataset, OUTPUT_DIR)
    
    # 7. Cloudflare Pages Functions 엣지 렌더러 생성
    create_cloudflare_edge_function(total_pages)

    # 8. GitHub Pages 정적 20,580개 HTML 일괄 생성
    generate_static_pages(dataset, base_html, OUTPUT_DIR)
    
    print("=== HOMPAGE_KEYWORD SEO 빌드 완료! ===")

if __name__ == "__main__":
    main()
