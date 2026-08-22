import os
import sys
import json
import re
import shutil
from datetime import datetime, timezone

# ==============================================================================
# HOMPAGE_KEYWORD 23대 슈퍼 허브(Super Hub) 아키텍처 마스터 빌더 (busaninterior.kr)
# - 구글 1위 조기 탈환 & AI Overviews / LLM 단독 인용 구조
# - 13대 주요 지역 전용 종합 허브 + 10대 진료과목 전용 전문 허브 (총 27개 정예 URL)
# - 네이버 톡톡 연동 + Schema 3종(LocalBusiness + BreadcrumbList + FAQPage)
# ==============================================================================

SITE_URL = "https://busaninterior.kr"
BRAND_NAME = "부산 병원 인테리어 전문 업체"
RECOMMENDED_PARTNER = "인디컴퍼니"
PARTNER_URL = "https://inde.co.kr"
NAVER_TALKTALK_URL = "https://talk.naver.com/ct/wc2c1f?frm=home"
OUTPUT_DIR = os.path.dirname(__file__)

# 13대 핵심 지역 데이터 (랜드마크, 서브타이틀, 특화 설명)
REGIONAL_HUBS = {
    "daegu": {
        "slug": "daegu.html",
        "region_name": "대구",
        "title": "대구 병원 인테리어 전문 업체 | 수성구·범어동·동성로 메디컬 공간 디자인",
        "desc": "대구 지역 병원·의원 인테리어 및 리모델링 전문! 수성구, 범어동, 만촌동, 동성로 등 대구 전 지역 1:1 무료 방문 실측 및 3D 도면 비교 견적 지원.",
        "badge": "대구 전 지역 메디컬 공간 특화",
        "h1": "성공적인 대구 개원의 시작,<br /><span class=\"text-primary\">대구 병원 인테리어 전문 업체</span>",
        "landmarks": ["수성구", "범어동", "만촌동", "동성로", "삼덕동", "반월당", "상인동", "칠곡", "두산동"],
        "highlight_text": "대구 메디컬 스트리트(수성구 범어네거리, 중구 동성로·삼덕동 일대)의 최신 개원 트렌드와 진료과목별 의료법 규격을 완벽하게 충족하는 맞춤형 공간 솔루션을 제공합니다.",
        "specialties_summary": "내과 호흡기 분리 대기실, 치과 체어 배관 인프라, 피부과 1인 관리실 조도 설계, 정형외과 C-arm 납차폐 등 대구 지역 병의원에 최적화된 시공을 약속합니다."
    },
    "changwon": {
        "slug": "changwon.html",
        "region_name": "창원",
        "title": "창원 병원 인테리어 전문 업체 | 상남동·마산·진해 메디컬 공간 디자인",
        "desc": "창원 병원·의원 인테리어 및 리모델링 전문! 상남동, 중앙동, 마산, 진해 등 창원 전 지역 1:1 무료 현장 실측 및 3D 설계 견적 지원.",
        "badge": "창원·마산·진해 메디컬 공간 특화",
        "h1": "성공적인 창원 개원의 시작,<br /><span class=\"text-primary\">창원 병원 인테리어 전문 업체</span>",
        "landmarks": ["상남동", "중앙동", "용호동", "마산합포구", "마산회원구", "진해구", "팔용동"],
        "highlight_text": "창원 최대 상권인 성산구 상남동 메디컬 빌딩 및 마산·진해 지역 신규 개원과 리모델링에 최적화된 프리미엄 공간 설계를 지원합니다.",
        "specialties_summary": "의료법 필수 면적 기준과 소방 대피 규정을 선제적으로 반영하여 공기 지연 없는 완벽한 준공을 보장합니다."
    },
    "ulsan": {
        "slug": "ulsan.html",
        "region_name": "울산",
        "title": "울산 병원 인테리어 전문 업체 | 삼산동·달동·옥동 메디컬 공간 디자인",
        "desc": "울산 병원·의원 인테리어 및 리모델링 전문! 남구 삼산동, 달동, 옥동, 무거동, 우정혁신도시 등 울산 전 지역 3D 도면 무료 견적 상담.",
        "badge": "울산 전 지역 메디컬 공간 특화",
        "h1": "성공적인 울산 개원의 시작,<br /><span class=\"text-primary\">울산 병원 인테리어 전문 업체</span>",
        "landmarks": ["삼산동", "달동", "성남동", "옥동", "무거동", "우정혁신도시", "남구 메디컬존"],
        "highlight_text": "울산 남구 삼산동·달동 메디컬 중심지의 프리미엄 병의원 인테리어부터 옥동·무거동 신규 클리닉까지 맞춤형 럭셔리 공간을 구현합니다.",
        "specialties_summary": "환자 동선과 의료진 서브 동선의 정밀한 분리로 진료 효율을 극대화하고 호텔 라운지급 대기실을 조성합니다."
    },
    "haeundae": {
        "slug": "haeundae.html",
        "region_name": "해운대",
        "title": "해운대 병원 인테리어 전문 업체 | 우동·중동·마린시티·좌동 메디컬 디자인",
        "desc": "해운대 병원·의원 인테리어 및 리모델링 전문! 우동, 중동, 마린시티, 좌동 신시가지, 엘시티 등 해운대구 전 지역 3D 무료 설계 견적.",
        "badge": "해운대·마린시티 하이엔드 메디컬 특화",
        "h1": "품격 있는 해운대 개원의 시작,<br /><span class=\"text-primary\">해운대 병원 인테리어 전문 업체</span>",
        "landmarks": ["우동", "중동", "좌동", "송정동", "마린시티", "센텀시티", "엘시티", "장산역", "해운대역"],
        "highlight_text": "해운대 마린시티와 중동·우동 상권에 어울리는 최고급 천연 대리석 및 친환경 도료 기반의 하이엔드 메디컬 라운지를 디자인합니다.",
        "specialties_summary": "피부과, 성형외과, 안과, 치과 등 프리미엄 진료과목에 걸맞은 호텔식 인테리어와 정밀 설비 인프라를 완벽 시공합니다."
    },
    "centum": {
        "slug": "centum.html",
        "region_name": "센텀",
        "title": "센텀 병원 인테리어 전문 업체 | 센텀시티·우동 메디컬 타운 디자인",
        "desc": "센텀시티 병원·의원 인테리어 전문! 센텀중앙로, 센텀동로, 벡스코 인근 메디컬 빌딩 특화 설계 및 3D 도면 무료 견적 상담.",
        "badge": "센텀시티 메디컬 타운 특화",
        "h1": "성공적인 센텀 개원의 시작,<br /><span class=\"text-primary\">센텀 병원 인테리어 전문 업체</span>",
        "landmarks": ["센텀중앙로", "센텀동로", "센텀시티역", "벡스코 인근", "우동 센텀 메디컬존"],
        "highlight_text": "부산 최고 수준의 병의원이 밀집한 센텀시티 메디컬 타운의 고품격 브랜드 아이덴티티를 확립하는 차별화된 디자인을 제공합니다.",
        "specialties_summary": "무균 수술실 공조 시스템, 대형 검진센터 원스톱 동선 기획 등 고난도 메디컬 엔지니어링을 책임 시공합니다."
    },
    "myeongji": {
        "slug": "myeongji.html",
        "region_name": "명지",
        "title": "명지 병원 인테리어 전문 업체 | 명지국제신도시·오션시티 메디컬 디자인",
        "desc": "명지국제신도시 병원·의원 인테리어 전문! 강서구 명지오션시티, 신호동 등 신도시 상권에 최적화된 소아과, 이비인후과, 내과 맞춤 설계.",
        "badge": "명지국제신도시 메디컬 특화",
        "h1": "성공적인 명지 개원의 시작,<br /><span class=\"text-primary\">명지 병원 인테리어 전문 업체</span>",
        "landmarks": ["명지국제신도시", "명지오션시티", "신호동", "강서구", "명지 메디컬타운"],
        "highlight_text": "젊은 가족 단위 환자가 많은 명지국제신도시 특성에 맞춰 감염 예방 호흡기 분리 동선과 안심 키즈존을 결합한 스마트 클리닉을 설계합니다.",
        "specialties_summary": "소아청소년과, 이비인후과, 치과, 내과, 정형외과 등 가족 중심 진료과목에 최적화된 안전하고 쾌적한 인테리어를 구현합니다."
    },
    "gimhae": {
        "slug": "gimhae.html",
        "region_name": "김해",
        "title": "김해 병원 인테리어 전문 업체 | 내외동·장유·율하 메디컬 공간 디자인",
        "desc": "김해 병원·의원 인테리어 및 리모델링 전문! 내외동, 삼계동, 율하신도시, 장유 등 김해 전 지역 1:1 방문 실측 및 3D 도면 무료 견적.",
        "badge": "김해·율하·장유 메디컬 특화",
        "h1": "성공적인 김해 개원의 시작,<br /><span class=\"text-primary\">김해 병원 인테리어 전문 업체</span>",
        "landmarks": ["내외동", "삼계동", "부원동", "율하", "장유", "진영", "구산동"],
        "highlight_text": "김해 내외동 중심 상권과 율하·장유 신도시의 신규 개원 병의원을 위한 합리적인 평당 공사비와 정밀 설비 시공을 지원합니다.",
        "specialties_summary": "실내건축공사업 면허 기반의 책임 시공과 하자보증증권 발행으로 안전한 개원을 뒷받침합니다."
    },
    "gumi": {
        "slug": "gumi.html",
        "region_name": "구미",
        "title": "구미 병원 인테리어 전문 업체 | 원평동·인동·옥계 메디컬 공간 디자인",
        "desc": "구미 병원·의원 인테리어 및 리모델링 전문! 원평동, 인동, 옥계동, 송정동, 형곡동 등 구미 전 지역 직영 감리 및 3D 도면 무료 견적.",
        "badge": "구미 전 지역 메디컬 공간 특화",
        "h1": "성공적인 구미 개원의 시작,<br /><span class=\"text-primary\">구미 병원 인테리어 전문 업체</span>",
        "landmarks": ["원평동", "인동", "옥계", "송정동", "형곡동", "사곡동", "진평동"],
        "highlight_text": "구미 원평동 및 옥계·인동 핵심 메디컬 상권의 병원 개원을 위해 직영 현장 감리팀이 상주하며 완벽한 공기를 준수합니다.",
        "specialties_summary": "진료과목별 특수 전기 승압, 엑스레이실 납차폐, 위생 급배수 설비를 철저한 기준에 맞춰 시공합니다."
    },
    "geoje": {
        "slug": "geoje.html",
        "region_name": "거제",
        "title": "거제 병원 인테리어 전문 업체 | 고현동·옥포동·아주동 메디컬 디자인",
        "desc": "거제 병원·의원 인테리어 및 리모델링 전문! 고현동, 옥포동, 장평동, 아주동 등 거제 전 지역 현장 실측 및 3D 도면 비교 견적 상담.",
        "badge": "거제 전 지역 메디컬 공간 특화",
        "h1": "성공적인 거제 개원의 시작,<br /><span class=\"text-primary\">거제 병원 인테리어 전문 업체</span>",
        "landmarks": ["고현동", "옥포동", "장평동", "아주동", "상문동", "수양동"],
        "highlight_text": "거제 고현동 메디컬 중심지 및 주요 주거 권역의 병의원 인테리어를 위해 내구성 높은 마감재와 신속한 AS 전담팀을 운영합니다.",
        "specialties_summary": "도서 및 해안 지역 특성을 고려한 방습·방염 자재 시공과 체계적인 감리로 만족도 높은 공간을 완성합니다."
    },
    "miryang": {
        "slug": "miryang.html",
        "region_name": "밀양",
        "title": "밀양 병원 인테리어 전문 업체 | 삼문동·내이동 메디컬 공간 디자인",
        "desc": "밀양 병원·의원 인테리어 및 리모델링 전문! 삼문동, 내이동, 가곡동 등 밀양 전 지역 맞춤형 메디컬 공간 기획 및 3D 무료 도면 지원.",
        "badge": "밀양 전 지역 메디컬 공간 특화",
        "h1": "성공적인 밀양 개원의 시작,<br /><span class=\"text-primary\">밀양 병원 인테리어 전문 업체</span>",
        "landmarks": ["삼문동", "내이동", "가곡동", "교동", "밀양역 인근"],
        "highlight_text": "밀양 삼문동 및 내이동 메디컬 상권의 내과, 정형외과, 한의원, 치과 등 진료과목별 맞춤 리모델링을 신속하게 지원합니다.",
        "specialties_summary": "환자 중심의 무단차 배리어프리 설계와 안락한 조도 디자인으로 지역 주민들의 신뢰를 얻는 병원을 만듭니다."
    },
    "gijang": {
        "slug": "gijang.html",
        "region_name": "기장",
        "title": "기장 병원 인테리어 전문 업체 | 정관신도시·일광신도시 메디컬 디자인",
        "desc": "기장 병원·의원 인테리어 전문! 정관신도시, 일광신도시, 오시리아 등 기장군 전 지역 신규 클리닉 인테리어 및 3D 도면 무료 상담.",
        "badge": "기장·정관·일광 신도시 메디컬 특화",
        "h1": "성공적인 기장 개원의 시작,<br /><span class=\"text-primary\">기장 병원 인테리어 전문 업체</span>",
        "landmarks": ["정관신도시", "일광신도시", "기장읍", "오시리아", "교리"],
        "highlight_text": "정관신도시와 일광신도시의 대형 상가 메디컬 빌딩에 입점하는 병의원을 위한 원스톱 공간 조닝 및 인테리어 솔루션을 제공합니다.",
        "specialties_summary": "소아과, 이비인후과, 치과, 피부과 등 신도시 맞춤형 스마트 동선과 감성적인 대기실 라운지를 연출합니다."
    },
    "gyeongnam": {
        "slug": "gyeongnam.html",
        "region_name": "경남",
        "title": "경남 병원 인테리어 전문 업체 | 양산·진주·통영·사천 메디컬 디자인",
        "desc": "경상남도 병원·의원 인테리어 및 리모델링 전문! 양산 물금, 진주 충무공동, 통영, 사천 등 경남 전역 1:1 방문 실측 및 3D 도면 지원.",
        "badge": "경남 전 지역 메디컬 공간 특화",
        "h1": "성공적인 경남 개원의 시작,<br /><span class=\"text-primary\">경남 병원 인테리어 전문 업체</span>",
        "landmarks": ["양산 물금", "진주 혁신도시", "통영", "사천", "김해", "창원", "거제"],
        "highlight_text": "양산 신도시, 진주 혁신도시를 비롯한 경상남도 전역의 병원·요양병원·의원 인테리어를 직영 시스템으로 책임 시공합니다.",
        "specialties_summary": "의료 시설 법정 규격 충족과 하자이행보증증권 공식 발급으로 믿을 수 있는 병원 시공 파트너가 되어 드립니다."
    },
    "busan": {
        "slug": "busan.html",
        "region_name": "부산",
        "title": "부산 병원 인테리어 전문 업체 | 서면·남포동·동래·연산 메디컬 디자인",
        "desc": "부산 전 지역 병원·의원 인테리어 및 리모델링 전문! 서면 메디컬 스트리트, 동래, 연산동, 남포동, 덕천 등 3D 무료 도면 비교 견적.",
        "badge": "부산 전 지역 메디컬 공간 특화",
        "h1": "성공적인 부산 개원의 시작,<br /><span class=\"text-primary\">부산 병원 인테리어 전문 업체</span>",
        "landmarks": ["서면 메디컬스트리트", "해운대", "센텀시티", "마린시티", "연산교차로", "동래역", "덕천", "남포동", "사상"],
        "highlight_text": "부산 전역(서면, 해운대, 센텀, 동래, 연산 등)의 메디컬 중심가에서 수많은 병의원 완공 실적을 쌓아온 검증된 면허 전문 업체입니다.",
        "specialties_summary": "진료과목별 최적 동선 기획과 최고급 프리미엄 마감재 적용으로 브랜드 가치를 극대화합니다."
    }
}

# 10대 진료과목 데이터 (전문 설비, 규격, 핵심 체크포인트)
SPECIALTY_HUBS = {
    "dental": {
        "slug": "dental.html",
        "specialty_name": "치과",
        "title": "치과 인테리어 전문 업체 | 체어 배관 인프라 & CT 납차폐 정밀 설계",
        "desc": "치과 인테리어 및 리모델링 전문! 유닛체어 전용 급배수/컴프레셔 설비 라인, 파노라마 CT실 방사선 차폐 규격, 중앙 멸균 소독실 맞춤 설계.",
        "badge": "치과 체어 설비 & 멸균 동선 특화",
        "h1": "성공적인 치과 개원의 시작,<br /><span class=\"text-primary\">치과 인테리어 전문 설계 & 시공</span>",
        "area_range": "35평 ~ 60평 (유닛체어 4~6대 기준)",
        "infra_highlight": "체어 전용 급배수·컴프레셔 배관, CT실 납차폐",
        "duration": "약 4주 ~ 5주",
        "spec_text": "체어 전용 급배수 및 기계실 배관 인프라, 파노라마/CT실 방사선 납차폐 벽체, 중앙 멸균 소독실의 위생적인 일방향 동선",
        "guide_title": "치과 개원 공간 설계 핵심 체크포인트",
        "guide_desc": "치과는 타 진료과목 대비 기계실(컴프레셔, 석션)과 체어 하부 배관 공사가 가장 핵심입니다. 진료 중 배수 역류나 공기압 저하가 발생하지 않도록 완벽한 구배와 전용 배관 슬리브를 사전 시공합니다."
    },
    "derma": {
        "slug": "derma.html",
        "specialty_name": "피부과",
        "title": "피부과 인테리어 전문 업체 | VIP 1인 관리실 조도 & 레이저 공조 설계",
        "desc": "피부과·에스테틱 인테리어 전문! VIP 1인 관리실 아늑한 간접 조도 설계, 고출력 레이저실 전력 승압 및 환기 공조, 프라이빗 파우더룸 기획.",
        "badge": "피부과 럭셔리 라운지 & 레이저 공조 특화",
        "h1": "품격 있는 피부과 개원의 시작,<br /><span class=\"text-primary\">피부과 프리미엄 인테리어 디자인</span>",
        "area_range": "50평 ~ 100평 (관리실 4~8실 기준)",
        "infra_highlight": "VIP 1인실 조도 제어, 레이저실 전력 승압",
        "duration": "약 4주 ~ 6주",
        "spec_text": "VIP 1인 관리실의 아늑한 간접 조도 설계, 프라이빗 파우더룸, 고출력 레이저 장비 전력 승압 및 환기 공조",
        "guide_title": "피부과 개원 공간 설계 핵심 체크포인트",
        "guide_desc": "피부과는 환자의 프라이버시 보호와 심리적 안락함이 최우선입니다. 눈부심을 억제한 간접 광원 설계와 고출력 레이저 장비 발열을 신속히 해소하는 전용 공조 배기 라인을 필수 시공합니다."
    },
    "plastic": {
        "slug": "plastic.html",
        "specialty_name": "성형외과",
        "title": "성형외과 인테리어 전문 업체 | 무균 양압 수술실 & 프라이빗 회복실",
        "desc": "성형외과 인테리어 전문! 의료법 기준 무균 수술실 양압 공조 시스템(HEPA 필터), 프라이빗 1인 회복실, 상담실-원장실 최단 진료 동선.",
        "badge": "무균 양압 수술실 & 회복실 특화",
        "h1": "성공적인 성형외과 개원의 시작,<br /><span class=\"text-primary\">성형외과 인테리어 전문 설계 & 시공</span>",
        "area_range": "60평 ~ 120평 (무균수술실 포함)",
        "infra_highlight": "무균 수술실 양압 공조(HEPA 필터), 1인 회복실",
        "duration": "약 5주 ~ 7주",
        "spec_text": "무균 수술실 양압 공조 시스템, 수술 후 프라이빗 회복실, 상담실과 원장실 간 최단 진료 동선",
        "guide_title": "성형외과 개원 공간 설계 핵심 체크포인트",
        "guide_desc": "의료법 기준에 부합하는 무균 수술실 클린룸 공조(HEPA 필터 0.3마이크론 포집, 차압 제어)와 수술 환자가 대기실에 노출되지 않고 퇴원할 수 있는 프라이빗 서브 동선을 완벽히 구획합니다."
    },
    "internal": {
        "slug": "internal.html",
        "specialty_name": "내과·검진센터",
        "title": "내과·건강검진센터 인테리어 | 호흡기 분리 동선 & 내시경 세척실",
        "desc": "내과 및 건강검진센터 인테리어 전문! 감염 방지 호흡기 분리 대기실, 내시경실 세척·소독 라인, 접수-기초검사-채혈-내시경 원스톱 검진 동선.",
        "badge": "내과 호흡기 분리 & 원스톱 검진 동선 특화",
        "h1": "성공적인 내과 개원의 시작,<br /><span class=\"text-primary\">내과·건강검진센터 인테리어 전문</span>",
        "area_range": "45평 ~ 150평 (진료실 및 검진존 기준)",
        "infra_highlight": "호흡기 분리 대기실, 내시경 세척실, 채혈실 동선",
        "duration": "약 4주 ~ 7주",
        "spec_text": "호흡기 환자 분리 대기 공간, 내시경실 세척·소독 설비 라인, 건강검진 기초검사 및 채혈실 연계 동선",
        "guide_title": "내과·검진센터 공간 설계 핵심 체크포인트",
        "guide_desc": "일반 환자와 호흡기 환자의 감염 예방 교차 방지 동선 및 내시경 검사실과 세척·소독실 간의 누수 없는 방수 급배수 배관 시공이 안정적인 병원 운영의 핵심입니다."
    },
    "ortho": {
        "slug": "ortho.html",
        "specialty_name": "정형외과·도수치료",
        "title": "정형외과·도수치료 인테리어 | C-arm 차폐 & 물리치료실 공간 조닝",
        "desc": "정형외과 및 도수치료센터 인테리어 전문! C-arm 방사선 차폐 벽체 공사, 물리치료실 베드 간격 최적화, 도수치료실 특수 이중 방음벽 시공.",
        "badge": "C-arm 차폐 & 도수치료실 방음 특화",
        "h1": "성공적인 정형외과 개원의 시작,<br /><span class=\"text-primary\">정형외과·도수치료 인테리어 전문</span>",
        "area_range": "60평 ~ 150평 (물리·도수치료실 포함)",
        "infra_highlight": "C-arm 납차폐 벽체, 도수치료실 이중 차음 방음",
        "duration": "약 5주 ~ 7주",
        "spec_text": "C-arm 방사선 차폐 벽체 공사, 물리치료실 베드 간격 최적화, 도수치료실 특수 방음 및 환자 탈의실 동선",
        "guide_title": "정형외과·도수치료 공간 설계 핵심 체크포인트",
        "guide_desc": "방사선실 납판 차폐와 함께 도수치료실의 환자 비명 및 기구 소음이 대기실로 전달되지 않도록 차음 석고와 흡음재를 적용한 특수 이중 벽체를 시공합니다."
    },
    "eye": {
        "slug": "eye.html",
        "specialty_name": "안과",
        "title": "안과 인테리어 전문 업체 | 정밀 암실 검사실 & 라식 수술실 공조",
        "desc": "안과 인테리어 전문! 정밀 암실 굴절 검사실 조도 제어 시스템, 라식·백내장 무균 수술실 공조 인프라, 처방 및 수납 라운지 동선 최적화.",
        "badge": "안과 암실 검사실 & 백내장 수술실 특화",
        "h1": "성공적인 안과 개원의 시작,<br /><span class=\"text-primary\">안과 인테리어 전문 설계 & 시공</span>",
        "area_range": "50평 ~ 120평 (검사실 및 수술실 포함)",
        "infra_highlight": "암실 굴절 검사실 조도 제어, 수술실 공조 설비",
        "duration": "약 4주 ~ 6주",
        "spec_text": "정밀 암실 굴절 검사실 조도 제어, 무균 수술실 공조 설비, 수납 및 안경 처방 라운지 동선",
        "guide_title": "안과 개원 공간 설계 핵심 체크포인트",
        "guide_desc": "시력 및 굴절 검사를 위한 완벽한 암실 조도 제어 시스템과 미세 먼지를 100% 통제하는 백내장·시력교정 전용 클린룸 수술실을 구축합니다."
    },
    "ent": {
        "slug": "ent.html",
        "specialty_name": "이비인후과·소아과",
        "title": "이비인후과·소아청소년과 인테리어 | 청력검사 부스 & 감염 예방 동선",
        "desc": "이비인후과 및 소아청소년과 인테리어 전문! 청력 검사 전용 방음 부스, 호흡기 치료기 체어 배선, 소아 안심 놀이 대기실 및 감염 분리실.",
        "badge": "청력검사 방음부스 & 소아 안심 대기실 특화",
        "h1": "성공적인 이비인후과 개원의 시작,<br /><span class=\"text-primary\">이비인후과·소아청소년과 인테리어</span>",
        "area_range": "35평 ~ 80평 (진료 및 치료실 기준)",
        "infra_highlight": "청력검사 방음 부스, 호흡기 체어 배선, 네블라이저",
        "duration": "약 3주 ~ 5주",
        "spec_text": "청력 검사 전용 방음 부스 시공, 호흡기 치료기 체어 배선, 네블라이저 공간 분리, 친환경 무독성 마감재",
        "guide_title": "이비인후과·소아과 공간 설계 핵심 체크포인트",
        "guide_desc": "오차 없는 청력 검사를 위한 특수 방음 부스 시공과 어린이 환자의 부딪힘 사고를 방지하는 둥근 모서리 코너 보호대 및 친환경 무독성 페인트를 적용합니다."
    },
    "oriental": {
        "slug": "oriental.html",
        "specialty_name": "한의원·한방병원",
        "title": "한의원·한방병원 인테리어 | 탕전실 배기 후드 & 입원실 규격 설계",
        "desc": "한의원 및 한방병원 인테리어 전문! 탕전실 대용량 배기 후드 및 방수 설비, 침구실 온돌/온열 전용 배선, 한방병원 입원실 병상 간격 기준 준수.",
        "badge": "탕전실 배기 & 침구실 온열 배선 특화",
        "h1": "성공적인 한의원 개원의 시작,<br /><span class=\"text-primary\">한의원·한방병원 인테리어 전문</span>",
        "area_range": "35평 ~ 200평 (침구실 및 입원실 기준)",
        "infra_highlight": "탕전실 배기 후드/방수, 침구실 온돌/온열 배선",
        "duration": "약 4주 ~ 8주",
        "spec_text": "탕전실 배기 후드 및 방수 설비, 침구실 온돌/온열 전용 배선, 약재 보관실과 원장 진료실 동선, 입원실 병상 규격",
        "guide_title": "한의원·한방병원 공간 설계 핵심 체크포인트",
        "guide_desc": "한약 냄새와 열기를 완벽히 배출하는 탕전실 직배기 덕트 라인과 환자가 편안하게 뜸과 침을 맞을 수 있는 베드별 독립 온열 제어 인프라를 구축합니다."
    },
    "vet": {
        "slug": "vet.html",
        "specialty_name": "동물병원",
        "title": "동물병원 인테리어 전문 업체 | 대형견 분리 대기실 & 멸균 수술실",
        "desc": "동물병원 인테리어 전문! 대형견·소형견 분리 대기 공간, 처치실 멸균 동선, 격리 입원실 특수 방음 및 냄새 역류 방지 전용 배기 공조 설계.",
        "badge": "반려동물 분리 대기실 & 격리실 방음 특화",
        "h1": "성공적인 동물병원 개원의 시작,<br /><span class=\"text-primary\">동물병원 인테리어 전문 설계 & 시공</span>",
        "area_range": "30평 ~ 80평 (처치실 및 수술실 기준)",
        "infra_highlight": "대형/소형견 분리 대기실, 격리 입원실 방음/배기",
        "duration": "약 3주 ~ 5주",
        "spec_text": "처치실 및 수술실 멸균 동선, 대형견·소형견 분리 대기실, 격리 입원실 방음 및 전용 배기 환기, 미끄럼 방지 바닥재",
        "guide_title": "동물병원 개원 공간 설계 핵심 체크포인트",
        "guide_desc": "동물 간의 시야 차단 및 소음 차단을 위한 분리 대기실과 반려동물 관절을 보호하는 논슬립 항균 바닥재, 냄새를 즉각 배출하는 전용 음압 환기 설비를 시공합니다."
    },
    "clinic": {
        "slug": "clinic.html",
        "specialty_name": "의원·클리닉",
        "title": "의원·클리닉 인테리어 전문 업체 | 원장실·진료실·대기공간 맞춤 조닝",
        "desc": "일반 의원 및 메디컬 클리닉 인테리어 전문! 원장실, 진료실, 처치실, 대기공간의 기능적 공간 조닝 및 소방 안전 기준 충족 3D 도면 무료 상담.",
        "badge": "원장실·진료실 최단 동선 & 가성비 시공 특화",
        "h1": "성공적인 클리닉 개원의 시작,<br /><span class=\"text-primary\">의원·클리닉 인테리어 전문 설계</span>",
        "area_range": "35평 ~ 80평 (진료실 및 처치실 기준)",
        "infra_highlight": "진료실-처치실 최단 동선, 소방 안전 기준 충족",
        "duration": "약 3주 ~ 5주",
        "spec_text": "원장실-진료실-처치실-대기공간의 효율적 공간 조닝, 소방 안전 기준 충족, 합리적인 평당 공사비 설계",
        "guide_title": "의원·클리닉 개원 공간 설계 핵심 체크포인트",
        "guide_desc": "한정된 면적 안에서도 데드스페이스를 없애고 원장님의 진료 동선과 환자의 접수·수납 동선이 부드럽게 흐르도록 컴팩트하고 세련된 공간을 완성합니다."
    }
}

def clean_all_old_directories(output_dir):
    print("Cleaning up old numeric directory trees and legacy sitemaps...")
    for entry in os.listdir(output_dir):
        full_path = os.path.join(output_dir, entry)
        if os.path.isdir(full_path) and (entry.isdigit() or entry == "sitemap"):
            shutil.rmtree(full_path, ignore_errors=True)
    print("All old numeric directories removed successfully.")

def build_super_hub_navigation():
    # 13대 지역 링크 뱃지 그리드
    reg_links = []
    for k, v in REGIONAL_HUBS.items():
        reg_links.append(f'<a href="{SITE_URL}/{v["slug"]}" title="{v["region_name"]} 병원 인테리어" class="p-3 bg-white hover:bg-[#fff7ed] border border-gray-200 hover:border-primary hover:text-primary rounded-xl text-xs text-gray-700 transition-all font-semibold flex items-center justify-between shadow-sm"><span>📍 {v["region_name"]} 병원 인테리어</span><i class="fas fa-chevron-right text-[10px] text-gray-400"></i></a>')
        
    # 10대 진료과목 링크 뱃지 그리드
    spec_links = []
    for k, v in SPECIALTY_HUBS.items():
        spec_links.append(f'<a href="{SITE_URL}/{v["slug"]}" title="{v["specialty_name"]} 인테리어" class="p-3 bg-white hover:bg-[#fff7ed] border border-gray-200 hover:border-primary hover:text-primary rounded-xl text-xs text-gray-700 transition-all font-semibold flex items-center justify-between shadow-sm"><span>🩺 {v["specialty_name"]} 인테리어</span><i class="fas fa-chevron-right text-[10px] text-gray-400"></i></a>')

    hub_html = f"""  <!-- 13대 주요 지역 & 10대 진료과목 메디컬 인테리어 슈퍼 허브 네비게이션 -->
  <section class="max-w-7xl mx-auto px-6 py-12 border-t border-gray-200" id="super-hub-section">
    <div class="bg-gray-50 border border-gray-200/80 rounded-2xl p-6 sm:p-8 shadow-sm space-y-8">
      
      <!-- 13대 주요 지역 허브 -->
      <div>
        <div class="flex items-center gap-2 mb-4">
          <span class="w-2.5 h-2.5 rounded-full bg-primary"></span>
          <h3 class="text-sm sm:text-base font-bold text-gray-800 uppercase tracking-wider">영남권 13대 주요 지역별 병원 인테리어 안내</h3>
        </div>
        <p class="text-xs text-gray-500 mb-4">부산 전역 및 대구, 창원, 울산 등 영남권 13개 주요 도시의 직영 방문 실측과 3D 도면 비교 견적을 확인하실 수 있습니다.</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5">
          {''.join(reg_links)}
        </div>
      </div>

      <!-- 10대 진료과목별 전문 허브 -->
      <div class="pt-6 border-t border-gray-200">
        <div class="flex items-center gap-2 mb-4">
          <span class="w-2.5 h-2.5 rounded-full bg-[#03c75a]"></span>
          <h3 class="text-sm sm:text-base font-bold text-gray-800 uppercase tracking-wider">진료과목별 특화 메디컬 인테리어 설계 가이드</h3>
        </div>
        <p class="text-xs text-gray-500 mb-4">치과, 피부과, 내과, 성형외과 등 진료과목별 필수 설비 인프라와 권장 평수, 의료법 시설 기준을 확인하실 수 있습니다.</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5">
          {''.join(spec_links)}
        </div>
      </div>

    </div>
  </section>
"""
    return hub_html

def update_main_index_html(base_html):
    print("Updating index.html with Super Hub Navigation & Naver TalkTalk...")
    html = base_html

    # 네이버 톡톡 배너
    naver_talktalk_banner = f"""  <!-- 네이버 톡톡 실시간 1:1 상담 배너 -->
  <section class="max-w-7xl mx-auto px-6 py-6 border-t border-gray-100" id="naver-talktalk-section">
    <div class="bg-gradient-to-r from-[#03c75a]/10 via-[#03c75a]/5 to-transparent border border-[#03c75a]/30 rounded-2xl p-5 sm:p-7 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
      <div class="flex items-center gap-4 text-center sm:text-left">
        <div class="w-12 h-12 rounded-2xl bg-[#03c75a] flex items-center justify-center text-white text-2xl shadow-md flex-shrink-0">
          <i class="fas fa-comment-dots"></i>
        </div>
        <div>
          <div class="flex items-center justify-center sm:justify-start gap-2 mb-1">
            <span class="px-2 py-0.5 bg-[#03c75a] text-white text-[10px] font-bold rounded-full">실시간 상담</span>
            <h3 class="text-base sm:text-lg font-bold text-[#111111]">네이버 톡톡으로 빠른 견적 & 도면 상담</h3>
          </div>
          <p class="text-xs text-gray-600">진료과목별 인테리어 견적과 3D 설계 문의를 네이버 톡톡으로 실시간 1:1 상담받으실 수 있습니다.</p>
        </div>
      </div>
      <a href="{NAVER_TALKTALK_URL}" target="_blank" rel="noopener noreferrer" class="w-full sm:w-auto px-6 py-3.5 bg-[#03c75a] hover:bg-[#02b150] text-white text-xs sm:text-sm font-bold rounded-xl transition-all duration-200 shadow-md hover:shadow-lg flex items-center justify-center gap-2 flex-shrink-0">
        <i class="fas fa-comment-dots text-base"></i>
        <span>네이버 톡톡 상담하기</span>
        <i class="fas fa-chevron-right text-[10px] ml-0.5"></i>
      </a>
    </div>
  </section>
"""

    hub_html = build_super_hub_navigation()
    bottom_block = f"{naver_talktalk_banner}\n{hub_html}"

    # 기존 sitemap-hub, naver-talktalk-section 치환
    if 'id="naver-talktalk-section"' in html:
        html = re.sub(r'<!-- 네이버 톡톡[\s\S]*?<!-- (주요 지역별|13대 주요 지역)[\s\S]*?</section>\n?', bottom_block, html)
    elif 'id="sitemap-hub"' in html:
        html = re.sub(r'<!-- (전체 사이트맵|전국 키워드|주요 지역별)[\s\S]*?</section>\n?', bottom_block, html)
    elif '<!-- Footer Section -->' in html:
        html = html.replace('<!-- Footer Section -->', f'{bottom_block}\n  <!-- Footer Section -->')
    else:
        html = html.replace('<footer', f'{bottom_block}\n  <footer')

    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved clean index.html with Super Hub Navigation.")
    return html

def generate_regional_pages(base_html):
    print("Generating 13 Regional Super Hub Pages...")
    for key, data in REGIONAL_HUBS.items():
        html = base_html
        canonical_url = f"{SITE_URL}/{data['slug']}"
        landmarks_str = ", ".join(data["landmarks"][:6])
        
        # 1. Head 메타태그 교체
        head_block = f"""  <title>{data["title"]}</title>
  
  <!-- Favicon Setting -->
  <link rel="icon" href="/favicon.ico" />
  <link rel="icon" href="/favicon.png" type="image/png" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <link rel="apple-touch-icon" href="/favicon.png" />
  
  <!-- SEO Meta Tags for Naver & Google -->
  <meta name="description" content="{data["desc"]}" />
  <link rel="canonical" href="{canonical_url}" />
  <meta name="keywords" content="{data["region_name"]} 병원 인테리어, {data["region_name"]} 의원 인테리어, {data["region_name"]} 병원 리모델링, {data["region_name"]} 병원 인테리어 전문 업체, {landmarks_str}" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="{BRAND_NAME}" />
  <meta name="google-site-verification" content="0f-j7HOTRJP6McdtJbnZNC-e6SibEW0xDkSq_J1YGUI" />
  
  <!-- Open Graph Tags (SNS Sharing) -->
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{BRAND_NAME}" />
  <meta property="og:title" content="{data["title"]}" />
  <meta property="og:description" content="{data["desc"]}" />
  <meta property="og:image" content="{SITE_URL}/main1.webp" />
  <meta property="og:url" content="{canonical_url}" />"""

        html = re.sub(r'<title>.*?</title>[\s\S]*?(?=<!-- Pretendard Web Font CDN -->)', f'{head_block}\n  \n  ', html, flags=re.I)

        # 2. Schema.org 3종 세트
        schema_json = [
            {
                "@context": "https://schema.org",
                "@type": "HomeAndConstructionBusiness",
                "name": f"{data['region_name']} 병원 인테리어 - {BRAND_NAME}",
                "description": data["desc"],
                "url": canonical_url,
                "telephone": "1588-0000",
                "priceRange": "$$",
                "areaServed": [data["region_name"]] + data["landmarks"][:5],
                "serviceType": f"{data['region_name']} 병원 인테리어 및 리모델링",
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
                        "name": f"{data['region_name']} 지역 병원 인테리어 무료 현장 실측이 가능한가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"네, {data['region_name']} 전 지역({landmarks_str} 등)에 직영 감리팀이 1:1로 방문하여 정밀 실측 및 3D 도면 비교 견적을 무료로 제공합니다."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"{data['region_name']} 병원 인테리어 공사 시 가장 중요한 점은 무엇인가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"{data['specialties_summary']} 실내건축공사업 면허를 보유한 정식 건설업체와 진행해야 안전합니다."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": "병원 인테리어 시 '실내건축공사업 면허'가 꼭 필요한가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "건설산업기본법에 따라 공사 금액이 1,500만 원 이상인 실내 인테리어 공사는 반드시 정부 등록 면허를 보유한 업체만 시공하도록 규정되어 있습니다. 국토교통부 키스콘(KISCON)에서 면허 보유 여부를 확인하실 수 있습니다."
                        }
                    }
                ]
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{SITE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": f"{data['region_name']} 병원 인테리어", "item": canonical_url}
                ]
            }
        ]

        schema_script = f"""<script type="application/ld+json">
  {json.dumps(schema_json, ensure_ascii=False, indent=2)}
  </script>"""
        html = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>', schema_script, html)

        # 3. 로고 서브 텍스트 치환
        html = html.replace('메디컬 공간 디자인</span>', f'{data["region_name"]} 병원 인테리어</span>')

        # 4. 히어로 섹션 동적 치환
        html = html.replace('안과 · 내과 복합 메디컬 공간 특화', data["badge"])
        html = html.replace('<span class="text-primary">부산 병원 공간 디자인</span>', f'<span class="text-primary">{data["region_name"]} 병원 인테리어 전문</span>')

        # 5. Information Gain 지역 실무 가이드 카드 주입
        regional_card = f"""    <!-- {data["region_name"]} 지역 특화 실무 정보 가이드 (Google Information Gain & NavBoost 극대화) -->
    <div class="mb-16 p-6 sm:p-8 bg-gradient-to-r from-gray-50 to-orange-50/40 rounded-2xl border border-gray-200/80 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-1 bg-primary text-white text-[11px] font-bold rounded">지역 가이드</span>
          <h3 class="text-base sm:text-lg font-bold text-[#111111]">{data["region_name"]} 병원 인테리어 핵심 설계 & 시공 안내</h3>
        </div>
        <a href="{NAVER_TALKTALK_URL}" target="_blank" rel="noopener noreferrer" class="self-start sm:self-auto px-3.5 py-1.5 bg-[#03c75a] hover:bg-[#02b150] text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 shadow-sm">
          <i class="fas fa-comment-dots"></i> 네이버 톡톡 상담
        </a>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        <div class="p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
          <span class="text-gray-400 block mb-1 font-medium">서비스 권역</span>
          <span class="font-bold text-gray-800 text-sm">{data["region_name"]} 전 지역 무료 실측</span>
        </div>
        <div class="p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
          <span class="text-gray-400 block mb-1 font-medium">핵심 메디컬 존</span>
          <span class="font-bold text-gray-800 text-sm">{data["landmarks"][0]}, {data["landmarks"][1]} 등</span>
        </div>
        <div class="p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
          <span class="text-gray-400 block mb-1 font-medium">안전 시공 보증</span>
          <span class="font-bold text-gray-800 text-sm">실내건축면허 & 하자보증</span>
        </div>
        <div class="p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
          <span class="text-gray-400 block mb-1 font-medium">1:1 맞춤 혜택</span>
          <span class="font-bold text-primary text-sm">3D 도면 무료 & 비교 견적</span>
        </div>
      </div>

      <div class="mt-4 p-4 bg-white/90 rounded-xl border border-gray-100 text-xs text-gray-700 leading-relaxed space-y-2">
        <p><strong>{data["region_name"]} 주요 거점 서비스 지역:</strong> {", ".join(data["landmarks"])} 등 {data["region_name"]} 전 지역 신규 개원 및 이전 리모델링 시공을 지원합니다.</p>
        <p class="text-gray-500">{data["highlight_text"]}</p>
      </div>
    </div>

    <!-- Section 1: Intro Section (병원 공간 철학) -->"""

        html = html.replace('<!-- Section 1: Intro Section (병원 공간 철학) -->', regional_card)

        # 6. Philosophy 인용구 맞춤화
        new_quote = f'"{data["region_name"]} 지역 병의원 개원 시, 각 진료과목 특성에 최적화된 동선과 소방/공조 시설 기준을 완벽하게 검토하여 설계합니다."'
        html = re.sub(r'"공간 기획 단계에서부터[\s\S]*?"', new_quote, html)

        # 7. FAQ 질문 치환
        html = html.replace('<span>부산 병원 프리미엄 인테리어는 일반 인테리어와 무엇이 다른가요?</span>', f'<span>{data["region_name"]} 지역 병원 인테리어 무료 현장 실측이 가능한가요?</span>')
        html = html.replace('<span>진료 과목별(내과, 치과, 피부과 등) 인테리어 설계 시 가장 중요한 점은 무엇인가요?</span>', f'<span>{data["region_name"]} 병원 인테리어 공사 시 가장 중요한 점은 무엇인가요?</span>')

        page_file = os.path.join(OUTPUT_DIR, data["slug"])
        with open(page_file, "w", encoding="utf-8") as f:
            f.write(html)
            
    print("Generated all 13 Regional Super Hub Pages successfully.")

def generate_specialty_pages(base_html):
    print("Generating 10 Specialty Super Hub Pages...")
    for key, data in SPECIALTY_HUBS.items():
        html = base_html
        canonical_url = f"{SITE_URL}/{data['slug']}"
        
        # 1. Head 메타태그 교체
        head_block = f"""  <title>{data["title"]}</title>
  
  <!-- Favicon Setting -->
  <link rel="icon" href="/favicon.ico" />
  <link rel="icon" href="/favicon.png" type="image/png" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <link rel="apple-touch-icon" href="/favicon.png" />
  
  <!-- SEO Meta Tags for Naver & Google -->
  <meta name="description" content="{data["desc"]}" />
  <link rel="canonical" href="{canonical_url}" />
  <meta name="keywords" content="{data["specialty_name"]} 인테리어, {data["specialty_name"]} 인테리어 전문 업체, {data["specialty_name"]} 리모델링, 부산 {data["specialty_name"]} 인테리어, {data["infra_highlight"]}" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="{BRAND_NAME}" />
  <meta name="google-site-verification" content="0f-j7HOTRJP6McdtJbnZNC-e6SibEW0xDkSq_J1YGUI" />
  
  <!-- Open Graph Tags (SNS Sharing) -->
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{BRAND_NAME}" />
  <meta property="og:title" content="{data["title"]}" />
  <meta property="og:description" content="{data["desc"]}" />
  <meta property="og:image" content="{SITE_URL}/main1.webp" />
  <meta property="og:url" content="{canonical_url}" />"""

        html = re.sub(r'<title>.*?</title>[\s\S]*?(?=<!-- Pretendard Web Font CDN -->)', f'{head_block}\n  \n  ', html, flags=re.I)

        # 2. Schema.org 3종 세트
        schema_json = [
            {
                "@context": "https://schema.org",
                "@type": "HomeAndConstructionBusiness",
                "name": f"{data['specialty_name']} 인테리어 - {BRAND_NAME}",
                "description": data["desc"],
                "url": canonical_url,
                "telephone": "1588-0000",
                "priceRange": "$$",
                "areaServed": ["부산", "대구", "울산", "창원", "김해", "해운대", "센텀", "명지", "경상남도"],
                "serviceType": f"{data['specialty_name']} 인테리어 및 리모델링",
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
                        "name": f"{data['specialty_name']} 인테리어 설계 시 가장 중요한 설비 기준은 무엇인가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"{data['spec_text']} 등 특수 조건들을 사전에 철저히 반영하여 안전하고 오차 없는 정밀 설계를 진행합니다."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"{data['specialty_name']} 개원 시 권장 평수와 공사 기간은 어떻게 되나요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"{data['specialty_name']}의 권장 개원 실평수는 {data['area_range']}이며, 평균 공사 기간은 {data['duration']}입니다."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": "병원 인테리어 시 '실내건축공사업 면허'가 꼭 필요한가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "건설산업기본법에 따라 공사 금액이 1,500만 원 이상인 실내 인테리어 공사는 반드시 정부 등록 면허를 보유한 업체만 시공하도록 규정되어 있습니다. 국토교통부 키스콘(KISCON)에서 면허 보유 여부를 확인하실 수 있습니다."
                        }
                    }
                ]
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{SITE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": f"{data['specialty_name']} 인테리어", "item": canonical_url}
                ]
            }
        ]

        schema_script = f"""<script type="application/ld+json">
  {json.dumps(schema_json, ensure_ascii=False, indent=2)}
  </script>"""
        html = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>', schema_script, html)

        # 3. 로고 서브 텍스트 치환
        html = html.replace('메디컬 공간 디자인</span>', f'{data["specialty_name"]} 인테리어</span>')

        # 4. 히어로 섹션 동적 치환
        html = html.replace('안과 · 내과 복합 메디컬 공간 특화', data["badge"])
        html = html.replace('<span class="text-primary">부산 병원 공간 디자인</span>', f'<span class="text-primary">{data["specialty_name"]} 인테리어 전문</span>')

        # 5. Information Gain 진료과목 실무 가이드 카드 주입
        spec_card = f"""    <!-- {data["specialty_name"]} 특화 실무 정보 가이드 (Google Information Gain & NavBoost 극대화) -->
    <div class="mb-16 p-6 sm:p-8 bg-gradient-to-r from-gray-50 to-orange-50/40 rounded-2xl border border-gray-200/80 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-1 bg-primary text-white text-[11px] font-bold rounded">진료과목 가이드</span>
          <h3 class="text-base sm:text-lg font-bold text-[#111111]">{data["specialty_name"]} 공간 설계 및 시공 핵심 체크포인트</h3>
        </div>
        <a href="{NAVER_TALKTALK_URL}" target="_blank" rel="noopener noreferrer" class="self-start sm:self-auto px-3.5 py-1.5 bg-[#03c75a] hover:bg-[#02b150] text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 shadow-sm">
          <i class="fas fa-comment-dots"></i> 네이버 톡톡 상담
        </a>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        <div class="p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
          <span class="text-gray-400 block mb-1 font-medium">권장 개원 실평수</span>
          <span class="font-bold text-gray-800 text-sm">{data["area_range"]}</span>
        </div>
        <div class="p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
          <span class="text-gray-400 block mb-1 font-medium">필수 인프라 설비</span>
          <span class="font-bold text-gray-800 text-sm">{data["infra_highlight"]}</span>
        </div>
        <div class="p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
          <span class="text-gray-400 block mb-1 font-medium">평균 공사 기간</span>
          <span class="font-bold text-gray-800 text-sm">{data["duration"]}</span>
        </div>
        <div class="p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
          <span class="text-gray-400 block mb-1 font-medium">영남권 지원</span>
          <span class="font-bold text-primary text-sm">3D 도면 무료 & 비교 견적</span>
        </div>
      </div>

      <div class="mt-4 p-4 bg-white/90 rounded-xl border border-gray-100 text-xs text-gray-700 leading-relaxed space-y-2">
        <p><strong>{data["guide_title"]}:</strong> {data["guide_desc"]}</p>
        <p class="text-gray-500">{data["spec_text"]}</p>
      </div>
    </div>

    <!-- Section 1: Intro Section (병원 공간 철학) -->"""

        html = html.replace('<!-- Section 1: Intro Section (병원 공간 철학) -->', spec_card)

        # 6. Philosophy 인용구 맞춤화
        new_quote = f'"{data["specialty_name"]} 인테리어 시, 진료 특성에 최적화된 동선과 소방/공조 시설 기준을 완벽하게 검토하여 설계합니다."'
        html = re.sub(r'"공간 기획 단계에서부터[\s\S]*?"', new_quote, html)

        # 7. FAQ 질문 치환
        html = html.replace('<span>부산 병원 프리미엄 인테리어는 일반 인테리어와 무엇이 다른가요?</span>', f'<span>{data["specialty_name"]} 인테리어 설계 시 가장 중요한 설비 기준은 무엇인가요?</span>')
        html = html.replace('<span>진료 과목별(내과, 치과, 피부과 등) 인테리어 설계 시 가장 중요한 점은 무엇인가요?</span>', f'<span>{data["specialty_name"]} 개원 시 권장 평수와 공사 기간은 어떻게 되나요?</span>')

        page_file = os.path.join(OUTPUT_DIR, data["slug"])
        with open(page_file, "w", encoding="utf-8") as f:
            f.write(html)
            
    print("Generated all 10 Specialty Super Hub Pages successfully.")

def generate_clean_sitemaps(output_dir):
    print("Generating Clean 27-URL sitemap.xml...")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    urls = [
        {"loc": f"{SITE_URL}/", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{SITE_URL}/portfolio-derma.html", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/portfolio-eye-internal.html", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/portfolio-dental.html", "priority": "0.9", "changefreq": "weekly"}
    ]
    
    # 13개 지역 허브
    for k, v in REGIONAL_HUBS.items():
        urls.append({"loc": f"{SITE_URL}/{v['slug']}", "priority": "0.9", "changefreq": "weekly"})
        
    # 10개 진료과목 허브
    for k, v in SPECIALTY_HUBS.items():
        urls.append({"loc": f"{SITE_URL}/{v['slug']}", "priority": "0.9", "changefreq": "weekly"})
        
    xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for u in urls:
        xml_content.append(f'  <url><loc>{u["loc"]}</loc><lastmod>{today}</lastmod><changefreq>{u["changefreq"]}</changefreq><priority>{u["priority"]}</priority></url>')
        
    xml_content.append('</urlset>')
    
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_content))
        
    print(f"Generated: {sitemap_path} (Total {len(urls)} Clean High-Value URLs)")
    
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

def main():
    print("=== HOMPAGE_KEYWORD 23대 슈퍼 허브 빌드 시작 ===")
    
    # 1. 기존 598개 구 디렉토리 및 sitemap 폴더 완전 삭제
    clean_all_old_directories(OUTPUT_DIR)
    
    # 2. base_html 로드
    base_file = os.path.join(OUTPUT_DIR, "busaninterior_base.html")
    if not os.path.exists(base_file):
        base_file = os.path.join(OUTPUT_DIR, "index.html")
    with open(base_file, "r", encoding="utf-8") as f:
        base_html = f.read()
        
    # 3. index.html 최신화
    updated_main_html = update_main_index_html(base_html)
    
    # 4. 13대 지역 슈퍼 페이지 생성
    generate_regional_pages(updated_main_html)
    
    # 5. 10대 진료과목 슈퍼 페이지 생성
    generate_specialty_pages(updated_main_html)
    
    # 6. 초경량 27개 클린 sitemap.xml 생성
    generate_clean_sitemaps(OUTPUT_DIR)
    
    # 7. GitHub Pages .nojekyll 보장
    nojekyll_path = os.path.join(OUTPUT_DIR, ".nojekyll")
    if not os.path.exists(nojekyll_path):
        with open(nojekyll_path, "w", encoding="utf-8") as f:
            f.write("")
            
    print("=== HOMPAGE_KEYWORD 23대 슈퍼 허브 빌드 완료! ===")

if __name__ == "__main__":
    main()
