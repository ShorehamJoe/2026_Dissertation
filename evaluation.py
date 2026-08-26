

import json
import os
import datetime

EVAL_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evaluation_data")
EVAL_FILE = os.path.join(EVAL_DIR, "responses.json")


QUESTIONS = [

    {
        "id":       "role",
        "section":  "Your profile",
        "text":     "Which best describes your role?",
        "type":     "radio",
        "options":  [
            "Financial / mortgage adviser",
            "Housing policy researcher / analyst",
            "Prospective first-time buyer",
            "Academic / student",
            "Other",
        ],
    },
    {
        "id":       "age_cohort",
        "section":  "Your profile",
        "text":     "Which generational cohort do you belong to?",
        "type":     "radio",
        "options":  ["Gen Z (18-27)", "Millennials (28-43)", "Gen X (44-59)", "Baby Boomers (60-78)"],
    },


    {
        "id":       "useful_overall",
        "section":  "Usefulness",
        "text":     "The dashboard gives me useful information about housing affordability.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "TAM-PU",
    },
    {
        "id":       "useful_generation",
        "section":  "Usefulness",
        "text":     "The generational breakdown (Gen Z, Millennials etc.) adds meaningful insight beyond a single national average.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "Research Q",
    },
    {
        "id":       "useful_forecast",
        "section":  "Usefulness",
        "text":     "The 2025-2027 ML price forecasts would inform decisions I make in my role.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "TAM-PU",
    },
    {
        "id":       "useful_sdlt",
        "section":  "Usefulness",
        "text":     "The stamp duty calculator provides information I would otherwise have to look up elsewhere.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "TAM-PU",
    },


    {
        "id":       "ease_navigation",
        "section":  "Ease of use",
        "text":     "The dashboard is easy to navigate.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "TAM-PEOU",
    },
    {
        "id":       "ease_filters",
        "section":  "Ease of use",
        "text":     "The filters (year, deposit %, property type, personal income) are straightforward to use.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "TAM-PEOU",
    },
    {
        "id":       "ease_interpretation",
        "section":  "Ease of use",
        "text":     "The data presented is easy to interpret without prior knowledge of housing statistics.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "TAM-PEOU",
    },

  
    {
        "id":       "gap_evidence",
        "section":  "Research findings",
        "text":     "The deposit gap analysis (years to save) clearly illustrates the intergenerational housing divide.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "Research Q",
    },
    {
        "id":       "rent_vs_buy",
        "section":  "Research findings",
        "text":     "The rent vs buy comparison reflects the real trade-offs facing younger generations.",
        "type":     "scale",
        "scale":    5,
        "anchors":  ["Strongly disagree", "Strongly agree"],
        "construct": "Research Q",
    },
    {
        "id":       "most_useful_feature",
        "section":  "Research findings",
        "text":     "Which feature did you find most useful?",
        "type":     "radio",
        "options":  [
            "Price trend sparkline (2015-2024)",
            "Years to save deposit by generation",
            "Deposit gap after 5 years",
            "ML price forecast (2025-2027)",
            "Stamp duty calculator",
            "Rent vs buy comparison",
            "LAD-level choropleth map",
            "Personal income adjustment",
        ],
    },


    {
        "id":      "improvements",
        "section": "Open feedback",
        "text":    "What would you change or add to improve the dashboard?",
        "type":    "textarea",
    },
    {
        "id":      "overall_comment",
        "section": "Open feedback",
        "text":    "Any other comments?",
        "type":    "textarea",
    },
]



def save_response(response_data: dict) -> str:
    """
    Save a single evaluation response to the JSON file.

    Args:
        response_data: dict of {question_id: answer}

    Returns:
        Response ID string.
    """
    os.makedirs(EVAL_DIR, exist_ok=True)

    responses = []
    if os.path.exists(EVAL_FILE):
        try:
            with open(EVAL_FILE, encoding="utf-8") as f:
                responses = json.load(f)
        except Exception:
            responses = []

    response_id = f"R{len(responses)+1:03d}"
    response_data["_id"]        = response_id
    response_data["_timestamp"] = datetime.datetime.now().isoformat()
    responses.append(response_data)

    with open(EVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=2)

    return response_id




def analyse_responses() -> dict:
    """
    Generate a summary of all collected evaluation responses.
    Prints a report to stdout and returns the summary dict.
    """
    if not os.path.exists(EVAL_FILE):
        print("No evaluation responses found.")
        print(f"Responses are saved to: {EVAL_FILE}")
        return {}

    with open(EVAL_FILE, encoding="utf-8") as f:
        responses = json.load(f)

    n = len(responses)
    if n == 0:
        print("No responses collected yet.")
        return {}

    print(f"\n{'='*55}")
    print(f"  EVALUATION SUMMARY  ({n} response{'s' if n!=1 else ''})")
    print(f"{'='*55}")

  
    scale_qs = [q for q in QUESTIONS if q["type"] == "scale"]
    print("\n  Likert scale averages (1=strongly disagree, 5=strongly agree):\n")

    scale_summary = {}
    for q in scale_qs:
        vals = [r[q["id"]] for r in responses if q["id"] in r and r[q["id"]]]
        if not vals:
            continue
        avg = sum(int(v) for v in vals) / len(vals)
        bar = "=" * round(avg * 4)
        print(f"  {q['id']:<28}  {avg:.2f}/5  [{bar:<20}]")
        scale_summary[q["id"]] = {"mean": round(avg, 2), "n": len(vals)}

   
    radio_qs = [q for q in QUESTIONS if q["type"] == "radio"]
    print("\n  Multiple choice distributions:\n")

    radio_summary = {}
    for q in radio_qs:
        vals = [r[q["id"]] for r in responses if q["id"] in r and r[q["id"]]]
        if not vals:
            continue
        counts = {opt: vals.count(opt) for opt in (q.get("options", []))}
        print(f"  {q['text'][:55]}")
        for opt, count in sorted(counts.items(), key=lambda x: -x[1]):
            if count:
                pct = count / len(vals) * 100
                print(f"    {opt:<40}  {count} ({pct:.0f}%)")
        radio_summary[q["id"]] = counts

    text_qs = [q for q in QUESTIONS if q["type"] == "textarea"]
    print("\n  Open text responses:\n")
    for q in text_qs:
        vals = [r[q["id"]] for r in responses
                if q["id"] in r and r[q["id"]] and str(r[q["id"]]).strip()]
        print(f"  {q['id']}: {len(vals)} responses received")
        for i, v in enumerate(vals, 1):
            print(f"    R{i}: {str(v)[:120]}")

    print(f"\n{'='*55}")
    print(f"  Responses file: {EVAL_FILE}")
    print(f"{'='*55}\n")

    return {"n": n, "scale": scale_summary, "radio": radio_summary}



def build_eval_form_html(existing_count: int = 0) -> str:
    """Build the evaluation form HTML for embedding in the dashboard."""

    sections = {}
    for q in QUESTIONS:
        sec = q["section"]
        sections.setdefault(sec, []).append(q)

    sections_html = ""
    for sec_name, qs in sections.items():
        sections_html += f'<div class="eval-section"><div class="eval-sec-hdr">{sec_name}</div>'
        for q in qs:
            sections_html += f'<div class="eval-q" id="eq-{q["id"]}">'
            sections_html += f'<div class="eval-q-text">{q["text"]}</div>'

            if q["type"] == "radio":
                for opt in q.get("options", []):
                    safe = opt.replace('"', "&quot;")
                    sections_html += (
                        f'<label class="eval-opt">'
                        f'<input type="radio" name="{q["id"]}" value="{safe}"> {opt}'
                        f'</label>'
                    )

            elif q["type"] == "scale":
                lo, hi = q["anchors"]
                sections_html += f'<div class="eval-scale-wrap">'
                sections_html += f'<span class="eval-anchor">{lo}</span>'
                for v in range(1, q["scale"] + 1):
                    sections_html += (
                        f'<label class="eval-num">'
                        f'<input type="radio" name="{q["id"]}" value="{v}"> {v}'
                        f'</label>'
                    )
                sections_html += f'<span class="eval-anchor">{hi}</span>'
                sections_html += f'</div>'

            elif q["type"] == "textarea":
                sections_html += (
                    f'<textarea name="{q["id"]}" class="eval-textarea" '
                    f'rows="3" placeholder="Optional..."></textarea>'
                )

            sections_html += '</div>'  # eval-q
        sections_html += '</div>'  # eval-section

    return f"""
<div id="eval-panel" style="display:none">
  <div class="eval-header">
    <div class="eval-title">User Evaluation Form</div>
    <div class="eval-sub">
      Dissertation Objective 5 - Sheffield Hallam University<br>
      Your responses are saved locally and used only for academic research.
      {f'<br><strong>{existing_count} response(s) already collected.</strong>' if existing_count else ''}
    </div>
  </div>
  <form id="eval-form">
    {sections_html}
    <div class="eval-submit-row">
      <button type="button" onclick="submitEval()" class="eval-submit">Submit evaluation</button>
      <div id="eval-msg" class="eval-msg"></div>
    </div>
  </form>
</div>
"""
