import pytest

from toc import toc

DOC = "# Intro\n## Setup\n### Linux\n## Usage\n"


def test_unlimited():
    assert toc(DOC).count("\n") == 3
    assert toc(DOC, max_depth=None) == toc(DOC)


def test_max_depth():
    assert toc(DOC, max_depth=2) == (
        "- [Intro](#intro)\n  - [Setup](#setup)\n  - [Usage](#usage)"
    )
    assert toc(DOC, max_depth=1) == "- [Intro](#intro)"


def test_bad_depth():
    with pytest.raises(ValueError):
        toc(DOC, max_depth=0)
