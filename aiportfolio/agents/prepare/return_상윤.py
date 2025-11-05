from aiportfolio.BL_MVO.prepare.preprocessing_수정중 import final

# python -m aiportfolio.agents.prepare.return

def indicator():
    a = final()
    print(a[a['date']=='2024-04-30']['sector_return'])

    return a

