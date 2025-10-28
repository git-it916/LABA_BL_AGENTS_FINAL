import re
import numpy as np
import pandas as pd
from pathlib import Path

input_path  = Path(r"C:\Users\shins\OneDrive\문서\final_stock_months.csv")
output_path = Path(r"C:\Users\shins\OneDrive\문서\sector_cap_weighted_returns_rounded.csv")

# ---------- 0) 안전 로드 ----------
def safe_read_csv(path: Path, encodings=("cp949","utf-8","utf-8-sig")) -> pd.DataFrame:
    last_err = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_err = e
    raise last_err

df = safe_read_csv(input_path)
df.columns = [c.strip().lower() for c in df.columns]

# ---------- 1) 숫자 문자열 클리너 ----------
def clean_numeric(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()

    # 빈값/대시 처리
    s = s.replace({"": np.nan, "-": np.nan, "–": np.nan, "—": np.nan})

    # 괄호 음수 처리: (123.4) -> -123.4
    neg_mask = s.str.match(r"^\(\s*.*\s*\)$", na=False)
    s = s.str.replace(r"^\(|\)$", "", regex=True)  # 괄호 제거
    s = s.where(~neg_mask, "-" + s.where(neg_mask, s))  # 음수 부호 추가

    # 통화/퍼센트/기호 제거
    s = s.str.replace(r"[,\s\$₩€£%]", "", regex=True)

    # 남은 숫자/소수점/부호만 유지(이외 제거)
    s = s.str.replace(r"[^0-9\.\-eE+]", "", regex=True)

    return pd.to_numeric(s, errors="coerce")

# ---------- 2) 컬럼 매핑 ----------
sp500_col  = "sp500"
cyear_col  = "cyear"
cmonth_col = "cmonth"
gsector_col= "gsector"
mcap_col   = "mthcap"   # 월말 시가총액
ret_col    = "mthret"   # 월간 수익률

# ---------- 3) 타입 강제: 문자열 숫자 정리 ----------
# 연/월/플래그 중 문자열이 있었으므로
for col in [sp500_col, cyear_col, cmonth_col]:
    df[col] = clean_numeric(df[col]).astype("Int64")  # 정수형(결측 허용)

# 시총/수익률 숫자화
df[mcap_col] = clean_numeric(df[mcap_col]).astype(float)
df[ret_col]  = clean_numeric(df[ret_col]).astype(float)

# ---------- 4) S&P500 == 1 필터 ----------
df_sp = df[df[sp500_col] == 1].copy()

# ---------- 5) 가중수익률 계산 ----------
df_sp["_ret_x_cap"] = df_sp[ret_col] * df_sp[mcap_col]

group_keys = [cyear_col, cmonth_col, gsector_col]
agg = (
    df_sp.groupby(group_keys, dropna=False)
        .agg(total_mktcap=(mcap_col, "sum"),
            ret_x_cap_sum=("_ret_x_cap", "sum"),
            n_stocks=("ticker", "count"))
        .reset_index()
)

# 분모 0 방지
agg["cap_weighted_return"] = np.where(
    agg["total_mktcap"] != 0,
    agg["ret_x_cap_sum"] / agg["total_mktcap"],
    np.nan
)

# 중간열 제거
agg = agg.drop(columns=["ret_x_cap_sum"])

# ---------- 6) 형식(반올림 & 정수 변환) ----------
# total_mktcap → 정수
agg["total_mktcap"] = agg["total_mktcap"].round(0).astype("Int64")  # 결측 허용 정수형
# cap_weighted_return → 소수점 5자리 반올림
agg["cap_weighted_return"] = agg["cap_weighted_return"].astype(float).round(5)

# 보기 좋게 정렬
result = agg.sort_values(group_keys).reset_index(drop=True)


# 저장 to database
output_dir = Path("database")
output_dir.mkdir(parents=True, exist_ok=True)  # 폴더 없으면 자동 생성

# 저장 파일 경로 지정
output_path = output_dir / "filtered_sp500_data.parquet"

# parquet 파일로 저장 (float_format 옵션은 CSV에만 적용되므로 제외)
result.to_parquet(output_path, index=False, engine="pyarrow")

print(f"✅ Parquet 저장 완료: {output_path.resolve()}")

