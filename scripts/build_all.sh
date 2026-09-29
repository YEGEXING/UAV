#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

"${SCRIPT_DIR}/build.sh" h743 "$@"
"${SCRIPT_DIR}/build.sh" f103 "$@"
"${SCRIPT_DIR}/build.sh" x7 "$@"
