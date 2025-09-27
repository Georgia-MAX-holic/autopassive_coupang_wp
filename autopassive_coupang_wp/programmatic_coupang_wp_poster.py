
import os, html, json, urllib.parse
from datetime import datetime, timedelta, timezone
import pandas as pd
import requests

WP_URL = os.getenv("WP_URL", "").rstrip("/")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASS = os.getenv("WP_APP_PASS", "")
COUPANG_DEEPLINK_PREFIX = os.getenv("COUPANG_DEEPLINK_PREFIX", "")
COUPANG_SUB_ID = os.getenv("COUPANG_SUB_ID", "")
POSTS_PER_RUN = int(os.getenv("POSTS_PER_RUN", "15"))
PUBLISH_MODE = os.getenv("PUBLISH_MODE", "publish")  # "publish" or "future"

if not (WP_URL and WP_USER and WP_APP_PASS and COUPANG_DEEPLINK_PREFIX):
    raise SystemExit("Missing env vars: WP_URL, WP_USER, WP_APP_PASS, COUPANG_DEEPLINK_PREFIX")

session = requests.Session()
session.auth = (WP_USER, WP_APP_PASS)
session.headers.update({"Content-Type": "application/json; charset=utf-8"})

def ensure_category(name="Coupang Picks"):
    r = session.get(f"{WP_URL}/wp-json/wp/v2/categories", params={"search": name, "per_page": 100})
    r.raise_for_status()
    for cat in r.json():
        if cat.get("name") == name:
            return cat["id"]
    r = session.post(f"{WP_URL}/wp-json/wp/v2/categories", data=json.dumps({"name": name}))
    r.raise_for_status()
    return r.json()["id"]

def title_exists(title):
    r = session.get(f"{WP_URL}/wp-json/wp/v2/posts", params={"search": title, "per_page": 10})
    if r.status_code == 404:
        return False
    r.raise_for_status()
    for p in r.json():
        if p.get("title", {}).get("rendered", "").strip().lower() == title.strip().lower():
            return True
    return False

def build_deeplink(target_url):
    prefix = COUPANG_DEEPLINK_PREFIX
    join_char = '&' if '?' in prefix else '?'
    parts = [prefix]
    if COUPANG_SUB_ID:
        parts.append(f"{join_char}subId={urllib.parse.quote_plus(COUPANG_SUB_ID)}")
        join_char = '&'
    parts.append(f"{join_char}targetUrl={urllib.parse.quote_plus(target_url)}")
    return "".join(parts)

def hero_image_html(image_url):
    if not image_url:
        return ""
    return f'<p><img src="{html.escape(image_url)}" alt="" referrerpolicy="no-referrer" style="max-width:100%;height:auto;border-radius:12px"/></p>'

def cta_button(label, deeplink):
    return (
        '<p><a href="' + html.escape(deeplink) + '" target="_blank" rel="nofollow sponsored noopener" '
        'style="display:inline-block;padding:12px 18px;border-radius:12px;text-decoration:none;font-weight:700;">'
        + html.escape(label) + '</a></p>'
        '<p style="font-size:12px;opacity:.7;margin-top:8px">*Affiliate link (I may earn a commission).</p>'
    )

def content_from_search(keyword, image_url, price_label):
    target = f"https://www.coupang.com/np/search?q={urllib.parse.quote_plus(keyword)}"
    deeplink = build_deeplink(target)
    body = []
    body.append("<p>빠르게 살펴보는 쿠팡 검색 추천입니다. 최신 가격과 재고는 아래 버튼으로 확인하세요.</p>")
    body.append(hero_image_html(image_url))
    if price_label:
        body.append(f"<p><b>가격 가이드:</b> {html.escape(price_label)}</p>")
    body.append("<h3>구매 체크리스트</h3>")
    body.append("<ul><li>리뷰 수/별점</li><li>최근 Q&A 응답</li><li>배송일정/반품 정책</li><li>공식 스토어 여부</li></ul>")
    body.append(cta_button(f"쿠팡에서 '{keyword}' 검색 결과 보기", deeplink))
    return "\n".join(body)

def content_from_product(product_url, image_url, price_label):
    deeplink = build_deeplink(product_url)
    body = []
    body.append("<p>쿠팡에서 가격/재고 변동이 잦습니다. 아래 버튼을 눌러 현재 최저가를 바로 확인하세요.</p>")
    body.append(hero_image_html(image_url))
    if price_label:
        body.append(f"<p><b>최근 가격대:</b> {html.escape(price_label)}</p>")
    body.append("<h3>구매 체크리스트</h3>")
    body.append("<ul><li>공식 판매자/정품 보증</li><li>교환/반품 규정</li><li>최근 리뷰 추세</li><li>쿠폰/카드할인 여부</li></ul>")
    body.append(cta_button("쿠팡에서 현재가 확인하기", deeplink))
    return "\n".join(body)

def publish_post(title, content, category_id, schedule_offset_minutes=0):
    payload = {
        "title": title,
        "content": content,
        "status": PUBLISH_MODE,
        "categories": [category_id]
    }
    if PUBLISH_MODE == "future" and schedule_offset_minutes > 0:
        dt = datetime.now(timezone.utc) + timedelta(minutes=schedule_offset_minutes)
        payload["date_gmt"] = dt.strftime("%Y-%m-%dT%H:%M:%S")
    r = session.post(f"{WP_URL}/wp-json/wp/v2/posts", data=json.dumps(payload))
    r.raise_for_status()
    return r.json().get("id")

def main():
    seeds = pd.read_csv("seeds.csv")
    cat_id = ensure_category("Coupang Picks")
    posted = 0
    schedule_step = 20
    schedule_offset = 20

    for _, row in seeds.iterrows():
        title = str(row["title"]).strip()
        typ = str(row["type"]).strip().lower()
        keyword = str(row.get("keyword", "") or "").strip()
        product_url = str(row.get("product_url", "") or "").strip()
        image_url = str(row.get("image_url", "") or "").strip()
        price_label = str(row.get("price_label", "") or "").strip()

        if not title or title_exists(title):
            continue

        if typ == "search" and keyword:
            content = content_from_search(keyword, image_url, price_label)
        elif typ == "product" and product_url:
            content = content_from_product(product_url, image_url, price_label)
        else:
            continue

        _post_id = publish_post(title, content, cat_id, schedule_offset_minutes=(schedule_offset if PUBLISH_MODE=="future" else 0))
        posted += 1
        schedule_offset += schedule_step
        if posted >= POSTS_PER_RUN:
            break

    print(f"Posted {posted} articles. Done.")

if __name__ == "__main__":
    main()
