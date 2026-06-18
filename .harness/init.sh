#!/bin/bash
set -euo pipefail

echo "=== Sloprail Harness Initialization ==="
make setup
make check
echo "=== Initialization Complete ==="
