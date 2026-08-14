/**
 * Cloudflare Pages Functions / Workers용 동적 SEO 엣지 렌더러
 * 대상 사이트: busaninterior.kr
 * 경로: functions/[id].js 및 functions/[id]/index.js
 */

export async function onRequest(context) {
  const { request, params } = context;
  const url = new URL(request.url);
  const idStr = params.id;
  const pageId = parseInt(idStr, 10);

  if (isNaN(pageId) || pageId < 1 || pageId > 25000) {
    return new Response('Page Not Found', { status: 404 });
  }

  // 1. 키워드 DB 조회
  const dataResponse = await fetch(new URL('/seo_keywords.json', url.origin));
  if (!dataResponse.ok) {
    return new Response('Keywords DB not loaded', { status: 500 });
  }
  const keywords = await dataResponse.json();
  const item = keywords.find(k => k.id === pageId);

  if (!item) {
    return new Response('Page Not Found', { status: 404 });
  }

  // 2. busaninterior 베이스 HTML 로드
  const baseResponse = await fetch(new URL('/busaninterior_base.html', url.origin));
  if (!baseResponse.ok) {
    return new Response('Base HTML not loaded', { status: 500 });
  }
  let html = await baseResponse.text();

  // 3. Title & 메타태그 치환 (White-hat SEO 표준)
  html = html.replace(
    /<title>.*?<\/title>/i,
    `<title>${item.title}</title>`
  );
  html = html.replace(
    /<meta name="description" content=".*?" \/>/i,
    `<meta name="description" content="${item.description}" />\n  <link rel="canonical" href="${item.url}" />`
  );
  html = html.replace(
    /<meta property="og:title" content=".*?" \/>/i,
    `<meta property="og:title" content="${item.title}" />`
  );
  html = html.replace(
    /<meta property="og:description" content=".*?" \/>/i,
    `<meta property="og:description" content="${item.description}" />\n  <meta property="og:url" content="${item.url}" />`
  );

  // 4. Schema.org JSON-LD 구조화 데이터 주입
  const schemaScript = `
  <!-- 동적 Schema.org 구조화 데이터 -->
  <script type="application/ld+json">
  ${JSON.stringify(item.schema_json)}
  </script>
</head>`;
  html = html.replace('</head>', schemaScript);

  // 5. 헤더 상단 로고 옆 서브 텍스트 치환
  html = html.replace(
    '메디컬 공간 디자인</span>',
    `${item.keyword}</span>`
  );

  // 6. 히어로 H1 메인 타이틀 치환
  html = html.replace(
    '<span class="text-primary">부산 병원 공간 디자인</span>',
    `<span class="text-primary">${item.keyword}</span>`
  );

  return new Response(html, {
    headers: {
      'content-type': 'text/html;charset=UTF-8',
      'cache-control': 'public, max-age=86400, s-maxage=604800'
    }
  });
}
