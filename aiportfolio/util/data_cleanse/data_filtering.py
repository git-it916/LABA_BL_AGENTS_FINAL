import pandas as pd
import os
# --- 1. 파일 경로 설정 ---
# !!! 중요: 사용자 환경에 맞게 아래 파일 경로를 직접 수정해주세요.
crsp_file_path = r"C:\Users\shins\OneDrive\문서\CRSP 2015.01-2024.12.csv"
sp500_file_path = r"C:\Users\shins\OneDrive\문서\sp500.csv"
end_file_path = r"C:\Users\shins\OneDrive\문서\sp500_ticker_start_end.csv"
output_path = r"C:\Users\shins\OneDrive\문서\merged_sp500.csv" 
final_path = r"C:\Users\shins\OneDrive\문서\merged_final.csv"
final2_path = r"C:\Users\shins\OneDrive\문서\merged_final2.csv"

# --- 2. 데이터 불러오기 ---
print("데이터를 불러오는 중입니다...")
crsp_df = pd.read_csv(crsp_file_path, encoding='cp949')
sp500_df = pd.read_csv(sp500_file_path, encoding='cp949')
end_df = pd.read_csv(end_file_path, encoding='cp949')
print("데이터 로딩 완료.")

# --- 3. 필터링할 Ticker 목록 지정 ---
tickers = [ 
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A",
    "APD","ABNB","AKAM","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL",
    "GOOG","MO","AMZN","AMCR","AEE","AEP","AXP","AIG","AMT","AWK",
    "AMP","AME","AMGN","APH","ADI","ANSS","AON","APA","APO","AAPL",
    "AMAT","APTV","ACGL","ADM","ANET","AJG","AIZ","T","ATO","ADSK",
    "ADP","AZO","AVB","AVY","AXON","BKR","BALL","BAC","BAX","BDX",
    "BRK.B","BBY","TECH","BIIB","BLK","BX","BK","BA","BKNG","BSX",
    "BMY","AVGO","BR","BRO","BF.B","BLDR","BG","BXP","CHRW","CDNS",
    "CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CAT","CBOE",
    "CBRE","CDW","COR","CNC","CNP","CF","CRL","SCHW","CHTR","CVX",
    "CMG","CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX",
    "CME","CMS","KO","CTSH","COIN","CL","CMCSA","CAG","COP","ED",
    "STZ","CEG","COO","CPRT","GLW","CPAY","CTVA","CSGP","COST","CTRA",
    "CRWD","CCI","CSX","CMI","CVS","DHR","DRI","DDOG","DVA","DAY",
    "DECK","DE","DELL","DAL","DVN","DXCM","FANG","DLR","DG","DLTR",
    "D","DPZ","DASH","DOV","DOW","DHI","DTE","DUK","DD","EMN",
    "ETN","EBAY","ECL","EIX","EW","EA","ELV","EMR","ENPH","ETR",
    "EOG","EPAM","EQT","EFX","EQIX","EQR","ERIE","ESS","EL","EG",
    "EVRG","ES","EXC","EXE","EXPE","EXPD","EXR","XOM","FFIV","FDS",
    "FICO","FAST","FRT","FDX","FIS","FITB","FSLR","FE","FI","F",
    "FTNT","FTV","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC",
    "GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GPN","GL",
    "GDDY","GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES",
    "HPE","HLT","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUBB",
    "HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD",
    "INTC","ICE","IFF","IP","IPG","INTU","ISRG","IVZ","INVH","IQV",
    "IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM","K","KVUE",
    "KDP","KEY","KEYS","KMB","KIM","KMI","KKR","KLAC","KHC","KR",
    "LHX","LH","LRCX","LW","LVS","LDOS","LEN","LII","LLY","LIN",
    "LYV","LKQ","LMT","L","LOW","LULU","LYB","MTB","MPC","MKTX",
    "MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT",
    "MRK","META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA",
    "MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI",
    "MSCI","NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI",
    "NDSN","NSC","NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI",
    "ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR","PKG",
    "PLTR","PANW","PARA","PH","PAYX","PAYC","PYPL","PNR","PEP","PFE",
    "PCG","PM","PSX","PNW","PNC","POOL","PPG","PPL","PFG","PG",
    "PGR","PLD","PRU","PEG","PTC","PSA","PHM","PWR","QCOM","DGX",
    "RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY",
    "ROK","ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX",
    "SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO",
    "LUV","SWK","SBUX","STT","STLD","STE","SYK","SMCI","SYF","SNPS",
    "SYY","TMUS","TROW","TTWO","TPR","TRGP","TGT","TEL","TDY","TER",
    "TSLA","TXN","TPL","TXT","TMO","TJX","TKO","TSCO","TT","TDG",
    "TRV","TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP",
    "UAL","UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN","VRSK",
    "VZ","VRTX","VTRS","VICI","V","VST","VMC","WRB","GWW","WAB",
    "WBA","WMT","DIS","WBD","WM","WAT","WEC","WFC","WELL","WST",
    "WDC","WY","WSM","WMB","WTW","WDAY","WYNN","XEL","XYL","YUM",
    "ZBRA","ZBH","ZTS","FLIR", "HFC", "ALXN", "LB", "MXIM", "NOV", "UNM", "PRGO", "COG", "KSU",
    "LEG", "HBI", "WU", "WLTW", "GPS", "XLNX", "VIAC", "INFO", "PBCT", "DISCA",
    "DISCK", "BLL", "CERN", "FB", "IPGP", "UA", "UAA", "ANTM", "PENN", "PVH",
    "DRE", "CTXS", "NLSN", "TWTR", "NLOK", "FBHS", "ABMD", "VNO", "SIVB", "SBNY",
    "LUMN", "FRC", "PKI", "FISV", "RE", "DISH", "AAP", "ABC", "NWL", "LNC",
    "DXC", "ATVI", "OGN", "SEDG", "ALK", "SEE", "CDAY", "PEAK", "ZION", "WHR",
    "FLT", "VFC", "XRAY", "PXD", "ILMN", "CMA", "RHI", "WRK", "BIO", "ETSY",
    "AAL", "BBWI", "MRO", "QRVO", "AMTM", "CTLT", "FMC", "CE", "TFX", "BWA",
    "DFS", "JNPR"
]

# --- 4. CRSP 데이터 필터링 ---
print("Ticker 목록을 기준으로 CRSP 데이터를 필터링합니다...")
filtered_df = crsp_df[crsp_df["TICKER"].isin(tickers)]
print("필터링 완료.")
print(end_df.head())
# --- 5. 필터링된 데이터와 S&P 500 데이터 병합 ---
# `filtered_df`의 'TICKER' 열과 `sp500_df`의 'Symbol' 열을 기준으로 inner join 수행
print("필터링된 데이터와 S&P 500 데이터를 병합합니다...")
merged_df = pd.merge(filtered_df, sp500_df, left_on="TICKER", right_on="Symbol", how= "inner")
print("병합 완료.")

# --- 6. 최종 결과 저장 ---
# encoding='utf-8-sig' 옵션은 엑셀에서 한글 깨짐을 방지합니다.
merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"\n모든 작업 완료! 최종 결과 파일이 아래 경로에 저장되었습니다:\n{output_path}")

# --- 7. 필터링된 데이터와 end day 데이터 병합 ---
# `filtered_df`의 'TICKER' 열과 `sp500_df`의 'Symbol' 열을 기준으로 inner join 수행
print("필터링된 데이터와 S&P 500 데이터를 병합합니다...")
merged_df = pd.merge(merged_df, end_df, left_on="TICKER", right_on="ticker", how="inner")
print("병합 완료.")
print(merged_df.head())
# --- 8. 최종 결과 저장 ---
# encoding='utf-8-sig' 옵션은 엑셀에서 한글 깨짐을 방지합니다.
merged_df.to_csv(final_path, index=False, encoding='utf-8-sig')

print(f"\n모든 작업 완료! 최종 결과 파일이 아래 경로에 저장되었습니다:\n{final_path}")


cols = ["date", "Date added", "end_date"]

def to_yyyymmdd_int(series: pd.Series) -> pd.Series:
    s = series.copy()

    # 엑셀 일련번호(대부분 20000~60000 범위)만 있는 컬럼 탐지 후 변환
    if s.dropna().apply(lambda x: isinstance(x, (int, float))).all():
        # 숫자인데 엑셀 직렬일 가능성 높은 값만 남겨 체크
        non_na = s.dropna().astype(float)
        if not non_na.empty and non_na.between(20000, 60000).mean() > 0.8:
            dt = pd.to_datetime(s, unit="D", origin="1899-12-30", errors="coerce")
        else:
            dt = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
    else:
        dt = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)

    out = dt.dt.strftime("%Y%m%d")
    out = out.fillna("30000000").astype(int)
    return out

for c in cols:
    merged_df[c] = to_yyyymmdd_int(merged_df[c])

print(merged_df.head())

# --- 9. 잘못된 구간 제거 ---
# date < Date added 이거나 date > end_date 인 행 삭제
merged_df = merged_df[~((merged_df["date"] < merged_df["Date added"]) | 
                        (merged_df["date"] > merged_df["end_date"]))]

print("조건에 맞는 행 삭제 완료.")
print(merged_df.head())

# 변환된 데이터를 새 엑셀 파일로 저장
merged_df.to_excel("your_file_converted.xlsx", index=False)

# --- 10. (TICKER, date) 기준 중복 제거 ---
print("중복 제거 진행...(TICKER, date 기준)")
before = merged_df.shape[0]

# Date added 기준으로 최신 정보 유지
merged_df = (
    merged_df
    .sort_values(["TICKER", "date", "Date added"], na_position="last")
    .drop_duplicates(subset=["TICKER", "date"], keep="last")
    .reset_index(drop=True)
)

after = merged_df.shape[0]
print(f"중복 제거 완료. {before} -> {after} 행")

# (선택) 중복 제거본 저장
folder_name = "database"
file_name = "merged_final2.csv"
full_path = os.path.join(folder_name, file_name)

# (선택) CSV 파일로 저장 (파일명 수정 및 경로 지정)
merged_df.to_csv(full_path, index=False, encoding="utf-8-sig")

print(f"중복 제거본 저장 완료: {full_path}")