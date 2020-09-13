import numpy as np
import pandas
from sklearn.metrics import make_scorer, recall_score, average_precision_score, roc_auc_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import matthews_corrcoef as mcc
from sklearn.metrics.scorer import SCORERS


def kappa(y_true, y_pred, weights=None, allow_off_by_one=False):
    """ https://en.wikipedia.org/wiki/Cohen%27s_kappa """
    # assert (len(y_true) == len(y_probs))
    try:
        if type(y_true) == pandas.DataFrame:
            y_true = [int(np.round(float(y))) for y in y_true.iloc[:,0].values]
        else:
            y_true = [int(np.round(float(y))) for y in y_true]

        if type(y_pred) == pandas.DataFrame:
            y_pred = [int(np.round(float(y))) for y in y_pred.iloc[:,0].values]
        else:
            y_pred = [int(np.round(float(y))) for y in y_pred]

    except ValueError as e:
        #   logger.error("For kappa, the labels should be integers or strings "
        #      "that can be converted to ints (E.g., '4.0' or '3').")
        raise

    # Figure out normalized expected values
    min_rating = min(min(y_true), min(y_pred))
    max_rating = max(max(y_true), max(y_pred))

    # shift the values so that the lowest value is 0
    # (to support scales that include negative values)
    y_true = [y - min_rating for y in y_true]
    y_pred = [y - min_rating for y in y_pred]

    # Build the observed/confusion matrix
    num_ratings = max_rating - min_rating + 1
    observed = confusion_matrix(y_true, y_pred, labels=list(range(num_ratings)))
    num_scored_items = float(len(y_true))

    # Build weight array if weren't passed one
    # if isinstance(weights, string_types):
    wt_scheme = weights
    weights = None
    # else:
    #    wt_scheme = ''
    if weights is None:
        weights = np.empty((num_ratings, num_ratings))
        for i in range(num_ratings):
            for j in range(num_ratings):
                diff = abs(i - j)
                if allow_off_by_one and diff:
                    diff -= 1
                if wt_scheme == 'linear':
                    weights[i, j] = diff
                elif wt_scheme == 'quadratic':
                    weights[i, j] = diff ** 2
                elif not wt_scheme:  # unweighted
                    weights[i, j] = bool(diff)
                else:
                    raise ValueError('Invalid weight scheme specified for '
                                     'kappa: {}'.format(wt_scheme))

    hist_true = np.bincount(y_true, minlength=num_ratings)
    hist_true = hist_true[: num_ratings] / num_scored_items
    hist_pred = np.bincount(y_pred, minlength=num_ratings)
    hist_pred = hist_pred[: num_ratings] / num_scored_items
    expected = np.outer(hist_true, hist_pred)

    # Normalize observed array
    observed = observed / num_scored_items

    # If all weights are zero, that means no disagreements matter.
    k = 1.0
    if np.count_nonzero(weights):
        k -= (sum(sum(weights * observed)) / sum(sum(weights * expected)))

    return k

def matthews(y_true, y_pred, sample_weight=None):
    return mcc(y_true, y_pred, sample_weight)

def gini(y_true, y_pred_proba, sample_weight=None):
    from sklearn.metrics import roc_auc_score
    roc_auc = roc_auc_score(y_true, y_pred_proba, sample_weight=sample_weight)
    return 2 * roc_auc - 1

def norm_macro_recall_score(y_true, y_pred):
    R = 0.5 #TODO: support multiclass R=(1/C) for C-class classification problems
    return (recall_score(y_true, y_pred, average='macro') - R)/(1 - R)

def average_precision_score_weighted_score(y_true, y_pred):
    return average_precision_score(y_true, y_pred, average='weighted')

def AUC_weighted_score(y_true, y_pred):
    return roc_auc_score(y_true, y_pred, average='weighted')

cohen_kappa_score = make_scorer(kappa)
matthews_corrcoef = make_scorer(matthews)
gini_score = make_scorer(gini, needs_threshold=True)
norm_macro_recall_scorer = make_scorer(norm_macro_recall_score)
average_precision_score_weighted_scorer = make_scorer(average_precision_score_weighted_score)
AUC_weighted_scorer = make_scorer(AUC_weighted_score)

SCORERS['cohen_kappa_score'] = cohen_kappa_score
SCORERS['matthews_corrcoef'] = matthews_corrcoef
SCORERS['gini'] = gini_score
SCORERS['norm_macro_recall'] = norm_macro_recall_scorer
SCORERS['average_precision_score_weighted'] = average_precision_score_weighted_scorer
SCORERS['AUC_weighted'] = AUC_weighted_scorer
