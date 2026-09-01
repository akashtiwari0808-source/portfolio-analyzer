📈 Quantitative Portfolio Analyzer



A professional-grade, automated portfolio analysis tool built in Python. This script takes a user's stock portfolio, fetches historical and real-time market data, and evaluates each holding using a combination of Fundamental and Technical analysis. It outputs a comprehensive, color-coded HTML dashboard, PDF report, and Excel/CSV sheets.



📸 Screenshots



<img width="1889" height="908" alt="{E774B885-35B9-4B54-B0ED-46640915BA46}" src="https://github.com/user-attachments/assets/3860faf4-d039-428a-bb2a-e46f0ff678c6" />




Interactive HTML Dashboard



Auto-Generated Technical Charts



🚀 Features



Multi-Format Data Input: Accepts CSV, Excel, JSON, or direct Python dictionary inputs.



Fundamental Scoring (0-100): Evaluates P/E, P/B, ROE, Debt-to-Equity, and Dividend Yield.



Technical Scoring (0-100): Analyzes Trend (20/50/200 DMA), Momentum (RSI), and MACD crossovers.



Timeframe Projections: Automatically generates quantitative outlooks for Short-term (1-4 weeks), Mid-term (1-6 months), and Long-term (1+ years).



Automated Charting: Generates PNG line charts with moving averages for every stock in the portfolio.



Risk Flags: Flags overvalued stocks, high debt, or bearish technical setups (e.g., "Trading below 200 DMA").



Multi-Format Export: Generates reports in HTML (styled with CSS), PDF, Excel, and CSV.



Resilient API Handling: Bypasses missing data or Yahoo Finance API server errors gracefully without crashing.



🛠️ Tech Stack



Language: Python 3



Data Manipulation: pandas, numpy



Market Data: yfinance



Technical Indicators: pandas\_ta



Data Visualization: matplotlib



Report Generation: reportlab (PDF), openpyxl (Excel)



💻 Installation \& Setup



1\. Clone the repository:



git clone https://github.com/akashtiwari0808-source/portfolio-analyzer.git

cd portfolio-analyzer





2\. Create a virtual environment (Recommended):



python -m venv venv

\# On Windows:

venv\\Scripts\\activate

\# On Mac/Linux:

source venv/bin/activate





3\. Install dependencies:




pip install -r requirements.txt




📊 Usage



1\. Prepare your portfolio data:

Update the portfolio\_input.csv file with your holdings. Note: For Indian/NSE stocks, ensure you append .NS to the ticker (e.g., ITC.NS).



symbol,quantity,average\_buy\_price,sector

ITC.NS,100,400.00,FMCG

M\&M.NS,50,1500.00,Auto

LT.NS,30,2800.00,Infrastructure

HDFCBANK.NS,100,1400.00,Banking





2\. Run the analyzer:



python portfolio\_analyzer.py





3\. View your reports:

Check the outputs/ folder for your HTML, PDF, Excel, and CSV reports. Check the charts/ folder for technical PNG charts.



📁 Folder Structure



portfolio\_analyzer/

│

├── portfolio\_analyzer.py      # Core analysis engine

├── portfolio\_input.csv        # User input file

├── README.md                  # Project documentation

├── .gitignore                 # Ignored files

├── outputs/                   # Generated reports (HTML, PDF, XLSX, CSV)

└── charts/                    # Generated moving average charts (PNG)





🤝 Contributing



Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.



📬 Contact



Your Name: Akash Tiwari



GitHub: @akashtiwari0808-source



LinkedIn: www.linkedin.com/in/akash-tiwari-28a0181b9




