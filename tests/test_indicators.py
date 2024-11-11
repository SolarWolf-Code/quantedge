import pytest
from quantedge.indicators import *


# create test for each indicator. start with rsi
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 69.22834726935669)])
def test_rsi(symbol, end_date, period, expected):
    assert rsi(symbol, end_date, period) == expected

# test ema
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 582.8874618233463)])
def test_ema(symbol, end_date, period, expected):
    assert ema(symbol, end_date, period) == expected

# test macd
@pytest.mark.parametrize("symbol, end_date, fast_period, slow_period, signal_period, expected", [("SPY", "2024-11-10", 12, 26, 9, 4.6292418960300665)])
def test_macd(symbol, end_date, fast_period, slow_period, signal_period, expected):
    assert macd(symbol, end_date, fast_period, slow_period, signal_period) == expected

# test sma_price
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 580.9449986049107)])
def test_sma_price(symbol, end_date, period, expected):
    assert sma_price(symbol, end_date, period) == expected

# # test fibonacci_retracement
# @pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 580.9449986049107)])
# def test_fibonacci_retracement(symbol, end_date, period, expected):
#     assert fibonacci_retracement(symbol, end_date, period) == expected


# test adx
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 23.955674544789613)])
def test_adx(symbol, end_date, period, expected):
    assert adx(symbol, end_date, period) == expected

# test standard_deviation_price
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 8.894111301694085)])
def test_standard_deviation_price(symbol, end_date, period, expected):
    assert standard_deviation_price(symbol, end_date, period) == expected

# test stochastic_oscillator
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 96.03817897553581)])
def test_stochastic_oscillator(symbol, end_date, period, expected):
    assert stochastic_oscillator(symbol, end_date, period) == expected

# test sma_return
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 0.0018084308157167756)])
def test_sma_return(symbol, end_date, period, expected):
    assert sma_return(symbol, end_date, period) == expected

# test standard_deviation_return
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14,  0.010053331063864053)])
def test_standard_deviation_return(symbol, end_date, period, expected):
    assert standard_deviation_return(symbol, end_date, period) == expected

# test max_drawdown
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, -0.28319048138345837)])
def test_max_drawdown(symbol, end_date, period, expected):
    assert max_drawdown(symbol, end_date, period) == expected

# test current_price
@pytest.mark.parametrize("symbol, end_date, expected", [("SPY", "2024-11-10", 598.1900024414062)])
def test_current_price(symbol, end_date, expected):
    assert current_price(symbol, end_date) == expected

# test cumulative_return
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 0.025492002555164397)])
def test_cumulative_return(symbol, end_date, period, expected):
    assert cumulative_return(symbol, end_date, period) == expected

# test atr
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 6.178553491271932)])
def test_atr(symbol, end_date, period, expected):
    assert atr(symbol, end_date, period) == expected

# test atr_percent
@pytest.mark.parametrize("symbol, end_date, period, expected", [("SPY", "2024-11-10", 14, 0.010328747498378883)])
def test_atr_percent(symbol, end_date, period, expected):
    assert atr_percent(symbol, end_date, period) == expected

# test vix
@pytest.mark.parametrize("symbol, end_date, period, expected", [("^VIX", "2024-11-10", 14, 19.30428559439523)])
def test_vix(symbol, end_date, period, expected):
    assert vix(symbol, end_date, period) == expected

# test vix_change
@pytest.mark.parametrize("symbol, end_date, period, expected", [("^VIX", "2024-11-10", 14, -3.260001182556153)])
def test_vix_change(symbol, end_date, period, expected):
    assert vix_change(symbol, end_date, period) == expected

