# (2022.02.27) Upbit용 Bitcoin 자동매매 Ver.R1
# (2022.02.27) K 기본값 0.6으로 수정
#              수수료 오류 수정 (0.05 -> 0.0005)

import time
import pyupbit
import datetime
import numpy as np

access_key = "lF01fmuy5mZKrhZhXvMDyTvBFYOWBlTt7YjKf7us"
secret_key = "7NxYSmNES4EYjjrvWbO91IojmkUx2woUInruZdmQ"

# 목표가 구하기
def get_target_price(ticker, k):  #ticker와 변동폭 상수를 받음
    
    # 전날과 오늘 일차트를 불러옴. 목표가 계산은 전날 대비 기준이므로 count가 2임
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    
    # iLoc -> dataframe에서 데이터에 접근하는 함수. 아래는 행별로 접근하도록 구현됨
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k

    return target_price #목표가 반환

#시작시간 조회, 업비트는 당일 오전 9시가 시작 시간임
def get_start_time(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

#잔고 조회
def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

#현재가 조회
def get_current_price(ticker):
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access_key, secret_key)
print("autotrade start")

# 수익률 계산기
def get_ror(dataFrame, k=0.6):

    df = dataFrame

    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.0005
    df['ror'] = np.where(df['high'] > df['target'], df['close'] / df['target'] - fee, 1.0)

    ror = df['ror'].cumprod()[-2]
    return ror

# 최적 상수 k 구하기
def get_best_k():

    df = pyupbit.get_ohlcv("KRW-BTC", count=14)

    rorList = []
    kList = []

    for k in np.arange(0.01, 1.00, 0.01):
        ror = get_ror(df, k)
        rorList.append(ror)
        kList.append(k)

    best_K = kList[rorList.index(max(rorList))]

    return best_K

# 자동매매 시작

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10): 
            target_price = get_target_price("KRW-BTC", k)
            ma15 = get_ma15("KRW-BTC")
            current_price = get_current_price("KRW-BTC")
            if target_price < current_price and ma15 < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-BTC", krw*0.9995)
        else:
            btc = get_balance("BTC")
            if btc > 0.00008:
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                k = get_best_k()     #전량 매도 후 k값 재계산
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)