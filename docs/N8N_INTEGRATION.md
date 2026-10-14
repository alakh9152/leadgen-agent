# n8n Integration Guide

Use n8n to automate lead generation, enrichment, and outreach.

## Quick Start

### 1. Get Your API URL
After deploying to Railway, copy your API URL:
```
https://your-app.up.railway.app
```

### 2. Create n8n Workflow

#### Node 1: Cron Trigger
- Type: Cron
- Interval: Daily at 9 AM
- Timezone: Asia/Kolkata (for India)

#### Node 2: HTTP Request (Trigger Lead Run)
- Method: POST
- URL: `{{ $json.api_url }}/api/n8n/run`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body:
  ```json
  {
    "vertical": "web_design_inau",
    "market": "{{ $json.market }}",
    "sources": ["osm"],
    "limit": 300,
    "country": "IN",
    "enrich": true,
    "enrich_cap": 100
  }
  ```

#### Node 3: HTTP Request (Get Leads)
- Method: GET
- URL: `{{ $json.api_url }}/api/runs/{{ $json.run_id }}/leads?limit=50`
- Headers:
  ```
  Authorization: Bearer {{ $json.token }}
  ```

#### Node 4: Code (Filter Tier A)
```javascript
return items.map(item => ({
  json: {
    ...item.json,
    is_tier_a: item.json.tier === 'A'
  }
})).filter(item => item.json.is_tier_a);
```

#### Node 5: Gmail (Send Notification)
- To: your email
- Subject: "New LeadGen Results: {{ $json.market }}"
- Body: "Found {{ $json.total }} leads, {{ $json.tier_a }} Tier A leads"

## Advanced: Automated Outreach

### Setup
1. Connect Gmail/Outlook to n8n
2. Create "Lead Follow-up" workflow
3. Trigger: When new Tier A lead added to database

### Workflow
```
Schedule (daily) → GET /api/runs/{id}/leads?tier=A&status=new
→ Code (prepare email)
→ Gmail (send personalized email)
→ PATCH /api/runs/{id}/leads/{lead_id} (update status to 'contacted')
```

## Example: Weekly Lead Generation

```json
{
  "name": "Weekly Lead Generation",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [{ "field": "weeks", "weeksInterval": 1 }]
        }
      },
      "type": "n8n-nodes-base.scheduleTrigger",
      "name": "Weekly Trigger",
      "position": [-240, 0]
    },
    {
      "parameters": {
        "requestMethod": "POST",
        "url": "https://your-api.up.railway.app/api/n8n/run",
        "authentication": "none",
        "body": {
          "vertical": "web_design_inau",
          "market": "Jaipur, Rajasthan, India",
          "sources": ["osm"],
          "limit": 300,
          "country": "IN"
        }
      },
      "type": "n8n-nodes-base.httpRequest",
      "name": "Start Lead Run",
      "position": [0, 0]
    },
    {
      "parameters": {
        "jsCode": "// Extract run ID from response\nreturn [{ json: { run_id: $node[\"Start Lead Run\"].json.run_id } }]"
      },
      "type": "n8n-nodes-base.code",
      "name": "Extract Run ID",
      "position": [240, 0]
    }
  ]
}
```

## Security Notes

- The `/api/n8n/run` endpoint has no auth (by design for n8n webhooks)
- Protect your Railway instance with IP allowlisting if possible
- Never hardcode API keys in n8n workflow JSON
- Use n8n's built-in credential system for sensitive data
