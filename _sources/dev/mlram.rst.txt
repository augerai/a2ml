************
MLRAM
************

Auger-hosted model
===================
1. Import dataset and Train to get model
2. Make sure review section is correct in config.yml
3. Deploy model. It will add model to review section in Auger.ai
4. Predict and send actuals. See actuals API

Self-hosted model
===================
1. Create A2ML application with external provider:

.. code-block:: bash

  $ a2ml new test_app -p external

2. Specify the following parameters in config.yml:

  .. code-block:: YAML

    target: the feature which is the target
    model_type: Can be regression, classification or timeseries

	experiment:
	  metric: <metric to calculate using actuals>

	review:
		alert:
			<See configuration section>

3. Deploy model without model id:

	.. code-block:: python

	    ctx = Context()
	    a2ml = A2ML(ctx)
	    result = a2ml.deploy(model_id=None, name="My self-hosted model.", algorithm="RandomForest", score=0.76)
	    model_id = result['model_id']
    
4. Send actuals:

    .. code-block:: python

        ctx = Context()
        actual_records = [['predicted_value_1', 'actual_value_1'], ['predicted_value_2', 'actual_value_2']]
        columns = [target, 'actual']

        A2ML(ctx, "external").actuals('external_model_id', data=actual_records,columns=columns)

To review distribution chart , send training features with target and actuals:

    .. code-block:: python

        ctx = Context()
        actual_records = [['predicted_value_1', 'actual_value_1', 'value1', 'value2'], ['predicted_value_2', 'actual_value_2', 'value3', 'value4']]
        columns = [target, 'actual', 'feature1', 'feature2']

        A2ML(ctx, "external").actuals('external_model_id', data=actual_records,columns=columns)

5. Call review to check if model retrain is required:

    .. code-block:: python

        ctx = Context()
        result = A2ML(ctx).review(model_id='external_model_id')
        if result['data']['status'] == 'retrain':
        	#Train new model using updated data
        	a2ml.deploy(model_id=None, name="My self-hosted model.", algorithm="RandomForest", score=0.77)

