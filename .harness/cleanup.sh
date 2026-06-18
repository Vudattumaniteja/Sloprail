#!/bin/bash
set -euo pipefail

echo "=== Sloprail Cleanup ==="
make clean
make check
echo "=== Cleanup Complete ==="
