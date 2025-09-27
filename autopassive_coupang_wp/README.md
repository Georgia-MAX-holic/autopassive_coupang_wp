# Auto-Passive Coupang + WordPress Engine (Starter Kit)

This repo auto-publishes affiliate posts to WordPress using **Coupang Partners deeplinks**.
No servers required: **GitHub Actions** runs the poster on a schedule.

## Files
- `programmatic_coupang_wp_poster.py` – Reads `seeds.csv` and posts to WordPress (REST API).
- `seeds.csv` – Your seed rows (type=search or product).
- `.github/workflows/wp_poster.yml` – GitHub Actions workflow (12-hour schedule).
- `requirements.txt` – Python deps.

## What you need
1) WordPress admin access + **Application Password**.
2) Coupang Partners account.
3) Your **affiliate deeplink prefix** from Coupang Partners link tool, e.g.
   - `COUPANG_DEEPLINK_PREFIX=https://link.coupang.com/a/XXXX?lptag=XXXX` (example format; use yours)
4) (Optional) `COUPANG_SUB_ID` for sub-tracking.

## Seeds
`seeds.csv` columns:
- `title` – Post title (unique).
- `type` – `search` or `product`
- `keyword` – used only when `type=search` (Coupang query string)
- `product_url` – used only when `type=product` (a normal Coupang product URL)
- `image_url` – optional product/hero image
- `price_label` – optional string (e.g., "₩49,900", "Under ₩30,000")

### How links are built
- For `type=search`: target URL = `https://www.coupang.com/np/search?q=<keyword>`
- For `type=product`: target URL = the given `product_url`
Then the script creates a deeplink: `<COUPANG_DEEPLINK_PREFIX>&subId=<COUPANG_SUB_ID>&targetUrl=<encoded target>`
(If your prefix ends with `?`, the script will insert `&` safely.)

## Setup (GitHub)
Create a public repo and upload this folder. Add **Actions Secrets**:
- `WP_URL` – e.g. `https://yourdomain.com` (no trailing slash)
- `WP_USER`
- `WP_APP_PASS`
- `COUPANG_DEEPLINK_PREFIX` – from Coupang Partners link generator
- `COUPANG_SUB_ID` – optional (e.g. `blog1`)

(Optional) Add **Repository Variable**:
- `POSTS_PER_RUN` – default 15

## Local test (optional)
```
pip install -r requirements.txt
export WP_URL="https://yourdomain.com"
export WP_USER="yourusername"
export WP_APP_PASS="app_password_here"
export COUPANG_DEEPLINK_PREFIX="https://link.coupang.com/a/XXXX?lptag=XXXX"
export COUPANG_SUB_ID="blog1"
python programmatic_coupang_wp_poster.py
```

## Compliance
- Add affiliate disclosure on your site.
- Follow Coupang Partners policy (category rates, cookie rules, etc.).
- Do not mislead or force clicks.

## Notes
- The script skips already-published titles.
- You can switch to scheduled publishing by setting `PUBLISH_MODE=future` inside the workflow env.
