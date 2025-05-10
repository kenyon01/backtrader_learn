import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import backtrader as bt
import pandas as pd  # 添加 pandas 库
import matplotlib.pyplot as plt  # 添加 matplotlib 库

class MACDDiff(bt.Indicator):
    lines = ('macd_diff',)
    plotlines = {
        'macd_diff': {
            '_name': 'MACD Diff',
            'color': 'green',
            'ls': '',
            '_width': 1,
            '_method': 'bar'
        }
    }

    def __init__(self):
        macd = bt.indicators.MACD(self.data)
        self.lines.macd_diff = macd.macd - macd.signal

class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)
        # self.macd = bt.indicators.MACD(self.datas[0])
        self.macd = bt.indicators.MACDHisto(self.datas[0])
        self.macd_diff = MACDDiff(self.datas[0])  # 使用自定义MACD差值指标

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])

        if self.order:
            return

        # if not self.position:
        #     if self.dataclose[0] > self.sma[0]:
        #         self.log('BUY CREATE, %.2f' % self.dataclose[0])
        #         self.order = self.buy()
        # else:
        #     if self.dataclose[0] < self.sma[0]:
        #         self.log('SELL CREATE, %.2f' % self.dataclose[0])
        #         self.order = self.sell()

        if not self.position:
            # Calculate the 3-day average of the MACD histogram
            macd_hist_avg = sum(self.macd.histo.get(size=3)) / 3

            if self.macd.histo[0] > macd_hist_avg:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()
        else:
            # Calculate the 3-day average of the MACD histogram
            macd_hist_avg = sum(self.macd.histo.get(size=3)) / 3

            if self.macd.histo[0] < macd_hist_avg:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()
        # else:
        #     if (self.macd_diff[0] < self.macd_diff[-1]) and (self.dataclose[0] < self.dataclose[-1]):
        #         self.log('SELL CREATE, %.2f' % self.dataclose[0])
        #         self.order = self.sell()


        if self.macd.macd[0] > self.macd.signal[0]:
            self.log('MACD Crossover: BUY Signal')
        elif self.macd.macd[0] < self.macd.signal[0]:
            self.log('MACD Crossover: SELL Signal')

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, 'data/513050.csv')

    # 使用 pandas 读取 CSV 文件，并将时间列解析为 datetime 对象
    df = pd.read_csv(datapath, encoding='utf-8', parse_dates=['date'])
    df = df.dropna(subset=['date'])  # 删除日期列为空的行
    df['date'] = pd.to_datetime(df['date'], errors='coerce')  # 确保日期格式正确

    # 确保时间列的名称与 CSV 文件中的列名一致

    # 将 pandas DataFrame 转换为 backtrader 数据格式
    data = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2024, 1, 1),
        todate=datetime.datetime(2024, 12, 31),
        datetime=0,  # 确保这里的索引与 `date` 列的位置一致
        open=1,
        high=2,
        low=3,    
        close=4,
        volume=5

    )

    cerebro.adddata(data)
    cerebro.broker.setcash(1000000000.0)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    cerebro.broker.setcommission(commission=0.0)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot(style='candlestick', plotname='Test Strategy')
    # cerebro.plot(style='line', plotname='Test Strategy')
    # cerebro.plot(style='bar', plotname='Test Strategy')
    # cerebro.plot(style='candle', plotname='Test Strategy')
