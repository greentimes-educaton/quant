import numpy as np
import pandas as pd
import statsmodels
from statsmodels.tsa.stattools import coint
import matplotlib.pyplot as plt
import pandas_datareader.data as web
import seaborn
import statsmodels.formula.api as sm
from datetime import datetime, timedelta


data = pd.read_csv('AUDUSD_NZDUSD.csv', index_col=0, parse_dates=True)
data = data['2017']




s1 = data['AUDUSD']
s2 = data['NZDUSD']

# CADF
resutl, pvalue, _ = coint(s2, s1)


plt.figure()
plt.scatter(s1, s2)

ratios = pd.DataFrame(index=data.index, columns=['b'])

# compute spread
lookback = 20

for t in data.index:
    if t < data.index[0] + timedelta(minutes=lookback):
        continue
    ols_result = sm.ols('AUDUSD ~ NZDUSD', data=data[t-timedelta(days=lookback):t]).fit()
    ratios.loc[t] = ols_result.params['NZDUSD']
    print(ols_result.params['NZDUSD'])

#fix bug: TODO find better solution
ratios = ratios['b']

plt.figure()
ratios.plot()


spread = s1 - ratios*s2
zscore = (spread-spread.rolling(lookback).mean())/spread.rolling(lookback).std()

plt.figure()
zscore.plot()

money = 0
profit = pd.DataFrame(index=zscore.index, columns=['return'])
profit = profit['return']
profit['return'] = 0
prev_money = 0
q = 1000
invested = False
countS1 = 0
countS2 = 0

z_entry = 1.5
z_exit = 0.5

for i in zscore.index:
    # Sell short if the z-score is > 1
    if invested == False:
        if zscore[i] > z_entry:
            prev_money = money
            money += q*(s1[i] - s2[i] * ratios[i])
            countS1 -= 1
            countS2 += ratios[i]
            print('Selling Ratio %s %s %s %s'%(money, ratios[i], countS1,countS2))
            invested = True
        # Buy long if the z-score is < 1
        elif zscore[i] < -z_entry:
            prev_money = money
            money -= q*(s1[i] - s2[i] * ratios[i])
            countS1 += 1
            countS2 -= ratios[i]
            print('Buying Ratio %s %s %s %s'%(money,ratios[i], countS1,countS2))
            invested = True
    # Clear positions if the z-score between -.5 and .5
    elif invested == True and abs(zscore[i]) < z_exit:
        prev_money = money
        money += q*(s1[i] * countS1 + s2[i] * countS2)
        countS1 = 0
        countS2 = 0
        print('Exit pos %s %s %s %s'%(money,ratios[i], countS1,countS2))
        invested = False

if invested==True:
    money += q*(s1[i] * countS1 + s2[i] * countS2)