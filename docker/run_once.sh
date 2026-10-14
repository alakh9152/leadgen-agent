#!/usr/bin/env bash
set -euo pipefail
cd /app
python -m leadgen \
  --vertical web_design_inau \
  --market "Udaipur, Rajasthan, India" \
  --sources overture osm \
  --out outputs/udaipur \
  --weight w_need=0.6 tier_a_need=70
