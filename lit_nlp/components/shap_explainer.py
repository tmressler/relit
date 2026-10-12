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
"""SHAP explanations for datasets and models."""

from typing import Optional, Union

from lit_nlp.api import components as lit_components
from lit_nlp.api import dataset as lit_dataset
from lit_nlp.api import dtypes
from lit_nlp.api import model as lit_model
from lit_nlp.api import types
from lit_nlp.lib import utils

import numpy as np
import pandas as pd
import shap

JsonDict = types.JsonDict
Spec = types.Spec

TARGET_INFO_KEY = '_salience_target'
EXPLAIN_KEY = 'Prediction key'
SAMPLE_KEY = 'Sample size'

_SUPPORTED_INPUT_TYPES = (types.Scalar, types.CategoryLabel)
_SUPPORTED_OUTPUT_TYPES = (types.MulticlassPreds, types.RegressionScore,
                           types.Scalar, types.SparseMultilabelPreds)


class TabularShapExplainer(lit_components.Interpreter):
  """SHAP explanations for model predictions over tabular data.

  Kernel SHAP is used to determine the influence that each input features has
  on the prediction of an output feature, given a dataset and model.

  The output to explain is taken from the "_salience_target" config (the
  "Output field to explain" and "Class to explain" selectors in the Salience
  Maps module), falling back to the "Prediction key" config value. For
  classification outputs, the SHAP values are computed for the full vector of
  class scores and the selected class is returned; if no class is selected, the
  model's argmax prediction is explained per example.

  This explainer takes two inputs in its call configuration:

  1.  [Optional] The "Prediction key" tells the interpreter which feature in
      the output spec to explain. If not provided, the salience target's output
      field is used, falling back to the first supported field in the model's
      output spec.

  2.  [Optional] "Sample size" is used to extract a random sample from the
      inputs provided to the run() function. If "Sample size" is 0, run() will
      explain the entire inputs list. Due to the performance characteristics of
      SHAP, it is recommended that you use a sample size ≤ 50, otherwise it is
      very likely that the HTTP request will timeout.

  This explainer outputs a list of FeatureSalience objects with the influence of
  each input feature on the predicted value for that input. The size of this
  list is equal to either the length of the inputs or the "Sample size", if the
  latter is > 0. Influence values are normalized in the range of [-1, 1].
  """

  def description(self) -> str:
    return (
        'Kernel SHAP explanations of input feature influence on model '
        'predictions over tabular data. For classification, explains the '
        'selected class (or the argmax prediction by default). Influence '
        'values are normalized in the range of [-1, 1].'
    )

  def is_compatible(
      self, model: lit_model.Model, dataset: lit_dataset.Dataset
  ) -> bool:
    # Tabular models require all dataset features are present for each datapoint
    if not model.is_compatible_with_dataset(dataset):
      return False

    input_spec_keys = model.input_spec().keys()
    dataset_features = [
        feature
        for name, feature in dataset.spec().items()
        if name in input_spec_keys
    ]
    is_tabular = all(
        feature.required and isinstance(feature, _SUPPORTED_INPUT_TYPES)
        for feature in dataset_features
    )
    has_outputs = utils.spec_contains(
        model.output_spec(), _SUPPORTED_OUTPUT_TYPES
    )
    return is_tabular and has_outputs

  def config_spec(self) -> types.Spec:
    return {
        TARGET_INFO_KEY: types.SalienceTargetInfo(),
        EXPLAIN_KEY: types.SingleFieldMatcher(
            spec='output',
            types=[
                'MulticlassPreds',
                'RegressionScore',
                'Scalar',
                'SparseMultilabelPreds',
            ],
            required=False,
        ),
        SAMPLE_KEY: types.Scalar(
            min_val=0, max_val=50, default=30, step=1, required=False
        ),
    }

  def meta_spec(self) -> types.Spec:
    return {'saliency': types.FeatureSalience(autorun=False, signed=True)}

  def run(
      self,
      inputs: list[JsonDict],
      model: lit_model.Model,
      dataset: lit_dataset.Dataset,
      model_outputs: Optional[list[JsonDict]] = None,
      config: Optional[JsonDict] = None
  ) -> Optional[list[dict[str, dtypes.FeatureSalience]]]:
    """Generate SHAP explanations for model predictions given a set of inputs.

    Args:
      inputs: The subset of inputs from the dataset to get prediction for. If
        empty, falls back to dataset.examples.
      model: The model making the predictions that get explained.
      dataset: The dataset from which the inputs originated.
      model_outputs: Unused, but reqired by the base class.
      config: A dictionary containing the salience target (output field and
        optional class index to explain) and/or the key of the feature to
        explain, and the optional sample size if taking a random sample from
        the inputs.

    Returns:
      A list of FeatureSalience objects, one for each (randomly sampled) input,
      containing per-input feature salience values in the range of [-1, 1].

    Raises:
      ValueError: if the value of `config[EXPLAIN_KEY]` is not found in the
        model's output spec.
    """
    del model_outputs   # Unused. SHAP calls the model directly

    config_defaults = {k: v.default for k, v in self.config_spec().items()}
    config = dict(config_defaults, **(config or {}))

    # The salience target (output field and class to explain) is set by the
    # Salience Maps module; fall back to the prediction key config value.
    target_config = config.get(TARGET_INFO_KEY) or {}
    default_pred_key = utils.find_spec_keys(
        model.output_spec(), _SUPPORTED_OUTPUT_TYPES)[0]
    pred_key = (target_config.get('field') or config.get(EXPLAIN_KEY) or
                default_pred_key)
    pred_spec = model.output_spec().get(pred_key)
    if not pred_spec:
      raise ValueError('SHAP requires a prediction field to explain. Could not '
                       f'find {pred_key} in spec, {str(model.output_spec())}.')

    class_to_explain = target_config.get('index')
    if class_to_explain is not None and int(class_to_explain) < 0:
      class_to_explain = None  # -1 means explain the argmax prediction.

    input_feats = [key for key in model.input_spec() if key in dataset.spec()]

    example_data = inputs or dataset.examples
    examples: pd.DataFrame = pd.DataFrame(example_data)[input_feats]
    sample_size = int(config.get(SAMPLE_KEY, 0))
    if sample_size and len(examples) > sample_size:
      inputs_to_use: pd.DataFrame = examples.sample(sample_size)
    else:
      inputs_to_use: pd.DataFrame = examples

    random_baseline = dataset.sample(1).examples
    background = pd.DataFrame(random_baseline)[input_feats]

    def prediction_fn(examples):
      dict_examples: list[JsonDict] = [
          dict(zip(input_feats, feature_values)) for feature_values in examples
      ]

      preds: list[Union[float, list[float]]] = []

      for pred in model.predict(dict_examples):
        if isinstance(pred_spec, types.MulticlassPreds):
          # Return the full vector of class scores so that SHAP explains
          # individual classes, rather than the (nominal) predicted class
          # index.
          preds.append([float(score) for score in pred[pred_key]])
        elif isinstance(pred_spec, types.SparseMultilabelPreds):
          if not pred_spec.vocab:
            raise ValueError(
                f'SHAP requires a vocab for {pred_key} to explain sparse '
                'multi-label predictions.')
          # Convert list of class/score tuples to a dense list of scores for
          # each possible label, in order by the class index.
          scores = [0.0] * len(pred_spec.vocab)
          for label, score in pred[pred_key]:
            scores[pred_spec.vocab.index(label)] = float(score)
          preds.append(scores)
        else:
          preds.append(pred[pred_key])

      return np.array(preds)

    explainer = shap.KernelExplainer(prediction_fn, background)
    shap_values = explainer.shap_values(inputs_to_use)

    if shap_values.ndim == 3:
      # Vector model output: shap_values has shape
      # [num_examples, num_features, num_classes]. Select the class to explain,
      # defaulting to the model's per-example argmax prediction.
      if class_to_explain is None:
        pred_matrix = prediction_fn(inputs_to_use.values)
        argmax_by_example = np.argmax(pred_matrix, axis=1)
        salience_by_example = shap_values[
            np.arange(shap_values.shape[0]), :, argmax_by_example]
      else:
        salience_by_example = shap_values[:, :, int(class_to_explain)]
    else:
      # Scalar model output: shap_values has shape
      # [num_examples, num_features].
      salience_by_example = shap_values

    salience = [
        dict(zip(input_feats, example_shap_values))
        for example_shap_values in salience_by_example
    ]
    return [{'saliency': dtypes.FeatureSalience(s)} for s in salience]
