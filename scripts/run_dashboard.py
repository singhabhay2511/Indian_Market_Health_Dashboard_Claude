#!/usr/bin/env python3
"""Morning Market Dashboard — Daily Runner (GitHub Actions)"""
import os, sys, traceback
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
def tg_photo(path, cap=""):
    with open(path,"rb") as f:
        _req.post(f"{TG}/sendPhoto",
                  data={"chat_id":CHAT_ID,"caption":cap,"parse_mode":"HTML"},
                  files={"photo":f}, timeout=30)

print("="*55)
print(f"  MORNING DASHBOARD  {datetime.now().strftime('%a %d %b %Y  %H:%M UTC')}")
print("="*55)

run_ok = False
try:
    import matplotlib; matplotlib.use("Agg")
    import nest_asyncio; nest_asyncio.apply()
    # Install playwright browsers if needed
    import subprocess as _sp
    _sp.run([sys.executable,"-m","playwright","install","chromium","--with-deps"],
            capture_output=True)
    # ── CELL 2 ──────────────────────────────────────
    # ── CELL 2: Imports & Config ─────────────────────────────────────────────────
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch
    from datetime import datetime, timedelta
    import requests, urllib.request, io, time, warnings
    warnings.filterwarnings('ignore')
    
    END      = datetime.today()
    START    = END - timedelta(days=450)
    START_1Y = END - timedelta(days=380)
    
    CONFIG = {
        'dma_long':200,'dma_medium':50,'dma_short':20,'dma_slope_window':20,
        'breadth_bullish':60,'breadth_bearish':40,
        'vix_bullish':15,'vix_bearish':20,
        'rsi_period':14,'rsi_overbought':70,'rsi_healthy_low':45,'rsi_oversold':30,
        'fii_bullish':2000,'fii_bearish':-2000,
        'weights':{'200dma':3,'50dma':2,'breadth':2,'vix':2,'rsi':1,'fii':2},
    }
    
    C = {
        'BULLISH':'#16A34A','NEUTRAL':'#D97706','BEARISH':'#DC2626',
        'bg':'#FFFFFF','card':'#F3F4F6','chartbg':'#F9FAFB',
        'text':'#111827','subtext':'#6B7280','border':'#D1D5DB',
        'grid':'#E5E7EB','blue':'#2563EB','gold':'#92400E','purple':'#7C3AED',
    }
    
    TICKERS = {
        'nifty50':'^NSEI','nifty500':'^CRSLDX','niftynext50':'^NSMIDCP',
        'niftysmlcap':'^CNXSC','vix':'^INDIAVIX',
        'bank':'^NSEBANK','it':'^CNXIT','pharma':'^CNXPHARMA',
        'auto':'^CNXAUTO','metal':'^CNXMETAL','fmcg':'^CNXFMCG',
        'energy':'^CNXENERGY','realty':'^CNXREALTY',
        'gold':'GOLDBEES.NS','usdinr':'USDINR=X',
    }
    
    # ── Live NSE constituent CSVs — updated by NSE after every rebalancing ────────
    # MICROCAP NOTE: NSE hosts the Microcap 250 CSV under a different path.
    # We try multiple URL patterns in order; first successful fetch wins.
    NSE_INDEX_URLS = {
        'NIFTY50'    : ['https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv'],
        'NEXT50'     : ['https://nsearchives.nseindia.com/content/indices/ind_niftynext50list.csv'],
        'MIDCAP150'  : ['https://nsearchives.nseindia.com/content/indices/ind_niftymidcap150list.csv'],
        'SMALLCAP250': ['https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv'],
        'MICROCAP250': [
            'https://nsearchives.nseindia.com/content/indices/ind_niftymicrocap250_list.csv',
            'https://nsearchives.nseindia.com/content/indices/ind_niftymicrocap250list.csv',
            'https://nsearchives.nseindia.com/content/equities/ind_niftymicrocap250list.csv',
            'https://www.nseindia.com/content/indices/ind_niftymicrocap250list.csv',
        ],
    }
    SEGMENT_ORDER  = ['NIFTY50','NEXT50','MIDCAP150','SMALLCAP250','MICROCAP250']
    SEGMENT_LABELS = {
        'NIFTY50':'Nifty 50','NEXT50':'Nifty Next 50',
        'MIDCAP150':'Nifty Midcap 150','SMALLCAP250':'Nifty Smallcap 250',
        'MICROCAP250':'Nifty Microcap 250',
    }
    
    # NSE Industry → our Sector label
    # NSE periodically renames their industry strings — we cover both old and new variants
    NSE_SECTOR_MAP = {
        # Financial Services
        'Financial Services':'Financial Services','Banks':'Financial Services',
        'Insurance':'Financial Services','Capital Markets':'Financial Services',
        'Diversified Financials':'Financial Services',
        # IT
        'Information Technology':'IT & Technology','IT':'IT & Technology',
        'IT & Technology':'IT & Technology',
        # Oil & Gas
        'Oil Gas & Consumable Fuels':'Oil & Gas','Oil  Gas & Consumable Fuels':'Oil & Gas',
        'Oil, Gas & Consumable Fuels':'Oil & Gas',
        # FMCG
        'Fast Moving Consumer Goods':'FMCG','FMCG':'FMCG',
        'Consumer Durables':'FMCG','Food Beverages & Tobacco':'FMCG',
        'Household Products':'FMCG','Agricultural Food & other Products':'FMCG',
        'Food & Beverages':'FMCG',
        # Healthcare
        'Pharmaceuticals & Biotechnology':'Healthcare & Pharma',
        'Pharma':'Healthcare & Pharma','Healthcare Services':'Healthcare & Pharma',
        'Healthcare':'Healthcare & Pharma',                  # ← NEW NSE label
        'Pharmaceuticals':'Healthcare & Pharma',
        # Auto — NSE uses both '&' and 'and'
        'Automobiles & Auto Components':'Auto','Automobiles':'Auto',
        'Auto Components':'Auto',
        'Automobile and Auto Components':'Auto',             # ← NEW NSE label
        # Metals
        'Metals & Mining':'Metals & Mining','Mining':'Metals & Mining',
        # Infrastructure
        'Construction':'Infrastructure','Cement & Construction Materials':'Infrastructure',
        'Construction Materials':'Infrastructure','Industrial Manufacturing':'Infrastructure',
        'Transportation':'Infrastructure','Forest Materials':'Infrastructure',
        'Infrastructure':'Infrastructure',
        # Real Estate
        'Realty':'Real Estate','Real Estate':'Real Estate',
        # Power
        'Power':'Power & Utilities','Utilities':'Power & Utilities','Gas':'Power & Utilities',
        'Power & Utilities':'Power & Utilities',
        # Telecom
        'Telecommunication':'Telecom','Telecom':'Telecom',
        # Chemicals
        'Chemicals':'Chemicals','Specialty Chemicals':'Chemicals',
        'Fertilizers & Agrochemicals':'Chemicals','Agrochemicals':'Chemicals',
        # Capital Goods
        'Capital Goods':'Capital Goods','Industrial Products':'Capital Goods',
        'Electrical Equipment':'Capital Goods','Aerospace & Defense':'Capital Goods',
        # Retail & Consumer
        'Consumer Services':'Retail & Consumer','Retailing':'Retail & Consumer',
        'Media Entertainment & Publication':'Retail & Consumer',
        'Textiles':'Retail & Consumer','Hotels Restaurants & Leisure':'Retail & Consumer',
        'Retail & Consumer':'Retail & Consumer',
        'Services':'Retail & Consumer',                       # ← NEW NSE label
        'Consumer Discretionary Goods & Services':'Retail & Consumer', # ← NEW NSE label
        # Diversified
        'Diversified':'Diversified','Trading':'Diversified','Conglomerate':'Diversified',
    }
    
    errors = []
    print(f'✅ Config ready  |  {START.date()} → {END.date()}')
    
    
    # ── CELL 3 ──────────────────────────────────────
    # ── CELL 3: STEP 1 — Index & VIX Closes ─────────────────────────────────────
    print('STEP 1: Fetching index closes...')
    closes = {}
    for key, ticker in TICKERS.items():
        try:
            df = yf.download(ticker, start=START, end=END, progress=False, auto_adjust=True)
            if not df.empty:
                closes[key] = df['Close'].squeeze()
                print(f'  ✅ {key:15s} {ticker:20s}  {len(df)} rows')
            else:
                print(f'  ⚠️  {key:15s} EMPTY')
        except Exception as e:
            errors.append(str(e)); print(f'  ❌ {key:15s} ERROR: {e}')
    
    BOND_TICKERS = [
        ('NIFTYGS10YR.NS','Nifty GS 10YR'),('GSECLONG.NS','GS Long Duration'),
        ('GSEC10YBEES.NS','G-Sec ETF'),('ICICIB22.NS','ICICI Bond ETF'),('LICNETFGSC.NS','LIC G-Sec ETF'),
    ]
    for bt,bl in BOND_TICKERS:
        try:
            df = yf.download(bt, start=START, end=END, progress=False, auto_adjust=True)
            if not df.empty and len(df)>50:
                closes['bonds'] = df['Close'].squeeze(); print(f'  ✅ bonds  ({bl})'); break
        except: pass
    
    nifty_df   = closes.get('nifty50')
    vix_series = closes.get('vix')
    last_date  = nifty_df.index[-1] if nifty_df is not None else END
    if nifty_df is None: raise ValueError('Nifty 50 unavailable.')
    print(f'\n✅ STEP 1 COMPLETE  |  Last trading day: {last_date.date()}')
    
    
    # ── CELL 4 ──────────────────────────────────────
    # ── CELL 4: STEP 2 — Dynamic Stock Universe from NSE Archives ────────────────
    #
    # NSE publishes constituent CSVs at nsearchives.nseindia.com.
    # Updated after every rebalancing — no hardcoded stock lists needed.
    # Microcap 250 has multiple possible URL paths; we try each in order.
    #
    print('STEP 2: Building dynamic universe from NSE archives...\n')
    
    def fetch_nse_index_csv(urls, segment):
        '''Try each URL in the list until one works. Returns list of (ticker, seg, sector).'''
        if isinstance(urls, str):
            urls = [urls]
        last_err = None
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=20) as r:
                    df = pd.read_csv(io.StringIO(r.read().decode('utf-8')))
                df.columns = [c.strip() for c in df.columns]
                records = []
                for _, row in df.iterrows():
                    sym = str(row.get('Symbol','')).strip()
                    ind = str(row.get('Industry', row.get('Sector','Unknown'))).strip()
                    if not sym or sym == 'nan': continue
                    sector = NSE_SECTOR_MAP.get(ind, ind)
                    records.append((sym + '.NS', segment, sector))
                return records, url
            except Exception as e:
                last_err = e
        raise Exception(f'All URLs failed. Last error: {last_err}')
    
    STOCK_UNIVERSE = []
    for segment, urls in NSE_INDEX_URLS.items():
        try:
            recs, used_url = fetch_nse_index_csv(urls, segment)
            STOCK_UNIVERSE.extend(recs)
            short_url = used_url.split('/')[-1]
            print(f'  ✅ {SEGMENT_LABELS[segment]:28s}: {len(recs):3d} stocks  ({short_url})')
        except Exception as e:
            errors.append(f'Universe {segment}: {e}')
            print(f'  ❌ {SEGMENT_LABELS[segment]:28s}: FAILED — {e}')
            print(f'     ℹ️  Continuing without {SEGMENT_LABELS[segment]} stocks.')
    
    # Deduplicate: stock in multiple indices → keep highest-priority segment
    priority = {s:i for i,s in enumerate(SEGMENT_ORDER)}
    seen = {}
    for ticker,seg,sector in STOCK_UNIVERSE:
        if ticker not in seen or priority[seg] < priority[seen[ticker][0]]:
            seen[ticker] = (seg, sector)
    
    STOCK_UNIVERSE = [(t,s,sec) for t,(s,sec) in seen.items()]
    TICKER_SEGMENT = {t:s   for t,s,_   in STOCK_UNIVERSE}
    TICKER_SECTOR  = {t:sec for t,_,sec in STOCK_UNIVERSE}
    ALL_TICKERS    = [t for t,_,_ in STOCK_UNIVERSE]
    
    total = len(ALL_TICKERS)
    secs  = sorted(set(sec for _,_,sec in STOCK_UNIVERSE))
    print(f'\n  Total unique stocks : {total}')
    print(f'  Sectors             : {secs}')
    if total < 400:
        print(f'  ⚠️  Below 400 stocks — some CSVs may have failed, breadth will still work')
    print(f'\n✅ STEP 2 COMPLETE')
    
    
    # ── CELL 5 ──────────────────────────────────────
    # ── CELL 5: STEP 3 — Fetch Stock Prices ─────────────────────────────────────
    print(f'STEP 3: Fetching prices for {len(ALL_TICKERS)} stocks (~90-120 sec)...\n')
    stock_data = {}
    total_batches = (len(ALL_TICKERS)+49)//50
    for i in range(0, len(ALL_TICKERS), 50):
        batch = ALL_TICKERS[i:i+50]; bn = i//50+1
        try:
            df  = yf.download(batch, start=START, end=END, progress=False, auto_adjust=True)
            if df.empty: print(f'  Batch {bn}/{total_batches} EMPTY'); continue
            cls = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df[['Close']].rename(columns={'Close':batch[0]})
            if isinstance(cls, pd.Series): cls = cls.to_frame()
            stock_data.update(cls.to_dict('series'))
        except Exception as e:
            errors.append(f'Price batch {bn}: {e}')
        if bn%5==0 or bn==total_batches:
            print(f'  Batch {bn:2d}/{total_batches}  — {len(stock_data)} stocks so far')
        time.sleep(0.5)
    prices_df = pd.DataFrame(stock_data).ffill().dropna(axis=1, thresh=200)
    print(f'\n  ✅  {prices_df.shape[1]} stocks with >= 200 days history')
    print('\n✅ STEP 3 COMPLETE')
    
    
    # ── CELL 6 ──────────────────────────────────────
    # ── CELL 6: STEP 4 — FII / DII Data ───────────────────────
    # Playwright (async, via nest_asyncio) renders the full JS page.
    # Fallback: manual input — paste values from
    # trendlyne.com/macro-data/fii-dii/latest/snapshot-pastmonth/
    print('STEP 4: Fetching FII/DII data...\n')
    import asyncio, nest_asyncio
    nest_asyncio.apply()  # lets asyncio run inside Colab's existing event loop
    from playwright.async_api import async_playwright
    
    def to_f(val):
        try: return float(str(val).replace(',','').replace('–','-').replace('−','-').strip())
        except: return None
    
    def build_series(v5, v10, v20):
        d5  = v5  / 5
        d10 = (v10 - v5)  / 5
        d20 = (v20 - v10) / 10
        return pd.Series([d5]*5 + [d10]*5 + [d20]*10, dtype=float)
    
    async def _playwright_fetch():
        url = 'https://trendlyne.com/macro-data/fii-dii/latest/snapshot-pastmonth/'
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=['--no-sandbox','--disable-setuid-sandbox'])
            page    = await browser.new_page(user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'
            ))
            await page.goto(url, wait_until='networkidle', timeout=60000)
            try:
                await page.wait_for_selector('text=Last 30 Days', timeout=25000)
                print('    Summary rows visible ✅')
            except:
                print('    Timeout — extracting whatever rendered')
            rows    = await page.query_selector_all('table tr')
            results = {}
            period_map = {'last 30 days':'20d', 'last 2 weeks':'10d', 'last 1 week':'5d'}
            for row in rows:
                cells = await row.query_selector_all('td, th')
                texts = [await c.inner_text() for c in cells]
                texts = [t.strip() for t in texts]
                if not texts: continue
                for ps, label in period_map.items():
                    if ps in texts[0].lower():
                        print(f'    {label}: {texts[:5]}')
                        val = to_f(texts[1]) if len(texts) >= 2 else None
                        if val is not None: results[label] = val
                        break
            await browser.close()
        return results
    
    def fetch_playwright():
        print('    Launching headless Chromium...')
        results = asyncio.get_event_loop().run_until_complete(_playwright_fetch())
        print(f'    Periods found: {results}')
        if len(results) < 2: raise ValueError(f'Only {len(results)} rows: {results}')
        v5, v10, v20 = results.get('5d',0), results.get('10d',0), results.get('20d',0)
        print(f'    5d:{v5:+,.1f}  10d:{v10:+,.1f}  20d:{v20:+,.1f} Cr')
        return build_series(v5,v10,v20), f'Trendlyne Playwright (5d:{v5:+,.0f}/10d:{v10:+,.0f}/20d:{v20:+,.0f})'
    
    def fetch_manual():
        print('  ── Manual input — open this URL in your browser:')
        print('  https://trendlyne.com/macro-data/fii-dii/latest/snapshot-pastmonth/')
        print('  Look at the SUMMARY tab, FII EQUITY column. Enter 0 if data is unavailable.')
        print()
        try:
            v20 = float(input('  Last 30 Days  FII Equity (e.g. 12253 or -5432): ').replace(',',''))
            v10 = float(input('  Last 2 Weeks  FII Equity (e.g. -829):           ').replace(',',''))
            v5  = float(input('  Last 1 Week   FII Equity (e.g. -10885):         ').replace(',',''))
        except Exception as e:
            raise ValueError(f'Invalid input: {e}')
        print(f'\n    Got: 5d:{v5:+,.1f}  10d:{v10:+,.1f}  20d:{v20:+,.1f} Cr')
        return build_series(v5,v10,v20), f'Manual input (5d:{v5:+,.0f}/10d:{v10:+,.0f}/20d:{v20:+,.0f})'
    
    def fetch_fii_validated():
        for label, fn in [('Trendlyne Playwright', fetch_playwright),
                          ('Manual input',         fetch_manual)]:
            print(f'\n  ── Trying {label} ──')
            try:
                net, desc = fn()
                n5,n10,n20 = float(net.head(5).sum()),float(net.head(10).sum()),float(net.head(20).sum())
                if len(net) >= 20 and not (n5==n10==n20):
                    print(f'  ✅ PASSED | 5d:{n5:+,.0f}  10d:{n10:+,.0f}  20d:{n20:+,.0f} Cr')
                    return net, desc
                print(f'  ❌ Validation failed')
            except KeyboardInterrupt:
                print('  Skipped.')
                break
            except Exception as e:
                import traceback
                print(f'  ❌ {label} ERROR: {e}')
                for ln in traceback.format_exc().strip().splitlines()[-4:]:
                    print(f'     {ln}')
        print('\n  ⚠️  FII data unavailable — indicator shows NEUTRAL.')
        return None, None
    
    fii_net_series, fii_source_label = fetch_fii_validated()
    print(f'\n✅ STEP 4 COMPLETE  |  Source: {fii_source_label or "none — NEUTRAL"}')
    
    # ── CELL 7 ──────────────────────────────────────
    # ── CELL 7: STEP 5 — Compute Indicators ─────────────────────────────────────
    
    def sma(s,w): return s.rolling(window=w,min_periods=w).mean()
    def rsi_calc(s,p=14):
        d=s.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
        return 100-100/(1+g.ewm(com=p-1,min_periods=p).mean()/l.ewm(com=p-1,min_periods=p).mean())
    
    def get_s(df_or_series, col='Close'):
        '''
        Safely extract a price series from either:
          - a pd.Series  (nifty_df, vix_series — already extracted in STEP 1)
          - a pd.DataFrame with normal columns
          - a pd.DataFrame with MultiIndex columns (yfinance >= 0.2.38 format)
        IMPORTANT: nifty_df and vix_series are already Series after STEP 1
        (built via df["Close"].squeeze()), so we must NOT try df["Close"] on them.
        '''
        if isinstance(df_or_series, pd.Series):
            return df_or_series.dropna()
        df = df_or_series
        if isinstance(df.columns, pd.MultiIndex):
            # yfinance MultiIndex: level 0 = Price type, level 1 = ticker
            lvl0 = df.columns.get_level_values(0)
            if col in lvl0:
                s = df.xs(col, level=0, axis=1)
                if isinstance(s, pd.DataFrame): s = s.iloc[:,0]
            else:
                s = df.iloc[:,0]
            return s.squeeze().dropna()
        if col in df.columns:
            return df[col].squeeze().dropna()
        return df.iloc[:,0].squeeze().dropna()
    
    def s2i(sig): return {'BULLISH':1,'NEUTRAL':0,'BEARISH':-1}[sig]
    def sem(sig):  return {'BULLISH':'🟢','NEUTRAL':'🟡','BEARISH':'🔴'}[sig]
    def scol(sig): return C[sig]
    
    def breadth_pct(sub,dma=200):
        above=total=0
        for col in sub.columns:
            s=sub[col].dropna()
            if len(s)<dma: continue
            total+=1
            if float(s.iloc[-1])>float(s.rolling(dma).mean().iloc[-1]): above+=1
        return (above/total*100 if total else 50.0),above,total
    
    def calc_200dma():
        c=get_s(nifty_df); d200=sma(c,200); sl=d200.diff(CONFIG['dma_slope_window'])
        p,d,s=float(c.iloc[-1]),float(d200.iloc[-1]),float(sl.iloc[-1]); pct=(p-d)/d*100
        if p>d and s>0:   sig='BULLISH'; r=f'Nifty {pct:+.1f}% above a RISING 200 DMA.'
        elif p>d:         sig='NEUTRAL'; r=f'Nifty {pct:+.1f}% above 200 DMA but DMA flat/declining.'
        elif s>0:         sig='NEUTRAL'; r=f'Nifty {abs(pct):.1f}% below 200 DMA but DMA still rising.'
        else:             sig='BEARISH'; r=f'Nifty {abs(pct):.1f}% below a DECLINING 200 DMA.'
        return dict(name='Long-Term Trend (200 DMA)',signal=sig,reason=r,
                    detail=dict(price=p,dma200=d,slope=s,pct=pct,close=c,dma=d200),
                    source='Stan Weinstein — Secrets for Profiting in Bull & Bear Markets',weight=CONFIG['weights']['200dma'])
    
    def calc_50dma():
        c=get_s(nifty_df); d200=sma(c,200); d50=sma(c,50); d20=sma(c,20)
        p,d50v,d20v,d200v=float(c.iloc[-1]),float(d50.iloc[-1]),float(d20.iloc[-1]),float(d200.iloc[-1])
        pct=(p-d50v)/d50v*100; stack=(p>d20v>d50v>d200v)
        if p>d50v and stack: sig='BULLISH'; r=f'Nifty {pct:+.1f}% above 50 DMA. Full MA stack aligned.'
        elif p>d50v:         sig='NEUTRAL'; r=f'Nifty {pct:+.1f}% above 50 DMA but stack misaligned.'
        elif abs(pct)<3:     sig='NEUTRAL'; r=f'Nifty {abs(pct):.1f}% below 50 DMA — at decision level.'
        else:                sig='BEARISH'; r=f'Nifty {abs(pct):.1f}% below 50 DMA — medium-term trend down.'
        return dict(name='Medium-Term Trend (50 DMA + MA Stack)',signal=sig,reason=r,
                    detail=dict(price=p,dma50=d50v,dma20=d20v,dma200=d200v,stack=stack,close=c,d50=d50,d20=d20),
                    source='Mark Minervini — Trade Like a Stock Market Wizard (SEPA)',weight=CONFIG['weights']['50dma'])
    
    def calc_breadth():
        print('  Computing breadth...')
        p200,ab200,tot=breadth_pct(prices_df,200); p50,ab50,_=breadth_pct(prices_df,50)
        seg_data={}
        for seg in SEGMENT_ORDER:
            tks=[t for t,s,_ in STOCK_UNIVERSE if s==seg and t in prices_df.columns]
            if not tks: seg_data[seg]=dict(pct200=50,pct50=50,count=0); continue
            sub=prices_df[tks]; p2,_,tc=breadth_pct(sub,200); p5,_,_=breadth_pct(sub,50)
            seg_data[seg]=dict(pct200=p2,pct50=p5,count=tc)
            print(f'    {SEGMENT_LABELS[seg]:28s}: {p2:.0f}% > 200 DMA ({tc} stocks)')
        sector_data={}
        for sec in sorted(set(s for _,_,s in STOCK_UNIVERSE)):
            tks=[t for t,_,s in STOCK_UNIVERSE if s==sec and t in prices_df.columns]
            if not tks: continue
            p2,_,tc=breadth_pct(prices_df[tks],200); sector_data[sec]=dict(pct200=p2,count=tc)
        if p200>=CONFIG['breadth_bullish']:   sig='BULLISH'; r=f'{p200:.0f}% of stocks > 200 DMA.'
        elif p200>=CONFIG['breadth_bearish']: sig='NEUTRAL'; r=f'{p200:.0f}% of stocks > 200 DMA — mixed.'
        else:                                 sig='BEARISH'; r=f'Only {p200:.0f}% of stocks > 200 DMA.'
        return dict(name='Market Breadth (% Stocks > 200 DMA)',signal=sig,reason=r,
                    detail=dict(pct200=p200,pct50=p50,above200=ab200,total=tot,seg_data=seg_data,sector_data=sector_data),
                    source='Ned Davis Research — Being Right or Making Money',weight=CONFIG['weights']['breadth'])
    
    def calc_vix():
        if vix_series is None:
            return dict(name='India VIX',signal='NEUTRAL',reason='VIX unavailable.',
                        detail={},source='NSE India VIX',weight=CONFIG['weights']['vix'])
        curr=float(get_s(vix_series).iloc[-1])
        vs=get_s(vix_series)
        tr='rising' if len(vs)>5 and float(vs.iloc[-1])>float(vs.iloc[-6]) else 'falling'
        if curr<CONFIG['vix_bullish']:   sig='BULLISH'; r=f'India VIX {curr:.1f} — calm conditions.'
        elif curr<CONFIG['vix_bearish']: sig='NEUTRAL'; r=f'India VIX {curr:.1f} ({tr}) — moderate volatility.'
        else:                            sig='BEARISH'; r=f'India VIX {curr:.1f} — ELEVATED. Poor risk-reward.'
        return dict(name='India VIX (Fear Gauge)',signal=sig,reason=r,
                    detail=dict(vix=curr,trend=tr,series=vs),
                    source='NSE India VIX — CBOE Methodology',weight=CONFIG['weights']['vix'])
    
    def calc_rsi():
        c=get_s(nifty_df); rs=rsi_calc(c,14); curr=float(rs.iloc[-1])
        dr='rising' if len(rs)>5 and curr>float(rs.iloc[-6]) else 'falling'
        if CONFIG['rsi_healthy_low']<=curr<=CONFIG['rsi_overbought']: sig='BULLISH'; r=f'RSI-14 {curr:.1f} — healthy momentum.'
        elif curr>CONFIG['rsi_overbought']:  sig='NEUTRAL'; r=f'RSI-14 {curr:.1f} — overbought.'
        elif curr>=CONFIG['rsi_oversold']:   sig='NEUTRAL'; r=f'RSI-14 {curr:.1f} — weakening.'
        else:                                sig='BEARISH'; r=f'RSI-14 {curr:.1f} — oversold / strong downtrend.'
        return dict(name='Nifty Momentum (RSI-14)',signal=sig,reason=r,
                    detail=dict(rsi_val=curr,direction=dr,series=rs),
                    source='J. Welles Wilder — New Concepts in Technical Trading (1978)',weight=CONFIG['weights']['rsi'])
    
    def calc_fii():
        if fii_net_series is None:
            return dict(name='FII Net Flow (5d / 10d / 20d)',signal='NEUTRAL',
                        reason='FII data unavailable.',detail={},
                        source='NSE India FII/DII',weight=CONFIG['weights']['fii'])
        n5  = float(fii_net_series.head(5).sum())
        n10 = float(fii_net_series.head(10).sum())
        n20 = float(fii_net_series.head(20).sum())
        if n20>=CONFIG['fii_bullish']:   sig='BULLISH'; r=f'FII 20d net inflow Rs{n20:,.0f} Cr.'
        elif n20<=CONFIG['fii_bearish']: sig='BEARISH'; r=f'FII 20d net outflow Rs{abs(n20):,.0f} Cr.'
        else:                            sig='NEUTRAL';  r=f'FII 20d net Rs{n20:+,.0f} Cr — no strong bias.'
        return dict(name='FII Net Flow (5d / 10d / 20d)',signal=sig,reason=r,
                    detail=dict(n5=n5,n10=n10,n20=n20,series=fii_net_series.head(60)),
                    source=f'{fii_source_label or "NSE India"}  |  Froot et al. (2001)',weight=CONFIG['weights']['fii'])
    
    print('Computing indicators...')
    ind_200dma  = calc_200dma()
    ind_50dma   = calc_50dma()
    ind_breadth = calc_breadth()
    ind_vix     = calc_vix()
    ind_rsi     = calc_rsi()
    ind_fii     = calc_fii()
    INDICATORS  = [ind_200dma,ind_50dma,ind_breadth,ind_vix,ind_rsi,ind_fii]
    print('\n📊 Summary:')
    for ind in INDICATORS:
        print(f'  {sem(ind["signal"])} {ind["name"]:45s} → {ind["signal"]}')
    print('\n✅ STEP 5 COMPLETE')
    
    
    # ── CELL 8 ──────────────────────────────────────
    # ── CELL 8: STEP 6 — Main Dashboard Chart ────────────────────────────────────
    
    def compute_verdict(indicators):
        tw=sum(i['weight'] for i in indicators); rs=sum(s2i(i['signal'])*i['weight'] for i in indicators)
        sc=(rs/tw+1)/2*10
        b=sum(1 for i in indicators if i['signal']=='BULLISH')
        n=sum(1 for i in indicators if i['signal']=='NEUTRAL')
        r=sum(1 for i in indicators if i['signal']=='BEARISH')
        if sc>=6.5:   v='CONDUCIVE TO TRADE  ✅';     vc=C['BULLISH']; vs='Conditions favour longs.'
        elif sc>=4.5: v='PROCEED WITH CAUTION  ⚠️';  vc=C['NEUTRAL']; vs='Mixed signals. Trade selectively.'
        else:         v='AVOID / REDUCE EXPOSURE  🚫';vc=C['BEARISH']; vs='Hostile. Preserve capital.'
        return dict(score=sc,verdict=v,v_color=vc,v_sub=vs,bullish=b,neutral=n,bearish=r)
    
    def draw_card(ax,ind):
        sc=ind['signal']; col=scol(sc)
        ax.set_facecolor(C['card']); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
        ax.add_patch(FancyBboxPatch((0.01,0.02),0.98,0.96,boxstyle='round,pad=0.03',facecolor=col+'18',edgecolor=col,linewidth=2))
        ax.text(0.5,0.88,ind['name'],color=C['text'],fontsize=8,ha='center',fontweight='bold')
        ax.add_patch(FancyBboxPatch((0.22,0.71),0.56,0.15,boxstyle='round,pad=0.02',facecolor=col+'25',edgecolor=col,linewidth=1.5))
        ax.text(0.5,0.785,f'{sem(sc)}  {sc}',color=col,fontsize=9,ha='center',fontweight='bold')
        words=ind['reason'].split(); lines=[]; line=''
        for w in words:
            if len(line)+len(w)+1<=44: line+=w+' '
            else: lines.append(line.strip()); line=w+' '
        lines.append(line.strip())
        for i,ln in enumerate(lines[:4]): ax.text(0.5,0.60-i*0.115,ln,color=C['subtext'],fontsize=7,ha='center')
        ax.text(0.5,0.14,'●'*ind['weight']+'○'*(3-min(ind['weight'],3)),color=C['subtext'],fontsize=7,ha='center')
        src=ind['source']; src=src[:47]+'…' if len(src)>50 else src
        ax.text(0.5,0.06,f'📚 {src}',color=C['subtext'],fontsize=5.5,ha='center',style='italic')
    
    def sax(ax,title=''):
        ax.set_facecolor(C['chartbg']); ax.tick_params(colors=C['subtext'],labelsize=8)
        ax.spines[['top','right']].set_visible(False); ax.spines[['bottom','left']].set_color(C['border'])
        ax.grid(color=C['grid'],lw=0.5,alpha=0.8)
        if title: ax.set_title(title,color=C['text'],fontsize=11,pad=8,fontweight='bold')
    
    def plot_main_dashboard():
        v=compute_verdict(INDICATORS)
        fig=plt.figure(figsize=(22,32),facecolor=C['bg'])
        gs=gridspec.GridSpec(7,3,figure=fig,height_ratios=[0.80,2.2,2.0,2.0,2.0,2.0,2.2],
                             hspace=0.45,wspace=0.28,top=0.965,bottom=0.02,left=0.05,right=0.97)
        fig.text(0.5,0.984,'🇮🇳  INDIAN MARKET HEALTH DASHBOARD',color=C['text'],fontsize=19,ha='center',fontweight='bold')
        fig.text(0.5,0.975,datetime.now().strftime('%A, %d %B %Y  ·  %I:%M %p'),color=C['subtext'],fontsize=10,ha='center')
        ax_bn=fig.add_subplot(gs[0,:])
        ax_bn.set_facecolor(C['card']); ax_bn.set_xlim(0,1); ax_bn.set_ylim(0,1); ax_bn.axis('off')
        ax_bn.add_patch(FancyBboxPatch((0.01,0.04),0.36,0.92,boxstyle='round,pad=0.03',facecolor=v['v_color']+'15',edgecolor=v['v_color'],linewidth=2))
        ax_bn.text(0.19,0.79,'MARKET VERDICT',color=C['subtext'],fontsize=9,ha='center',fontweight='bold')
        ax_bn.text(0.19,0.47,v['verdict'],color=v['v_color'],fontsize=13,ha='center',fontweight='bold')
        ax_bn.text(0.19,0.19,v['v_sub'],color=C['text'],fontsize=8,ha='center',style='italic')
        ax_bn.add_patch(FancyBboxPatch((0.40,0.04),0.19,0.92,boxstyle='round,pad=0.03',facecolor='#EFF6FF',edgecolor=C['border'],linewidth=1.5))
        ax_bn.text(0.495,0.79,'HEALTH SCORE',color=C['subtext'],fontsize=9,ha='center',fontweight='bold')
        ax_bn.text(0.495,0.42,f"{v['score']:.1f}",color=v['v_color'],fontsize=32,ha='center',fontweight='bold')
        ax_bn.text(0.495,0.14,'/ 10',color=C['subtext'],fontsize=12,ha='center')
        ax_bn.add_patch(FancyBboxPatch((0.62,0.04),0.37,0.92,boxstyle='round,pad=0.03',facecolor='#F0FDF4',edgecolor=C['border'],linewidth=1.5))
        ax_bn.text(0.805,0.79,'SIGNAL COUNT',color=C['subtext'],fontsize=9,ha='center',fontweight='bold')
        ax_bn.text(0.685,0.40,f"🟢 {v['bullish']}  BULLISH",color=C['BULLISH'],fontsize=11,ha='center',fontweight='bold')
        ax_bn.text(0.805,0.40,f"🟡 {v['neutral']}  NEUTRAL",color=C['NEUTRAL'],fontsize=11,ha='center',fontweight='bold')
        ax_bn.text(0.930,0.40,f"🔴 {v['bearish']}  BEARISH",color=C['BEARISH'],fontsize=11,ha='center',fontweight='bold')
        c=get_s(nifty_df); d200=sma(c,200); d50=sma(c,50); d20=sma(c,20); N=252
        ax_n=fig.add_subplot(gs[1,:2])
        ax_n.plot(c.iloc[-N:].index,c.iloc[-N:].values,color=C['blue'],lw=1.8,label='Nifty 50',zorder=3)
        ax_n.plot(d200.iloc[-N:].index,d200.iloc[-N:].values,color='#EF4444',lw=1.5,ls='--',label='200 DMA')
        ax_n.plot(d50.iloc[-N:].index,d50.iloc[-N:].values,color=C['gold'],lw=1.3,ls='--',label='50 DMA')
        ax_n.plot(d20.iloc[-N:].index,d20.iloc[-N:].values,color=C['purple'],lw=1.0,ls=':',label='20 DMA',alpha=0.8)
        cs=c.iloc[-N:]; ds=d200.iloc[-N:]
        ax_n.fill_between(cs.index,cs.values,ds.values,where=(cs.values>=ds.values),alpha=0.07,color=C['BULLISH'])
        ax_n.fill_between(cs.index,cs.values,ds.values,where=(cs.values<ds.values),alpha=0.07,color=C['BEARISH'])
        sax(ax_n,'Nifty 50 — Price vs Moving Averages (1 Year)')
        ax_n.legend(loc='upper left',ncol=2,facecolor='white',edgecolor=C['border'],labelcolor=C['text'],fontsize=8)
        ax_n.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'{x:,.0f}'))
        lp=float(c.iloc[-1])
        ax_n.annotate(f' {lp:,.0f}',xy=(c.index[-1],lp),color=C['blue'],fontsize=9,fontweight='bold',xytext=(3,0),textcoords='offset points')
        ax_v=fig.add_subplot(gs[1,2])
        if vix_series is not None:
            vc=vix_series.iloc[-200:]
            ax_v.fill_between(vc.index,vc.values,alpha=0.2,color='#DC2626')
            ax_v.plot(vc.index,vc.values,color='#DC2626',lw=1.8)
            ax_v.axhline(15,color=C['BULLISH'],ls='--',lw=1.3,alpha=0.9,label='15 — Calm')
            ax_v.axhline(20,color=C['NEUTRAL'],ls='--',lw=1.3,alpha=0.9,label='20 — Caution')
            cv=float(vc.iloc[-1]); vcol=C['BULLISH'] if cv<15 else(C['NEUTRAL'] if cv<20 else C['BEARISH'])
            ax_v.annotate(f' {cv:.1f}',xy=(vc.index[-1],cv),color=vcol,fontsize=11,fontweight='bold',xytext=(3,0),textcoords='offset points')
        sax(ax_v,'India VIX — Fear Gauge')
        ax_v.legend(loc='upper right',facecolor='white',edgecolor=C['border'],labelcolor=C['text'],fontsize=8)
        ax_r=fig.add_subplot(gs[2,:2])
        rs=rsi_calc(get_s(nifty_df),14).iloc[-200:]
        ax_r.plot(rs.index,rs.values,color=C['purple'],lw=1.8)
        ax_r.axhline(70,color=C['BEARISH'],ls='--',lw=1,alpha=0.8,label='70 Overbought')
        ax_r.axhline(45,color=C['BULLISH'],ls=':',lw=1,alpha=0.7,label='45 Healthy floor')
        ax_r.axhline(30,color=C['BULLISH'],ls='--',lw=1,alpha=0.8,label='30 Oversold')
        ax_r.fill_between(rs.index,70,rs.values,where=(rs.values>70),alpha=0.12,color=C['BEARISH'])
        ax_r.fill_between(rs.index,rs.values,30,where=(rs.values<30),alpha=0.12,color=C['BULLISH'])
        ax_r.set_ylim(0,100)
        cr=float(rs.iloc[-1]); rcol=C['BULLISH'] if 45<=cr<=70 else(C['NEUTRAL'] if cr>70 or cr>=30 else C['BEARISH'])
        ax_r.annotate(f'RSI: {cr:.1f}',xy=(rs.index[-1],cr),color=rcol,fontsize=10,fontweight='bold',xytext=(-80,12),textcoords='offset points')
        sax(ax_r,'Nifty RSI-14 — Momentum')
        ax_r.legend(loc='upper left',ncol=3,facecolor='white',edgecolor=C['border'],labelcolor=C['text'],fontsize=8)
        ax_br=fig.add_subplot(gs[2,2])
        bd=ind_breadth['detail']; p200,p50,tot=bd['pct200'],bd['pct50'],bd.get('total','?')
        bars=ax_br.barh(['Above 200 DMA','Above 50 DMA'],[p200,p50],
                        color=[C['BULLISH'] if p200>=60 else(C['NEUTRAL'] if p200>=40 else C['BEARISH']),
                               C['BULLISH'] if p50>=60  else(C['NEUTRAL'] if p50>=40  else C['BEARISH'])],
                        height=0.35,alpha=0.85,edgecolor='white')
        ax_br.set_xlim(0,100)
        ax_br.axvline(60,color=C['subtext'],ls='--',lw=1,alpha=0.6); ax_br.axvline(40,color=C['subtext'],ls=':',lw=0.8,alpha=0.4)
        for bar,val in zip(bars,[p200,p50]):
            ax_br.text(val+1.5,bar.get_y()+bar.get_height()/2,f'{val:.0f}%',va='center',color=C['text'],fontsize=11,fontweight='bold')
        sax(ax_br,f'Overall Breadth ({tot} stocks)')
        for idx,ind in enumerate(INDICATORS):
            ax_c=fig.add_subplot(gs[3+idx//3, idx%3]); draw_card(ax_c,ind)
        ax_fii=fig.add_subplot(gs[6,:]); ax_fii.set_facecolor(C['chartbg'])
        fd=ind_fii['detail']
        if fd and 'series' in fd:
            fs=fd['series'].iloc[:40][::-1]
            ax_fii.bar(range(len(fs)),fs.values,color=[C['BULLISH'] if x>=0 else C['BEARISH'] for x in fs.values],alpha=0.80,width=0.7,edgecolor='white')
            ax_fii.axhline(0,color=C['subtext'],lw=0.8)
            n5,n10,n20=fd['n5'],fd['n10'],fd['n20']
            ax_fii.axhline(n20/20,color='#1D4ED8',ls='--',lw=1.3,alpha=0.7,label=f'20d avg/day Rs{n20/20:+,.0f}')
            ax_fii.axhline(n5/5,  color='#7C3AED',ls=':',lw=1.3,alpha=0.7,label=f'5d avg/day  Rs{n5/5:+,.0f}')
            ax_fii.set_xticks([]); ax_fii.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'Rs{x:,.0f}'))
            ttl=f'FII Daily Net Flow — Last 40 Sessions  |  5d: Rs{n5:+,.0f}Cr   10d: Rs{n10:+,.0f}Cr   20d: Rs{n20:+,.0f}Cr'
        else:
            ax_fii.text(0.5,0.5,'FII data unavailable',color=C['subtext'],ha='center',va='center',fontsize=13,transform=ax_fii.transAxes); ttl='FII Daily Net Flow'
        sax(ax_fii,ttl)
        ax_fii.legend(loc='upper left',facecolor='white',edgecolor=C['border'],labelcolor=C['text'],fontsize=8)
        plt.savefig('dashboard_main.png',dpi=150,bbox_inches='tight',facecolor=C['bg'],edgecolor='none')
        plt.show(); print('✅ dashboard_main.png saved')
        return v
    
    verdict = plot_main_dashboard()
    
    
    # ── CELL 9 ──────────────────────────────────────
    # ── CELL 9: STEP 7 — Breadth Deep-Dive Chart ─────────────────────────────────
    def bar_color(p):
        return C['BULLISH'] if p>=60 else(C['NEUTRAL'] if p>=40 else C['BEARISH'])
    
    def plot_breadth_dashboard():
        bd=ind_breadth['detail']; seg_data=bd.get('seg_data',{}); sector_data=bd.get('sector_data',{})
        fig,axes=plt.subplots(1,2,figsize=(22,10),facecolor=C['bg'])
        fig.subplots_adjust(wspace=0.38,top=0.88,bottom=0.10,left=0.07,right=0.97)
        fig.suptitle(f'🇮🇳  Market Breadth Deep-Dive — {datetime.now().strftime("%A, %d %B %Y")}',
                     color=C['text'],fontsize=15,fontweight='bold',y=0.97)
        ax=axes[0]; ax.set_facecolor(C['chartbg'])
        segs=[s for s in SEGMENT_ORDER if s in seg_data and seg_data[s]['count']>0]
        p200=[seg_data[s]['pct200'] for s in segs]; p50=[seg_data[s]['pct50'] for s in segs]
        cnts=[seg_data[s]['count'] for s in segs]; labs=[SEGMENT_LABELS[s] for s in segs]
        y=np.arange(len(labs)); h=0.32
        b200=ax.barh(y+h/2,p200,height=h,color=[bar_color(p) for p in p200],alpha=0.90,edgecolor='white',label='Above 200 DMA')
        b50 =ax.barh(y-h/2,p50, height=h,color=[bar_color(p) for p in p50], alpha=0.50,edgecolor='white',hatch='//',label='Above 50 DMA')
        for bar,val in zip(b200,p200): ax.text(min(val+1.5,97),bar.get_y()+bar.get_height()/2,f'{val:.0f}%',va='center',color=C['text'],fontsize=10,fontweight='bold')
        for bar,val in zip(b50,p50):   ax.text(min(val+1.5,97),bar.get_y()+bar.get_height()/2,f'{val:.0f}%',va='center',color=C['subtext'],fontsize=8.5)
        ax.set_yticks(y); ax.set_yticklabels([f'{l}\n({c} stocks)' for l,c in zip(labs,cnts)],fontsize=9.5,color=C['text'])
        ax.set_xlim(0,110)
        ax.axvline(60,color=C['BULLISH'],ls='--',lw=1.3,alpha=0.7,label='60% — Bullish')
        ax.axvline(40,color=C['BEARISH'],ls=':',lw=1.1,alpha=0.6,label='40% — Bearish')
        ax.set_xlabel('% of stocks',color=C['subtext'],fontsize=9)
        ax.tick_params(colors=C['subtext'],labelsize=8)
        ax.spines[['top','right']].set_visible(False); ax.spines[['bottom','left']].set_color(C['border'])
        ax.grid(color=C['grid'],lw=0.5,alpha=0.8,axis='x')
        ax.set_title('Breadth by Market Cap Segment',color=C['text'],fontsize=12,pad=10,fontweight='bold')
        ax.legend(loc='lower right',facecolor='white',edgecolor=C['border'],labelcolor=C['text'],fontsize=8.5)
        ax2=axes[1]; ax2.set_facecolor(C['chartbg'])
        srt=sorted(sector_data.items(),key=lambda x:x[1]['pct200'],reverse=True)
        snames=[s for s,_ in srt]; spcts=[d['pct200'] for _,d in srt]; scnts=[d['count'] for _,d in srt]
        ys=np.arange(len(snames))
        bars=ax2.barh(ys,spcts,height=0.60,color=[bar_color(p) for p in spcts],alpha=0.88,edgecolor='white')
        for bar,val,cnt in zip(bars,spcts,scnts):
            ax2.text(min(val+1,105),bar.get_y()+bar.get_height()/2,f'{val:.0f}%  ({cnt})',va='center',color=C['text'],fontsize=8.5,fontweight='bold')
        ax2.set_yticks(ys); ax2.set_yticklabels(snames,fontsize=9.5,color=C['text'])
        ax2.set_xlim(0,120)
        ax2.axvline(60,color=C['BULLISH'],ls='--',lw=1.3,alpha=0.7); ax2.axvline(40,color=C['BEARISH'],ls=':',lw=1.1,alpha=0.6)
        ax2.set_xlabel('% stocks above 200 DMA',color=C['subtext'],fontsize=9)
        ax2.tick_params(colors=C['subtext'],labelsize=8)
        ax2.spines[['top','right']].set_visible(False); ax2.spines[['bottom','left']].set_color(C['border'])
        ax2.grid(color=C['grid'],lw=0.5,alpha=0.8,axis='x')
        ax2.set_title('Breadth by Sector  (strongest → weakest)',color=C['text'],fontsize=12,pad=10,fontweight='bold')
        ax2.legend(handles=[
            mpatches.Patch(color=C['BULLISH'],label='>60%  Bullish'),
            mpatches.Patch(color=C['NEUTRAL'],label='40–60%  Neutral'),
            mpatches.Patch(color=C['BEARISH'],label='<40%  Bearish'),
        ],loc='lower right',facecolor='white',edgecolor=C['border'],labelcolor=C['text'],fontsize=8.5)
        plt.savefig('dashboard_breadth.png',dpi=150,bbox_inches='tight',facecolor=C['bg'],edgecolor='none')
        plt.show(); print('✅ dashboard_breadth.png saved')
    
    plot_breadth_dashboard()
    
    
    # ── CELL 10 ──────────────────────────────────────
    # ── CELL 10: Text Summary ────────────────────────────────────────────────────
    
    def print_summary():
        sep='='*72; thin='─'*60; vd=verdict; bd=ind_breadth['detail']
        print(sep)
        print(f'  🇮🇳  INDIAN MARKET HEALTH DASHBOARD   |   {datetime.now().strftime("%A, %d %B %Y — %I:%M %p")}')
        print(f'  Universe: {len(ALL_TICKERS)} stocks fetched live  |  Prices loaded: {prices_df.shape[1]}')
        print(f'  FII source: {fii_source_label or "unavailable"}')
        print(sep)
        print(f"\n  HEALTH SCORE : {vd['score']:.1f} / 10")
        print(f"  VERDICT      : {vd['verdict']}")
        print(f"  DETAIL       : {vd['v_sub']}")
        print(f"\n  Signals → 🟢 {vd['bullish']} Bullish  · 🟡 {vd['neutral']} Neutral  · 🔴 {vd['bearish']} Bearish")
        print(f'\n{sep}'); print('  INDICATOR BREAKDOWN'); print(sep)
        for i,ind in enumerate(INDICATORS,1):
            print(f"\n  [{i}] {ind['name']}")
            print(f'  {thin}')
            print(f"  Signal  : {sem(ind['signal'])}  {ind['signal']}")
            print(f"  Analysis: {ind['reason']}")
            if 'n5' in ind.get('detail',{}):
                fd=ind['detail']
                print(f"  FII     :  5d Rs{fd['n5']:+,.0f} Cr  |  10d Rs{fd['n10']:+,.0f} Cr  |  20d Rs{fd['n20']:+,.0f} Cr")
            print(f"  Weight  : {ind['weight']}/3  |  Source: {ind['source'][:72]}")
        print(f'\n{sep}'); print('  BREADTH BY CAP SEGMENT'); print(sep)
        print(f"  {'Segment':<28} {'>200 DMA':>10} {'>50 DMA':>10} {'Stocks':>8} {'Signal':>10}")
        for seg in SEGMENT_ORDER:
            d=bd.get('seg_data',{}).get(seg,{})
            if not d or d.get('count',0)==0: continue
            sg='🟢 BULL' if d['pct200']>=60 else('🟡 NEUT' if d['pct200']>=40 else'🔴 BEAR')
            print(f"  {SEGMENT_LABELS[seg]:<28} {d['pct200']:>9.0f}% {d['pct50']:>9.0f}% {d['count']:>8} {sg}")
        print(f'\n{sep}'); print('  BREADTH BY SECTOR (strongest → weakest)'); print(sep)
        print(f"  {'Sector':<30} {'>200 DMA':>10} {'Stocks':>8} {'Signal':>10}")
        srt=sorted(bd.get('sector_data',{}).items(),key=lambda x:x[1]['pct200'],reverse=True)
        for sec,d in srt:
            if d.get('count',0)==0: continue
            sg='🟢 BULL' if d['pct200']>=60 else('🟡 NEUT' if d['pct200']>=40 else'🔴 BEAR')
            print(f"  {sec:<30} {d['pct200']:>9.0f}% {d['count']:>8} {sg}")
        print(f'\n{sep}'); print('  TRADING GUIDANCE'); print(sep)
        sc=vd['score']
        if sc>=6.5:   print('  ✅ GREEN  — Market favours longs. Normal position sizing.')
        elif sc>=4.5: print('  ⚠️  YELLOW — Select setups only. Cut size 30-50%. Tighter stops.')
        else:         print('  🚫 RED    — Avoid new longs. Cash/hedge. Wait for breadth + VIX to improve.')
        if srt:
            top3=[s for s,d in srt[:3] if d.get('count',0)>0]
            bot3=[s for s,d in reversed(srt[-3:]) if d.get('count',0)>0]
            print(f'\n  📈 Strongest: {", ".join(top3)}')
            print(f'  📉 Weakest  : {", ".join(bot3)}')
        print(f'\n{sep}\n')
    
    print_summary()
    
    run_ok = True
    print("\n✅  All cells completed.")
except Exception as e:
    print(f"\n❌  Failed: {e}"); traceback.print_exc()

today = datetime.now().strftime("%A, %d %b %Y")
if run_ok:
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
            f"<b>Score:</b> {verdict['score']:.1f}/10  |  <b>Verdict:</b> {verdict['verdict']}{fii_ln}\n"
            f"━"*25+"\n{ind_ln}"
            f"━"*25+"\n"
            f"Universe: {len(ALL_TICKERS)} stocks  |  FII: {fii_source_label or 'n/a'}"
        )
    except Exception as e:
        msg = f"🇮🇳 <b>Morning Dashboard — {today}</b>\nCompleted — see images."; print(e)
    tg_msg(msg)
    for img, cap in [("dashboard_main.png",f"📊 Main — {today}"),
                     ("dashboard_breadth.png",f"📈 Breadth — {today}")]:
        if os.path.exists(img): tg_photo(img, cap)
        else: print(f"  ⚠️ {img} not found")
else:
    tg_msg(f"⚠️ <b>Morning Dashboard — {today}</b>\nRun failed. Check GitHub Actions logs.")

print("\n✅  Done.")
