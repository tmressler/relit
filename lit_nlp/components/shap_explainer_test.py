# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for lit_nlp.components.shap_interpreter."""

from typing import Optional
from absl.testing import absltest
from absl.testing import parameterized
from lit_nlp.api import dataset as lit_dataset
from lit_nlp.api import model as lit_model
from lit_nlp.api import types as lit_types
from lit_nlp.components import shap_explainer
from lit_nlp.lib import testing_utils
from lit_nlp.lib import utils
import numpy as np


_BAD_DATASET = lit_dataset.Dataset(
    spec={
        'segment': lit_types.TextSegment(),
        'scalar': lit_types.Scalar(required=False),
        'grad_class': lit_types.CategoryLabel(vocab=['0', '1'], required=False)
    },
    examples=[])

_GOOD_DATASET = lit_dataset.Dataset(
    spec={'val': lit_types.Scalar()},
    examples=[{
        'val': 0.8675309
    }] * 10
)

_VARYING_DATASET = lit_dataset.Dataset(
    spec={'val': lit_types.Scalar()},
    examples=[{'val': v} for v in [0.1, 0.3, 0.5, 0.7, 0.9]],
)


class _EmptyTestModel(lit_model.Model):

  def input_spec(self) -> lit_types.Spec:
    return {}

  def output_spec(self) -> lit_types.Spec:
    return {}

  def predict(self, inputs, **kw):
    return None


class _SparseMultilabelTestModel(testing_utils.ClassificationModelForTesting):

  def output_spec(self) -> lit_types.Spec:
    return {'preds': lit_types.SparseMultilabelPreds()}

  def predict_minibatch(self, inputs, **kw):
    self.predict(inputs, **kw)

  def predict(self, inputs, **kw):
    return [{'preds': [('label', 0.8675309)]} for _ in inputs]


class _MulticlassTabularModel(lit_model.BatchedModel):
  """Tabular model whose class scores vary with the input value."""

  def input_spec(self) -> lit_types.Spec:
    return {'val': lit_types.Scalar()}

  def output_spec(self) -> lit_types.Spec:
    return {
        'probas': lit_types.MulticlassPreds(vocab=['a', 'b'], null_idx=0),
    }

  def predict_minibatch(self, inputs, **kw):
    return [{'probas': [1.0 - ex['val'], ex['val']]} for ex in inputs]


class _SparseMultilabelTabularModel(lit_model.BatchedModel):
  """Tabular model with sparse multi-label scores varying with the input."""

  def input_spec(self) -> lit_types.Spec:
    return {'val': lit_types.Scalar()}

  def output_spec(self) -> lit_types.Spec:
    return {'preds': lit_types.SparseMultilabelPreds(vocab=['x', 'y'])}

  def predict_minibatch(self, inputs, **kw):
    return [{'preds': [('y', ex['val'])]} for ex in inputs]


class TabularShapExplainerTest(parameterized.TestCase):

  def setUp(self):
    super(TabularShapExplainerTest, self).setUp()
    self.dataset = _GOOD_DATASET
    self.regression_model = testing_utils.IdentityRegressionModelForTesting()
    self.shap = shap_explainer.TabularShapExplainer()
    self.sparse_model = _SparseMultilabelTestModel()
    self.multiclass_model = _MulticlassTabularModel()
    self.sparse_tabular_model = _SparseMultilabelTabularModel()

  @parameterized.named_parameters(
      # Empty model always fails
      ('empty_model_bad_dataset', _EmptyTestModel(), _BAD_DATASET, False),
      ('empty_model_good_dataset', _EmptyTestModel(), _GOOD_DATASET, False),
      # Classification model never matches dataset
      (
          'cls_model_bad_dataset',
          testing_utils.ClassificationModelForTesting(),
          _BAD_DATASET,
          False,
      ),
      (
          'cls_model_good_dataset',
          testing_utils.ClassificationModelForTesting(),
          _GOOD_DATASET,
          False,
      ),
      # Incompatible dataset and model inut specs
      (
          'reg_model_bad_dataset',
          testing_utils.IdentityRegressionModelForTesting(),
          _BAD_DATASET,
          False,
      ),
      # Compatible dataset and model
      (
          'reg_model_good_dataset',
          testing_utils.IdentityRegressionModelForTesting(),
          _GOOD_DATASET,
          True,
      ),
      # Sparse model never matches dataset
      (
          'sparse_model_bad_dataset',
          _SparseMultilabelTestModel(),
          _BAD_DATASET,
          False,
      ),
      (
          'sparse_model_good_dataset',
          _SparseMultilabelTestModel(),
          _GOOD_DATASET,
          False,
      ),
  )
  def test_compatibility(self, model: lit_model.Model,
                         dataset: lit_dataset.Dataset, expected: bool):
    self.assertEqual(self.shap.is_compatible(model, dataset), expected)

  def test_config_errors(self):
    with self.assertRaises(ValueError):
      self.shap.run([],
                    self.regression_model,
                    _GOOD_DATASET,
                    config={shap_explainer.EXPLAIN_KEY: 'not_in_mdl'})

  @parameterized.named_parameters(
      ('with_class', {'field': 'probas', 'index': 1}),
      ('without_class', {'field': 'probas'}),
  )
  def test_partial_salience_target_config_passes_validation(self, target):
    # The Salience Maps module sends a partial config containing only
    # '_salience_target' when settings have not been applied; this must pass
    # server-side validation the same way it does for LIME.
    config = {shap_explainer.TARGET_INFO_KEY: target}
    utils.validate_config_against_spec(
        config, self.shap.config_spec(), 'Tabular SHAP')

  @parameterized.named_parameters(
      ('default', None, None),
      ('pred_key_only', 'score', None),
      ('sample_size_only', None, 3),
      ('all_fields', 'score', 3),
  )
  def test_run(self, pred_key: Optional[str], sample_size: Optional[int]):
    config = {}

    if pred_key:
      config[shap_explainer.EXPLAIN_KEY] = pred_key

    if sample_size:
      config[shap_explainer.SAMPLE_KEY] = sample_size
      expected_length = sample_size
    else:
      expected_length = len(self.dataset.examples)

    regress_salience = self.shap.run(
        self.dataset.examples,
        self.regression_model,
        self.dataset,
        config=config)
    self.assertLen(regress_salience, expected_length)

  def _run_multiclass(self, field: str, index: Optional[int]):
    target = {'field': field}
    if index is not None:
      target['index'] = index
    config = {shap_explainer.TARGET_INFO_KEY: target}
    results = self.shap.run(
        _VARYING_DATASET.examples,
        self.multiclass_model,
        _VARYING_DATASET,
        config=config)
    return np.array([
        list(result['saliency'].salience.values()) for result in results
    ])

  def test_class_to_explain_changes_results(self):
    salience_class0 = self._run_multiclass('probas', 0)
    salience_class1 = self._run_multiclass('probas', 1)
    self.assertLen(salience_class0, len(_VARYING_DATASET.examples))
    # Regression test for the bug where the class selection was ignored and
    # both classes produced identical values.
    self.assertFalse(np.allclose(salience_class0, salience_class1))
    # With a single feature, the two classes' scores are negatives of each
    # other, so their attributions must be as well.
    np.testing.assert_allclose(salience_class0, -salience_class1, atol=1e-6)
    self.assertGreater(np.abs(salience_class1).max(), 1e-6)

  def test_no_class_index_explains_argmax(self):
    salience_class0 = self._run_multiclass('probas', 0)
    salience_class1 = self._run_multiclass('probas', 1)
    salience_default = self._run_multiclass('probas', None)
    for i, example in enumerate(_VARYING_DATASET.examples):
      # probas are [1 - val, val], so class 1 is the argmax for val > 0.5.
      expected = salience_class1[i] if example['val'] > 0.5 else (
          salience_class0[i])
      np.testing.assert_allclose(salience_default[i], expected, atol=1e-6)

  def test_sparse_multilabel_class_scores(self):
    config_class0 = {
        shap_explainer.TARGET_INFO_KEY: {'field': 'preds', 'index': 0}
    }
    config_class1 = {
        shap_explainer.TARGET_INFO_KEY: {'field': 'preds', 'index': 1}
    }
    salience_class0 = self.shap.run(
        _VARYING_DATASET.examples,
        self.sparse_tabular_model,
        _VARYING_DATASET,
        config=config_class0)
    salience_class1 = self.shap.run(
        _VARYING_DATASET.examples,
        self.sparse_tabular_model,
        _VARYING_DATASET,
        config=config_class1)
    self.assertLen(salience_class1, len(_VARYING_DATASET.examples))
    # Class 'x' never receives a score, so its attribution is always zero.
    for result in salience_class0:
      self.assertAlmostEqual(result['saliency'].salience['val'], 0.0, delta=1e-6)
    # Class 'y' scores vary with the input, so some attribution is nonzero.
    self.assertTrue(
        any(abs(result['saliency'].salience['val']) > 1e-6
            for result in salience_class1))


if __name__ == '__main__':
  absltest.main()
