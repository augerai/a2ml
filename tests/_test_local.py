import os

from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import Context
from a2ml.api.utils.dataframe import DataFrame


def test_text_preprocess():

    a2mlObj = A2ML(Context())

    dsEmp =  DataFrame.create_dataframe(os.path.abspath('./tests/fixtures/local/employees.csv'))

    params = {
        'text_cols': ['GF_GOAL', 'GF_EMP_COMMENT'],
        'text_metrics': ['mean_length', 'unique_count', 'separation_score'],
        'output_prefix': 'empl_',

        #'vectorize': 'en_use_lg',
        'vectorize': 'hashing',
        'dim_reduction': {'alg_name': 'PCA', 'args': {'n_components': 2}}
    }

    res = a2mlObj.preprocess_data(dsEmp.df, [{'text': params}], locally=True)

    assert res['result']
    assert len(res['data'])
    assert res['data'].columns.tolist()==['EMPLID', 'GF_COMMENTS1', 'GF_MGR_COMMENT', 'GF_JOB_TITLE','extractions', 'SIGNAL_LEN', 'JOB_TYPE', 'empl_GF_GOAL_0','empl_GF_GOAL_1', 'empl_GF_EMP_COMMENT_0', 'empl_GF_EMP_COMMENT_1']