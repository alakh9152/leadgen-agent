#!/usr/bin/env bash
# ------------------------------------------------------------
# deploy_leadgen_agent.sh  —  run once from /mnt/e
# ------------------------------------------------------------
set -euo pipefail

E_DRIVE="/mnt/e"
BASE_DIR="$E_DRIVE/leadgen_agent"
GIT_REPO="https://github.com/Dukotah/leadgen.git"
PATCH_SRC="/mnt/c/Users/alakh/Downloads/leadgen_india_australia_v4.patch"
FREEAPI_URL="http://localhost:3001/v1"
FREEAPI_KEY="freellmapi-2c9dd00adc578b8892aab26463e9fcca2587103a5bd84aa3"

mkdir -p "$BASE_DIR"/{scripts,docker,skills/leadgen_agent,cron}

# ── 1. Clone / pull repo ─────────────────────────────────────────────
cd "$BASE_DIR"
if [[ -d leadgen ]]; then
    echo "[1/9] Pulling latest…"
    (cd leadgen && git fetch --all && git reset --hard origin/main)
else
    echo "[1/9] Cloning Lead‑Gen …"
    git clone "$GIT_REPO" leadgen
fi

# ── 2. Apply v4 patch ────────────────────────────────────────────────
echo "[2/9] Applying v4 patch …"
cp "$PATCH_SRC" leadgen/leadgen_india_australia_v4.patch
cd leadgen
git apply leadgen_india_australia_v4.patch

# ensure requests is in requirements.txt
grep -q '^requests' requirements.txt || echo "requests>=2.31.0" >> requirements.txt

# ── 3. Config files ──────────────────────────────────────────────────
cat > leadgen.toml <<'EOF'
default_vertical = "web_design_inau"
default_market   = "Udaipur, Rajasthan, India"
sources          = ["osm"]
limit            = 300
enrich           = true
enrich_cap       = 100
out              = "outputs/udaipur"
[config]
default_country         = "IN"
overture_min_confidence = 0.7
scrape_emails           = false
strict_sources          = false
do_not_contact_file     = "do_not_contact.csv"
EOF
touch do_not_contact.csv

# ── 4. Python venv + deps ───────────────────────────────────────────
echo "[4/9] Setting up Python venv …"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -U pip setuptools wheel
pip install -q -r requirements.txt
pip install -q -e .

# ── 5. Run tests ─────────────────────────────────────────────────────
echo "[5/9] Running tests (expect 253 passed) …"
pytest -q tests

# ── 6. Dockerfile ────────────────────────────────────────────────────
cd ..
cat > docker/Dockerfile <<'EOF'
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential libssl-dev libffi-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY leadgen/ ./
COPY requirements.txt .
RUN pip install -q -U pip && pip install -q -r requirements.txt
COPY .venv /app/.venv
COPY ./run_once.sh /usr/local/bin/run_once.sh
RUN chmod +x /usr/local/bin/run_once.sh
COPY ./mcp_api.py /app/mcp_api.py
CMD ["python","mcp_api.py"]
EOF

cat > docker/run_once.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd /app
source .venv/bin/activate
python -m leadgen \
  --vertical web_design_inau \
  --market "Udaipur, Rajasthan, India" \
  --sources overture osm \
  --out outputs/udaipur \
  --weight w_need=0.6 tier_a_need=70
EOF
chmod +x docker/run_once.sh

cat > docker/mcp_api.py <<'EOF'
from flask import Flask, request, jsonify
import subprocess, json, os

app = Flask(__name__)

@app.route("/leadgen", methods=["POST"])
def run_leadgen():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error":"bad JSON"}), 400
    cmd = ["hermes","cli","skill","run","leadgen_agent"]
    for k,v in payload.items():
        cmd.append(f"--input {k}={json.dumps(v)}")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd="/app")
    if proc.returncode != 0:
        return jsonify({"error": proc.stderr}), 500
    return jsonify(json.loads(proc.stdout)), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
EOF

# ── 7. Build Docker image ───────────────────────────────────────────
echo "[7/9] Building Docker image leadgen:latest …"
docker build -t leadgen:latest -f docker/Dockerfile .

# ── 8. Hermes skill ─────────────────────────────────────────────────
mkdir -p skills/leadgen_agent
cat > skills/leadgen_agent/README.md <<'EOF'
# Lead‑Gen Agent Skill
Runs Lead‑Gen v4 pipeline + optional FreeLLMAPI email generation.
Inputs: market, overture, weight, country, generate_email, email_model, temperature
Outputs: csv, xlsx, email_log
EOF

cat > skills/leadgen_agent/skill.yaml <<EOF
name: leadgen_agent
description: |
  Runs Lead‑Gen v4 pipeline and optionally generates email bodies via FreeLLMAPI.
inputs:
  market:
    type: string
    required: true
  overture:
    type: bool
    default: false
  weight:
    type: map
    default: {}
  country:
    type: string
    default: "IN"
  generate_email:
    type: bool
    default: false
  email_model:
    type: string
    default: "gpt-3.5-turbo"
  temperature:
    type: float
    default: 0.7
outputs:
  csv:
    type: string
  xlsx:
    type: string
  email_log:
    type: string
EOF

cat > skills/leadgen_agent/execute.py <<PYEOF
import json, os, pathlib, subprocess, sys, uuid, requests

FREEAPI_URL = "${FREEAPI_URL}"
FREEAPI_KEY = "${FREEAPI_KEY}"

def run_leadgen(repo, market, overture=False, weight=None, country=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    env["LEADGEN_DEFAULT_COUNTRY"] = country or "IN"
    args = [
        "python", "-m", "leadgen",
        "--vertical", "web_design_inau",
        "--market", market,
        "--sources", ("overture," if overture else "") + "osm",
        "--out", "outputs/udaipur",
    ]
    if weight:
        for k,v in weight.items():
            args.extend(["--weight", f"{k}={v}"])
    subprocess.run(args, cwd=repo, env=env, check=True)
    return {
        "csv": str(repo / "outputs" / "udaipur_crm.csv"),
        "xlsx": str(repo / "outputs" / "udaipur.xlsx"),
    }

def generate_email_body(prompt, model="gpt-3.5-turbo", temperature=0.7):
    payload = {"model": model, "messages": [{"role":"user","content":prompt}],
               "temperature": temperature, "max_tokens": 250}
    headers = {"Authorization": f"Bearer {FREEAPI_KEY}", "Content-Type": "application/json"}
    r = requests.post(f"{FREEAPI_URL}/chat/completions", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def main():
    inp = json.load(sys.stdin)
    repo = pathlib.Path(__file__).resolve().parents[3] / "leadgen"
    paths = run_leadgen(repo, inp["market"], inp.get("overture"),
                        inp.get("weight"), inp.get("country","IN"))
    email_log = str(repo / "outputs" / "email_log.jsonl")
    if inp.get("generate_email"):
        import csv
        with open(paths["csv"], newline="", encoding="utf-8") as f, open(email_log,"w",encoding="utf-8") as log:
            reader = csv.DictReader(f)
            for row in reader:
                prompt = (f"Write a professional one-paragraph email introducing "
                          f"{row.get('Business',row.get('name','your business'))} "
                          f"as a potential web-design client in {row.get('City','')}. "
                          f"Tone: friendly, concise. Mention they lack a meta description.")
                body = generate_email_body(prompt, inp.get("email_model","gpt-3.5-turbo"),
                                           inp.get("temperature",0.7))
                log.write(json.dumps({"lead_id":str(uuid.uuid4()),"email_body":body,
                                      "model_used":inp.get("email_model","gpt-3.5-turbo")}) + "\n")
    paths["email_log"] = email_log
    print(json.dumps(paths))

if __name__ == "__main__":
    main()
PYEOF

# ── 9. Cron script ───────────────────────────────────────────────────
cat > cron/run_leadgen_daily.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
hermes cli skill run leadgen_agent \
  --input market="Udaipur, Rajasthan, India" \
  --input overture=true \
  --input generate_email=true \
  --input temperature=0.7
EOF
chmod +x cron/run_leadgen_daily.sh

echo "✅ Done! Agent is at $BASE_DIR"
echo ""
echo "Quick commands:"
echo "  hermes cli skill reload leadgen_agent"
echo "  hermes cli skill run leadgen_agent --input market='Udaipur, Rajasthan, India' --input overture=true --input generate_email=true"
echo "  docker run -d -p 8000:8000 --name leadgen_agent_img leadgen:latest"
echo "  # Add cron: 0 2 * * * $BASE_DIR/cron/run_leadgen_daily.sh >> /tmp/leadgen_daily.log 2>&1"
