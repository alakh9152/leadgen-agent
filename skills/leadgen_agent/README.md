# Lead‑Gen Agent Skill

Runs the Lead‑Gen v4 pipeline and optionally generates email bodies via FreeLLMAPI.

**Inputs**
| key | type | description |
|-----|------|-------------|
| market | string | `"Udaipur, Rajasthan, India"` or `"Brisbane, Queensland, Australia"` |
| overture | bool | pull from Overture Maps too |
| weight | map | e.g. `{w_need: 0.6, tier_a_need: 70}` |
| country | string | `"IN"` or `"AU"` |
| generate_email | bool | call FreeLLMAPI for each lead |
| email_model | string | LLM model name (default `gpt-3.5-turbo`) |
| temperature | float | sampling temp (default `0.7`) |

**Outputs**
| key | type | description |
|-----|------|-------------|
| csv | string | path to `_crm.csv` |
| xlsx | string | path to `_xlsx` |
| email_log | string | path to JSONL log of generated emails |
