import pandas as pd

df = pd.read_csv(r"C:\Users\shins\OneDrive\문서\final_stock_months.csv")
print(df['Ticker'].nunique())


# 3️⃣ 티커의 고유 개수 계산
unique_tickers = df['Ticker'].nunique()   # 컬럼명이 다르면 여기를 바꾸세요
print(f"티커의 고유 개수는 {unique_tickers}개입니다.")

# 4️⃣ (선택) 고유 티커 목록을 보고 싶다면:
print(df['Ticker'].unique())