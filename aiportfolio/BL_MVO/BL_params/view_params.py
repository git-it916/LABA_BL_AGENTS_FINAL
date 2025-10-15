# 우리가 만든 뷰
#  5개 비교군에 대한 애널리스트 4명의 '현재' 수익률 차이 전망치 (R_i,j)(상윤,승종,은서, 승훈 순)
'''
import numpy as np
current_forecasts = np.array([
    # IT>Fin, Disc>Stap, Health>Ind, Energy>Ind, Util>Fin / 이 기준대로
    [-0.03, 0.03, 0.035, 0.01],  # 뷰 1: IT vs Financials
    [0.02, 0.035, -0.02, 0.02],  # 뷰 2: Discretionary vs Staples
    [0.01, -0.015, -0.025, -0.01],  # 뷰 3: Healthcare vs Industrials
    [0.005, 0.04, 0.04, -0.008], # 뷰 4: Energy vs Industrials
    [0.02, -0.025, 0.015, -0.01]  # 뷰 5: Utilities vs Financials
])
'''
from aiportfolio.agents.generator import llamaAgent

agent = llamaAgent()
reply = agent.chat(
    "You are a short-term strategist (1-3 months horizon) with a moderately aggressive style. "
    "You aim to identify near-term opportunities using recent ExcessReturn patterns, "
    "but avoid making extreme or speculative bets.",

    f"Input data (sector monthly excess returns and market sizes):\n"
    f"{sector_table}\n\n"
    "Instructions:\n"
    "- Analyze short-term performance momentum among sectors.\n"
    "- Emphasize the speed and consistency of recent positive returns.\n"
    "- Be open to taking slightly higher-risk, high-beta sectors when justified by data.\n"
    "- Generate 3–5 relative views (lhs - rhs = expected excess return) based on near-term patterns.\n"
    "Return STRICT JSON only."
)

print(reply)
