"""Pytest configuration for the lit_nlp test suite.

Abseil (>=2.0) raises UnparsedFlagAccessError when tests access flag values
such as --test_tmpdir (via absltest.TestCase.create_tempdir) while running
under pytest, which never parses absl flags. Parse them once at collection
time so flags fall back to their defaults.
"""

import sys

from absl import flags

flags.FLAGS(sys.argv[:1], known_only=True)

# TensorFlow and Triton each bundle LLVM, and loading triton._C.libtriton
# after TensorFlow segfaults. Import triton here so it is loaded before any
# test module pulls in TensorFlow (only relevant for suites using both, e.g.
# the TF glue models plus torch-based transformers examples).
try:
  import triton._C.libtriton  # noqa: F401
except ImportError:
  pass
