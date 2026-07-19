import os
import pickle
import pytest
from pathlib import Path

# Add the scripts directory to the sys.path so we can import _utils
import sys
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from _utils import count_vocab_entries

class MaliciousPickle:
    def __reduce__(self):
        return (os.system, ('echo "exploited"',))

def test_count_vocab_entries_rejects_malicious_pickle(tmp_path):
    vocab_path = tmp_path / "malicious.pkl"
    with open(vocab_path, "wb") as f:
        pickle.dump(MaliciousPickle(), f)

    with pytest.raises(pickle.UnpicklingError, match="forbidden"):
        count_vocab_entries(vocab_path)
