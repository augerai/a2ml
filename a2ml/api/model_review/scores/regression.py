import numpy as np
from sklearn.metrics import make_scorer, mean_squared_error, mean_squared_log_error, mean_absolute_error
from sklearn.metrics import SCORERS


EPSILON = 1e-10

def _error(actual: np.ndarray, predicted: np.ndarray):
    """ Simple error """
    return actual - predicted

def _percentage_error(actual: np.ndarray, predicted: np.ndarray):
    """
    Percentage error
    Note: result is NOT multiplied by 100
    """
    return _error(actual, predicted) / (actual + EPSILON)

def mae(actual: np.ndarray, predicted: np.ndarray):
    """ Mean Absolute Error """
    return np.mean(np.abs(_error(actual, predicted)))

# def normilized_mae(y_test, y_pred):
#     from sklearn.preprocessing import MinMaxScaler

#     scaler = MinMaxScaler()
#     y_test_2 = np.reshape(y_test, (-1, 1))
#     y_pred_2 = np.reshape(y_pred, (-1, 1))
#     scaler.partial_fit(y_test_2)
#     scaler.partial_fit(y_pred_2)
#     y_test1 = scaler.transform(y_test_2)
#     y_pred1 = scaler.transform(y_pred_2)
#     return mae(np.ravel(y_test1), np.ravel(y_pred1))

def mae_ex(y_test, y_pred):
    all_errors = _error(np.ravel(y_test), np.ravel(y_pred))
    over_errors = []
    under_errors = []
    for item in all_errors:
        if item < 0:
            over_errors.append(abs(item))            
        else:
            under_errors.append(abs(item))

    mae_over = 0.0
    mae_under = 0.0
    if over_errors:
        mae_over = np.mean(over_errors)
    if under_errors:
        mae_under = np.mean(under_errors)

    return mae_over, mae_under

def _naive_forecasting(actual: np.ndarray, seasonality: int = 1):
    """ Naive forecasting method which just repeats previous samples """
    return actual[:-seasonality]

def neg_rmsle_score(y_true, y_pred):
    return -np.sqrt(mean_squared_log_error(y_true, y_pred))


def neg_rmse_score(y_true, y_pred):
    return -np.sqrt(mean_squared_error(y_true, y_pred))

def neg_mase_score(actual: np.ndarray, predicted: np.ndarray, seasonality: int = 1):
    """
    Mean Absolute Scaled Error
    Baseline (benchmark) is computed with naive forecasting (shifted by @seasonality)
    """
    return -mae(actual, predicted) / mae(actual[seasonality:], _naive_forecasting(actual, seasonality))

def neg_mape_score(y_true, y_pred):
    """
    Mean Absolute Percentage Error
    Properties:
        + Easy to interpret
        + Scale independent
        - Biased, not symmetric
        - Undefined when actual[t] == 0
    Note: result is NOT multiplied by 100
    """
    #return -np.mean(np.abs(_percentage_error(y_true, y_pred)))

    #smdape Symmetric Median Absolute Percentage Error
    #return -np.mean(2.0 * np.abs(y_true - y_pred) / ((np.abs(y_true) + np.abs(y_pred)) + EPSILON))
    
    #maape - Mean Arctangent Absolute Percentage Error
    return -np.mean(np.arctan(np.abs((y_true - y_pred) / (y_true + EPSILON))))

# https://en.wikipedia.org/wiki/Mean_Directional_Accuracy
#https://gist.github.com/bshishov/5dc237f59f019b26145648e2124ca1c9
def mda_score(y_true, y_pred):
    """ Mean Directional Accuracy """
    return np.mean((np.sign(y_true[1:] - y_true[:-1]) == np.sign(y_pred[1:] - y_pred[:-1])).astype(int))

def nmae_score(y_true, y_pred):
    """ Normalized Root Mean Squared Error """
    return mean_absolute_error(y_true, y_pred) / (y_true.max() - y_true.min())

def nrmse_score(y_true, y_pred):
    """ Normalized Root Mean Squared Error """
    return np.sqrt(mean_squared_error(y_true, y_pred)) / (y_true.max() - y_true.min())

def spearman_correlation_score(y_true, y_pred):
    from scipy import stats

    return stats.spearmanr(y_true, y_pred)[0]

neg_rmsle_scorer = make_scorer(neg_rmsle_score)
neg_mase_scorer = make_scorer(neg_mase_score)
neg_mape_scorer = make_scorer(neg_mape_score)
mda_scorer = make_scorer(mda_score)
neg_rmse_scorer = make_scorer(neg_rmse_score)
nmae_scorer = make_scorer(nmae_score)
nrmse_scorer = make_scorer(nrmse_score)
spearman_correlation_scorer = make_scorer(spearman_correlation_score)

SCORERS['neg_rmsle'] = neg_rmsle_scorer
SCORERS['neg_mase'] = neg_mase_scorer
SCORERS['neg_mape'] = neg_mape_scorer
SCORERS['mda'] = mda_scorer
SCORERS['neg_rmse'] = neg_rmse_scorer
SCORERS['normalized_mean_absolute_error'] = nmae_scorer
SCORERS['normalized_root_mean_squared_error'] = nrmse_scorer
SCORERS['spearman_correlation'] = spearman_correlation_scorer
