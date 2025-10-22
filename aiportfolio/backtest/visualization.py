import pandas as pd
import matplotlib.pyplot as plt

def creating_plot(results):
    # 1. Convert the 'results' list into a pandas DataFrame.
    # This makes it easier to work with time-series data.
    df = pd.DataFrame(results)
    df['forecast_date'] = pd.to_datetime(df['forecast_date'])
    df.set_index('forecast_date', inplace=True)

    print(df)

    # 2. Calculate the cumulative return for each portfolio.
    # We assume 'performance' is the periodic return, so we calculate the cumulative product.
    df['cumulative_benchmark1'] = (1 + df['performance_benchmark1']).cumprod()
    df['cumulative_benchmark2'] = (1 + df['performance_benchmark2']).cumprod()
    df['cumulative_aiportfolio'] = (1 + df['performance_aiportfolio']).cumprod()

    # 3. Create the plot.
    plt.figure(figsize=(14, 8)) # Set the figure size for better readability.

    # Plot each portfolio's cumulative return.
    plt.plot(df.index, df['cumulative_benchmark1'], label='Benchmark 1', marker='o', linestyle='--')
    plt.plot(df.index, df['cumulative_benchmark2'], label='Benchmark 2', marker='x', linestyle=':')
    plt.plot(df.index, df['cumulative_aiportfolio'], label='AI Portfolio', marker='s', linestyle='-')

    # 4. Add labels, title, and other elements to make the chart clear.
    plt.title('Portfolio Cumulative Return Over Time', fontsize=20)
    plt.xlabel('Forecast Date', fontsize=14)
    plt.ylabel('Cumulative Return', fontsize=14)
    plt.legend(fontsize=12) # Add a legend to identify each line.
    plt.grid(True) # Add a grid for easier value reading.
    plt.xticks(rotation=45) # Rotate date labels to prevent overlap.
    plt.tight_layout() # Adjust plot to ensure everything fits without overlapping.

    # X축 눈금을 DataFrame의 인덱스(모든 날짜)로 설정합니다.
    ax = plt.gca()
    ax.set_xticks(df.index)
    # X축 레이블 포맷을 '년-월' 형태로 지정합니다.
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

    # 5. Display the generated plot.
    plt.show()

    return