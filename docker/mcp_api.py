from flask import Flask, request, jsonify
import subprocess, json, os

app = Flask(__name__)

@app.route("/leadgen", methods=["POST"])
def run_leadgen():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error":"bad JSON"}), 400
    cmd = ["python","-m","leadgen","--vertical","web_design_inau",
           "--market", payload.get("market","Udaipur, Rajasthan, India"),
           "--sources", ("overture," if payload.get("overture") else "") + "osm",
           "--out", "outputs/udaipur"]
    w = payload.get("weight", {})
    if w:
        for k,v in w.items():
            cmd += ["--weight", f"{k}={v}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd="/app",
                          env={**os.environ, "LEADGEN_DEFAULT_COUNTRY": payload.get("country","IN")})
    if proc.returncode != 0:
        return jsonify({"error": proc.stderr}), 500
    return jsonify({"status":"ok","csv":"/app/outputs/udaipur_crm.csv","xlsx":"/app/outputs/udaipur.xlsx"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
