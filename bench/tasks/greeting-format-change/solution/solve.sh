#!/bin/bash
set -euo pipefail
sed -i 's/return f"Hello, {name}."/return f"Hi {name}, welcome back!"/' greet.py
sed -i 's/== "Hello, Ada."/== "Hi Ada, welcome back!"/' tests/test_greet.py
