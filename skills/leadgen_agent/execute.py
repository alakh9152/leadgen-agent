import json, os, pathlib, subprocess, sys, uuid, requests

FREEAPI_URL = "http://localhost:3001/v1"
FREEAPI_KEY = "freellmapi-2c9dd00adc578b8892aab26463e9fcca2587103a5bd84aa3"

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
                name = row.get("Business", row.get("name", "your business"))
                city = row.get("City", "")
                cat  = row.get("Category", "")
                prompt = (
                    f"Write a professional one-paragraph cold outreach email to introduce "
                    f"web design services to {name}, a {cat} in {city}. "
                    f"Tone: friendly and concise. Mention they lack a meta description on their website "
                    f"and could benefit from a modern, mobile-friendly site."
                )
                body = generate_email_body(prompt, inp.get("email_model","gpt-3.5-turbo"),
                                           inp.get("temperature",0.7))
                log.write(json.dumps({"lead_id":str(uuid.uuid4()),"email_body":body,
                                      "model_used":inp.get("email_model","gpt-3.5-turbo")}) + "\n")
    paths["email_log"] = email_log
    print(json.dumps(paths))

if __name__ == "__main__":
    main()
