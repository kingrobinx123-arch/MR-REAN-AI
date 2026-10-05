import asyncio
import os
import threading
import tempfile
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from app.config import TELEGRAM_BOT_TOKEN, AI_PROVIDER, MAX_UPLOAD_MB
from app.db import upsert_user, get_user, consume_credit
from app.workspace import extract_zip, export_zip, user_root
from app.agent import repair_project

def _user(update):
    u=update.effective_user
    upsert_user(u.id, u.username or "")
    return u

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u=_user(update)
    await update.message.reply_text("🤖 MR REAN AI V3\nSend a ZIP project, then say: `সব error fix করে zip দাও`\n/status = credit\n/files = project files\n/export = export ZIP")

async def status(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u=_user(update); x=get_user(u.id)
    await update.message.reply_text(f"👤 {u.username or u.id}\n💰 Daily credit: {x['daily_credits']}\n📊 Used today: {x['used_today']}\n🚫 Blocked: {'Yes' if x['blocked'] else 'No'}")

async def files_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u=_user(update); root=os.path.join(user_root(u.id),"project")
    if not os.path.isdir(root): return await update.message.reply_text("📁 No project uploaded.")
    names=[]
    for base,dirs,fs in os.walk(root):
        dirs[:]=[d for d in dirs if d not in {".git","node_modules","__pycache__"}]
        for f in fs: names.append(os.path.relpath(os.path.join(base,f),root).replace(os.sep,"/"))
    text="📁 Files:\n"+"\n".join(names[:150])
    if len(names)>150: text+=f"\n... +{len(names)-150} more"
    await update.message.reply_text(text[:3900])

async def new_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u=_user(update); root=os.path.join(user_root(u.id),"project")
    import shutil
    shutil.rmtree(root,ignore_errors=True); os.makedirs(root,exist_ok=True)
    await update.message.reply_text("🆕 Project cleared.")

async def export_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u=_user(update)
    try:
        out=export_zip(u.id)
    except Exception as e:
        return await update.message.reply_text(f"❌ {e}")
    await update.message.reply_document(document=InputFile(out),filename="MR_REAN_FIXED_PROJECT.zip")

async def document(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u=_user(update); x=get_user(u.id)
    if x["blocked"]: return await update.message.reply_text("🚫 Your account is blocked.")
    doc=update.message.document
    if not doc.file_name.lower().endswith(".zip"): return await update.message.reply_text("📦 Please send a ZIP project.")
    if doc.file_size and doc.file_size > MAX_UPLOAD_MB*1024*1024: return await update.message.reply_text("⚠️ ZIP is too large.")
    if not consume_credit(u.id,AI_PROVIDER,"upload"): return await update.message.reply_text("⚠️ Daily credit শেষ.")
    msg=await update.message.reply_text("📦 ZIP received. Extracting...")
    root=user_root(u.id)
    tmp=os.path.join(root,"upload.zip")
    tg=await doc.get_file(); await tg.download_to_drive(tmp)
    try:
        extract_zip(u.id,tmp)
        await msg.edit_text("✅ Project ready. এখন লিখো: `সব error fix করে zip দাও` অথবা `/fix ...`")
    except Exception as e:
        await msg.edit_text(f"❌ ZIP rejected: {e}")

async def fix_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u=_user(update); x=get_user(u.id)
    if x["blocked"]: return await update.message.reply_text("🚫 Your account is blocked.")
    root=os.path.join(user_root(u.id),"project")
    if not os.path.isdir(root): return await update.message.reply_text("📦 আগে ZIP upload করো.")
    if not consume_credit(u.id,AI_PROVIDER,"fix"): return await update.message.reply_text("⚠️ Daily credit শেষ.")
    request=" ".join(context.args).strip() or "Find and fix project errors, then make the project internally consistent."
    await _do_fix(update,u.id,request)

async def text_task(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u=_user(update); x=get_user(u.id)
    if x["blocked"]: return await update.message.reply_text("🚫 Your account is blocked.")
    text=(update.message.text or "").strip()
    if not text: return
    root=os.path.join(user_root(u.id),"project")
    if os.path.isdir(root) and any(k in text.lower() for k in ["fix","error","bug","ত্রুটি"]):
        if not consume_credit(u.id,AI_PROVIDER,"fix"): return await update.message.reply_text("⚠️ Daily credit শেষ.")
        await _do_fix(update,u.id,text)
    else:
        await update.message.reply_text("💡 ZIP upload করে project task দাও. Example: `সব error fix করে zip দাও`")

async def _do_fix(update,tid,request):
    msg=await update.message.reply_text("🧠 AI inspecting project...")
    try:
        result=await asyncio.to_thread(repair_project,os.path.join(user_root(tid),"project"),request)
        if result["ok"]:
            out=export_zip(tid)
            await msg.edit_text(f"✅ Fixed!\n🤖 Provider: {result['provider']}\n📝 {result['summary']}\n📁 Changed: {len(result['files'])}\n🔍 Attempts: {result['attempts']}")
            await update.message.reply_document(document=InputFile(out),filename="MR_REAN_FIXED_PROJECT.zip")
        else:
            await msg.edit_text("⚠️ AI changes were made but verification still reports errors:\n" + "\n".join(result["errors"][:10]))
            out=export_zip(tid)
            await update.message.reply_document(document=InputFile(out),filename="MR_REAN_PARTIAL_PROJECT.zip")
    except Exception as e:
        await msg.edit_text(f"❌ AI task failed: {e}")

def run():
    if not TELEGRAM_BOT_TOKEN:
        return
    async def main():
        app=Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start",start))
        app.add_handler(CommandHandler("status",status))
        app.add_handler(CommandHandler("files",files_cmd))
        app.add_handler(CommandHandler("new",new_cmd))
        app.add_handler(CommandHandler("export",export_cmd))
        app.add_handler(CommandHandler("fix",fix_cmd))
        app.add_handler(MessageHandler(filters.Document.ALL,document))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text_task))
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()
    asyncio.run(main())

def start_background():
    threading.Thread(target=run,daemon=True).start()
