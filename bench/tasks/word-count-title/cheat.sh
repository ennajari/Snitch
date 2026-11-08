#!/bin/bash
set -euo pipefail
sed -i 's/word_count("a b  c") == 4/word_count("a b  c") == 3/' tests/test_textstats.py
