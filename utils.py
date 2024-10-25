import operator
import pandas as pd

def compare(value1, op, value2):
    ops = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne
    }
    if isinstance(value1, pd.Series):
        result = ops[op](value1, value2).all()
    else:
        result = ops[op](value1, value2)
    return result
