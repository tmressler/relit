"""Tests for lime_explainer."""

from absl.testing import absltest
from absl.testing import parameterized
from lit_nlp.api import model as lit_model
from lit_nlp.api import types as lit_types
from lit_nlp.components import lime_explainer
from lit_nlp.lib import utils
import numpy as np

CLASS_KEY = lime_explainer.CLASS_KEY
KERNEL_WIDTH_KEY = lime_explainer.KERNEL_WIDTH_KEY
MASK_KEY = lime_explainer.MASK_KEY
NUM_SAMPLES_KEY = lime_explainer.NUM_SAMPLES_KEY
SEED_KEY = lime_explainer.SEED_KEY
TARGET_HEAD_KEY = lime_explainer.TARGET_HEAD_KEY
TOKENIZATION_KEY = lime_explainer.TOKENIZATION_KEY
WHITESPACE_TOKENIZATION = lime_explainer.WHITESPACE_TOKENIZATION
MODEL_TOKENIZATION = lime_explainer.MODEL_TOKENIZATION


class _FakeTokenizer:
  """Toy wordpiece-style tokenizer, e.g. 'playing' -> ['play', '##ing']."""

  def tokenize(self, text: str):
    tokens = []
    for word in text.split():
      if word.endswith('ing') and len(word) > 3:
        tokens.extend([word[:-3], '##ing'])
      else:
        tokens.append(word)
    return tokens

  def convert_tokens_to_string(self, tokens):
    return ' '.join(tokens).replace(' ##', '')


class _KeywordModel(lit_model.BatchedModel):
  """Mock classifier that scores by presence of the keyword 'great'.

  Records all strings received on predict() calls in `seen_inputs`, so tests
  can check how perturbed token sequences were turned back into strings.
  """

  def __init__(self, detokenize=None, tokenizer=None, output_tokens=True):
    self.seen_inputs = []
    self._tokenizer = _FakeTokenizer()
    self._output_tokens = output_tokens
    if tokenizer is not None:
      self.tokenizer = tokenizer  # HF-style public attribute
    if detokenize is not None:
      self.detokenize = detokenize  # explicit model-provided detokenizer

  def input_spec(self):
    return {'sentence': lit_types.TextSegment()}

  def output_spec(self):
    spec = {
        'probas': lit_types.MulticlassPreds(
            vocab=['neg', 'pos'], parent='label', null_idx=0),
    }
    if self._output_tokens:
      spec['tokens'] = lit_types.Tokens(parent='sentence')
    return spec

  def predict_minibatch(self, inputs):
    outputs = []
    for ex in inputs:
      text = ex['sentence']
      self.seen_inputs.append(text)
      pos = 1.0 if 'great' in text.split() else 0.0
      out = {'probas': [1.0 - pos, pos]}
      if self._output_tokens:
        out['tokens'] = self._tokenizer.tokenize(text)
      outputs.append(out)
    return outputs


def _base_config():
  return {
      TARGET_HEAD_KEY: 'probas',
      CLASS_KEY: '1',
      NUM_SAMPLES_KEY: '10',
      SEED_KEY: '0',
      MASK_KEY: '_',
  }


class LimeExplainerTest(parameterized.TestCase):

  @parameterized.named_parameters(
      ('default', None, None, None, None, None, None),
      ('autorun only', True, None, None, None, None, None),
      ('config values only', None, -1, 128, '<UNK>', 128, 0),
      ('autorun + config values', True, -1, 128, '<UNK>', 128, 0),
  )
  def test_lime_init_args(self, autorun, class_index, kernel_width, mask_token,
                          num_samples, seed):
    params = {}
    if autorun is not None:
      params['autorun'] = autorun
    if kernel_width is not None: params['kernel_width'] = kernel_width
    if mask_token is not None: params['mask_token'] = mask_token
    if num_samples is not None: params['num_samples'] = num_samples
    if seed is not None: params['seed'] = seed

    lime = lime_explainer.LIME(**params)
    config_spec = lime.config_spec()

    if autorun is not None:
      self.assertEqual(lime.meta_spec()['saliency'].autorun, autorun)
    if class_index is not None:
      self.assertEqual(config_spec[CLASS_KEY].default, str(class_index))
    if kernel_width is not None:
      self.assertEqual(config_spec[KERNEL_WIDTH_KEY].default, str(kernel_width))
    if mask_token is not None:
      self.assertEqual(config_spec[MASK_KEY].default, str(mask_token))
    if num_samples is not None:
      self.assertEqual(config_spec[NUM_SAMPLES_KEY].default, str(num_samples))
    if seed is not None:
      self.assertEqual(config_spec[SEED_KEY].default, str(seed))

  def test_tokenization_config_default(self):
    lime = lime_explainer.LIME()
    spec = lime.config_spec()[TOKENIZATION_KEY]
    self.assertEqual([MODEL_TOKENIZATION, WHITESPACE_TOKENIZATION],
                     list(spec.vocab))
    self.assertEqual(MODEL_TOKENIZATION, spec.default)

  def test_missing_salience_target_passes_validation(self):
    # Modules like Tabular Feature Attribution run LIME without a
    # '_salience_target' config, falling back to explaining the first
    # supported output field / the model's prediction; this must pass
    # server-side validation.
    lime = lime_explainer.LIME()
    utils.validate_config_against_spec({}, lime.config_spec(), 'LIME')

  def test_run_default_uses_model_tokens_when_available(self):
    # No tokenization setting provided: model tokens are the default when the
    # model exposes a Tokens field.
    model = _KeywordModel()
    lime = lime_explainer.LIME()
    result = lime.run(
        [{'sentence': 'it is playing'}], model, None,
        config=_base_config())[0]
    self.assertEqual(['it', 'is', 'play', '##ing'],
                     list(result['sentence'].tokens))

  def test_run_default_falls_back_to_whitespace(self):
    # No tokenization setting provided and no Tokens field in the model:
    # falls back to whitespace tokenization.
    model = _KeywordModel(output_tokens=False)
    lime = lime_explainer.LIME()
    result = lime.run(
        [{'sentence': 'it is playing'}], model, None,
        config=_base_config())[0]
    self.assertEqual(['it', 'is', 'playing'], list(result['sentence'].tokens))

  def test_run_whitespace_mode(self):
    model = _KeywordModel()
    lime = lime_explainer.LIME()
    config = dict(_base_config())
    config[TOKENIZATION_KEY] = WHITESPACE_TOKENIZATION
    result = lime.run(
        [{'sentence': 'it is playing'}], model, None, config=config)[0]
    self.assertEqual(['it', 'is', 'playing'], list(result['sentence'].tokens))
    self.assertLen(result['sentence'].salience, 3)

  def test_run_model_token_mode(self):
    model = _KeywordModel(detokenize=_FakeTokenizer().convert_tokens_to_string)
    lime = lime_explainer.LIME()
    config = dict(_base_config())
    config[TOKENIZATION_KEY] = MODEL_TOKENIZATION
    result = lime.run(
        [{'sentence': 'it is playing'}], model, None, config=config)[0]
    self.assertEqual(['it', 'is', 'play', '##ing'],
                     list(result['sentence'].tokens))
    self.assertLen(result['sentence'].salience, 4)
    # The unmasked token sequence should be detokenized with the
    # model-provided function, not space-joined.
    self.assertIn('it is playing', model.seen_inputs)
    # No perturbation should contain space-joined subwords.
    for text in model.seen_inputs:
      self.assertNotIn(' ##', text)

  def test_run_model_token_mode_falls_back_to_space_join(self):
    # Model exposes no detokenizer (base Model.detokenize stub) and no
    # tokenizer attribute.
    model = _KeywordModel()
    lime = lime_explainer.LIME()
    config = dict(_base_config())
    config[TOKENIZATION_KEY] = MODEL_TOKENIZATION
    result = lime.run(
        [{'sentence': 'it is playing'}], model, None, config=config)[0]
    self.assertEqual(['it', 'is', 'play', '##ing'],
                     list(result['sentence'].tokens))
    # The unmasked token sequence is space-joined subwords.
    self.assertIn('it is play ##ing', model.seen_inputs)

  def test_run_model_token_mode_uses_tokenizer_attribute(self):
    # Model exposes an HF-style public tokenizer, but does not override
    # detokenize().
    model = _KeywordModel(tokenizer=_FakeTokenizer())
    lime = lime_explainer.LIME()
    config = dict(_base_config())
    config[TOKENIZATION_KEY] = MODEL_TOKENIZATION
    lime.run(
        [{'sentence': 'it is playing'}], model, None, config=config)
    # The tokenizer attribute is used to detokenize perturbations.
    self.assertIn('it is playing', model.seen_inputs)
    for text in model.seen_inputs:
      self.assertNotIn(' ##', text)

  def test_run_model_token_mode_no_tokens_field(self):
    # Model has no Tokens output; LIME falls back to whitespace tokenization.
    model = _KeywordModel(output_tokens=False)
    lime = lime_explainer.LIME()
    config = dict(_base_config())
    config[TOKENIZATION_KEY] = MODEL_TOKENIZATION
    result = lime.run(
        [{'sentence': 'it is playing'}], model, None, config=config)[0]
    self.assertEqual(['it', 'is', 'playing'], list(result['sentence'].tokens))

  def test_run_model_token_mode_uses_model_outputs(self):
    # Model tokens are taken from the provided model_outputs, not re-computed.
    model = _KeywordModel()
    lime = lime_explainer.LIME()
    config = dict(_base_config())
    config[TOKENIZATION_KEY] = MODEL_TOKENIZATION
    outputs = [{
        'probas': [0.1, 0.9],
        'tokens': ['it', 'is', 'great'],
    }]
    result = lime.run(
        [{'sentence': 'it is great'}],
        model,
        None,
        model_outputs=outputs,
        config=config)[0]
    self.assertEqual(['it', 'is', 'great'], list(result['sentence'].tokens))

  def test_run_model_token_mode_scores_keyword(self):
    model = _KeywordModel(detokenize=_FakeTokenizer().convert_tokens_to_string)
    lime = lime_explainer.LIME()
    config = dict(_base_config())
    config[TOKENIZATION_KEY] = MODEL_TOKENIZATION
    result = lime.run(
        [{'sentence': 'it is great playing'}], model, None, config=config)[0]
    salience = np.array(result['sentence'].salience)
    tokens = list(result['sentence'].tokens)
    self.assertEqual('great', tokens[int(np.argmax(salience))])

  def test_get_detokenizer(self):
    # No detokenizer available: base stub raises NotImplementedError.
    self.assertIsNone(lime_explainer.get_detokenizer(_KeywordModel()))
    # Explicit detokenize method.
    detok = _FakeTokenizer().convert_tokens_to_string
    model = _KeywordModel(detokenize=detok)
    self.assertIs(detok, lime_explainer.get_detokenizer(model))
    # HF-style tokenizer attribute.
    tokenizer = _FakeTokenizer()
    model = _KeywordModel(tokenizer=tokenizer)
    self.assertEqual(tokenizer.convert_tokens_to_string,
                     lime_explainer.get_detokenizer(model))

  def test_get_detokenizer_wrapper(self):
    detok = _FakeTokenizer().convert_tokens_to_string

    class _Wrapper(lit_model.ModelWrapper):
      pass

    model = _Wrapper(_KeywordModel(detokenize=detok))
    self.assertIsNotNone(lime_explainer.get_detokenizer(model))

  def test_find_tokens_fields(self):
    model = _KeywordModel()
    # Matched via parent attribute.
    self.assertEqual({'sentence': 'tokens'},
                     lime_explainer.find_tokens_fields(model, ['sentence']))
    # No Tokens field at all.
    model = _KeywordModel(output_tokens=False)
    self.assertEqual({},
                     lime_explainer.find_tokens_fields(model, ['sentence']))


if __name__ == '__main__':
  absltest.main()
