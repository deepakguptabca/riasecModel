from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import os, json, time
from dotenv import load_dotenv
from google import genai

# ---------------- ENV ----------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY","AIzaSyCB_SljG27O4qdKUS3nUxXJKr8StKCwE9M")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY missing")

client = genai.Client(api_key=API_KEY)

# ---------------- APP ----------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ---------------- RIASEC ----------------
RIASEC_ORDER = ["R","I","A","S","E","C","R","I","A","S","E","C"]

RIASEC_INTENTS = {
    "R": "hands-on work, tools, machines, physical tasks",
    "I": "problem solving, logic, analysis, critical thinking",
    "A": "creativity, imagination, design, expression",
    "S": "helping, teaching, guiding, supporting people",
    "E": "leading, persuading, decision making, business thinking",
    "C": "organizing, planning, working with data and rules"
}

OPTION_SCORES = [3,2,1,0]

# ---------------- STATE ----------------
questions = []
questions_ready = False

state = {
    "current": 0,
    "scores": {"R":0,"I":0,"A":0,"S":0,"E":0,"C":0}
}

# ---------------- GEMINI ----------------
def generate_all_questions():
    mapping = ""
    for i, r in enumerate(RIASEC_ORDER, start=1):
        mapping += f"{i}. {r}: {RIASEC_INTENTS[r]}\n"

    prompt = f"""
Generate EXACTLY 12 UNIQUE student-life scenario questions with equal weight options.

Each question must follow the assigned intent.

Assigned intents:
{mapping}

Rules:
- Do NOT mention psychology or RIASEC
- Real-life student situations
- Exactly 4 options each
- All questions MUST be different
- Simple English
- RETURN ONLY JSON ARRAY
- Each item must have ONLY: question, options
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    data = json.loads(raw)

    if not isinstance(data, list) or len(data) != 12:
        raise ValueError("Invalid Gemini response")

    # 🔥 IMPORTANT FIX: inject riasec ourselves
    final_questions = []
    for i, q in enumerate(data):
        final_questions.append({
            "riasec": RIASEC_ORDER[i],
            "question": q["question"],
            "options": q["options"]
        })

    return final_questions



# ---------------- ROUTES ----------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/start")
def start_test():
    global questions, questions_ready

    questions_ready = False
    questions = []

    state["current"] = 0
    state["scores"] = {"R":0,"I":0,"A":0,"S":0,"E":0,"C":0}

    try:
        questions = generate_all_questions()
        questions_ready = True
    except Exception as e:
        print("❌ GEMINI FAILED:", e)
        questions_ready = False

    return {"ready": questions_ready}

@app.get("/question")
def get_question():
    if not questions_ready:
        return {"loading": True}

    i = state["current"]

    if i >= len(questions):
        return {"done": True}

    q = questions[i]
    return {
        "riasec": q["riasec"],
        "question": q["question"],
        "options": q["options"],
        "step": i + 1,
        "total": len(questions)
    }

@app.post("/answer")
async def submit_answer(payload: dict):
    state["scores"][payload["riasec"]] += OPTION_SCORES[payload["option"]]
    state["current"] += 1
    return {"ok": True}


@app.get("/result")
def result():
    sorted_scores = sorted(
        state["scores"].items(),
        key=lambda x: x[1],
        reverse=True
    )
    code = "".join([x[0] for x in sorted_scores[:3]])
    return {"code": code, "scores": state["scores"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
