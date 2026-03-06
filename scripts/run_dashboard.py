#!/usr/bin/env python3
"""Morning Market Dashboard — Daily Runner (GitHub Actions)"""
import os, sys, traceback, subprocess
import requests as _req
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID","")
if not BOT_TOKEN or not CHAT_ID:
    print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set"); sys.exit(1)

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

def tg_msg(text):
    _req.post(f"{TG}/sendMessage",
              data={"chat_id":CHAT_ID,"text":text,"parse_mode":"HTML"}, timeout=15)

def tg_document(path, caption=""):
    """Send file as document — preserves quality, no Telegram compression."""
    with open(path,"rb") as f:
        _req.post(f"{TG}/sendDocument",
                  data={"chat_id":CHAT_ID,"caption":caption,"parse_mode":"HTML"},
                  files={"document":f}, timeout=60)

print("="*55)
print(f"  MORNING DASHBOARD  {datetime.now().strftime('%a %d %b %Y  %H:%M UTC')}")
print("="*55)

# Install Playwright browsers (fast if already cached)
subprocess.run([sys.executable,"-m","playwright","install","chromium","--with-deps"],
               capture_output=True)

run_ok = False
try:
    import matplotlib; matplotlib.use("Agg")
    import nest_asyncio; nest_asyncio.apply()

    # ── execute notebook cells ──────────────────────────────────────────────
    # Cells are inlined below. Cell 1 (pip install) is handled by requirements.txt.
    # NOTEBOOK_CODE_PLACEHOLDER
    # ───────────────────────────────────────────────────────────────────────

    run_ok = True
    print("\n✅  All cells completed.")

except Exception as e:
    print(f"\n❌  Failed: {e}"); traceback.print_exc()

today = datetime.now().strftime("%A, %d %b %Y")

if run_ok and os.path.exists("dashboard_report.pdf"):
    # Build short header message
    try:
        sigs   = {"BULLISH":"🟢","NEUTRAL":"🟡","BEARISH":"🔴"}
        ind_ln = "".join(f"  {sigs[i['signal']]} {i['name']}\n" for i in INDICATORS)
        fii_ln = ""
        if fii_net_series is not None:
            n5,n10,n20 = (float(fii_net_series.head(k).sum()) for k in (5,10,20))
            fii_ln = f"\n<b>FII Equity:</b>  5d Rs{n5:+,.0f}  10d Rs{n10:+,.0f}  20d Rs{n20:+,.0f} Cr"
        msg = (
            f"🇮🇳 <b>Morning Dashboard — {today}</b>\n"
            f"━"*25+"\n"
            f"<b>Score:</b> {verdict['score']:.1f}/10  <b>Verdict:</b> {verdict['verdict']}{fii_ln}\n"
            f"━"*25+"\n"
            f"{ind_ln}"
            f"━"*25+"\n"
            f"Universe: {len(ALL_TICKERS)} stocks"
        )
    except Exception as e:
        msg = f"🇮🇳 <b>Morning Dashboard — {today}</b>\nRun complete. See PDF below."; print(e)

    tg_msg(msg)
    tg_document("dashboard_report.pdf",
                f"📊 Full Report — {today} (3 pages: Summary · Charts · Breadth)")
    print("✅  Sent to Telegram.")

else:
    tg_msg(f"⚠️ <b>Morning Dashboard — {today}</b>\n"
           f"{'Run failed' if not run_ok else 'PDF missing'}. Check GitHub Actions logs.")

print("\n✅  Done.")
