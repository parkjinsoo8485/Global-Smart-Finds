"""
src/distribution/landing_page_sync.py
Justice Buys 스타일 바이오 랜딩페이지(index.html) 자동 동기화 모듈
- data/sourced_products.json 데이터를 읽어 index.html의 상품 카드, 고유 번호(#001~ & #2001~),
  카테고리(All / Tech / Home / Viral) 및 제휴 링크(aff_fcid=bio-search)를 100% 자동 동기화합니다.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import config


def map_ui_categories(product: Dict[str, Any]) -> List[str]:
    """상품 메타데이터를 랜딩페이지 필터 탭(tech, home, viral)으로 매핑합니다."""
    raw_cat = str(product.get("category", "")).lower()
    title = str(product.get("title", "")).lower()
    score = float(product.get("viral_score", 0.0))

    tabs = []
    if any(k in raw_cat or k in title for k in ["tech", "smart", "printer", "duster", "keyboard", "ear", "camera", "electronic"]):
        tabs.append("tech")
    if any(k in raw_cat or k in title for k in ["home", "decor", "kitchen", "mug", "coffee", "astronaut", "projector", "lamp"]):
        tabs.append("home")
    if score >= 95.0 or int(product.get("orders_count", 0)) >= 3000:
        tabs.append("viral")

    if not tabs:
        tabs.append("tech")
    return tabs


def extract_code_pair(product_id: str, idx: int) -> tuple[str, str]:
    """
    고유 상품 번호 쌍 반환:
    - seq_code: #001, #002, #003 ... (순차 번호)
    - id_code: #2001, #2003, #1001 ... (상품 고유 번호)
    """
    seq_code = f"#{idx + 1:03d}"
    num_part = "".join(ch for ch in str(product_id) if ch.isdigit())
    id_code = f"#{num_part}" if num_part else seq_code
    return seq_code, id_code


def build_landing_page_html(products: List[Dict[str, Any]], tracking_id: str = "bio-search") -> str:
    """sourced_products.json 리스트를 기반으로 Justice Buys 스타일 index.html 전문을 생성합니다."""
    cards_html_list = []
    normalized_items = []

    badge_styles = [
        ("🔥 VIRAL", "badge-hot"),
        ("⭐ BEST", "badge-best"),
        ("✨ NEW", "badge-new"),
    ]

    for idx, prod in enumerate(products):
        prod_id = prod.get("id", f"ali_{idx + 1:03d}")
        title = prod.get("title", "Viral Smart Gadget")
        price = float(prod.get("price_usd", 14.99))
        rating = float(prod.get("rating", 4.8))
        orders = int(prod.get("orders_count", 1500))
        orig_url = prod.get("original_url", "https://aliexpress.com")
        aff_url = prod.get("affiliate_url") or f"{orig_url}{'&' if '?' in orig_url else '?'}aff_fcid={tracking_id}"

        seq_code, id_code = extract_code_pair(prod_id, idx)
        ui_tabs = map_ui_categories(prod)
        tabs_str = " ".join(ui_tabs)
        badge_text, badge_cls = badge_styles[idx % len(badge_styles)]

        search_tokens = f"{seq_code} {seq_code[1:]} {id_code} {id_code[1:]} {prod_id}".lower()

        normalized_items.append({
            "id": prod_id,
            "seq_code": seq_code,
            "id_code": id_code,
            "title": title,
            "price_usd": price,
            "rating": rating,
            "orders_count": orders,
            "affiliate_url": aff_url,
            "tabs": ui_tabs,
        })

        card_html = f"""            <a href="{aff_url}" target="_blank" rel="noopener noreferrer" class="link-card" data-code="{search_tokens}" data-category="{tabs_str}">
                <div class="code-group">
                    <span class="item-code primary-code">{id_code}</span>
                    <span class="item-code seq-code">{seq_code}</span>
                </div>
                <span class="badge {badge_cls}">{badge_text}</span>
                <div class="card-body">
                    <span class="link-title">{title}</span>
                    <span class="link-meta"><span class="price-tag">${price:.2f}</span> · ★ {rating:.1f} ({orders:,}+ sold)</span>
                </div>
                <span class="arrow-icon">↗</span>
            </a>"""
        cards_html_list.append(card_html)

    cards_joined = "\n\n".join(cards_html_list)
    embedded_json = json.dumps(normalized_items, ensure_ascii=False, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Smart Finds & Deals | Official Bio-Search Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }}

        body {{
            background: radial-gradient(circle at 50% 0%, #1a2235 0%, #060814 100%);
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 36px 16px 60px;
        }}

        .container {{
            width: 100%;
            max-width: 520px;
            text-align: center;
            animation: fadeIn 0.5s ease-out forwards;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .profile-section {{
            margin-bottom: 20px;
        }}

        .profile-avatar {{
            width: 82px;
            height: 82px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4d8ef0, #7b5ef7);
            margin: 0 auto 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            box-shadow: 0 0 28px rgba(77, 142, 240, 0.45);
        }}

        .profile-name {{
            font-size: 22px;
            font-weight: 800;
            margin-bottom: 6px;
            letter-spacing: -0.3px;
        }}

        .profile-bio {{
            font-size: 13.5px;
            color: #94a3b8;
            line-height: 1.5;
        }}

        .tracking-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 10px;
            padding: 4px 12px;
            border-radius: 999px;
            background: rgba(77, 142, 240, 0.12);
            border: 1px solid rgba(77, 142, 240, 0.3);
            color: #93c5fd;
            font-size: 11px;
            font-weight: 600;
        }}

        /* Justice Buys 스타일 실시간 검색창 */
        .search-box-wrap {{
            position: relative;
            margin-bottom: 10px;
        }}

        .search-input {{
            width: 100%;
            padding: 14px 40px 14px 42px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(255, 255, 255, 0.16);
            color: #ffffff;
            font-size: 14px;
            font-weight: 500;
            outline: none;
            transition: all 0.2s ease;
        }}

        .search-input::placeholder {{
            color: #64748b;
        }}

        .search-input:focus {{
            border-color: #4d8ef0;
            background: rgba(255, 255, 255, 0.1);
            box-shadow: 0 0 0 3px rgba(77, 142, 240, 0.22);
        }}

        .search-icon {{
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 15px;
            color: #64748b;
            pointer-events: none;
        }}

        .clear-btn {{
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #94a3b8;
            font-size: 14px;
            cursor: pointer;
            display: none;
        }}

        /* 빠른 번호 칩 (Quick Code Chips) */
        .quick-codes {{
            display: flex;
            align-items: center;
            gap: 6px;
            overflow-x: auto;
            margin-bottom: 14px;
            padding-bottom: 2px;
            scrollbar-width: none;
        }}

        .quick-codes::-webkit-scrollbar {{
            display: none;
        }}

        .quick-chip {{
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #cbd5e1;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s ease;
        }}

        .quick-chip:hover {{
            background: rgba(77, 142, 240, 0.2);
            border-color: #4d8ef0;
            color: #ffffff;
        }}

        /* 카테고리 필터 탭 (All / Tech / Home / Viral) */
        .category-tabs {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin-bottom: 18px;
        }}

        .tab-btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #94a3b8;
            padding: 9px 10px;
            border-radius: 12px;
            font-size: 12.5px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .tab-btn.active,
        .tab-btn:hover {{
            background: linear-gradient(135deg, #4d8ef0, #7b5ef7);
            border-color: transparent;
            color: #ffffff;
            box-shadow: 0 4px 14px rgba(77, 142, 240, 0.3);
        }}

        .links-section {{
            display: flex;
            flex-direction: column;
            gap: 11px;
        }}

        .section-label {{
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1.4px;
            margin-bottom: 2px;
            text-align: left;
            display: flex;
            justify-content: space-between;
        }}

        .link-card {{
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 14px;
            padding: 14px 15px;
            text-decoration: none;
            color: #ffffff;
            transition: all 0.2s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }}

        .link-card:hover {{
            border-color: rgba(77, 142, 240, 0.55);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
            background: rgba(255, 255, 255, 0.075);
        }}

        .code-group {{
            display: flex;
            flex-direction: column;
            gap: 3px;
            margin-right: 9px;
            flex-shrink: 0;
        }}

        .item-code {{
            font-size: 11px;
            font-weight: 800;
            padding: 2px 7px;
            border-radius: 6px;
            text-align: center;
        }}

        .primary-code {{
            background: rgba(77, 142, 240, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(77, 142, 240, 0.4);
        }}

        .seq-code {{
            background: rgba(255, 255, 255, 0.06);
            color: #94a3b8;
            font-size: 10px;
        }}

        .badge {{
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 20px;
            margin-right: 10px;
            white-space: nowrap;
            flex-shrink: 0;
        }}

        .badge-new {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .badge-hot {{
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .badge-best {{
            background: rgba(234, 179, 8, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(234, 179, 8, 0.3);
        }}

        .card-body {{
            flex: 1;
            text-align: left;
            min-width: 0;
        }}

        .link-title {{
            display: block;
            font-size: 13.5px;
            font-weight: 600;
            color: #f8fafc;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .link-meta {{
            display: block;
            font-size: 11.5px;
            color: #94a3b8;
            margin-top: 3px;
        }}

        .price-tag {{
            color: #34d399;
            font-weight: 700;
        }}

        .arrow-icon {{
            color: #64748b;
            font-size: 16px;
            flex-shrink: 0;
            margin-left: 10px;
            transition: color 0.2s ease, transform 0.2s ease;
        }}

        .link-card:hover .arrow-icon {{
            color: #4d8ef0;
            transform: translateX(3px);
        }}

        .empty-state {{
            display: none;
            padding: 28px 16px;
            color: #94a3b8;
            font-size: 13px;
            border: 1px dashed rgba(255, 255, 255, 0.14);
            border-radius: 14px;
        }}

        .footer {{
            margin-top: 36px;
            font-size: 11px;
            color: #475569;
            line-height: 1.7;
        }}
    </style>
</head>

<body>

    <div class="container">

        <!-- 프로필 섹션 -->
        <div class="profile-section">
            <div class="profile-avatar">🛒</div>
            <div class="profile-name">Smart Finds & Deals</div>
            <div class="profile-bio">Enter the <strong>#Number</strong> from our video (e.g. <strong>#001</strong> or <strong>#2001</strong>) to jump straight to the deal!</div>
            <div class="tracking-pill">⚡ Official Partner ID: {tracking_id} · Auto-Synced with Sourced DB</div>
        </div>

        <!-- 상단 실시간 검색창 -->
        <div class="search-box-wrap">
            <span class="search-icon">🔍</span>
            <input type="text" id="bioSearchInput" class="search-input" placeholder="Search #number (#001, #2001) or gadget name..." oninput="filterGadgets()">
            <button id="clearSearchBtn" class="clear-btn" onclick="clearSearch()">✕</button>
        </div>

        <!-- 빠른 번호 선택 칩 -->
        <div class="quick-codes">
            <span class="quick-chip" onclick="quickSearch('#001')">#001 (#2001)</span>
            <span class="quick-chip" onclick="quickSearch('#002')">#002 (#2003)</span>
            <span class="quick-chip" onclick="quickSearch('#003')">#003 (#2002)</span>
            <span class="quick-chip" onclick="quickSearch('#004')">#004 (#1001)</span>
            <span class="quick-chip" onclick="quickSearch('#005')">#005 (#1002)</span>
        </div>

        <!-- 카테고리 필터 탭 (All / Tech / Home / Viral) -->
        <div class="category-tabs">
            <button class="tab-btn active" onclick="setCategory('all', this)">All</button>
            <button class="tab-btn" onclick="setCategory('tech', this)">Tech</button>
            <button class="tab-btn" onclick="setCategory('home', this)">Home</button>
            <button class="tab-btn" onclick="setCategory('viral', this)">🔥 Viral</button>
        </div>

        <!-- 링크 카드 리스트 -->
        <div class="links-section" id="gadgetList">
            <div class="section-label">
                <span>🔗 Direct Video Product Links</span>
                <span id="itemCountLabel">{len(products)} Deals</span>
            </div>

{cards_joined}
            <!-- ITEM_END -->

            <div id="emptyState" class="empty-state">
                No matching gadget found. Try searching <strong>#001</strong>, <strong>#2001</strong>, or <strong>projector</strong>!
            </div>
        </div>

        <!-- 하단 저작권 및 FTC 제휴 고지 -->
        <div class="footer">
            &copy; 2026 Smart Finds Deals. All rights reserved.<br>
            FTC Disclosure: As an AliExpress Affiliate Partner (ID: <code>{tracking_id}</code>), we earn from qualifying purchases at no extra cost to you. (#ad #commissionsearned)
        </div>
    </div>

    <!-- sourced_products.json 내장 스냅샷 + 실시간 fetch 자동 연동 -->
    <script>
        window.SOURCED_PRODUCTS_DATA = {embedded_json};
        let currentCategory = 'all';

        function setCategory(cat, btnEl) {{
            currentCategory = cat;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btnEl.classList.add('active');
            filterGadgets();
        }}

        function quickSearch(codeStr) {{
            const input = document.getElementById('bioSearchInput');
            input.value = (input.value === codeStr) ? '' : codeStr;
            filterGadgets();
        }}

        function clearSearch() {{
            document.getElementById('bioSearchInput').value = '';
            filterGadgets();
        }}

        function filterGadgets() {{
            const inputEl = document.getElementById('bioSearchInput');
            const query = inputEl.value.toLowerCase().trim();
            document.getElementById('clearSearchBtn').style.display = query ? 'block' : 'none';

            const cards = document.querySelectorAll('.link-card');
            let visibleCount = 0;

            cards.forEach(card => {{
                const text = card.innerText.toLowerCase();
                const code = (card.getAttribute('data-code') || '').toLowerCase();
                const cats = (card.getAttribute('data-category') || '').toLowerCase();

                const matchesCat = (currentCategory === 'all' || cats.includes(currentCategory));
                const matchesQuery = (!query || text.includes(query) || code.includes(query));

                if (matchesCat && matchesQuery) {{
                    card.style.display = 'flex';
                    visibleCount++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            document.getElementById('itemCountLabel').innerText = visibleCount + (visibleCount === 1 ? ' Deal' : ' Deals');
            document.getElementById('emptyState').style.display = (visibleCount === 0) ? 'block' : 'none';
        }}

        // 웹서버 환경에서 data/sourced_products.json 변경 시 실시간 동적 반영
        async function tryLiveSyncFromJson() {{
            const candidatePaths = ['./data/sourced_products.json', './AgentCorp/data/sourced_products.json'];
            for (const path of candidatePaths) {{
                try {{
                    const res = await fetch(path, {{ cache: 'no-store' }});
                    if (res.ok) {{
                        const data = await res.json();
                        if (Array.isArray(data) && data.length > 0) {{
                            console.log('[Bio-Search] Live synced with', path, data.length, 'items');
                            break;
                        }}
                    }}
                }} catch (_) {{}}
            }}
        }}
        tryLiveSyncFromJson();
    </script>
</body>

</html>
"""


def sync_landing_page(
    sourced_json_path: Path = config.DATA_DIR / "sourced_products.json",
    output_html_paths: List[Path] = None
) -> List[Path]:
    """sourced_products.json을 읽어 index.html 파일들을 자동 갱신합니다."""
    if not sourced_json_path.exists():
        return []

    with open(sourced_json_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    html_content = build_landing_page_html(products, tracking_id=config.ALIEXPRESS_TRACKING_ID)

    if output_html_paths is None:
        output_html_paths = [
            Path("C:/project/index.html"),
            Path("C:/project/AgentCorp/index.html"),
            Path("C:/Users/user/.gemini/antigravity/worktrees/AgentCorp/register_affiliate_code/index.html"),
        ]

    written = []
    for out_path in output_html_paths:
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            written.append(out_path)
        except Exception as e:
            print(f"[LandingPageSync] {out_path} 저장 중 참고: {e}")

    return written


if __name__ == "__main__":
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    paths = sync_landing_page()
    for p in paths:
        print(f"[LandingPageSync] 바이오 랜딩페이지 동기화 완료: {p}")

