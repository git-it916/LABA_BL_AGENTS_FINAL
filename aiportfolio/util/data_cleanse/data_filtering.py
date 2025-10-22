import pandas as pd
import os
from pathlib import Path
# 1. 경로 설정 - 신승훈
crsp_file_path = r"C:\Users\shins\OneDrive\문서\CRSP 2015.01-2024.12.csv"
mrge_file_path = r"C:\Users\shins\OneDrive\문서\sp500_ticker_start_end.csv"
output_path = r"C:\Users\shins\OneDrive\문서\merged_sp500.csv"
final_path = r"C:\Users\shins\OneDrive\문서\merged_final_nonGICS.csv"
final2_path = r"C:\Users\shins\OneDrive\문서\merged_final_GICS.csv"

# 2. 데이터 불러오기
print("데이터를 불러오는 중입니다...")
crsp_df = pd.read_csv(crsp_file_path, encoding='cp949')
sp500_df = pd.read_csv(mrge_file_path, encoding='cp949')
print("데이터 로딩 완료.")

# 3. 필터링할 Ticker 목록 지정
tickers = ["A","AABA","AAL","AAL","AAMRQ","AAP","AAPL","ABBV","ABC","ABI","ABKFQ","ABMD","ABNB","ABS","ABT","ABX","ACAS","ACGL","ACKH","ACN","ACS","ACV","ADBE","ADCT","ADI","ADM","ADP","ADS","ADSK","ADT","AEE","AEP","AES","AET","AFL","AFS.A","AGC","AGN","AHM","AIG","AIT","AIV","AIZ","AJG","AKAM","AKS","AL","ALB","ALGN","ALK","ALL","ALLE","ALTR","ALXN","AM","AMAT","AMCC","AMCR","AMD","AMD","AME","AMG","AMGN","AMH","AMP","AMP","AMT","AMTM","AMZN","AN","AN","ANDV","ANDW","ANET","ANF","ANRZQ","ANSS","ANTM","ANV","AON","AOS","APA","APC","APCC","APD","APH","APO","APOL","APTV","AR","ARC","ARE","ARG","ARNC","AS","ASC","ASH","ASN","ASND","ASO","AT","ATGE","ATI","ATO","ATVI","AV","AVB","AVGO","AVP","AVY","AW","AWE","AWK","AXON","AXP","AYE","AYI","AZA.A","AZO","BA","BAC","BALL","BAX","BAY","BBBY","BBI","BBT","BBWI","BBY","BC","BCO","BCR","BDK","BDX","BEAM","BEN","BEV","BF.B","BFI","BFO","BG","BGEN","BGG","BHF","BHGE","BHMSQ","BIG","BIIB","BIO","BJS","BK","BKB","BKNG","BKR","BLDR","BLK","BLL","BLS","BLY","BMC","BMET","BMGCA","BMS","BMY","BNI","BNL","BOAT","BOL","BR","BR","BRCM","BRK.B","BRL","BRO","BSC","BSX","BT","BTUUQ","BUD","BVSN","BWA","BX","BXLT","BXP","C","CA","CAG","CAH","CAL","CAM","CAR","CARR","CAT","CB","CBB","CBE","CBE","CBH","CBOE","CBRE","CBS","CBSS","CCB","CCE","CCEP","CCI","CCI","CCK","CCL","CCTYQ","CCU","CDAY","CDNS","CDW","CE","CE","CEG","CEG","CELG","CEN","CEPH","CERN","CF","CF","CFC","CFG","CFL","CFN","CG","CGP","CHA","CHD","CHIR","CHK","CHRS","CHRW","CHTR","CI","CIEN","CIN","CINF","CIT.A","CITGQ","CL","CLF","CLX","CMA","CMB","CMCSA","CMCSK","CME","CMG","CMI","CMS","CMVT","CMX","CNC","CNC","CNG","CNP","CNW","CNX","CNXT","COC.B","COF","COG","COIN","COL","COMS","COO","COP","COR","COST","COTY","COV","COV","COV","CPAY","CPB","CPGX","CPNLQ","CPQ","CPRI","CPRT","CPT","CPWR","CR","CRL","CRM","CRR","CRWD","CSCO","CSE","CSGP","CSR","CSRA","CSX","CTAS","CTB","CTL","CTLT","CTRA","CTSH","CTVA","CTX","CTXS","CVC","CVG","CVH","CVS","CVX","CXO","CYM","CYR","CZR","D","DAL","DALRQ","DASH","DAY","DCNAQ","DD","DD","DDOG","DDR","DDS","DE","DEC","DECK","DELL","DELL","DF","DFS","DG","DG","DGN","DGX","DHI","DHR","DI","DIGI","DIS","DISCA","DISCK","DISH","DJ","DLR","DLTR","DLX","DNB","DNR","DO","DOC","DOV","DOW","DOW","DPHIQ","DPZ","DRE","DRI","DTE","DTV","DUK","DVA","DVN","DWD","DWDP","DXC","DXC","DXCM","DYN","EA","EBAY","EC","ECH","ECL","ECO","ED","EDS","EFU","EFX","EG","EHC","EIX","EKDKQ","EL","ELV","EMC","EMN","EMR","ENDP","ENPH","ENRNQ","ENS","EOG","EOP","EP","EPAM","EQ","EQIX","EQR","EQT","EQT","ERIE","ES","ESRX","ESS","ESV","ESV","ETFC","ETN","ETR","ETS","ETSY","EVHC","EVRG","EW","EXC","EXE","EXPD","EXPE","EXR","F","FANG","FAST","FB","FBF","FBHS","FBO","FCN","FCPT","FCX","FDC","FDO","FDS","FDX","FE","FFIV","FG","FHN","FI","FICO","FII","FIS","FISV","FITB","FJ","FL","FL","FLIR","FLMIQ","FLR","FLS","FLT","FLTWQ","FMC","FMC","FMCC","FMY","FNMA","FOSL","FOX","FOXA","FPC","FRC","FRO","FRT","FRX","FSH","FSL","FSLR","FSLR","FTI","FTL.A","FTNT","FTR","FTV","FWLT","G","GAPTQ","GAS","GAS","GD","GDDY","GDT","GDW","GE","GEHC","GEN","GENZ","GEV","GFS.A","GGP","GGP","GHC","GIDL","GILD","GIS","GL","GLD","GLK","GLW","GM","GMCR","GME","GNRC","GNT","GNW","GOOG","GOOGL","GP","GPC","GPN","GPS","GPU","GR","GRA","GRMN","GRN","GS","GSX","GT","GTE","GTW","GWF","GWW","GX","H","H","HAL","HAR","HAS","HBAN","HBI","HBOC","HCA","HCA","HCBK","HCP","HCR","HD","HDLM","HES","HET","HFC","HFS","HI","HIG","HII","HLT","HLT","HM","HMA","HNZ","HOG","HOLX","HON","HOT","HP","HP","HPC","HPE","HPH","HPQ","HRB","HRL","HRS","HRS","HSH","HSIC","HSP","HST","HSY","HUBB","HUM","HWM","I","IAC","IBM","ICE","IDXX","IEX","IFF","IGT","IKN","ILMN","IMNX","INCLF","INCY","INFO","INGR","INTC","INTU","INVH","IP","IPG","IPGP","IQV","IR","IR","IRM","ISRG","IT","ITT","ITW","IVZ","J","JAVA","JBHT","JBL","JBL","JCI","JCP","JEC","JEF","JH","JHF","JKHY","JNJ","JNPR","JNS","JNY","JOS","JOY","JP","JPM","JWN","K","KATE","KBH","KDP","KDP","KEY","KEYS","KG","KHC","KIM","KKR","KLAC","KM","KMB","KMG","KMI","KMI","KMX","KO","KORS","KR","KRB","KRFT","KRI","KSE","KSS","KSU","KSU","KVUE","KWP","L","LB","LDG","LDOS","LDOS","LDW.B","LEG","LEHMQ","LEN","LH","LHX","LIFE","LII","LIN","LKQ","LLL","LLTC","LLX","LLY","LM","LMT","LNC","LNT","LO","LOR","LOW","LPX","LRCX","LSI","LU","LUB","LULU","LUMN","LUV","LVLT","LVS","LW","LXK","LYB","LYV","M","MA","MAA","MAC","MAR","MAS","MAT","MAY","MBI","MCD","MCHP","MCIC","MCK","MCO","MD","MDLZ","MDP","MDR","MDT","MEA","MEDI","MEE","MEE","MEL","MER","MERQ","MET","META","MFE","MGM","MHK","MHS","MI","MII","MIL","MIR","MIR","MJN","MKC","MKG","MKTX","MLM","MMC","MMI","MMM","MNK","MNR","MNST","MO","MOB","MOH","MOLX","MON","MOS","MPC","MPWR","MRK","MRNA","MRO","MS","MSCI","MSFT","MSI","MST","MTB","MTCH","MTD","MTG","MTL","MTLQQ","MTW","MU","MUR","MWI","MWV","MWW","MXIM","MXIM","MYG","MYL","MZIAQ","NAE","NAV","NAVI","NBL","NBR","NC","NCC","NCE","NCLH","NCR","NDAQ","NDSN","NE","NE","NEE","NEM","NFB","NFLX","NFX","NGH","NI","NKE","NKTR","NLC","NLOK","NLSN","NLV","NMK","NOC","NOV","NOVL","NOW","NRG","NRTLQ","NSC","NSI","NSM","NTAP","NTRS","NUE","NVDA","NVLS","NVR","NWL","NWS","NWSA","NXPI","NXTL","NYN","NYT","NYX","O","OAT","ODFL","ODP","OGN","OI","OI","OK","OKE","OKE","OM","OMC","OMX","ON","ONE","ORCL","ORLY","ORX","OTIS","OWENQ","OXY","PAC","PALM","PANW","PARA","PAS","PAYC","PAYX","PBCT","PBG","PBI","PBY","PCAR","PCG","PCG","PCH","PCL","PCP","PCS","PD","PDCO","PDG","PEAK","PEG","PEL","PENN","PEP","PET","PETM","PFE","PFG","PG","PGL","PGN","PGR","PH","PHA","PHB","PHM","PKG","PKI","PLD","PLL","PLTR","PM","PMCS","PMI","PNC","PNR","PNU","PNW","PODD","POM","POOL","PPG","PPL","PPW","PRD","PRGO","PRU","PSA","PSFT","PSX","PTC","PTC","PTV","PVH","PVN","PVT","PWER","PWJ","PWR","PX","PXD","PYPL","PZE","Q","QCOM","QEP","QLGC","QRVO","QTRN","R","RAD","RAI","RAL","RATL","RBD","RBK","RCL","RDC","RDS.A","RE","REG","REGN","RF","RHI","RHT","RIG","RIG","RJF","RL","RLM","RMD","RML","RNB","ROH","ROK","ROL","ROP","ROST","RRC","RRD","RSG","RSHCQ","RTN","RTX","RVTY","RX","RYAN","RYC","RYI","S","SAF","SAI","SANM","SAPE","SB","SBAC","SBL","SBNY","SBUX","SCG","SCHW","SCI","SDS","SE","SEBL","SEDG","SEE","SEG","SFA","SFS","SGID","SGP","SHLD","SHN","SHW","SIAL","SIG","SII","SIVB","SJM","SK","SLB","SLG","SLM","SLR","SMCI","SMI","SMS","SNA","SNDK","SNI","SNPS","SNT","SNV","SO","SOLV","SOTR","SOV","SPG","SPGI","SPLS","SRCL","SRE","SRR","SSP","STE","STI","STJ","STLD","STO","STR","STT","STX","STZ","SUB","SUN","SUNEQ","SVU","SW","SWK","SWKS","SWN","SWY","SXCL","SYF","SYK","SYMC","SYY","T","TA","TAP","TCOMA","TDC","TDG","TDM","TDY","TE","TECH","TEG","TEK","TEL","TEL","TEN","TER","TER","TEX","TFC","TFX","TGNA","TGT","THC","THY","TIE","TIF","TIN","TJX","TKO","TKR","TLAB","TMC","TMC.A","TMK","TMO","TMUS","TMUS","TNB","TOS","TOY","TPL","TPR","TRB","TRGP","TRIP","TRMB","TROW","TRV","TRW","TSCO","TSG","TSLA","TSN","TSS","TT","TT","TTWO","TUP","TWC","TWTR","TWX","TX","TXN","TXT","TXU","TYL","UA","UAA","UAL","UAWGQ","UBER","UCC","UCL","UCM","UDR","UHS","UIS","UK","ULTA","UMG","UN","UNH","UNM","UNP","UPC","UPR","UPS","URBN","URI","USB","USBC","USH","USHC","USS","UST","USW","UTX","UVN","V","VAR","VAT","VFC","VIAB","VIAC","VIAV","VICI","VLO","VLTO","VMC","VNO","VNT","VO","VRSK","VRSN","VRTS","VRTX","VST","VSTNQ","VTR","VTRS","VTSS","VZ","WAB","WAI","WAMUQ","WAT","WB","WBA","WBD","WCG","WCOEQ","WDAY","WDC","WEC","WELL","WEN","WFC","WFM","WFT","WHR","WIN","WLA","WLL","WLP","WLTW","WM","WMB","WMT","WMX","WNDXQ","WOR","WPX","WRB","WRK","WSM","WST","WTW","WU","WWY","WY","WYE","WYND","WYNN","X","XEC","XEL","XL","XLNX","XOM","XRAY","XRX","XTO","XYL","YNR","YRCW","YUM","ZBH","ZBRA","ZION","ZTS"]

# 4. CRSP 데이터 필터링
print("Ticker 목록을 기준으로 CRSP 데이터를 필터링합니다...")
filtered_df = crsp_df[crsp_df["TICKER"].isin(tickers)]
print("필터링 완료.")

# 5. 병합
print("필터링된 데이터와 S&P 500 데이터를 병합합니다...")
merged_df = pd.merge(filtered_df, sp500_df, left_on="TICKER", right_on="ticker", how="inner")
print("병합 완료.")

# 6. 날짜형으로 변환
for col in ["date", "start_date", "end_date"]:
    if col in merged_df.columns:
        merged_df[col] = pd.to_datetime(merged_df[col], errors="coerce")

# 7. 조건 필터링 수행 (조건 중요함!!)
print("날짜 조건(start_date <= date <= end_date)에 맞지 않는 행을 제거합니다...")
# (1) start_date가 존재하고 date보다 작으면 False
cond_start = (merged_df["start_date"].isna()) | (merged_df["date"] >= merged_df["start_date"])
# (2) end_date가 존재하고 date보다 크면 False
cond_end = (merged_df["end_date"].isna()) | (merged_df["date"] <= merged_df["end_date"])
# and 조건 결합
filtered_final_df = merged_df[cond_start & cond_end]

# 8. 결과 저장
filtered_final_df.to_csv(final_path, index=False, encoding="utf-8-sig")
print(f"\n✅ 필터링 완료! 최종 데이터가 아래 경로에 저장되었습니다:\n{final_path}")
print(f"총 {len(filtered_final_df):,}행 남음 (원본 {len(merged_df):,}행 중)")

save_dir = Path("database")
save_dir.mkdir(parents=True, exist_ok=True)  # 폴더 없으면 자동 생성



filtered_final_GICS.df = merged_df[cond_start & cond_end & (merged_df["GICS Sector"].notna())]

parquet_path = save_dir / "filtered_sp500_data.parquet"
filtered_final_GICS_df.to_parquet(parquet_path, index=False)