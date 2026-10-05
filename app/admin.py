from html import escape
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.auth import valid_admin, is_logged_in
from app.db import list_users, set_blocked, set_credits, stats

router=APIRouter()

CSS='''<style>
body{font-family:system-ui,-apple-system,sans-serif;background:#0b1020;color:#eef2ff;margin:0;padding:22px}
.wrap{max-width:1100px;margin:auto}.card{background:#151c31;border:1px solid #29334f;border-radius:16px;padding:18px;margin:14px 0}
input,button{padding:9px;border-radius:9px;border:1px solid #46516d;background:#0d1425;color:#fff}
button{cursor:pointer;background:#273451}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
table{width:100%;border-collapse:collapse}td,th{padding:9px;border-bottom:1px solid #29334f;text-align:left}
a{color:#fff}.muted{color:#aab4cc}@media(max-width:700px){.grid{grid-template-columns:1fr}table{font-size:12px}}
</style>'''

@router.get("/admin/login",response_class=HTMLResponse)
def login_page():
    return HTMLResponse(CSS+'''<div class="wrap"><div class="card"><h1>👑 MR REAN AI Admin</h1>
    <form method="post"><p><input name="username" placeholder="Admin username" required></p>
    <p><input name="password" type="password" placeholder="Admin password" required></p>
    <button type="submit">Login</button></form></div></div>''')

@router.post("/admin/login")
def login(username:str=Form(...),password:str=Form(...)):
    if not valid_admin(username,password):
        return HTMLResponse(CSS+"<div class='wrap'><div class='card'>❌ Invalid login</div></div>",401)
    r=RedirectResponse("/admin",303)
    r.set_cookie("mr_rean_admin","1",httponly=True,samesite="lax",secure=True)
    return r

@router.get("/admin/logout")
def logout():
    r=RedirectResponse("/admin/login",303); r.delete_cookie("mr_rean_admin"); return r

@router.get("/admin",response_class=HTMLResponse)
def dashboard(request:Request):
    if not is_logged_in(request): return RedirectResponse("/admin/login",303)
    s=stats()
    html=CSS+f'''<div class="wrap"><h1>👑 MR REAN AI V3</h1>
    <p class="muted">Admin control panel</p>
    <p><a href="/admin/logout">Logout</a> · <a href="/">Home</a></p>
    <div class="grid"><div class="card">👥 Users<br><b>{s["users"]}</b></div>
    <div class="card">🚫 Blocked<br><b>{s["blocked"]}</b></div>
    <div class="card">📊 Total usage<br><b>{s["usage"]}</b></div></div>
    <div class="card"><h2>Users</h2><div style="overflow:auto"><table>
    <tr><th>Telegram</th><th>User</th><th>Status</th><th>Daily</th><th>Used</th><th>Controls</th></tr>'''
    for u in list_users():
        status="🚫" if u["blocked"] else "🟢"
        action="Unblock" if u["blocked"] else "Block"
        html += f'''<tr><td>{escape(str(u["telegram_id"]))}</td><td>{escape(u["username"] or "-")}</td>
        <td>{status}</td><td><form method="post" action="/admin/users/credits">
        <input type="hidden" name="tid" value="{escape(str(u["telegram_id"]))}">
        <input name="credits" type="number" min="0" value="{u["daily_credits"]}" style="width:70px">
        <button>Save</button></form></td><td>{u["used_today"]}</td><td>
        <form method="post" action="/admin/users/block"><input type="hidden" name="tid" value="{escape(str(u["telegram_id"]))}">
        <input type="hidden" name="blocked" value="{0 if u["blocked"] else 1}"><button>{action}</button></form></td></tr>'''
    return HTMLResponse(html+"</table></div></div></div>")

@router.post("/admin/users/block")
def block(request:Request,tid:str=Form(...),blocked:int=Form(...)):
    if not is_logged_in(request): return RedirectResponse("/admin/login",303)
    set_blocked(tid,blocked); return RedirectResponse("/admin",303)

@router.post("/admin/users/credits")
def credits(request:Request,tid:str=Form(...),credits:int=Form(...)):
    if not is_logged_in(request): return RedirectResponse("/admin/login",303)
    set_credits(tid,credits); return RedirectResponse("/admin",303)
