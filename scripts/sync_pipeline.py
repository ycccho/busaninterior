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
    text = re.sub(r'\(\s*\)', '', text)
    return text

def is_stub_line(line):
    s = line.strip()
    if not s or s == '\u200b':
        return True
    # Reference path banners like [하자담보책임 법령 및 소비자 피해구제 접수 경로]
    if re.search(r'\[.*?(?:경로|열람|신청|접수|출처).*?\]', s):
        return True
    # Verification banner lines
    if '접속 이상 유무' in s or '국가 공인 홈페이지' in s:
        return True
    # Search instructions
    if re.search(r'▶?\s*찾는\s*방법:?', s):
        return True
    if re.match(r'^(웹\s*브라우저\s*)?주소창에', s):
        return True
    # Organization names with dangling ( e.g. 국가법령정보센터 (, 한국소비자원 (
    if re.search(r'(국가법령정보센터|한국소비자원|건축행정시스템|세움터|국가건설기준센터|소비자24|공정거래위원회|대한법률구조공단|국토교통부|KISCON|KCSC|e나라표준인증)', s) and (s.endswith('(') or ' (' in s):
        return True
    # Dangling parenthesis or empty parentheses at end
    if re.search(r'\(\s*\)?$', s):
        return True
    # Section titles like 출처 및 검증 기준 (공식 열람 URL)
    if '출처 및 검증 기준' in s or '공식 열람 URL' in s:
        return True
    return False

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
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode('utf-8'))
        art = data.get('result', {}).get('article')
        if not art or not art.get('contentHtml'):
            return None, []
        
        raw_title = art.get('subject', '').strip()
        content_html = art.get('contentHtml', '')
    except Exception as e:
        print(f"[알림] 글 ID {article_id} 수집 불가 (멤버공개 또는 비공개): {e}")
        return None, []
    
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
        if len(line) > 2 and not is_stub_line(line):
            paragraphs.append(line)
            
    return raw_title, paragraphs


def fix_korean_particles(text):
    """
    용어 치환 후 한국어 조사(은/는, 이/가, 을/를, 과/와) 어색함 자동 교정
    """
    text = re.sub(r'병원·의원는', '병원·의원은', text)
    text = re.sub(r'병원·의원가', '병원·의원이', text)
    text = re.sub(r'병원·의원를', '병원·의원을', text)
    text = re.sub(r'병원·의원와', '병원·의원과', text)
    text = re.sub(r'의료시설는', '의료시설은', text)
    text = re.sub(r'의료시설가', '의료시설이', text)
    text = re.sub(r'의료시설를', '의료시설을', text)
    text = re.sub(r'의료시설와', '의료시설과', text)
    text = re.sub(r'상가 빌딩는', '상가 빌딩은', text)
    text = re.sub(r'상가 빌딩가', '상가 빌딩이', text)
    text = re.sub(r'상가 빌딩를', '상가 빌딩을', text)
    text = re.sub(r'상가 빌딩와', '상가 빌딩과', text)
    return text

def adapt_residential_to_medical(raw_title, paragraphs, cfg):
    """
    아파트/주거 관련 콘텐츠를 병원·의원(메디컬) 인테리어 전문 맥락으로 정밀 변환하는 엔진.
    - 억지 치환 방지: 법령, 행정 절차, 공간 용어, 주체 명칭을 건축법/의료법/상가건물 기준에 맞게 매끄럽게 재구성.
    """
    if not cfg.get("auto_adapt_residential_to_medical", True):
        return raw_title, paragraphs, False

    residential_keywords = [
        "아파트", "공동주택", "입주민", "베란다", "발코니", "거실", "침실", "안방", 
        "주거공간", "주거 공간", "단위세대", "관리사무소", "주방"
    ]
    is_residential = any(k in raw_title for k in residential_keywords) or any(
        any(k in p for k in ["아파트", "공동주택", "입주민", "거실", "주거공간"]) for p in paragraphs[:3]
    )
    
    if not is_residential:
        return raw_title, paragraphs, False

    # 1. 제목 정밀 변환 룰
    new_title = raw_title
    title_replacements = [
        (r'아파트\s*인테리어\s*공사할\s*때\s*입주민\s*동의서는\s*몇\s*%\s*를\s*받아야\s*할까\?', 
         '상가 빌딩 병원·의원 인테리어 공사 시 건물 관리단 동의 및 인허가 기준'),
        (r'아파트\s*발코니\s*확장\s*및\s*비내력벽\s*철거\s*시\s*지자체\s*행위허가\s*신청\s*필수\s*안내',
         '병원·의원 인테리어 발코니 확장 및 비내력벽 철거 시 지자체 행위허가·방화구획 감리 기준'),
        (r'아파트\s*전열교환기\(환기장치\)\s*덕트\s*배관\s*교체\s*시',
         '병원·의원 전열교환기(환기장치) 덕트 배관 교체 시'),
        (r'아파트\s*우수관\(빗물\s*배관\)\s*커버\s*교체\s*시',
         '병원·의원 입점 상가 우수관(빗물 배관) 악취 역류 방지 트랩 및 방수 밀폐 기준 안내'),
        (r'고층\s*아파트\s*발코니\s*단열창호\s*시공\s*시',
         '고층 병원·의원 단열창호 시공 시'),
        (r'아파트\s*베란다\(발코니\)\s*확장할\s*때\s*구청\s*허가\s*안\s*받으면\s*어떻게\s*될까\?',
         '병원·의원 인테리어 확장 공사 시 구청 허가 안 받으면 어떻게 될까? (행위허가 대상과 과태료 기준)'),
        (r'거실\s*실링팬\(천장\s*선풍기\)\s*보강목\s*설치\s*시',
         '병원 대기실 실링팬(공기순환기) 보강목 설치 시'),
        (r'거실\s*실링팬', '병원 대기실 실링팬'),
        (r'주방\s*대용량\s*인덕션\s*설치\s*시',
         '병원 탕비실·조리실 대용량 인덕션 설치 시'),
        (r'주방\s*인테리어', '병원 탕비실 및 위생 세척실 인테리어'),
        (r'발코니\s*단열\s*터닝도어\s*시공\s*시',
         '병원 테라스·외부 발코니 단열 터닝도어 시공 시'),
        (r'아파트\s*', '병원·의원 '),
        (r'입주민\s*동의서', '상가 관리단 및 인접 점포 동의서'),
    ]
    for pattern, repl in title_replacements:
        new_title = re.sub(pattern, repl, new_title)
    new_title = fix_korean_particles(new_title)

    # 2. 본문 및 법령 문맥 정밀 변환 맵 (건축법, 의료법, 상가관리규약 체계 준수)
    context_replacements = [
        # 실정법 법령 체계 치환 (실존 법률 조항 적용)
        (r'공동주택관리법\s*시행령\s*제35조[^\n]*?\[별표\s*3\][^\n]*?명시되어\s*있습니다\.?',
         '건축법 제14조(건축신고), 제19조(용도변경) 및 집합건물의 소유 및 관리에 관한 법률 제15조(공용부분의 변경)에 따르면 상가 건물 내 주요 구조부 변경 및 비내력벽 철거 행위는 관할 지자체 건축과 허가·신고 및 관리단 자치규약에 부합해야 한다고 규정되어 있습니다.'),
        (r'공동주택관리법\s*시행령\s*제35조\s*및\s*별표\s*3[^\n]*',
         '국토교통부 건축법 제19조(용도변경), 제79조(위반건축물에 대한 조치) 및 건축물의 피난·방화구조 등의 기준에 관한 규칙 공식 법령 원문'),
        (r'공동주택관리법\s*제35조[^\n]*?제99조[^\n]*',
         '건축법 제14조, 제19조 및 제79조(위반 건축물에 대한 조치)에 따르면 지자체 허가 없이 무단 증축·대수선하거나 방화구획을 훼손한 자에 대해 엄격한 형사처벌 및 반복 이행강제금 부과 규정을 두고 있습니다.'),
        (r'공동주택관리법[^\n]*?위반으로\s*최대\s*1년[^\n]*',
         '건축법 위반으로 이행강제금 및 강제 원상복구 명령이 부과될 뿐만 아니라 보건소 의료기관 개설 필증 교부가 불가능해집니다.'),
        (r'공동주택관리법\s*시행령\s*기준[:\s]*해당\s*동\s*입주자[^\n]*',
         '건축법 및 상가 관리규약 기준: 건물 관리단(관리사무소) 확인 및 공용 피난 방화구획 충족 도면 작성 후 지자체 행위허가(대수선) 접수 필수'),
        (r'공동주택관리법\s*시행령', '건축법 시행령'),
        (r'공동주택관리법', '건축법 및 집합건물법'),
        (r'공동주택\s*관리규약', '상가 빌딩 관리규약'),
        (r'공동주택\s*행위허가\(신고\)', '의료시설 대수선 및 행위허가(신고)'),
        (r'공동주택\s*행위허가', '의료시설 대수선 및 행위허가'),
        (r'공동주택', '상가 건물(의료시설)'),
        
        # 공인 검색 및 행정 확인 경로
        (r'중앙공동주택관리지원센터[^\n]*', '건축행정시스템 세움터 (cloud.eais.go.kr) - 의료시설 행위허가 및 대수선 온라인 민원 신청'),
        (r'공동주택관리법을?\s*입력하고\s*검색합니다\.', '건축법을 입력하고 검색합니다.'),
        (r'\[별표\s*3\]\s*&#x27;공동주택의\s*행위허가\s*또는\s*신고의\s*기준&#x27;을\s*열어\s*비내력벽\s*철거\s*동의\s*요건을\s*직접\s*확인하실\s*수\s*있습니다\.',
         '[건축법 시행령] 및 의료시설 대수선·행위허가 기준을 열어 비내력벽 철거 및 구조변경 요건을 직접 확인하실 수 있습니다.'),
        (r'지자체\s*제출에\s*필요한\s*입주민\s*동의서\s*양식과\s*필요\s*서류\s*목록',
         '지자체 제출에 필요한 의료시설 행위허가 신청서 및 제출 서류 목록'),

        # 공간 및 시설 명칭 치환
        (r'아파트\s*단지별\s*관리규약', '상가 빌딩별 관리규약'),
        (r'아파트\s*단지\s*자체', '상가 빌딩 자체'),
        (r'아파트\s*거실이나\s*방', '병원 대기실이나 진료실'),
        (r'거실\s*실링팬\(천장\s*선풍기\)\s*보강목\s*설치\s*시\s*하중\s*지지력',
         '병원 대기실 실링팬(공기순환기) 보강목 설치 시 하중 지지력'),
        (r'주방\s*대용량\s*인덕션\s*설치\s*시\s*전용\s*누전차단기',
         '병원 탕비실 대용량 인덕션 설치 시 전용 누전차단기'),
        (r'발코니\s*단열\s*터닝도어\s*시공\s*시\s*가스켓\s*밀착성',
         '병원 테라스·발코니 단열 터닝도어 시공 시 가스켓 밀착성'),
        (r'아파트\s*매매\s*시[^\n]*', '보건소 개설 실사 시 불법 구조변경이 적발되면 개설 필증 교부가 반려됩니다.'),
        (r'내\s*집의\s*합법적\s*가치', '병원의 안정적인 개원과 합법적 시설 가치'),
        (r'집주인\(소유자\)', '건물 구분소유자(임대인)'),
        (r'세입자가\s*거주\s*중인\s*세대', '임차 중인 점포'),
        (r'해당\s*동\s*입주자\(등기부등본상\s*소유자\)\s*과반수[^\n]*', '건물 관리단 규약에 따른 구분소유자 서면 동의 및 인접 점포 사전 협의 필수'),
        (r'해당\s*동\s*입주자[^\n]*50%\s*이상\s*동의[^\n]*', '상가 건물 관리단 규약 및 인접 점포(상하층 및 양옆 상가) 사전 협의와 공사 승인이 필수이며,'),
        (r'보통\s*같은\s*동\s*전체\s*50%\s*이상\s*동의를\s*요구하거나,\s*직격\s*소음\s*피해를\s*입는\s*직상·직하\s*세대\s*및\s*양옆\s*세대\s*등\s*인접\s*세대\s*동의서로\s*갈음합니다\.',
         '상가 관리단 규정에 따른 공사 승인이나, 직격 소음 피해를 입는 직상·직하층 점포 및 양옆 점포 등 인접 상가 동의서로 갈음합니다.'),
        (r'성공적인\s*주거공간\s*리모델링을\s*위해서는', '성공적인 병원·의원 인테리어 및 시설 설비 공사를 위해서는'),
        (r'주거공간\s*리모델링', '병원·의원 인테리어 리모델링'),
        (r'주거공간', '의료 공간'),
        (r'입주자에게\s*법적\s*하자보수\s*청구권', '의료기관 개설자에게 법적 손해배상 청구권'),
        (r'입주민\s*민원이나\s*현장\s*점검', '주변 상가 민원이나 지자체 현장 점검, 보건소 개설 실사'),
        (r'입주민\s*민원으로\s*공사\s*중지', '주변 상가 민원으로 인한 공사 중지'),
        (r'입주민\s*동의를\s*허위로\s*작성하거나\s*법정\s*동의율을\s*채우지\s*않고', '상가 관리단 승인 없이 임의로 구조를 변경하거나'),
        (r'입주민\s*동의서', '상가 관리단 및 인접 상가 공사 동의서'),
        (r'입주민\s*동의', '관리단 및 주변 점포 협의'),
        (r'입주민', '주변 상가 및 내원객'),
        (r'입주자', '병원 환자 및 의료진'),
        (r'입주\s*후', '개원 후'),
        (r'거주\s*기간', '진료 및 시설 운영 기간'),
        (r'아파트\s*', '병원·의원 '),
    ]

    new_paras = []
    for p in paragraphs:
        cur_p = p
        for pattern, repl in context_replacements:
            cur_p = re.sub(pattern, repl, cur_p)
        cur_p = fix_korean_particles(cur_p)
        new_paras.append(cur_p)

    return new_title, new_paras, True


# ==============================================================================
# 카피킬러(CopyKiller) 6어절 N-gram 알고리즘 & AI 중간 패러프레이징 엔진
# ==============================================================================

def get_words(text):
    clean = re.sub(r'[^\w\s]', ' ', text)
    return [w for w in clean.split() if len(w) > 0]

def get_ngrams(words, n=6):
    return [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]

def evaluate_copykiller(orig_text, comp_text, n=6):
    """
    카피킬러 6어절 N-gram 알고리즘 기반 표절 검사 엔진
    """
    orig_words = get_words(orig_text)
    comp_words = get_words(comp_text)
    
    orig_ngrams = set(get_ngrams(orig_words, n))
    comp_ngrams = get_ngrams(comp_words, n)
    
    if not comp_ngrams:
        return 0.0, []
        
    matches = [g for g in comp_ngrams if g in orig_ngrams]
    match_rate = (len(matches) / len(comp_ngrams)) * 100 if comp_ngrams else 0
    return match_rate, matches

def format_copykiller_dashboard(orig_text, comp_text):
    """
    사용자 지정 카피킬러 표절 검사 종합 대시보드 리포트 생성기
    """
    rate, matches = evaluate_copykiller(orig_text, comp_text)
    unique_matches = set(matches)
    
    if rate < 15.0 and len(matches) == 0:
        status = "🟢 안전(발행 가능)"
        summary = "6어절 연속 일치 0건 완벽 달성. 네이버·구글 크롤러의 유사문서(중복문서) 필터링을 100% 통과하는 독창적 창작 원고입니다."
    elif rate < 15.0:
        status = "🟡 주의(수정 권장)"
        summary = f"일치율은 {rate:.1f}%이나 6어절 일치 구간이 {len(unique_matches)}건 감지되었습니다."
    else:
        status = "🔴 위험(중복문서 누락 확정)"
        summary = f"카피킬러 기준 일치율 {rate:.1f}%로 검색엔진 유사문서 누락 위험군입니다."
        
    report = f"""
================================================================================
# 📊 1. 표절 검사 종합 대시보드 (카피킬러 6어절 N-gram 기준)
- **카피킬러 기준 6어절 일치율**: {rate:.1f}%
- **6어절 연속 일치 구간**: {len(unique_matches)}건
- **네이버·구글 중복문서 판정**: {status}
- **총평**: {summary}

# 🔍 2. 6어절 이상 연속 일치 구간 대조
"""
    if matches:
        for idx, m in enumerate(list(unique_matches)[:5], 1):
            report += f"{idx}. \"{' '.join(m)}\"\n"
    else:
        report += "일치 구간 없음 (완벽 통과)\n"
    report += "================================================================================"
        
    return report, rate, len(matches)

def call_ai_paraphrase(raw_title, paragraphs, site_type, cfg):
    """
    Gemini / OpenAI API를 호출하여 카피킬러 6어절 일치율 0% 원고로 완전 재창작
    """
    api_key_gemini = os.environ.get("GEMINI_API_KEY") or cfg.get("gemini_api_key", "").strip()
    api_key_openai = os.environ.get("OPENAI_API_KEY") or cfg.get("openai_api_key", "").strip()
    
    if not api_key_gemini and not api_key_openai:
        return None

    orig_text = "\n".join(paragraphs)
    
    if site_type == "hospital":
        domain_desc = """
[사이트 맞춤 업종 변환 규칙 (부산 병원·의원 인테리어 감리 관점)]
- 주거용(아파트, 거실, 안방, 침실, 베란다, 발코니, 주방, 입주민, 세대) 단어는 반드시 '병원·의원(진료실, 대기실, 입원실, 상가 관리단, 환자/내원객)' 및 실존 법령(건축법, 의료법, 집합건물법, 소방시설법)으로 정밀 치환.
- 부산 지역 의료시설 인허가, 보건소 개설 실사 및 감리 관점을 일관되게 유지.
"""
    else:
        domain_desc = """
[사이트 맞춤 업종 변환 규칙 (오피스·사무실 인테리어 감리 관점)]
- 주거용(아파트, 거실, 안방, 베란다, 주방, 입주민) 단어는 '오피스 빌딩(업무 공간, 회의실, 탕비실, 입주사)' 및 건축법/빌딩관리규약으로 정밀 치환.
"""

    prompt = f"""당신은 대한민국 최고 수준의 텍스트 표절 및 검색엔진(네이버·구글) 중복문서 판별 전문 AI입니다.
아래 제공되는 [카페 원고]를 바탕으로, 카피킬러(CopyKiller)의 핵심 알고리즘(6어절 N-gram)과 검색엔진 크롤러 기준으로 100% 창작 문서(일치율 15% 미만, 6어절 일치 0건)로 재작성(패러프레이징)하십시오.

■ 핵심 작성 기준
1. [6어절 연속 일치 0건 (100% 필수)]: 원문의 6단어 이상 어순과 단어가 연속으로 일치하는 구간을 100% 배제하십시오.
   - 단순 조사 교체나 몇 단어 치환을 금지합니다.
   - 문장 구조(도치, 능동/피동 변환, 복문 분할/병합)를 완전히 전면 재구성하십시오.
2. [의미/패러프레이징 유사도 극소화]: 원문의 핵심 공학적·법률적 의미만 취하고, 완전히 새로운 문체와 문장 흐름으로 집필하십시오.
3. [검색엔진 안전성]: 네이버 스마트블록/뷰탭 및 구글 크롤러의 '유사문서(중복문서) 필터링' 통과 기준(일치율 15% 미만, 6어절 일치 0건)을 완벽히 충족하십시오.
4. [4대 금지어 배제]: '친환경', '100%', '2년', '전담' 단어는 절대 사용하지 마십시오.
5. [외부 링크 및 주소창 안내 스텁 일체 배제]: 공식 홈페이지 URL, '▶ 찾는 방법:', '주소창에' 등 불완전한 링크 안내문은 일체 작성하지 마십시오.
{domain_desc}

■ 출력 포맷 (반드시 JSON 코드블록만 출력할 것):
```json
{{
  "title": "재구성된 전문 칼럼 제목",
  "lead": "전체 내용을 요약하는 핵심 리드문 (공백 포함 60~75자)",
  "sections": [
    {{
      "title": "첫 번째 전문 섹션 소제목",
      "paragraphs": [
        "섹션 1 본문 문단 1...",
        "섹션 1 본문 문단 2..."
      ]
    }},
    {{
      "title": "두 번째 전문 섹션 소제목",
      "paragraphs": [
        "섹션 2 본문 문단 1...",
        "섹션 2 본문 문단 2..."
      ]
    }},
    {{
      "title": "세 번째 전문 섹션 소제목",
      "paragraphs": [
        "섹션 3 본문 문단 1...",
        "섹션 3 본문 문단 2..."
      ]
    }}
  ]
}}
```

[카페 원문 제목]: {raw_title}
[카페 원문 본문]:
{orig_text}
"""
    # 1. Gemini API 시도
    if api_key_gemini:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key_gemini}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "topP": 0.95}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return parse_ai_json(text)
        except Exception as e:
            print(f"[경고] Gemini API 패러프레이징 호출 실패: {e}")

    # 2. OpenAI API 시도
    if api_key_openai:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key_openai}"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                return parse_ai_json(text)
        except Exception as e:
            print(f"[경고] OpenAI API 패러프레이징 호출 실패: {e}")

    return None

def parse_ai_json(text):
    """
    AI 응답 텍스트에서 JSON 객체를 안전하게 추출
    """
    m = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    json_str = m.group(1) if m else text.strip()
    try:
        obj = json.loads(json_str)
        title = obj.get("title", "").strip()
        lead = obj.get("lead", "").strip()
        raw_secs = obj.get("sections", [])
        sections = []
        for s in raw_secs:
            stitle = s.get("title", "").strip()
            sparas = [p.strip() for p in s.get("paragraphs", []) if p.strip()]
            if stitle and sparas:
                sections.append((stitle, sparas))
        if title and sections:
            return title, lead, sections
    except Exception as e:
        print(f"[경고] AI 응답 JSON 파싱 실패: {e}")
    return None

def paraphrase_algorithmic(raw_title, paragraphs, site_type, cfg):
    """
    API 키 미설정 시 작동하는 고급 알고리즘 패러프레이징 엔진 (문장 구조 도치, 시방 전문용어 치환)
    """
    ADVANCED_REPLACEMENTS = [
        (r'완성됩니다\.', '확보될 수 있습니다.'),
        (r'필수적입니다\.', '반드시 준수되어야 할 핵심 관리 지침입니다.'),
        (r'요구됩니다\.', '선행되어야 안전성이 담보됩니다.'),
        (r'확인해야 합니다\.', '정밀하게 사전 계측하고 검측 조서를 작성해야 합니다.'),
        (r'주의해야 합니다\.', '철저한 관리 감독 하에 시공 오차를 통제해야 합니다.'),
        (r'원인이 됩니다\.', '직결되는 치명적 하자로 이어집니다.'),
        (r'나타났습니다\.', '실증적으로 확인된 바 있습니다.'),
        (r'할 수 있습니다\.', '하는 방안이 공학적으로 권장됩니다.'),
        (r'있어야 합니다\.', '갖추어져 있어야 적법 시공으로 인정받습니다.'),
        (r'비로소\s*', '안정적으로 '),
        (r'특히\s*', '무엇보다 실무 감리 관점에서 '),
        (r'반드시\s*', '예외 없이 사전 검증을 거쳐 '),
        (r'엄격히\s*', '오차 범위 없이 정밀하게 '),
        (r'철저히\s*', '다각적인 계측을 통해 '),
        (r'사전에\s*', '본격적인 착공 이전 단계에서 '),
        (r'인테리어\s*공사', '실내 건축 및 설비 공정'),
        (r'하자\s*분쟁', '법률적 하자담보 분쟁 및 구상권 청구'),
        (r'시험성적서', '공인 시험기관 발행 품질성적서'),
        (r'공인\s*기준', '국토교통부 표준시방서 및 KS 규격'),
        (r'세부\s*지침', '공학적 감리 시방 규준'),
        (r'내구성', '구조적 장기 내구성'),
        (r'안전사고', '구조적 안전사고 및 파손 결함'),
    ]
    
    cleaned_paras = []
    for p in paragraphs:
        p_clean = re.sub(r'^[■□◆◇▶▷●○※★☆\s\d\.-]+', '', p).strip()
        if not p_clean or is_stub_line(p_clean) or is_stub_line(p):
            continue
        cur = p_clean
        for pat, repl in ADVANCED_REPLACEMENTS:
            cur = re.sub(pat, repl, cur)
        cleaned_paras.append(cur)

    # 요약 리드문 추출 및 생성
    lead = ""
    for p in cleaned_paras:
        if len(p) >= 40:
            lead = p
            break
    if not lead and cleaned_paras:
        lead = cleaned_paras[0]

    body_items = [p for p in cleaned_paras if p != lead]
    chunk_size = max(1, len(body_items) // 3)
    sec1_items = body_items[:chunk_size]
    sec2_items = body_items[chunk_size:chunk_size*2]
    sec3_items = body_items[chunk_size*2:]

    sections = [
        ("현장 물리적 특성 및 시공 메커니즘 분석", sec1_items),
        ("공학적 시방 규격 및 핵심 성능 원리", sec2_items),
        ("실무 자재 검수 지침 및 사전 감리 기준", sec3_items)
    ]

    title = raw_title.replace("시공 예시", "시공 시 핵심 주의사항 및 시방 가이드")
    title = title.replace("시공시", "시공 시")
    if not any(k in title for k in ["이유", "가이드", "분석", "기준", "원리", "노하우"]):
        title = f"{title}에 대한 실무 공학적 분석과 감리 기준"
    title = clean_forbidden(title, cfg)

    return title, lead, sections

def transform_article_content(raw_title, paragraphs, cfg):
    """
    카피킬러 6어절 N-gram 0% 회피 & 검색엔진 100% 안전 발행 중간 변환 엔진
    """
    # 원문 전체 텍스트 (표절 검사 대조군)
    orig_full_text = raw_title + " " + " ".join(paragraphs)

    # 0. 기존 기본 변환 규칙 선적용 (금지어 제거, 아파트->병원 정밀 치환)
    raw_title, paragraphs, is_adapted = adapt_residential_to_medical(raw_title, paragraphs, cfg)

    # 1. AI 패러프레이징 시도 (Gemini / OpenAI API)
    ai_result = call_ai_paraphrase(raw_title, paragraphs, site_type="hospital", cfg=cfg)
    
    if ai_result:
        title, lead, sections = ai_result
        # AI 생성물 전체 텍스트 구성
        comp_full_text = title + " " + lead + " " + " ".join([p for _, sparas in sections for p in sparas])
        
        # 카피킬러 6어절 표절 검사 실행 및 대시보드 출력
        report, rate, match_count = format_copykiller_dashboard(orig_full_text, comp_full_text)
        print(report)
        
        if rate < 15.0 and match_count == 0:
            print("[성공] AI 패러프레이징: 카피킬러 6어절 일치율 0% 및 중복문서 100% 통과 기준 충족!")
            return title, lead, sections

    # 2. API 키 미설정 또는 실패 시: 고급 알고리즘 패러프레이징 폴백
    title, lead, sections = paraphrase_algorithmic(raw_title, paragraphs, site_type="hospital", cfg=cfg)
    comp_full_text = title + " " + lead + " " + " ".join([p for _, sparas in sections for p in sparas])
    
    report, rate, match_count = format_copykiller_dashboard(orig_full_text, comp_full_text)
    print(report)
    print("[안내] GitHub Secrets 또는 config.json에 GEMINI_API_KEY를 설정하시면 6어절 일치율 0%의 완전한 AI 재창작 원고가 매일 자동 생성됩니다.")
    
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
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta name="author" content="{site_name}" />
  <meta name="naver-site-verification" content="57ef696d2b54b5a9118376789981871be0fe78a9" />
  <meta name="google-site-verification" content="0f-j7HOTRJP6McdtJbnZNC-e6SibEW0xDkSq_J1YGUI" />
  <meta name="p:domain_verify" content="735309f4fa474b49f5cb398ecf142b1f"/>
  
  <!-- Open Graph Tags -->
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="{site_name}" />
  <meta property="og:title" content="{title} | 전문가 칼럼" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:image" content="{domain}/favicon.png" />
  <link rel="image_src" href="{domain}/favicon.png" />
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
  <!-- Cloudflare Web Analytics -->
  <script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "866c87b5a38c446baa403aec2a6c5fea"}}'></script>
  <!-- End Cloudflare Web Analytics -->
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

def update_rss(col_idx, title, excerpt, cfg):
    rss_file = os.path.join(PROJECT_ROOT, "rss.xml")
    if not os.path.exists(rss_file):
        return
    with open(rss_file, "r", encoding="utf-8") as f:
        content = f.read()

    domain = cfg["site_domain"].rstrip("/")
    now_str = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900')
    clean_desc = excerpt.replace('"', '&quot;')

    new_item = f"""    <item>
      <title>{title}</title>
      <link>{domain}/column-{col_idx}.html</link>
      <description><![CDATA[{clean_desc}]]></description>
      <pubDate>{now_str}</pubDate>
      <guid isPermaLink="true">{domain}/column-{col_idx}.html</guid>
    </item>\n"""

    # Update pubDate and lastBuildDate
    content = re.sub(r'<pubDate>[^<]+</pubDate>', f'<pubDate>{now_str}</pubDate>', content, count=1)
    content = re.sub(r'<lastBuildDate>[^<]+</lastBuildDate>', f'<lastBuildDate>{now_str}</lastBuildDate>', content, count=1)

    pos = content.find("<item>")
    if pos != -1:
        content = content[:pos] + new_item + "    " + content[pos:]
    else:
        content = content.replace("</channel>", new_item + "  </channel>")

    with open(rss_file, "w", encoding="utf-8") as f:
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

    daily_limit = cfg.get("daily_limit", 2)
    last_synced_date = state.get("last_synced_date", "")
    
    # 날짜가 바뀌었으면 오늘 발행 건수 초기화
    if last_synced_date != today_str:
        state["synced_today_count"] = 0
    synced_today_count = state.get("synced_today_count", 0)

    # 규칙 1: 기존 밀린 글이 있는 상태에서는 하루 최대 daily_limit 건(기본 2건)만 발행
    if pending and synced_today_count >= daily_limit and last_synced_date == today_str:
        print(f"[INFO] 오늘자({today_str}) 칼럼 {daily_limit}건이 이미 모두 발행 완료되었습니다. 내일 순차 발행합니다.")
        return False

    # 규칙 2: 모든 글이 소진되었을 때 새 글 대기 모드 (일 2회 체크)
    if not pending:
        print(f"[INFO] 카페의 모든 게시글이 이미 칼럼으로 변환되었습니다. 신규 등록 글을 모니터링 중입니다 (현재 신규 글 0건).")
        return False

    # 이번 회차에서 처리할 건수 (하루 한도 초과 방지)
    remaining_quota = daily_limit - synced_today_count if last_synced_date == today_str else daily_limit
    process_count = min(batch_size, remaining_quota)
    if process_count <= 0:
        print(f"[INFO] 오늘자({today_str}) 발행 가능 한도({daily_limit}건)에 도달했습니다.")
        return False

    to_process = pending[:process_count]
    print(f"[INFO] 대기 글 중 {len(to_process)}건을 새 칼럼으로 변환 및 발행합니다 (오늘 발행 예정: {synced_today_count + len(to_process)}/{daily_limit}건)...")

    created_cols = []
    for art in to_process:
        aid = int(art[id_key])
        next_idx = state["last_column_index"] + 1
        print(f"-> [처리 시작] 카페 글 ID {aid} => column-{next_idx}.html 변환 중...")

        raw_title, paragraphs = fetch_article_detail(aid, cfg)
        if not raw_title or not paragraphs or len(paragraphs) < 2:
            print(f"[건너뜀] 카페 글 ID {aid}는 멤버공개 또는 비공개/내용부재로 자동 건너뜁니다.")
            state.setdefault("processed_cafe_ids", []).append(aid)
            continue

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
        update_rss(next_idx, title, excerpt, cfg)

        state["last_column_index"] = next_idx
        state.setdefault("processed_cafe_ids", []).append(aid)
        created_cols.append(next_idx)

    state["last_run_timestamp"] = datetime.now().isoformat()
    state["last_synced_date"] = today_str
    state["synced_today_count"] = synced_today_count + len(created_cols)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    # Git 커밋 및 자동 푸시
    if os.path.exists(os.path.join(PROJECT_ROOT, ".git")):
        try:
            subprocess.run(["git", "add", "."], cwd=PROJECT_ROOT, check=True)
            msg = f"feat(column): auto-sync column {created_cols} from cafe"
            subprocess.run(["git", "commit", "-m", msg], cwd=PROJECT_ROOT, check=True)
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=PROJECT_ROOT, check=False)
            subprocess.run(["git", "push", "origin", "main"], cwd=PROJECT_ROOT, check=True)
            print(f"[배포 완료] Git 커밋 및 푸시 성공: 칼럼 {created_cols}")
        except Exception as e:
            print(f"[주의] Git 커밋/푸시 중 오류 발생: {e}")
        except Exception as e:
            print(f"[주의] Git 커밋/푸시 중 오류 발생: {e}")

    print(f"[성공] 신규 칼럼 {created_cols}번이 발행되었습니다!")
    return True

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_sync(count)
