# 🇮🇳 Indian Market Health Dashboard — Automated Delivery

Runs every weekday at **9:00 AM IST** via GitHub Actions.  
Sends two dashboard images + a summary to your **Telegram** automatically. Free forever.

---

## What you receive every morning

| Message | Content |
|---------|---------|
| 📋 Text summary | Health score, verdict, all 6 indicator signals, FII 5d/10d/20d |
| 📊 Main dashboard | Nifty chart, VIX, RSI, indicator cards, FII bar chart |
| 📈 Breadth deep-dive | Breadth by cap segment + by sector |

---

## One-time Setup (15 minutes)

### Step 1 — Create your Telegram Bot (3 min)

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Give it a name (e.g. `Prashant Market Bot`) and a username (e.g. `prashant_market_bot`)
4. BotFather gives you a **token** like `7123456789:AAHxxxxx...` — **save this**

### Step 2 — Get your Chat ID (2 min)

1. Search for your new bot in Telegram and press **Start**
2. Open this URL in your browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. You'll see JSON. Find `"chat":{"id":XXXXXXXXX}` — that number is your **Chat ID**
4. If the JSON is empty, send `/start` to your bot again and refresh

### Step 3 — Create GitHub Repository (5 min)

1. Go to [github.com/new](https://github.com/new)
2. Name it `morning-dashboard` (private is fine)
3. **Upload these files** maintaining this exact folder structure:
   ```
   morning-dashboard/
   ├── .github/
   │   └── workflows/
   │       └── morning_dashboard.yml
   ├── scripts/
   │   └── run_dashboard.py
   ├── requirements.txt
   └── README.md
   ```
   > Easiest way: create each file via GitHub's web editor  
   > (New file → paste content → commit)

### Step 4 — Add Secrets (2 min)

1. In your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add TWO secrets:

   | Name | Value |
   |------|-------|
   | `TELEGRAM_BOT_TOKEN` | The token from BotFather (e.g. `7123456789:AAHxxxxx`) |
   | `TELEGRAM_CHAT_ID` | Your chat ID number (e.g. `987654321`) |

### Step 5 — Test it immediately

1. Go to your repo → **Actions** tab
2. Click **🇮🇳 Morning Market Dashboard** → **Run workflow** → **Run workflow**
3. Watch it run (~8-12 min). You should get Telegram messages when it finishes.

---

## Schedule

```
Runs at 03:30 UTC = 09:00 IST, Monday to Friday
```

To change the time, edit `.github/workflows/morning_dashboard.yml`:
```yaml
- cron: '30 3 * * 1-5'   # minute hour * * days(1=Mon,5=Fri)
```

Common IST times:
| IST | UTC cron |
|-----|----------|
| 8:00 AM | `0 2 * * 1-5` |
| 9:00 AM | `30 3 * * 1-5` |
| 9:30 AM | `0 4 * * 1-5` |

---

## Troubleshooting

**Bot sent nothing / run failed**
→ Go to Actions tab → click the failed run → read the logs

**"TELEGRAM_BOT_TOKEN not set"**
→ Secrets are case-sensitive. Confirm names match exactly.

**"Chat not found" Telegram error**
→ You need to send `/start` to your bot at least once before it can message you.

**FII indicator shows NEUTRAL every day**
→ All three FII data sources (Trendlyne, NSE JSON, NSE HTML) failed.  
→ Check the logs for Cell 6 output — the specific error tells you which URL is returning what.

**GitHub Actions free tier limits**
→ 2,000 minutes/month for free accounts. Each run takes ~10 min.  
→ 20 weekday runs/month × 10 min = ~200 min/month. Well within limits.

---

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/morning_dashboard.yml` | Cron schedule + Actions config |
| `scripts/run_dashboard.py` | All dashboard logic + Telegram delivery |
| `requirements.txt` | Python dependencies |

