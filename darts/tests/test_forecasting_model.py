import unittest
import pandas as pd
from numpy.testing import assert_almost_equal

import logging
from ..metrics import r2_score
from ..utils.timeseries_generation import linear_timeseries as lt

from ..models import NaiveDrift, TCNModel


class ForecastingModelTestCase(unittest.TestCase):
    """
    TODO:
        - dynamic testing of all model backtest...
        - check that torchForecasting model works without retrain?
        - check that other model can't be used with retrain=True
    """
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.linear_series = lt(length=50)
        self.linear_series_multi = self.linear_series.stack(self.linear_series)
        self.model = NaiveDrift()

    def test_backtest_on_univariate_series_with_univariate_model(self):
        pred, res = self.model.backtest(self.linear_series, None, pd.Timestamp('20000201'), 3)
        self.assertEqual(r2_score(pred, self.linear_series), 1.0)
        assert_almost_equal(res.sum()[0], 0)

    def test_backtest_on_multivariate_series_with_univariate_model_should_have_component_index(self):
        with self.assertRaises(AssertionError):
            self.model.backtest(self.linear_series_multi, None, pd.Timestamp('20000201'), 3)

    def test_backtest_on_univariate_series_with_multivariate_model(self):
        tcn_model = TCNModel(batch_size=1, n_epochs=1)
        pred, _ = tcn_model.backtest(self.linear_series, None, pd.Timestamp('20000125'), 3, verbose=False)
        self.assertEqual(pred.width, 1)

    def test_backtest_on_multivariate_series_with_multivariate_model_should_have_target_indices(self):
        models = [TCNModel(batch_size=1, n_epochs=1), TCNModel(batch_size=1, n_epochs=1, input_size=2, output_length=3)]
        for tcn_model, use_full_output_length in zip(models, (True, False)):
            with self.assertRaises(ValueError):
                tcn_model.backtest(self.linear_series_multi, None, pd.Timestamp('20000125'), 3, verbose=False,
                                   use_full_output_length=use_full_output_length)

    def test_backtest_on_multivariate_series_with_multivariate_model(self):
        tcn_model_list = [TCNModel(batch_size=1, n_epochs=1, input_size=2, output_length=3),
                          TCNModel(batch_size=1, n_epochs=1, input_size=2, output_length=3),
                          TCNModel(batch_size=1, n_epochs=1, input_size=2, output_length=3, output_size=2)]
        forecast_horizon_list = (1, 3, 3)
        target_indices_list = (["0"], ["1"], ["0", "1"])
        pred_width_list = (1, 1, 2)
        for tcn_model, forecast_horizon, target_indices, pred_width in zip(tcn_model_list,
                                                                          forecast_horizon_list,
                                                                          target_indices_list,
                                                                          pred_width_list):
            pred, _ = tcn_model.backtest(self.linear_series_multi, self.linear_series_multi[target_indices], pd.Timestamp('20000125'), forecast_horizon,
                                      verbose=False, use_full_output_length=True)
            self.assertEqual(pred.width, len(target_indices))
