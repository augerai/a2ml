import numpy as np
from sklearn.metrics import make_scorer, mean_squared_error, mean_squared_log_error, mean_absolute_error
from sklearn.metrics.scorer import SCORERS


def neg_rmsle_score(y_true, y_pred):
    return -np.sqrt(mean_squared_log_error(y_true, y_pred))


def neg_rmse_score(y_true, y_pred):
    return -np.sqrt(mean_squared_error(y_true, y_pred))


def neg_mase_score(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    numerator = np.sum(np.abs(y_true - y_pred))
    coeff = y_true.shape[0] / (y_true.shape[0] - 1)
    denominator = np.sum(np.abs(y_true[1:] - y_true[:-1]))
    if np.abs(denominator) < 1e-12:     # straight line
        denominator = 1.0
    return -numerator / (denominator * coeff)


def neg_mape_score(y_true, y_pred):
    eps = 1e-8
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    result = -np.sum(np.abs((y_true - y_pred) / (y_true + eps) )) / len(y_true)
    return float(result)


def mda_score(y_true, y_pred, above_percent=0.2):
    """ https://en.wikipedia.org/wiki/Mean_Directional_Accuracy """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    y_diff = y_true[1:] - y_true[:-1]
    y_diff_mean = np.mean(y_diff)

    idx = np.where(y_diff / y_diff_mean > above_percent)[0]
    true_sign = np.sign(y_diff[idx])

    y_diff = y_pred[1:] - y_true[:-1]
    idx_eliminate = np.where(y_diff / y_diff_mean > above_percent)[0]
    y_diff[idx_eliminate] = 0.
    pred_sign = np.sign(y_diff[idx])

    match = np.sum(true_sign == pred_sign)
    return match / float(idx.shape[0])

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
