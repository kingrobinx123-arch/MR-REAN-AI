import json
import time
import requests
from app.config import GEMINI_API_KEY, OPENAI_API_KEY, MANUS_API_KEY

TIMEOUT = 90

SYSTEM = '''You are MR REAN AI, a careful software repair agent.
Given a project snapshot and a user request, inspect the files and return ONLY valid JSON:
{
  "summary": "short summary",
  "changes": [
    {"path": "relative/path.ext", "content": "COMPLETE new file content"}
  ]
}
Rules:
- Only modify files needed for the request.
- Return complete file content, not diffs.
- Never use absolute paths.
- Never add secrets or API keys.
- Do not invent files unless needed.
'''

def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n",1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3]
    try:
        return json.loads(text)
    except Exception:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end+1])
        raise ValueError("AI did not return valid JSON.")

def _prompt(user_request, context, errors):
    return SYSTEM + "\nUSER REQUEST:\n" + user_request + "\n\nVERIFICATION ERRORS:\n" + ("\n".join(errors) if errors else "none") + "\n\nPROJECT FILES:\n" + context

def gemini(prompt):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    r = requests.post(url, headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type":"application/json"},
                      json={"contents":[{"parts":[{"text":prompt}]}],
                            "generationConfig":{"responseMimeType":"application/json"}},
                      timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return _extract_json(text)

def openai(prompt):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    url = "https://api.openai.com/v1/responses"
    r = requests.post(url, headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"},
                      json={"model":"gpt-5","input":[
                          {"role":"system","content":SYSTEM},
                          {"role":"user","content":prompt}
                      ]}, timeout=TIMEOUT)
    r.raise_for_status()
    data=r.json()
    text=data.get("output_text")
    if not text:
        for item in data.get("output",[]):
            for c in item.get("content",[]):
                if c.get("type")=="output_text":
                    text=c.get("text","")
                    break
    return _extract_json(text)

def manus(prompt):
    if not MANUS_API_KEY:
        raise RuntimeError("MANUS_API_KEY is not configured.")
    url="https://api.manus.ai/v2/task.create"
    schema={
        "type":"object",
        "properties":{
            "summary":{"type":"string"},
            "changes":{"type":"array","items":{"type":"object","properties":{
                "path":{"type":"string"},"content":{"type":"string"}
            },"required":["path","content"],"additionalProperties":False}}
        },
        "required":["summary","changes"],"additionalProperties":False
    }
    r=requests.post(url,headers={"Content-Type":"application/json","x-manus-api-key":MANUS_API_KEY},
                    json={"message":{"content":prompt},"agent_profile":"standard",
                          "title":"MR REAN project repair","structured_output_schema":schema},
                    timeout=TIMEOUT)
    r.raise_for_status()
    task=r.json()["task_id"]
    deadline=time.time()+240
    while time.time()<deadline:
        q=requests.get("https://api.manus.ai/v2/task.listMessages",
                       headers={"x-manus-api-key":MANUS_API_KEY},
                       params={"task_id":task,"order":"desc","limit":50},timeout=30)
        q.raise_for_status()
        data=q.json()
        for m in data.get("messages",[]):
            if m.get("type")=="structured_output_result":
                result=m.get("structured_output_result",{})
                if result.get("success"):
                    return result.get("value",{})
                raise RuntimeError(result.get("error","Manus structured output failed"))
            if m.get("type")=="error_message":
                raise RuntimeError(m.get("error_message",{}).get("content","Manus error"))
        time.sleep(4)
    raise TimeoutError("Manus task timed out.")

def ask(provider, prompt):
    provider=(provider or "auto").lower()
    funcs={"gemini":gemini,"openai":openai,"manus":manus}
    if provider in funcs:
        return funcs[provider](prompt), provider
    errors=[]
    for name in ("gemini","openai","manus"):
        try:
            return funcs[name](prompt), name
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise RuntimeError("All configured AI providers failed: " + " | ".join(errors))
