# AI Lead Qualification Automation

An AI-powered pipeline that reads raw leads from a CSV file, analyzes each lead using
OpenAI, and outputs a fully qualified leads report with scores, industry
tags, business needs, and recommended sales actions.

---

### 1. Clone / Download the project

```bash
git clone <your-repo-url>
cd project_lead
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your OpenAI API Key in .env

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-...your-key-here...
```

```bash
export OPENAI_API_KEY=sk-...your-key-here...   # in macOS/Linux
set OPENAI_API_KEY=sk-...your-key-here...      # in Windows CMD
```

### 5. Run the pipeline

```bash
python main.py
```

---

##  Output

After running, `leads.csv` is generated with these columns:

| Column | Description |
|---|---|
| Name | Lead's full name |
| Email | Lead's email address |
| Company | Company name |
| Job Title | Lead's role |
| Lead Score | 0–100 numeric score |
| Tier | Hot 🔥 / Warm 🟡 / Cold 🔵 |
| Industry | Industry category (e.g. SaaS, HealthTech) |
| Business Need | AI-identified primary need |
| Recommended Action | Suggested next step for sales |
| Reasoning | Short explanation of the score |
| Original Message | The raw message from the lead |

### Example Output

```
Lead Name   : Sarah Johnson
Company     : BrightTech
Score       : 82  🔥 Hot
Industry    : SaaS / Operations
Business Need: Workflow automation to reduce manual repetitive work
Recommended Action: Schedule a product demo with the sales team
```

---

##  Workflow Diagram

```
CSV Input (leads.csv)
        │
        ▼
  Load & Parse Leads
        │
        ▼

    For each lead:                     
      → Build prompt                   
      → Call OpenAI (for api key)      
      → Parse JSON response            
      → Merge with original lead data  
        │
        ▼
  Save to qualified_leads.csv
        │
        ▼ (if given)
  Push to Google Sheets
        │
        ▼
  Print Summary Report
```

---

##  if you want : Google Sheets Integration

To push results to a Google Sheet:

1. Create a Google Cloud project and enable the **Google Sheets API** and **Google Drive API**.
2. Create a **Service Account** and download the JSON credentials file.
3. Share your Google Sheet with the service account email.
4. Set these environment variables:

```
USE_GOOGLE_SHEETS=true
GOOGLE_SHEET_ID= your_google_sheet_ID
GOOGLE_CREDS_FILE=google_credentials.json
```

---

