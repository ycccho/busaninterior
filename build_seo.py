import os
import sys
import json
import math
import re
import shutil
from datetime import datetime, timezone

# ==============================================================================
# HOMPAGE_KEYWORD SEO 자동화 마스터 빌더 (busaninterior.kr 전용)
# 네이버 Yeti / 구글 Googlebot 가이드라인 100% 준수
# 598개 고품질 핵심 타겟 키워드 정적 HTML 빌더 + 사이트맵/로봇 최적화
# ==============================================================================

SITE_URL = "https://busaninterior.kr"
BRAND_NAME = "부산 병원 인테리어 전문 업체"
RECOMMENDED_PARTNER = "인디컴퍼니"
PARTNER_URL = "https://inde.co.kr"
RAW_KEYWORD_FILE = os.path.join(os.path.dirname(__file__), "키워드작업", "keyword_combination.txt")
OUTPUT_DIR = os.path.dirname(__file__)

# 13개 핵심 타겟 지역 매핑
REGIONS = [
    "부산", "대구", "밀양", "구미", "창원", "센텀", "해운대", "명지", "거제", "기장", "김해", "울산", "경남"
]

# 진료과목별 고유 특화 전문 설명 DB (D.I.A+ 적합도 및 Thin Content 탈피용)
CATEGORY_SPECS = {
    "치과": "체어 전용 급배수 및 컴프레셔 설비 라인, 파노라마/CT실 방사선 납차폐 규격, 중앙 멸균 소독실의 위생 동선",
    "피부과": "VIP 1인 관리실의 아늑한 간접 조도 설계, 프라이빗 파우더룸, 고출력 레이저 장비 전력 승압 및 환기 공조",
    "성형외과": "무균 수술실 양압 공조 시스템, 수술 후 프라이빗 회복실, 상담실과 원장실 간 최단 진료 동선",
    "내과": "호흡기 환자 분리 대기 공간, 내시경실 세척·소독 설비 라인, 건강검진 기초검사 및 채혈실 연계 동선",
    "안과": "정밀 암실 굴절 검사실 조도 제어, 무균 수술실 공조 설비, 수납 및 안경 처방 라운지 동선",
    "정형외과": "C-arm 방사선 차폐 벽체 공사, 물리치료실 베드 간격 최적화, 도수치료실 특수 방음 및 환자 탈의실 동선",
    "도수치료": "도수치료실 벽체 이중 차음 방음 공사, 운동치료실 넓은 개방감 및 충격 흡수 바닥재, 쾌적한 환기 설비",
    "이비인후과": "청력 검사 전용 방음 부스 시공, 호흡기 치료기 체어 배선, 네블라이저 공간 분리",
    "한의원": "탕전실 배기 후드 및 방수 설비, 침구실 온돌/온열 전용 배선, 약재 보관실과 원장 진료실 동선",
    "한방병원": "입원실 병상 간격 기준 준수, 탕전실 대용량 배기 공조, 물리치료실 및 침구치료실의 분리 조닝",
    "산부인과": "프라이빗 진료 및 초음파실 조도 설계, 가족 분만실 및 회복실 방음, 신생아실 항균 공조",
    "비뇨기과": "환자 프라이버시를 최우선한 진료/상담실 방음, 요역동학 검사실 및 처치실의 독립적 조닝",
    "외과": "외래 처치실 및 무균 수술실 공조 인프라, 멸균 소독실과 회복실 간의 막힘없는 의료진 서브 동선",
    "어린이병원": "어린이 눈높이 친환경 무독성 마감재, 안전 코너 보호대, 소아 전용 놀이 대기실 및 감염 분리실",
    "요양병원": "휠체어·스트레처카 회전 반경 확보, 병실 간 넓은 복도 및 안전 손잡이, 각 층별 간호 스테이션 시야 확보",
    "암요양병원": "온열치료실 및 면역치료실 특수 전력 설비, 쾌적한 웰니스 힐링 라운지, 환자 안심 친환경 마감",
    "건강검진센터": "접수-기초검사-채혈-내시경-초음파로 이어지는 원스톱 원방향 검진 동선, 대형 라운지 대기 공간",
    "노인주간보호센터": "낙상 방지 미끄럼 방지 바닥재, 문턱 없는 무단차 설계, 프로그램실 및 생활실의 채광 중심 배치",
    "노인요양원": "치매 전담실 및 안전 케어 동선, 기저귀 교환 및 목욕실 특수 방수/배수, 소방 피난 구조 설비",
    "약국": "조제실 클린 환기 및 약품 수납장 최적화, 처방전 접수·복약지도 카운터 동선, 대기 공간 시야 확보",
    "산후조리원": "신생아실 개별 음압/양압 공조, 산모 전용 마사지 및 스파룸, 호텔 스위트급 객실 방음 및 공기정화",
    "동물병원": "처치실 및 수술실 멸균 동선, 대형견·소형견 분리 대기실, 격리 입원실 방음 및 전용 배기 환기",
    "병원": "진료과목별 의료법 규격 동선 설계, 무균 수술실 및 특수 공조 설비, 환자 신뢰를 주는 프리미엄 로비",
    "의원": "원장실-진료실-처치실-대기공간의 효율적 공간 조닝, 소방 안전 기준 충족, 합리적인 평당 공사비 설계"
}

def parse_keyword(kw: str):
    kw = kw.strip()
    if not kw:
        return None
    
    found_region = "부산"
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
        category = "병원"
        
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
        
        # 타이틀 (클린 & 전문성)
        title = f"{raw} 견적 및 시공 추천 | {BRAND_NAME}"
        
        # 설명문 (민감 단어 완전 배제 & 전문 메디컬 가이드)
        desc = f"{region} 지역 {category} {action} 전문! 의료 공간 최적화 동선 설계, 3D 도면 무료 제공 및 합리적인 평당 공사 비용 비교 견적 상담."
            
        canonical = f"{SITE_URL.rstrip('/')}/{page_id}/"
        
        # 고유 메타 키워드 (해당 페이지 지역 & 과목 맞춤형)
        meta_keywords = f"{region} {category} {action}, {region} {category} 인테리어, {region} {category} 리모델링, {category} 인테리어 전문 업체, {region} 병원 인테리어, {region} 병원 리모델링"
        
        # 카테고리별 특화 스펙 텍스트
        spec_text = CATEGORY_SPECS.get(category, CATEGORY_SPECS.get("병원"))
        
        schema_json = [
            {
                "@context": "https://schema.org",
                "@type": "HomeAndConstructionBusiness",
                "name": f"{raw} - {BRAND_NAME}",
                "description": desc,
                "url": canonical,
                "telephone": "1588-0000",
                "priceRange": "$$",
                "areaServed": {
                    "@type": "AdministrativeArea",
                    "name": region if region != "경남" else "경상남도"
                },
                "serviceType": f"{category} {action}",
                "provider": {
                    "@type": "Organization",
                    "name": BRAND_NAME,
                    "url": SITE_URL
                }
            },
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"{region} {category} 프리미엄 {action}는 일반 인테리어와 무엇이 다른가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"{region} {category} 프리미엄 {action}는 최고급 프리미엄 마감재를 엄선하여 사용하며, 환자에게 안락함을 선사하는 정교한 조도 설계와 호텔 라운지급 대기실 조성을 통해 차별화된 가치와 브랜딩을 실현합니다."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"{region} {category} 공간 인테리어 설계 시 가장 중요한 점은 무엇인가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"{region} {category} 개원 시 {spec_text} 등 특수 조건들을 사전에 철저히 반영하여 안전하고 오차 없는 정밀 설계를 진행합니다."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": "병원 인테리어 시 '실내건축공사업 면허'가 꼭 필요한가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "건설산업기본법에 따라 공사 금액이 1,500만 원 이상인 실내 인테리어 공사는 반드시 정부 등록 면허를 보유한 업체만 시공하도록 규정되어 있습니다. 무면허 업체 시공 시 하자보수(AS) 거부, 돌연 중단 및 먹튀, 소방 안전 기준 미달 등 중대 손실이 발생할 수 있습니다. 고객이 국토교통부 키스콘(KISCON, 건설산업지식정보시스템) 사이트에서 해당 인테리어 업체의 면허 보유 여부를 필히 조회할 것을 권장합니다."
                        }
                    }
                ]
            }
        ]
        
        item = {
            "id": page_id,
            "keyword": raw,
            "region": region,
            "category": category,
            "action": action,
            "spec_text": spec_text,
            "title": title,
            "description": desc,
            "meta_keywords": meta_keywords,
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
    
    # 598개 핵심 타겟 키워드 랜딩 페이지
    for item in dataset:
        loc = item["url"]
        xml_content.append(f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')
        
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

def generate_html_sitemaps(dataset, base_html, output_dir):
    PAGE_SIZE = 300
    total_items = len(dataset)
    total_pages = max(1, math.ceil(total_items / PAGE_SIZE))
    
    sitemap_base_dir = os.path.join(output_dir, "sitemap")
    # 기존 sitemap 폴더 정리
    if os.path.exists(sitemap_base_dir):
        shutil.rmtree(sitemap_base_dir, ignore_errors=True)
    os.makedirs(sitemap_base_dir, exist_ok=True)
    os.makedirs(os.path.join(sitemap_base_dir, "page"), exist_ok=True)
    
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * PAGE_SIZE
        end_idx = min(total_items, page_num * PAGE_SIZE)
        page_items = dataset[start_idx:end_idx]
        
        # 앵커 텍스트 링크 그리드 생성
        list_items = []
        for item in page_items:
            list_items.append(f'<li><a href="{item["url"]}" title="{item["keyword"]}" class="block p-2.5 bg-white hover:bg-[#fff7ed] border border-gray-200 hover:border-[#dd5828] hover:text-[#dd5828] rounded text-xs text-gray-700 transition-all duration-150 truncate font-medium">• {item["keyword"]}</a></li>')
        list_str = "\n".join(list_items)
        
        # 페이지네이션 링크 생성
        pagination_html = []
        pagination_html.append('<div class="flex flex-wrap justify-center gap-1.5 my-4">')
        if page_num > 1:
            prev_url = f"{SITE_URL}/sitemap/page/{page_num - 1}/" if page_num > 2 else f"{SITE_URL}/sitemap/"
            pagination_html.append(f'<a href="{prev_url}" class="px-2.5 py-1 bg-white hover:bg-[#dd5828] hover:text-white border border-gray-200 rounded text-xs text-gray-600 transition-all font-medium">&laquo; 이전</a>')
            
        for p in range(1, total_pages + 1):
            p_url = f"{SITE_URL}/sitemap/page/{p}/" if p > 1 else f"{SITE_URL}/sitemap/"
            active_class = "bg-[#dd5828] text-white font-bold" if p == page_num else "bg-white text-gray-600 hover:bg-[#dd5828] hover:text-white"
            pagination_html.append(f'<a href="{p_url}" class="px-2.5 py-1 border border-gray-200 rounded text-xs transition-all {active_class}">{p}</a>')
            
        if page_num < total_pages:
            next_url = f"{SITE_URL}/sitemap/page/{page_num + 1}/"
            pagination_html.append(f'<a href="{next_url}" class="px-2.5 py-1 bg-white hover:bg-[#dd5828] hover:text-white border border-gray-200 rounded text-xs text-gray-600 transition-all font-medium">다음 &raquo;</a>')
        pagination_html.append('</div>')
        pagination_str = "".join(pagination_html)
        
        # 앵커 텍스트 허브 섹션 (풀 메인 홈페이지 하단)
        sitemap_section = f"""  <!-- 전국 키워드 모음 앵커 텍스트 크롤러 허브 (풀 홈페이지 내장형) -->
  <section class="max-w-7xl mx-auto px-6 py-10 border-t border-gray-200" id="sitemap-hub">
    <div class="bg-gray-50 border border-gray-200/80 rounded-xl p-5 sm:p-6 text-center shadow-sm">
      <div class="flex items-center justify-center gap-2 mb-2">
        <span class="w-2.5 h-2.5 rounded-full bg-[#dd5828]"></span>
        <h3 class="text-sm font-bold text-gray-800 uppercase tracking-wider">주요 지역별 병원 인테리어 키워드 모음 (페이지 {page_num} / {total_pages})</h3>
      </div>
      <p class="text-xs text-gray-500 mb-4">원하시는 지역과 병원 진료과목의 맞춤 인테리어 포트폴리오 및 견적 정보를 바로 확인하실 수 있습니다.</p>
      
      {pagination_str}
      
      <ul class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 text-left my-6 list-none p-0">
        {list_str}
      </ul>
      
      {pagination_str}
    </div>
  </section>
"""
        
        html = base_html
        canonical_url = f"{SITE_URL}/sitemap/page/{page_num}/" if page_num > 1 else f"{SITE_URL}/sitemap/"
        html = re.sub(r'<title>.*?</title>', f'<title>부산 병원 인테리어 전문 업체 | 주요 키워드 모음 ({page_num}/{total_pages})</title>', html, flags=re.I)
        html = re.sub(r'<meta name="robots" content=".*?" />', f'<meta name="robots" content="noindex, follow" />\n  <link rel="canonical" href="{canonical_url}" />', html, flags=re.I)
        
        if 'id="sitemap-hub"' in html:
            html = re.sub(r'<!-- (전체 사이트맵|전국 키워드)[\s\S]*?</section>\n?', sitemap_section, html)
        elif '<!-- Footer Section -->' in html:
            html = html.replace('<!-- Footer Section -->', f'{sitemap_section}\n  <!-- Footer Section -->')
        else:
            html = html.replace('<footer', f'{sitemap_section}\n  <footer')
            
        if page_num == 1:
            with open(os.path.join(sitemap_base_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
                
        page_dir = os.path.join(sitemap_base_dir, "page", str(page_num))
        os.makedirs(page_dir, exist_ok=True)
        with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
            
    print(f"Generated: {total_pages} Full-featured HTML sitemap pages with anchor links in {sitemap_base_dir}")

def update_index_and_base_html(total_pages):
    index_file = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. 모든 상대 경로(./)를 루트 절대 경로(/)로 변환
    html = html.replace('href="./', 'href="/')
    html = html.replace('src="./', 'src="/')
    html = html.replace('content="./', f'content="{SITE_URL}/')

    # 2. 파비콘 태그 보강 (/favicon.ico, /favicon.png)
    favicon_tags = """  <!-- Favicon Setting -->
  <link rel="icon" href="/favicon.ico" />
  <link rel="icon" href="/favicon.png" type="image/png" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <link rel="apple-touch-icon" href="/favicon.png" />"""
    
    if '<!-- Favicon Setting -->' in html:
        html = re.sub(r'<!-- Favicon Setting -->[\s\S]*?(?=<!-- SEO Meta Tags)', f'{favicon_tags}\n  \n  ', html)

    # 3. 메인 홈페이지 & 개별 페이지용 컴팩트 네비게이션 허브
    sitemap_section = f"""  <!-- 주요 지역별 키워드 모음 네비게이션 허브 -->
  <section class="max-w-7xl mx-auto px-6 py-6 border-t border-gray-200" id="sitemap-hub">
    <div class="bg-gray-50 border border-gray-200/80 rounded-xl p-4 sm:p-5 text-center shadow-sm">
      <div class="flex items-center justify-center gap-2 mb-3">
        <span class="w-2 h-2 rounded-full bg-[#dd5828]"></span>
        <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">주요 지역별 병원 인테리어 모음</h3>
      </div>
      <div class="flex items-center justify-center flex-wrap gap-1.5 text-xs">
        <a href="{SITE_URL}/sitemap/" title="사이트맵 1페이지 바로가기" class="px-2.5 py-1 bg-white hover:bg-[#dd5828] hover:text-white border border-gray-200 rounded text-xs text-gray-600 transition-all font-medium">1</a>
        <a href="{SITE_URL}/sitemap/page/2/" title="사이트맵 2페이지 바로가기" class="px-2.5 py-1 bg-white hover:bg-[#dd5828] hover:text-white border border-gray-200 rounded text-xs text-gray-600 transition-all font-medium">2</a>
        <a href="{SITE_URL}/sitemap/page/2/" title="사이트맵 다음 페이지 바로가기" class="px-3 py-1 bg-white hover:bg-[#dd5828] hover:text-white border border-gray-200 rounded text-xs text-[#dd5828] hover:text-white transition-all font-semibold ml-1">다음 &raquo;</a>
      </div>
    </div>
  </section>
"""

    if 'id="sitemap-hub"' in html:
        html = re.sub(r'<!-- (전체 사이트맵|전국 키워드|주요 지역별)[\s\S]*?</section>\n?', sitemap_section, html)
    elif '<!-- Footer Section -->' in html:
        html = html.replace('<!-- Footer Section -->', f'{sitemap_section}\n  <!-- Footer Section -->')
    else:
        html = html.replace('<footer', f'{sitemap_section}\n  <footer')

    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated index.html with simple sitemap navigation hub and root asset paths.")

    # busaninterior_base.html 생성
    base_file = os.path.join(OUTPUT_DIR, "busaninterior_base.html")
    with open(base_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Created/Updated busaninterior_base.html template.")
    return html

def clean_old_directories(output_dir, new_dataset_len):
    print("Cleaning up old directory trees...")
    # 숫자로 된 디렉토리들 중 새로운 범위(1~new_dataset_len) 외의 디렉토리 및 기존 디렉토리 안전 정리
    for entry in os.listdir(output_dir):
        full_path = os.path.join(output_dir, entry)
        if os.path.isdir(full_path) and entry.isdigit():
            shutil.rmtree(full_path, ignore_errors=True)
    print("Old directories cleaned.")

def generate_static_pages(dataset, base_html, output_dir):
    print(f"Generating all {len(dataset)} static keyword HTML pages with rich contextual enrichment...")
    
    for item in dataset:
        page_id = item["id"]
        page_dir = os.path.join(output_dir, str(page_id))
        os.makedirs(page_dir, exist_ok=True)

        html = base_html

        # 1. Head 영역: Title, Description, Canonical, Single Og Tags, Meta Keywords 정밀 교체
        head_block = f"""  <title>{item["title"]}</title>
  
  <!-- Favicon Setting -->
  <link rel="icon" href="/favicon.ico" />
  <link rel="icon" href="/favicon.png" type="image/png" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <link rel="apple-touch-icon" href="/favicon.png" />
  
  <!-- SEO Meta Tags for Naver & Google -->
  <meta name="description" content="{item["description"]}" />
  <link rel="canonical" href="{item["url"]}" />
  <meta name="keywords" content="{item["meta_keywords"]}" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="{BRAND_NAME}" />
  <meta name="google-site-verification" content="0f-j7HOTRJP6McdtJbnZNC-e6SibEW0xDkSq_J1YGUI" />
  
  <!-- Open Graph Tags (SNS Sharing) -->
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{BRAND_NAME}" />
  <meta property="og:title" content="{item["title"]}" />
  <meta property="og:description" content="{item["description"]}" />
  <meta property="og:image" content="{SITE_URL}/main1.webp" />
  <meta property="og:url" content="{item["url"]}" />"""

        # 1. <head> 내부의 SEO 메타 블록 전체를 교체
        html = re.sub(r'<title>.*?</title>[\s\S]*?(?=<!-- Pretendard Web Font CDN -->)', f'{head_block}\n  \n  ', html, flags=re.I)

        # 2. Schema.org JSON-LD 단일 통합 주입 (동적 FAQPage 및 로컬 비즈니스 완벽 동기화)
        schema_script = f"""<script type="application/ld+json">
  {json.dumps(item["schema_json"], ensure_ascii=False, indent=2)}
  </script>"""
        if '<script type="application/ld+json">' in html:
            html = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>', schema_script, html)
        else:
            html = html.replace('</head>', f'  {schema_script}\n</head>')

        # 3. 헤더 로고 서브 텍스트 치환
        html = html.replace('메디컬 공간 디자인</span>', f'{item["keyword"]}</span>')

        # 4. 히어로 섹션 동적 치환 (H1 + 뱃지 + 설명문)
        html = html.replace('안과 · 내과 복합 메디컬 공간 특화', f'{item["region"]} {item["category"]} 특화 메디컬 공간 디자인')
        html = html.replace('<span class="text-primary">부산 병원 공간 디자인</span>', f'<span class="text-primary">{item["keyword"]}</span>')

        # 5. 본문 Intro 철학 인용구 동적 맞춤화 (D.I.A+ 본문 연관도 점수 극대화)
        old_quote = '"공간 기획 단계에서부터 의료법과 현장 소방/공조 시설 기준을 완벽하게 검토하여 설계합니다."'
        new_quote = f'"{item["region"]} 지역 {item["category"]} {item["action"]} 시, 진료과목 특성에 최적화된 동선과 소방/공조 시설 기준을 완벽하게 검토하여 설계합니다."'
        html = html.replace(old_quote, new_quote)

        # 6. FAQ 1 & 2 질문 및 답변 동적 맞춤화 (본문 형태소 매칭)
        old_faq1 = '<span>부산 병원 프리미엄 인테리어는 일반 인테리어와 무엇이 다른가요?</span>'
        new_faq1 = f'<span>{item["region"]} {item["category"]} 프리미엄 {item["action"]}는 일반 인테리어와 무엇이 다른가요?</span>'
        html = html.replace(old_faq1, new_faq1)

        old_faq2 = '<span>진료 과목별(내과, 치과, 피부과 등) 인테리어 설계 시 가장 중요한 점은 무엇인가요?</span>'
        new_faq2 = f'<span>{item["region"]} {item["category"]} 공간 인테리어 설계 시 가장 중요한 점은 무엇인가요?</span>'
        html = html.replace(old_faq2, new_faq2)

        # FAQ 2 답변 내 진료과목별 특화 설명 삽입
        old_faq2_ans = '의료 시설 법정 기준에 미달해 준공 검사가 지연되거나 수술실이 비법정 규격으로 완공될 시 대규모의 매몰 비용과 재공사가 수반될 수 있습니다.'
        new_faq2_ans = f'{item["region"]} {item["category"]} 개원 시 {item["spec_text"]} 등 특수 조건들을 사전에 철저히 반영하여 안전하고 오차 없는 정밀 설계를 진행합니다.'
        html = html.replace(old_faq2_ans, new_faq2_ans)

        with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)

    print(f"Successfully generated all {len(dataset)} enriched static pages in {output_dir}")

def main():
    print("=== HOMPAGE_KEYWORD SEO 자동화 빌드 시작 ===")
    print(f"대상 사이트: {SITE_URL}")
    print(f"브랜드: {BRAND_NAME}")
    
    if not os.path.exists(RAW_KEYWORD_FILE):
        print(f"Error: {RAW_KEYWORD_FILE} not found.")
        sys.exit(1)
        
    with open(RAW_KEYWORD_FILE, "r", encoding="utf-8") as f:
        raw_keywords = [line.strip() for line in f if line.strip()]
        
    print(f"로딩된 키워드 수: {len(raw_keywords)}개")
    dataset = generate_seo_dataset(raw_keywords)
    print(f"파싱 완료된 고유 키워드 수: {len(dataset)}개")
    
    # 1. seo_keywords.json 저장
    json_path = os.path.join(OUTPUT_DIR, "seo_keywords.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Saved: {json_path}")
    
    # 2. total_pages 계산 및 index.html / busaninterior_base.html 최신화
    PAGE_SIZE = 300
    total_pages = max(1, math.ceil(len(dataset) / PAGE_SIZE))
    base_html = update_index_and_base_html(total_pages)
    
    # 3. sitemap.xml & robots.txt 생성
    generate_sitemaps(dataset, OUTPUT_DIR)
    
    # 4. HTML 사이트맵 생성 (noindex, follow 적용된 풀 홈페이지 템플릿)
    generate_html_sitemaps(dataset, base_html, OUTPUT_DIR)
    
    # 5. 기존 구 디렉토리 정리 및 598개 정적 HTML 생성
    clean_old_directories(OUTPUT_DIR, len(dataset))
    generate_static_pages(dataset, base_html, OUTPUT_DIR)
    
    # 6. GitHub Pages용 .nojekyll 보장
    nojekyll_path = os.path.join(OUTPUT_DIR, ".nojekyll")
    if not os.path.exists(nojekyll_path):
        with open(nojekyll_path, "w", encoding="utf-8") as f:
            f.write("")
        print(f"Created: {nojekyll_path}")
        
    print("=== HOMPAGE_KEYWORD SEO 빌드 완료! ===")

if __name__ == "__main__":
    main()
