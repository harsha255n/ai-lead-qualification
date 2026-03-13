
import csv
import json
import os
import time
from pathlib import Path
from openai import OpenAI


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
INPUT_CSV      = "leads.csv"
OUTPUT_CSV     = "qualified_leads.csv"
MODEL          = "gpt-4o-mini"          
BATCH_DELAY    = 0.5                    


USE_GOOGLE_SHEETS  = os.getenv("USE_GOOGLE_SHEETS", "false").lower() == "true"
GOOGLE_SHEET_ID    = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_FILE  = os.getenv("GOOGLE_CREDS_FILE", "google_credentials.json")

client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are an expert B2B sales qualification AI. Your job is to analyze incoming leads
and determine how valuable they are to a software/SaaS company.

For each lead you receive, you must respond with ONLY a valid JSON object (no extra text)
containing exactly these fields:

{
  "lead_score": <integer 0-100>,
  "industry": "<industry category>",
  "business_need": "<concise description of the lead's primary business need>",
  "recommended_action": "<specific recommended next step for the sales team>",
  "qualification_tier": "<Hot|Warm|Cold>",
  "reasoning": "<1-2 sentence explanation of the score>"
}

Scoring guidelines:
- 80-100 (Hot)  : Decision-maker, clear pain point, enterprise/mid-market company, high urgency
- 50-79  (Warm) : Potential buyer, some indicators of need but missing urgency or authority
- 0-49   (Cold) : Early stage, unclear need, very small budget, or non-decision-maker

Be accurate and objective. Do not over-inflate scores.
""".strip()


def build_user_prompt(lead: dict) -> str:
    return f"""
Analyze the following lead:

Name       : {lead.get('Name', 'N/A')}
Email      : {lead.get('Email', 'N/A')}
Company    : {lead.get('Company Name', 'N/A')}
Job Title  : {lead.get('Job Title', 'N/A')}
Message    : {lead.get('Message from Lead', 'N/A')}

Return ONLY the JSON object as described.
""".strip()



#  API Call

def analyze_lead(lead: dict, retries: int = 3) -> dict:
    """Send a lead to OpenAI and parse the JSON response."""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": build_user_prompt(lead)},
                ],
                temperature=0.2,
                max_tokens=400,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content.strip()
            return json.loads(raw)

        except json.JSONDecodeError as e:
            print(f"  [!] JSON parse error on attempt {attempt+1}: {e}")
        except Exception as e:
            print(f"  [!] API error on attempt {attempt+1}: {e}")
            time.sleep(2 ** attempt)  

   
    return {
        "lead_score": 0,
        "industry": "Unknown",
        "business_need": "Could not analyze",
        "recommended_action": "Manual review required",
        "qualification_tier": "Cold",
        "reasoning": "API error — please review manually.",
    }



# CSV 

def load_leads(filepath: str) -> list[dict]:
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_results_csv(results: list[dict], filepath: str) -> None:
    if not results:
        print("No results to save.")
        return

    fieldnames = list(results[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Results saved to: {filepath}")



#  Google Sheets 

# def push_to_google_sheets(results: list[dict]) -> None:
   
#     try:
#         import gspread
#         from google.oauth2.service_account import Credentials

#         scopes = [
#             "https://www.googleapis.com/auth/spreadsheets",
#             "https://www.googleapis.com/auth/drive",
#         ]
#         creds  = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scopes)
#         gc     = gspread.authorize(creds)
#         sheet  = gc.open_by_key(GOOGLE_SHEET_ID).sheet1

       
#         if results:
#             headers = list(results[0].keys())
#             sheet.clear()
#             sheet.append_row(headers)
#             for row in results:
#                 sheet.append_row(list(row.values()))

#         print(f"✅ Results pushed to Google Sheets (ID: {GOOGLE_SHEET_ID})")

#     except ImportError:
#         print("⚠️  gspread not installed. Run: pip install gspread google-auth")
#     except Exception as e:
#         print(f"⚠️  Google Sheets error: {e}")



# Main Workflow

def run_pipeline(input_csv: str = INPUT_CSV, output_csv: str = OUTPUT_CSV) -> list[dict]:
    print("=" * 60)
    print("  AI Lead Qualification Automation")
    print("=" * 60)

    leads = load_leads(input_csv)
    print(f"\n📋 Loaded {len(leads)} leads from '{input_csv}'\n")

    results = []

    for i, lead in enumerate(leads, start=1):
        name    = lead.get("Name", "Unknown")
        company = lead.get("Company Name", "Unknown")
        print(f"[{i:02d}/{len(leads)}] Analyzing: {name} @ {company} ...", end=" ", flush=True)

        analysis = analyze_lead(lead)

       
        result = {
            "Name"              : lead.get("Name", ""),
            "Email"             : lead.get("Email", ""),
            "Company"           : lead.get("Company Name", ""),
            "Job Title"         : lead.get("Job Title", ""),
            "Lead Score"        : analysis.get("lead_score", 0),
            "Tier"              : analysis.get("qualification_tier", "Cold"),
            "Industry"          : analysis.get("industry", ""),
            "Business Need"     : analysis.get("business_need", ""),
            "Recommended Action": analysis.get("recommended_action", ""),
            "Reasoning"         : analysis.get("reasoning", ""),
            "Original Message"  : lead.get("Message from Lead", ""),
        }

        tier_emoji = {"Hot": "🔥", "Warm": "🟡", "Cold": "🔵"}.get(result["Tier"], "⚪")
        print(f"Score: {result['Lead Score']:3d}  {tier_emoji} {result['Tier']}")

        results.append(result)
        time.sleep(BATCH_DELAY)

 
    save_results_csv(results, output_csv)

    # if USE_GOOGLE_SHEETS and GOOGLE_SHEET_ID:
    #     push_to_google_sheets(results)

    # ── Summary ──
    hot  = sum(1 for r in results if r["Tier"] == "Hot")
    warm = sum(1 for r in results if r["Tier"] == "Warm")
    cold = sum(1 for r in results if r["Tier"] == "Cold")

    print("\n" + "=" * 60)
    print("  Pipeline Summary")
    print("=" * 60)
    print(f"  Total Leads Processed : {len(results)}")
    print(f"  🔥 Hot   (80-100)     : {hot}")
    print(f"  🟡 Warm  (50-79)      : {warm}")
    print(f"  🔵 Cold  (0-49)       : {cold}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_pipeline()
