import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.db import init_db
from app.admin import router as admin_router
from app.telegram_bot import start_background

app=FastAPI(title="MR REAN AI V3 FINAL")
app.include_router(admin_router)

@app.on_event("startup")
def startup():
    init_db()
    start_background()

@app.get("/",response_class=HTMLResponse)
def home():
    domain=os.getenv("RAILWAY_PUBLIC_DOMAIN","")
    link=(f"https://{domain}/admin" if domain else "/admin")
    return f'''<html><head><title>MR REAN AI</title><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="font-family:system-ui;background:#0b1020;color:white;padding:40px;text-align:center">
    <h1>🤖 MR REAN AI V3</h1><p>Telegram AI Agent is running.</p>
    <p><a href="{link}" style="color:white;background:#334155;padding:12px 18px;border-radius:10px;text-decoration:none">👑 Open Admin Panel</a></p>
    <p style="opacity:.7">{domain}</p></body></html>'''

@app.get("/health")
def health():
    return {"ok":True,"service":"MR REAN AI V3 FINAL"}
