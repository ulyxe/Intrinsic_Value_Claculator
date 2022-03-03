from quickfs import QuickFS
import os
import datetime as dt
import time
import pandas as pd
from credentials import Credentials as cd


# load the key from the environment variables
### api_key = os.environ['API_QUICKFS']

api_key = cd().api_key

client = QuickFS(api_key)

ticker = input("Insert ticker: ")
methods = ["eps", "cash", "dividends"]
method = methods[int(input("Select method (0=eps, 1=cash, 2=dividends): "))]

price = int(client.get_data_range(symbol=ticker, metric='price', period='TTM'))
shares = int(client.get_data_range(symbol=ticker, metric='shares_basic', period='TTM'))

# price = 100
metric = 0
tot_cash = 0
tot_liabilities = 0
# shares = 245060
stock_data = pd.DataFrame()


def gather_data(period):
    global metric
    global tot_cash
    global tot_liabilities
    if method == "eps":
        metric = int(client.get_data_range(symbol=ticker, metric='eps_basic', period=period))
        print(f"Earnings per share {period} = {metric}")
    elif method == "cash":
        # tot_cash = int(client.get_data_range(symbol=ticker, metric='cash_and_equiv', period=period))
        # tot_liabilities = int(client.get_data_range(symbol=ticker, metric='total_liabilities', period=period))
        metric = int(client.get_data_range(symbol=ticker, metric='fcf_per_share', period=period))
        print(f"FCF per share {period} = {metric}")
    elif method == "dividends":
        metric = int(client.get_data_range(symbol=ticker, metric='dividends', period=period))
        print(f"Dividend per share {period} = {metric}")


try:
    gather_data(period="TTM")
except TypeError:
    try:
        gather_data(period="FY")
    except TypeError:
        gather_data(period="FQ")

# tot_cash = 423371
# tot_liabilities = 233998
# metric = 421387
# metric = 12.8
# metric = 1.75
sum_intrinsic_value = 0

growth_rate_five = [0.05, 0.07, 0.0]
growth_rate_ten = [0.05, 0.07, 0.0]
terminal_multiple = [20, 30, 15]
discount_rate = 0.1
margin_of_safety = 0.25
probabilities = [0.6, 0.2, 0.2]

current_year = int(dt.datetime.today().strftime("%Y"))
year = current_year + 1

future_values = {
    "normal": {
        year: {
            method: metric * (1 + growth_rate_five[0]),
            "pv": 0
        }
    },
    "best": {
        year: {
            method: metric * (1 + growth_rate_five[1]),
            "pv": 0
        }
    },
    "worst": {
        year: {
            method: metric * (1 + growth_rate_five[2]),
            "pv": 0
        }
    }
}
for case in future_values:
    if method == "dividends":
        future_values[case][year]["pv"] = future_values[case][year][method] / (
                    (1 + discount_rate) ** (year - current_year))

j = 0

for case in future_values:
    for i in range(0, 9):
        year += 1
        if i < 4:
            new_metric_value = future_values[case][year - 1][method] * (1 + growth_rate_five[j])
        else:
            new_metric_value = future_values[case][year - 1][method] * (1 + growth_rate_ten[j])
        future_values[case][year] = {
            method: new_metric_value,
            "pv": 0
        }
        if method == "dividends":
            future_values[case][year]["pv"] = future_values[case][year][method] / (
                        (1 + discount_rate) ** (year - current_year))

    terminal_value = future_values[case][year - 1][method] * terminal_multiple[j]
    future_values[case]["terminal_value"] = {
        method: terminal_value,
        "pv": terminal_value * (1 + discount_rate) ** (-10)
    }
    future_values[case]["intrinsic_value"] = sum([value["pv"] for key, value in future_values[case].items()])
    print(future_values[case])
    intrinsic_value = round(future_values[case]['intrinsic_value'], 2)
    # if method == "cash":
    #     intrinsic_value += tot_cash + tot_liabilities
    #     intrinsic_value /= shares
    print(f"Intrinsic Value {case} case: {intrinsic_value} $")
    sum_intrinsic_value += intrinsic_value * probabilities[j]

    year = current_year + 1
    j += 1

price_comp = (price - round(sum_intrinsic_value, 2)) / price * 100
print(f"Final Intrinsic Value at {discount_rate * 100}% = {round(sum_intrinsic_value, 2)} $")
if price_comp > 0:
    print(f"Current Price = {price} $. Overvalued of {round(price_comp, 1)}%\n\n")
else:
    print(f"Current Price = {price} $. Undervalued of {round(price_comp, 1)}%\n\n")

resp = client.get_usage()
print(resp)
