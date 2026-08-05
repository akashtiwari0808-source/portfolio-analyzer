import os
import json
import warnings
from datetime import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Suppress pandas chained assignment warnings for clean output
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

class PortfolioAnalyzer:
    """
    A robust tool for analyzing stock portfolios using Fundamental and Technical analysis.
    Fetches real-time/historical data via yfinance and generates multi-format reports.
    """
    
    def __init__(self, data_source, output_dir="outputs", charts_dir="charts"):
        self.output_dir = output_dir
        self.charts_dir = charts_dir
        
        # Ensure output directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)
        
        self.portfolio_df = self._load_data(data_source)
        self.analysis_results = []
        self.portfolio_summary = {}

    def _load_data(self, data_source):
        """Loads portfolio data from CSV, Excel, JSON, or Python list of dicts."""
        if isinstance(data_source, str):
            ext = data_source.split('.')[-1].lower()
            if ext == 'csv':
                df = pd.read_csv(data_source)
            elif ext == 'xlsx':
                df = pd.read_excel(data_source)
            elif ext == 'json':
                df = pd.read_json(data_source)
            else:
                raise ValueError("Unsupported file format. Use CSV, Excel, or JSON.")
        elif isinstance(data_source, list):
            df = pd.DataFrame(data_source)
        else:
            raise ValueError("Invalid data source format.")
        
        # Ensure required columns exist
        required_cols = ['symbol', 'quantity', 'average_buy_price']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
                
        return df

    def fetch_market_data(self, symbol):
        """Fetches historical price data and fundamental info via yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            # Fetch 1 year of daily data for technical analysis
            hist = ticker.history(period="1y")
            info = ticker.info
            return hist, info
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None, None

    def analyze_fundamentals(self, info):
        """Calculates a fundamental score (0-100) based on key valuation metrics."""
        score = 0
        notes = []
        
        if not info:
            return 50, ["No fundamental data available"]

        # Market Cap
        mcap = info.get('marketCap', 0)
        
        # PE Ratio (Score up to 25)
        pe = info.get('trailingPE', None)
        if pe is not None and pe > 0:
            if pe < 15: score += 25
            elif pe < 25: score += 15
            elif pe < 40: score += 5
            if pe > 50: notes.append("High valuation (PE > 50)")
        
        # Price to Book (Score up to 20)
        pb = info.get('priceToBook', None)
        if pb is not None and pb > 0:
            if pb < 1.5: score += 20
            elif pb < 3: score += 10
            elif pb < 5: score += 5
            
        # Return on Equity (Score up to 25)
        roe = info.get('returnOnEquity', None)
        if roe is not None:
            if roe > 0.15: score += 25
            elif roe > 0.08: score += 15
            else: notes.append("Weak Return on Equity")
            
        # Debt to Equity (Score up to 20)
        debt_eq = info.get('debtToEquity', None)
        if debt_eq is not None:
            if debt_eq < 50: score += 20
            elif debt_eq < 100: score += 10
            else: notes.append("High debt levels")
            
        # Dividend Yield (Score up to 10)
        div = info.get('dividendYield', None)
        if div is not None and div > 0.02:
            score += 10

        return min(score, 100), notes

    def analyze_technicals(self, hist):
        """Calculates a technical score (0-100) using price trends and momentum."""
        score = 0
        notes = []
        
        if hist is None or hist.empty or len(hist) < 200:
            return 50, ["Insufficient historical data for technicals"]

        # Calculate Indicators using pandas_ta
        hist.ta.sma(length=20, append=True)
        hist.ta.sma(length=50, append=True)
        hist.ta.sma(length=200, append=True)
        hist.ta.rsi(length=14, append=True)
        hist.ta.macd(fast=12, slow=26, signal=9, append=True)
        
        latest = hist.iloc[-1]
        price = latest['Close']
        
        # Moving Averages Trend (Score up to 40)
        sma20 = latest.get('SMA_20', price)
        sma50 = latest.get('SMA_50', price)
        sma200 = latest.get('SMA_200', price)
        
        if price > sma20: score += 10
        if price > sma50: score += 10
        if price > sma200: score += 20
        else: notes.append("Trading below 200 DMA (Long-term downtrend)")
        
        # RSI Momentum (Score up to 30)
        rsi = latest.get('RSI_14', 50)
        if 40 <= rsi <= 60: score += 15
        elif 60 < rsi < 70: score += 30
        elif rsi >= 70: 
            score += 5
            notes.append("Overbought (RSI > 70)")
        elif rsi <= 30: 
            score += 20
            notes.append("Oversold (RSI < 30) - Potential bounce")
            
        # MACD (Score up to 30)
        macd = latest.get('MACD_12_26_9', 0)
        macd_sig = latest.get('MACDs_12_26_9', 0)
        if macd > macd_sig: 
            score += 30
        elif macd < macd_sig and macd > 0:
            score += 10
        else:
            notes.append("Bearish MACD crossover")
            
        return min(score, 100), notes

    def determine_recommendation(self, total_score):
        """Translates a 0-100 combined score into an actionable tag."""
        if total_score >= 80: return "Strong Buy"
        elif total_score >= 60: return "Buy"
        elif total_score >= 45: return "Hold"
        elif total_score >= 30: return "Weak"
        else: return "Avoid"

    def generate_timeframe_views(self, f_score, t_score, hist):
        """Generates Short, Mid, and Long term views based on quant data."""
        short_term, mid_term, long_term = "Neutral", "Neutral", "Neutral"
        
        # 1. Short & Mid Term Logic (Requires Technical Data)
        if hist is not None and not hist.empty and len(hist) >= 200:
            latest = hist.iloc[-1]
            price = latest['Close']
            sma20 = latest.get('SMA_20', price)
            sma50 = latest.get('SMA_50', price)
            sma200 = latest.get('SMA_200', price)
            rsi = latest.get('RSI_14', 50)
            macd = latest.get('MACD_12_26_9', 0)
            macd_sig = latest.get('MACDs_12_26_9', 0)

            # Short Term: Momentum
            if rsi >= 70:
                short_term = "Overbought (Caution)"
            elif rsi <= 30:
                short_term = "Oversold (Bounce possible)"
            elif price > sma20 and macd > macd_sig:
                short_term = "Bullish"
            elif price < sma20 and macd < macd_sig:
                short_term = "Bearish"

            # Mid Term: Trend & Moving Averages
            if price > sma50 and sma50 > sma200:
                mid_term = "Bullish (Uptrend)"
            elif price < sma50 and sma50 < sma200:
                mid_term = "Bearish (Downtrend)"
            elif t_score >= 60:
                mid_term = "Positive Bias"
            elif t_score <= 40:
                mid_term = "Negative Bias"

        # 2. Long Term Logic (Primarily Fundamental)
        if f_score >= 75:
            long_term = "Strong Accumulate"
        elif f_score >= 55:
            long_term = "Hold / SIP"
        elif f_score >= 40:
            long_term = "Hold"
        elif f_score < 30:
            long_term = "Exit / Avoid"
        else:
            long_term = "Weak Fundamentals"

        return short_term, mid_term, long_term

    def process_portfolio(self):
        """Iterates through portfolio, running full analysis on each holding."""
        print("Starting portfolio analysis. Fetching data...")
        total_invested = 0
        total_current_value = 0
        
        for index, row in self.portfolio_df.iterrows():
            symbol = row['symbol']
            qty = row['quantity']
            avg_price = row['average_buy_price']
            
            print(f"Analyzing {symbol}...")
            hist, info = self.fetch_market_data(symbol)
            
            # Use real-time price if available, else fallback
            current_price = hist['Close'].iloc[-1] if (hist is not None and not hist.empty) else avg_price
            
            f_score, f_notes = self.analyze_fundamentals(info)
            t_score, t_notes = self.analyze_technicals(hist)
            
            combined_score = (f_score * 0.5) + (t_score * 0.5)
            recommendation = self.determine_recommendation(combined_score)
            
            invested_amount = qty * avg_price
            current_val = qty * current_price
            pnl = current_val - invested_amount
            pnl_pct = (pnl / invested_amount) * 100 if invested_amount > 0 else 0
            
            # --- NEW: Generate Timeframe Views ---
            short_term, mid_term, long_term = self.generate_timeframe_views(f_score, t_score, hist)
            
            total_invested += invested_amount
            total_current_value += current_val
            
            # Save chart for the stock
            if hist is not None and not hist.empty:
                self._generate_chart(symbol, hist)
                
            self.analysis_results.append({
                'Symbol': symbol,
                'Quantity': qty,
                'Avg Buy Price': round(avg_price, 2),
                'Current Price': round(current_price, 2),
                'Invested': round(invested_amount, 2),
                'Current Value': round(current_val, 2),
                'P/L Amount': round(pnl, 2),
                'P/L %': round(pnl_pct, 2),
                'Fundamental Score': f_score,
                'Technical Score': t_score,
                'Combined Score': combined_score,     # RESTORED
                'Short-Term View': short_term,        # NEW
                'Mid-Term View': mid_term,            # NEW
                'Long-Term View': long_term,          # NEW
                'Recommendation': recommendation,     # RESTORED
                'Risk Flags': " | ".join(f_notes + t_notes) if (f_notes or t_notes) else "None"
            })
            
        # Calculate overall metrics
        overall_pnl = total_current_value - total_invested
        overall_pnl_pct = (overall_pnl / total_invested * 100) if total_invested > 0 else 0
        
        self.portfolio_summary = {
            'Total Invested': round(total_invested, 2),
            'Total Current Value': round(total_current_value, 2),
            'Total P/L': round(overall_pnl, 2),
            'Total P/L %': round(overall_pnl_pct, 2),
            'Average Portfolio Score': round(np.mean([x['Combined Score'] for x in self.analysis_results]), 2)
        }

    def _generate_chart(self, symbol, hist):
        """Generates a quick price & moving average chart and saves to disk."""
        plt.figure(figsize=(10, 5))
        plt.plot(hist.index, hist['Close'], label='Close Price')
        if 'SMA_50' in hist.columns: plt.plot(hist.index, hist['SMA_50'], label='50 DMA')
        if 'SMA_200' in hist.columns: plt.plot(hist.index, hist['SMA_200'], label='200 DMA')
        
        plt.title(f"{symbol} - 1 Year Price Trend")
        plt.legend()
        plt.grid(True, alpha=0.3)
        filepath = os.path.join(self.charts_dir, f"{symbol}_chart.png")
        plt.savefig(filepath, bbox_inches='tight')
        plt.close()

    def generate_reports(self):
        """Exports the analyzed data into Console, CSV, Excel, HTML, and PDF formats."""
        if not self.analysis_results:
            print("No data to generate report. Run process_portfolio() first.")
            return

        # THIS IS THE CRUCIAL LINE THAT WAS MISSING
        df_out = pd.DataFrame(self.analysis_results)
        
        # 1. Console Summary
        print("\n" + "="*50)
        print("PORTFOLIO SUMMARY REPORT")
        print("="*50)
        for k, v in self.portfolio_summary.items():
            print(f"{k}: {v}")
        print("-" * 50)
        print(df_out[['Symbol', 'P/L %', 'Combined Score', 'Recommendation']].to_string(index=False))
        print("="*50 + "\n")

        # 2. CSV Export
        df_out.to_csv(os.path.join(self.output_dir, "report.csv"), index=False)
        
        # 3. Excel Export
        df_out.to_excel(os.path.join(self.output_dir, "report.xlsx"), index=False)
        
        # --- PROFESSIONAL HTML EXPORT ---
        # 1. Format the summary metrics cleanly
        total_inv = float(self.portfolio_summary['Total Invested'])
        total_cur = float(self.portfolio_summary['Total Current Value'])
        total_pnl = float(self.portfolio_summary['Total P/L'])
        total_pnl_pct = float(self.portfolio_summary['Total P/L %'])
        avg_score = float(self.portfolio_summary['Average Portfolio Score'])

        pnl_color = "#28a745" if total_pnl >= 0 else "#dc3545"

        summary_html = f"""
        <div class="summary-container">
            <div class="metric-box">
                <div class="label">Total Invested</div>
                <div class="value">₹{total_inv:,.2f}</div>
            </div>
            <div class="metric-box">
                <div class="label">Current Value</div>
                <div class="value">₹{total_cur:,.2f}</div>
            </div>
            <div class="metric-box">
                <div class="label">Total P/L</div>
                <div class="value" style="color: {pnl_color};">₹{total_pnl:,.2f}</div>
            </div>
            <div class="metric-box">
                <div class="label">P/L %</div>
                <div class="value" style="color: {pnl_color};">{total_pnl_pct:.2f}%</div>
            </div>
            <div class="metric-box">
                <div class="label">Avg Portfolio Score</div>
                <div class="value">{avg_score:.2f} / 100</div>
            </div>
        </div>
        """

        # 2. Format the DataFrame for display
        df_display = df_out.copy()
        
        # Format currency columns
        curr_cols = ['Avg Buy Price', 'Current Price', 'Invested', 'Current Value', 'P/L Amount']
        for col in curr_cols:
            df_display[col] = df_display[col].apply(lambda x: f"₹{float(x):,.2f}")
            
        # Format percentage columns
        df_display['P/L %'] = df_display['P/L %'].apply(lambda x: f"{float(x):.2f}%")

        # 3. Inject CSS styling
        html_template = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; margin: 40px; }}
                h2, h3 {{ color: #1a365d; }}
                .summary-container {{ display: flex; gap: 20px; margin-bottom: 30px; }}
                .metric-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #1a365d; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                .label {{ font-size: 12px; text-transform: uppercase; color: #6c757d; font-weight: bold; margin-bottom: 5px; }}
                .value {{ font-size: 24px; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                th {{ background-color: #1a365d; color: white; padding: 12px; text-align: left; font-weight: 500; }}
                td {{ padding: 12px; border-bottom: 1px solid #dee2e6; }}
                tr:nth-child(even) {{ background-color: #f8f9fa; }}
                tr:hover {{ background-color: #e9ecef; }}
            </style>
        </head>
        <body>
            <h2>Quantitative Portfolio Analysis</h2>
            {summary_html}
            <h3>Holding Details</h3>
            {df_display.to_html(index=False, border=0, classes="dataframe", escape=False)}
        </body>
        </html>
        """

        with open(os.path.join(self.output_dir, "report.html"), "w", encoding="utf-8") as f:
            f.write(html_template)
            
        # 4. PDF Export using ReportLab
        self._generate_pdf(df_out)
        
        print(f"Reports successfully generated in the '{self.output_dir}' directory.")
        print(f"Charts saved in the '{self.charts_dir}' directory.")

    def _generate_pdf(self, df):
        """Generates a minimalist PDF report."""
        pdf_path = os.path.join(self.output_dir, "report.pdf")
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Portfolio Analysis Report")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, 720, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        
        y = 690
        for k, v in self.portfolio_summary.items():
            c.drawString(50, y, f"{k}: {v}")
            y -= 20
            
        c.setFont("Helvetica-Bold", 12)
        y -= 20
        c.drawString(50, y, "Holdings Summary (Top 10):")
        y -= 20
        
        c.setFont("Helvetica", 10)
        # Limit to top 10 for simple PDF text layout
        for idx, row in df.head(10).iterrows():
            text = f"{row['Symbol']} | P/L: {row['P/L %']}% | Score: {row['Combined Score']} | {row['Recommendation']}"
            c.drawString(50, y, text)
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
                
        c.save()

if __name__ == "__main__":
    # Point the analyzer directly to your CSV file
    analyzer = PortfolioAnalyzer(data_source="portfolio_input.csv")
    
    analyzer.process_portfolio()
    analyzer.generate_reports()