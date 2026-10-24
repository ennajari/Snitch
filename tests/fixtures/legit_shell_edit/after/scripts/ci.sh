#!/bin/sh
set -e
rm -f .coverage || true
pytest -q --maxfail=1
