from pathlib import Path
import pandas as pd

# python database/csv_to_parquet.py

input_path  = Path("C:/Users/김상희/OneDrive/바탕 화면/final_stock_months.csv")
df = pd.read_csv(input_path)

# 저장 to database
output_dir = Path("database")
output_dir.mkdir(parents=True, exist_ok=True)  # 폴더 없으면 자동 생성

# 저장 파일 경로 지정
output_path = output_dir / "final_stock_months.parquet"

df.to_parquet(output_path, index=False, engine="pyarrow")

print(f"✅ Parquet 저장 완료: {output_path.resolve()}")