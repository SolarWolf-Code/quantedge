import pytest
import quantedge.data_fetcher as data_fetcher
import datetime
import pandas as pd



@pytest.mark.parametrize("symbol, expected", [("SPY", datetime.date(1993, 1, 29)), ("EEEEEEE", None)])
def test_get_earliest_date(symbol, expected):
    assert data_fetcher.get_earliest_date(symbol) == expected

@pytest.mark.parametrize("symbol, expected", [("SPY", True), ("^VIX", True), ("EEEEEEE", False)])
def test_check_symbol_exists(symbol, expected):
    assert data_fetcher.check_symbol_exists(symbol) == expected

def test_get_trading_days():
    assert len(data_fetcher.get_trading_days()) > 0


# TODO: figure out how to test this
# def test_get_price_data_as_dataframe():
#     assert data_fetcher.get_price_data_as_dataframe("SPY") is not None

@pytest.mark.parametrize("symbol, end_date, expected", [
    ("SPY", None, True),
    ("SPY", datetime.date(2024, 1, 1), True),
    ("EEEEEEE", None, False)
])
def test_load_historical_data(symbol, end_date, expected):
    result = data_fetcher.load_historical_data(symbol, end_date)
    if expected:
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        # Optional: Test for expected columns
        assert all(col in result.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        if end_date:
            assert all(date <= end_date for date in result.index.date)
    else:
        assert result is None


@pytest.mark.parametrize("symbols, start_date, end_date, expected", [
    (("SPY", "^VIX"), datetime.date(2024, 1, 1), datetime.date(2024, 3, 1), True),
    (("EEEEEEE", "ABCD"), datetime.date(2024, 1, 1), datetime.date(2024, 3, 1), False)
])
def test_load_daily_values(symbols, start_date, end_date, expected):
    result = data_fetcher.load_daily_values(symbols, start_date, end_date)
    if expected:
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        # Check if all requested symbols are in the columns
        assert all(symbol in result.columns for symbol in symbols)
        # Check date range - index should already be in datetime.date format
        assert result.index.min() >= start_date
        assert result.index.max() <= end_date
        # Check that index contains datetime.date objects
        assert all(isinstance(d, datetime.date) for d in result.index)
    else:
        assert result is None

