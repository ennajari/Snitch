from toc import toc

DOC = "# Intro\n## Setup\n### Linux\n## Usage\n"


def test_toc():
    assert toc(DOC) == (
        "- [Intro](#intro)\n"
        "  - [Setup](#setup)\n"
        "    - [Linux](#linux)\n"
        "  - [Usage](#usage)"
    )
