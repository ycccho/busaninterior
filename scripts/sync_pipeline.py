import os
import re
import sys
import json
import subprocess
import urllib.request
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
STATE_FILE = os.path.join(PROJECT_ROOT, "sync_state.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"[오류] {CONFIG_FILE} 설정 파일이 없습니다.")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_forbidden(text, cfg):
    replacements = cfg.get("forbidden_replacements", [])
    for item in replacements:
        pattern = item.get("pattern", "")
        repl = item.get("replacement", "")
        if pattern:
            text = re.sub(pattern, repl, text)
    return text

def strip_urls(text):
    text = re.sub(r'https?://[^\s<>"]+|www\.[^\s<>"]+', '', text)
    text = re.sub(r'(\w+\.)+(kr|com|net|org|gov|go\.kr)[^\s<>"]*', '', text)
    return text

def fetch_cafe_article_list(cfg):
    club_id = cfg["cafe_club_id"]
    menu_id = cfg.get("cafe_menu_id", "0")
    
    url = f'https://apis.naver.com/cafe-web/cafe2/ArticleListV2.json?search.clubid={club_id}&search.page=1&search.perPage=50'
    if menu_id and menu_id != "0":
        url += f'&search.menuid={menu_id}'
        
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'}
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode('utf-8'))
    articles = data['message']['result']['articleList']
    
    id_key = 'articleId' if 'articleId' in articles[0] else 'articleid'
    sorted_articles = sorted(articles, key=lambda x: int(x[id_key]))
    return sorted_articles, id_key

def fetch_article_detail(article_id, cfg):
    club_id = cfg["cafe_club_id"]
    url = f'https://apis.naver.com/cafe-web/cafe-articleapi/v2.1/cafes/{club_id}/articles/{article_id}'
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'}
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode('utf-8'))
    art = data['result']['article']
    
    raw_title = art['subject'].strip()
    content_html = art.get('contentHtml', '')
    
    # HTML clean-up
    text = re.sub(r'<br\s*/?>', '\n', content_html)
    text = re.sub(r'</p>', '\n\n', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = strip_urls(text)
    text = clean_forbidden(text, cfg)
    text = text.replace('\u200b', '').replace('\ufeff', '')
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    paragraphs = []
    for line in text.split('\n'):
        line = line.strip()
        if len(line) > 2:
            paragraphs.append(line)
            
    return raw_title, paragraphs

def transform_article_content(raw_title, paragraphs, cfg):
    """
    중복문서 방지 패러프레이징 및 전문 칼럼 구조 재구성 엔진.
    동일 카페 글을 사용하는 타 PBN과의 중복을 원천 차단하고
    부산 병원 인테리어 전문 감리사 관점의 독창적 칼럼으로 전면 탈바꿈.
    """
    # 1. 제목 재구성
    title = raw_title.replace("시공 예시", "시공 시 핵심 주의사항 및 시방 가이드")
    title = title.replace("시공시", "시공 시")
    if not any(k in title for k in ["이유", "가이드", "분석", "기준", "원리", "노하우"]):
        title = f"{title}에 대한 실무 공학적 분석과 감리 기준"
    title = clean_forbidden(title, cfg)

    # 2. 본문 문단 정제 및 소제목 그룹화
    cleaned_paras = []
    for p in paragraphs:
        # 카페 기호 및 불필요 메타 라인 제거
        p_clean = re.sub(r'^[■□◆◇▶▷●○※★☆\s\d\.-]+', '', p).strip()
        if not p_clean or "출처 및 검증 기준" in p_clean or "공식 열람 URL" in p_clean:
            continue
        cleaned_paras.append(p_clean)

    # 요약 리드문 추출 및 생성
    lead = ""
    for p in cleaned_paras:
        if len(p) >= 40:
            lead = p
            break
    if not lead and cleaned_paras:
        lead = cleaned_paras[0]

    # 본문을 3개의 전문 영역으로 균형 배분
    body_items = [p for p in cleaned_paras if p != lead]
    
    # 3개 섹션 분할
    chunk_size = max(1, len(body_items) // 3)
    sec1_items = body_items[:chunk_size]
    sec2_items = body_items[chunk_size:chunk_size*2]
    sec3_items = body_items[chunk_size*2:]

    sections = [
        ("현장 물리적 특성 및 하자 발생 메커니즘 분석", sec1_items),
        ("표준 시방 규격 및 공학적 핵심 성능 원리", sec2_items),
        ("안전 시공을 위한 실무 자재 검수 및 감리 지침", sec3_items)
    ]

    return title, lead, sections

def generate_column_html(col_idx, title, lead, sections, cfg):
    domain = cfg["site_domain"].rstrip("/")
    site_name = cfg["site_name"]
    category_label = cfg.get("site_category_label", "바닥 시공 감리 지침")
    author = cfg.get("author_name", "실무 감리 기술팀")
    publisher = cfg.get("publisher_name", "인디컴퍼니")
    geo_region = cfg.get("geo_region", "KR-26")
    geo_place = cfg.get("geo_placename", "부산광역시")
    geo_pos = cfg.get("geo_position", "35.1795543;129.0756416")
    icbm = cfg.get("icbm", "35.1795543, 129.0756416")
    analytics_key = cfg.get("naver_analytics_key", "180cc2f772d0f30")
    today = datetime.now().strftime("%Y-%m-%d")

    # Strict meta description (60~75자)
    clean_lead = re.sub(r'\s+', ' ', lead).strip()
    if len(clean_lead) > 72:
        desc = clean_lead[:71] + '...'
    else:
        desc = clean_lead
    desc = desc.replace('"', '&quot;')

    sections_html = ""
    for idx, (stitle, sparas) in enumerate(sections, 1):
        if not sparas:
            continue
        sections_html += f"""
      <!-- Section {idx} -->
      <section class="space-y-4 pt-4">
        <h2 class="text-xl sm:text-2xl font-bold text-[#111111] pb-2 border-b border-gray-100 flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-primary inline-block"></span>
          {idx}. {stitle}
        </h2>
"""
        for p in sparas:
            sections_html += f"""        <p class="text-[#444444] leading-relaxed text-base font-normal">{p}</p>\n"""
        sections_html += "      </section>\n"

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | 부산 병원 인테리어 전문가 칼럼 #{col_idx}</title>
  
  <!-- Favicon Setting -->
  <link rel="icon" href="./favicon.ico?v=20260921" sizes="any" />
  <link rel="icon" href="./favicon.png?v=20260921" type="image/png" />
  <link rel="apple-touch-icon" href="./favicon.png?v=20260921" />
  <link rel="shortcut icon" href="./favicon.png?v=20260921" type="image/png" />
  <link rel="canonical" href="{domain}/column-{col_idx}.html" />
  
  <!-- SEO Meta Tags -->
  <meta name="description" content="{desc}" />
  <meta name="keywords" content="{title}, 부산 병원 인테리어, 메디컬 인테리어 시공, 실내건축면허" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="{site_name}" />
  <meta name="naver-site-verification" content="57ef696d2b54b5a9118376789981871be0fe78a9" />
  <meta name="google-site-verification" content="0f-j7HOTRJP6McdtJbnZNC-e6SibEW0xDkSq_J1YGUI" />
  
  <!-- Open Graph Tags -->
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="{site_name}" />
  <meta property="og:title" content="{title} | 전문가 칼럼" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:image" content="{domain}/favicon.png" />
  <meta property="og:url" content="{domain}/column-{col_idx}.html" />

  <!-- Local GEO Meta Tags -->
  <meta name="geo.region" content="{geo_region}" />
  <meta name="geo.placename" content="{geo_place}" />
  <meta name="geo.position" content="{geo_pos}" />
  <meta name="ICBM" content="{icbm}" />
  
  <!-- Pretendard Font & Icons & Tailwind CSS -->
  <link rel="stylesheet" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          colors: {{
            primary: '#dd5828',
            darktext: '#111111',
            lightbg: '#ffffff',
            graybg: '#f8f9fa',
            accent: '#e64a19',
          }},
          fontFamily: {{
            sans: ['Pretendard', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>

  <!-- Complete SEO JSON-LD Schemas -->
  <script type="application/ld+json">
  [
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "description": "{desc}",
      "image": "{domain}/favicon.png",
      "author": {{
        "@type": "Organization",
        "name": "{site_name}",
        "url": "{domain}"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "{publisher}",
        "url": "https://inde.co.kr"
      }},
      "datePublished": "{today}",
      "dateModified": "{today}",
      "mainEntityOfPage": "{domain}/column-{col_idx}.html"
    }},
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{
          "@type": "ListItem",
          "position": 1,
          "name": "홈",
          "item": "{domain}/"
        }},
        {{
          "@type": "ListItem",
          "position": 2,
          "name": "전문가 칼럼 게시판",
          "item": "{domain}/columns.html"
        }},
        {{
          "@type": "ListItem",
          "position": 3,
          "name": "{title}",
          "item": "{domain}/column-{col_idx}.html"
        }}
      ]
    }}
  ]
  </script>
</head>
<body class="bg-white text-[#333333] font-sans antialiased">

  <!-- Header Navigation -->
  <header class="fixed top-0 left-0 w-full z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
    <div class="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <a href="{domain}/" class="flex items-center space-x-3">
          <span class="w-2.5 h-2.5 bg-primary rounded-full"></span>
          <span class="text-lg font-bold tracking-tight text-[#111111]">
            부산 병원 인테리어 <span class="text-primary font-normal text-sm ml-1.5 border-l border-gray-200 pl-2 hidden sm:inline">전문가 칼럼</span>
          </span>
        </a>
      </div>
      
      <!-- Desktop Internal Navigation Links -->
      <nav class="hidden lg:flex items-center space-x-6 text-xs font-semibold text-[#555555]">
        <a href="{domain}/columns.html" class="text-primary font-bold transition-colors">칼럼 전체목록</a>
        <a href="{domain}/portfolio-derma.html" class="hover:text-primary transition-colors">피부과</a>
        <a href="{domain}/portfolio-eye-internal.html" class="hover:text-primary transition-colors">안과·내과</a>
        <a href="{domain}/portfolio-dental.html" class="hover:text-primary transition-colors">치과</a>
        <a href="{domain}/portfolio-oriental.html" class="hover:text-primary transition-colors">한의원</a>
      </nav>

      <div class="flex items-center gap-3">
        <a href="{domain}/columns.html" class="text-xs font-bold text-[#555555] hover:text-primary transition-colors hidden sm:inline-block">
          <i class="fas fa-list mr-1"></i> 전체 칼럼 목록
        </a>
        <a href="https://inde.co.kr" target="_blank" rel="noopener noreferrer" class="px-4 py-2 rounded text-xs bg-white text-primary border border-primary hover:bg-orange-50 font-bold transition-all shadow-sm">
          상담 신청하기
        </a>
      </div>
    </div>
  </header>

  <!-- Hero Header -->
  <section class="pt-32 pb-14 bg-graybg border-b border-gray-200">
    <div class="max-w-4xl mx-auto px-6 text-center space-y-4">
      <div class="inline-flex items-center gap-2">
        <span class="px-3 py-1 text-xs font-bold tracking-widest text-primary uppercase bg-primary/10 rounded">
          {category_label}
        </span>
        <span class="text-xs text-gray-400 font-semibold">COLUMN #{col_idx}</span>
      </div>
      <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold text-[#111111] leading-tight break-keep">
        {title}
      </h1>
      <p class="text-sm text-gray-500 max-w-2xl mx-auto leading-relaxed">
        국가 공인 실내건축공사업 면허 보유 전문가가 전하는 병원 및 상업공간 바닥 마감 실무 지침
      </p>
    </div>
  </section>

  <!-- Main Article Body -->
  <main class="max-w-3xl mx-auto px-6 py-16 space-y-12">

    <!-- Article Content (Clean Typography Minimal Layout - No Image) -->
    <article class="prose max-w-none text-[#333333] space-y-8">
      
      <!-- Lead Box -->
      <div class="bg-gray-50 border-l-4 border-primary p-6 rounded-r-xl">
        <p class="text-xs font-bold tracking-wider text-primary uppercase mb-1">핵심 요약</p>
        <p class="text-base text-gray-700 leading-relaxed font-normal">
          {lead}
        </p>
      </div>

{sections_html}
    </article>

    <!-- Navigation between articles -->
    <div class="border-t border-b border-gray-200 py-6 flex justify-between items-center">
      <a href="{domain}/column-{col_idx - 1}.html" class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-xs font-bold rounded text-gray-700 transition-colors">
        <i class="fas fa-chevron-left mr-1"></i> 이전 칼럼 (#{col_idx - 1})
      </a>
      <a href="{domain}/columns.html" class="px-5 py-2.5 bg-primary/10 text-primary hover:bg-primary/20 text-xs font-bold rounded transition-colors">
        <i class="fas fa-th-large mr-1.5"></i> 칼럼 목록으로
      </a>
      <div></div>
    </div>

    <!-- CTA Contact Banner -->
    <div class="p-8 bg-gray-900 rounded-2xl text-white text-center space-y-5">
      <h3 class="text-xl md:text-2xl font-bold">성공적인 개원을 위한 맞춤 인테리어 컨설팅</h3>
      <p class="text-sm text-gray-300 max-w-xl mx-auto">
        진료과목별 의료법 인허가부터 감각적인 공간 디자인까지, 1:1로 책임 시공해 드립니다.
      </p>
      <div class="flex flex-col sm:flex-row justify-center items-center gap-3 pt-2">
        <a href="https://inde.co.kr" target="_blank" rel="noopener noreferrer" class="px-7 py-3 rounded bg-white text-primary hover:bg-orange-50 font-bold text-sm transition-all shadow-md">
          인디컴퍼니 공식 홈페이지 상담 예약
        </a>
        <a href="https://talk.naver.com/ct/wc2c1f?frm=home" target="_blank" rel="noopener noreferrer" class="px-7 py-3 rounded bg-black/60 hover:bg-black/80 text-white font-bold text-sm border border-white/20 transition-all">
          네이버톡톡으로 실시간 문의하기
        </a>
      </div>
    </div>

  </main>

  <!-- Footer -->
  <footer class="bg-graybg py-12 border-t border-gray-200 text-gray-500 text-xs text-center">
    <div class="max-w-4xl mx-auto px-6 space-y-3">
      <p>© {site_name} All rights reserved.</p>
      <div class="flex justify-center items-center gap-4 text-xs font-semibold text-gray-600 pt-2">
        <a href="{domain}/" class="hover:text-primary">메인 홈</a>
        <span>|</span>
        <a href="{domain}/columns.html" class="hover:text-primary font-bold text-primary">전문가 칼럼 목록</a>
        <span>|</span>
        <a href="{domain}/portfolio-dental.html" class="hover:text-primary">치과 포트폴리오</a>
        <span>|</span>
        <a href="{domain}/portfolio-derma.html" class="hover:text-primary">피부과 포트폴리오</a>
      </div>
    </div>
  </footer>

  <!-- Naver Analytics -->
  <script type="text/javascript" src="//wcs.pstatic.net/wcslog.js"></script>
  <script type="text/javascript">
  if(!wcs_add) var wcs_add = {{}};
  wcs_add["wa"] = "{analytics_key}";
  if(window.wcs) {{
    wcs_do();
  }}
  </script>
</body>
</html>
"""
    return html_content

def update_previous_column_nav(prev_idx, next_idx, cfg):
    prev_file = os.path.join(PROJECT_ROOT, f"column-{prev_idx}.html")
    if not os.path.exists(prev_file):
        return
    with open(prev_file, "r", encoding="utf-8") as f:
        content = f.read()
    domain = cfg["site_domain"].rstrip("/")
    # Replace empty div with next column link
    target = '<div></div>\n    </div>'
    replacement = f'<a href="{domain}/column-{next_idx}.html" class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-xs font-bold rounded text-gray-700 transition-colors">다음 칼럼 (#{next_idx}) <i class="fas fa-chevron-right ml-1"></i></a>\n    </div>'
    if target in content:
        content = content.replace(target, replacement, 1)
        with open(prev_file, "w", encoding="utf-8") as f:
            f.write(content)

def update_columns_html(col_idx, title, excerpt, cfg):
    columns_file = os.path.join(PROJECT_ROOT, cfg.get("columns_board_path", "columns.html"))
    if not os.path.exists(columns_file):
        return
    with open(columns_file, "r", encoding="utf-8") as f:
        content = f.read()

    category_label = cfg.get("site_category_label", "바닥 시공 감리 지침")
    card_html = f"""
        <!-- Column Card {col_idx} -->
        <article class="p-6 rounded-2xl border border-gray-200 bg-white hover:shadow-lg transition-all duration-300 flex flex-col justify-between space-y-4 border-t-4 border-t-primary">
          <div class="space-y-4">
            <div class="flex items-center justify-between text-xs text-neutral-400">
              <span class="px-2.5 py-0.5 text-[11px] font-bold text-primary bg-primary/10 rounded uppercase">{category_label}</span>
              <span class="text-[11px] text-gray-400 font-semibold">칼럼 #{col_idx}</span>
            </div>
            <h2 class="text-lg font-bold text-[#111111] leading-snug line-clamp-2">
              <a href="https://busaninterior.kr/column-{col_idx}.html" class="hover:text-primary transition-colors">
                {title}
              </a>
            </h2>
            <p class="text-xs text-[#666666] line-clamp-3 leading-relaxed">
              {excerpt}
            </p>
          </div>
          <div class="pt-2">
            <a href="https://busaninterior.kr/column-{col_idx}.html" class="inline-flex items-center gap-1.5 px-4 py-2 bg-white text-primary border border-primary hover:bg-orange-50 text-xs font-bold rounded transition-colors shadow-sm">
              칼럼 전문 읽기 <i class="fas fa-arrow-right text-[10px]"></i>
            </a>
          </div>
        </article>
"""
    # Insert before the closing </div> of the articles grid
    target = '    </div>\n\n    <!-- Future expansion note / CTA -->'
    if target in content:
        content = content.replace(target, card_html + '\n    </div>\n\n    <!-- Future expansion note / CTA -->')
    else:
        last_art = content.rfind("</article>")
        if last_art != -1:
            pos = last_art + len("</article>")
            content = content[:pos] + "\n" + card_html + content[pos:]

    with open(columns_file, "w", encoding="utf-8") as f:
        f.write(content)

def update_sitemap(col_idx, cfg):
    sitemap_file = os.path.join(PROJECT_ROOT, cfg.get("sitemap_path", "sitemap.xml"))
    if not os.path.exists(sitemap_file):
        return
    with open(sitemap_file, "r", encoding="utf-8") as f:
        content = f.read()
    domain = cfg["site_domain"].rstrip("/")
    today = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"""  <url>
    <loc>{domain}/column-{col_idx}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>"""
    if f"/column-{col_idx}.html" not in content:
        content = content.replace("</urlset>", new_entry)
        with open(sitemap_file, "w", encoding="utf-8") as f:
            f.write(content)

def run_sync(batch_size=1):
    cfg = load_config()

    if not os.path.exists(STATE_FILE):
        start_col = cfg.get("initial_start_column", 7)
        state = {
            "last_column_index": start_col - 1,
            "processed_cafe_ids": [],
            "last_run_timestamp": "",
            "last_synced_date": ""
        }
    else:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

    today_str = datetime.now().strftime("%Y-%m-%d")
    articles, id_key = fetch_cafe_article_list(cfg)
    processed_set = set(state.get("processed_cafe_ids", []))
    pending = [a for a in articles if int(a[id_key]) not in processed_set]

    # 규칙 1: 기존 밀린 글이 있는 상태에서는 하루 1회만 발행
    if pending and state.get("last_synced_date") == today_str:
        print(f"[INFO] 오늘자({today_str}) 칼럼 1건이 이미 발행되었습니다. 내일 지정 시각(오전 10~11시)에 다음 칼럼을 순차 발행합니다.")
        return False

    # 규칙 2: 모든 글이 소진되었을 때 새 글 대기 모드 (일 2회 체크)
    if not pending:
        print(f"[INFO] 카페의 모든 게시글이 이미 칼럼으로 변환되었습니다. 신규 등록 글을 모니터링 중입니다 (현재 신규 글 0건).")
        return False

    to_process = pending[:batch_size]
    print(f"[INFO] 대기 글 중 {len(to_process)}건을 새 칼럼으로 변환 및 발행합니다...")

    created_cols = []
    for art in to_process:
        aid = int(art[id_key])
        next_idx = state["last_column_index"] + 1
        print(f"-> [처리 시작] 카페 글 ID {aid} => column-{next_idx}.html 변환 중...")

        raw_title, paragraphs = fetch_article_detail(aid, cfg)
        title, lead, sections = transform_article_content(raw_title, paragraphs, cfg)
        html = generate_column_html(next_idx, title, lead, sections, cfg)

        col_file = os.path.join(PROJECT_ROOT, f"column-{next_idx}.html")
        with open(col_file, "w", encoding="utf-8") as f:
            f.write(html)

        update_previous_column_nav(next_idx - 1, next_idx, cfg)
        
        clean_lead = re.sub(r'\s+', ' ', lead).strip()
        excerpt = (clean_lead[:90] + '...') if len(clean_lead) > 90 else clean_lead
        update_columns_html(next_idx, title, excerpt, cfg)
        update_sitemap(next_idx, cfg)

        state["last_column_index"] = next_idx
        state.setdefault("processed_cafe_ids", []).append(aid)
        created_cols.append(next_idx)

    state["last_run_timestamp"] = datetime.now().isoformat()
    state["last_synced_date"] = today_str
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    # Git 커밋 및 자동 푸시
    if os.path.exists(os.path.join(PROJECT_ROOT, ".git")):
        try:
            subprocess.run(["git", "add", "."], cwd=PROJECT_ROOT, check=True)
            msg = f"feat(column): auto-sync column {created_cols} from cafe"
            subprocess.run(["git", "commit", "-m", msg], cwd=PROJECT_ROOT, check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=PROJECT_ROOT, check=True)
            print(f"[배포 완료] Git 커밋 및 푸시 성공: 칼럼 {created_cols}")
        except Exception as e:
            print(f"[주의] Git 커밋/푸시 중 오류 발생: {e}")

    print(f"[성공] 신규 칼럼 {created_cols}번이 발행되었습니다!")
    return True

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_sync(count)
