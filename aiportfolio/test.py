from .util.making_rollingdate import get_rolling_dates
from .util.save_log_as_json import save_performance_as_json
from aiportfolio.backtest.visualization import creating_plot
from aiportfolio.backtest.making_benchmark import BackTest
from aiportfolio.backtest.calculating_performance import calculating_performance

def test(forecast_period):
    forecast_period = forecast_period
    forecast_date = get_rolling_dates(forecast_period)

    results = []

    # 기간별 backtest 수행
    for i, period in enumerate(forecast_date):

        print(f"--- forecast_date: {period['forecast_date']} ---")
        start_date = period['start_date']
        end_date = period['end_date']
        
        backtest = BackTest(start_date=start_date, end_date=end_date)
        
        benchmark = backtest.prepare_benchmark()

        benchmark1 = backtest.calculating_performance(benchmark[0])
        benchmark2 = backtest.calculating_performance(benchmark[1])
        aiportfolio = backtest.calculating_performance(benchmark[2])
        
        # 결과 저장
        test_result = {
            "forecast_date": period['forecast_date'],
            "sector_benchmark1": benchmark[0]['SECTOR'].tolist(),
            "w_benchmark1": [f"{i * 100:.4f}%" for i in benchmark[0]['Weight']],
            "performance_benchmark1": benchmark1,
            "sector_benchmark2": benchmark[1]['SECTOR'].tolist(),
            "w_benchmark2": [f"{i * 100:.4f}%" for i in benchmark[1]['Weight']],
            "performance_benchmark2": benchmark2,
            "sector_aiportfolio": benchmark[2]['SECTOR'].tolist(),
            "w_aiportfolio": [f"{i * 100:.4f}%" for i in benchmark[2]['Weight']],
            "performance_aiportfolio": aiportfolio
        }
        results.append(test_result)

    save_performance_as_json(results)

    creating_plot(results=results)
    final = calculating_performance(results)
    
    return final