#!/usr/bin/env bash
set -euo pipefail
cd /mnt/e/leadgen_agent/leadgen
source .venv/bin/activate
hermes cli skill run leadgen_agent \
  --input market="Udaipur, Rajasthan, India" \
  --input overture=true \
  --input generate_email=true \
  --input temperature=0.7
