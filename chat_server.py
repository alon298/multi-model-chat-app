#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-Model Chat App - 多模型对话应用后端（对标 LobeChat/Open WebUI）。"""
import json, os, sqlite3, time
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

DB = "chat.db"
MODELS = {
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "key_env": "DEEPSEEK_API_KEY"},
    "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus", "key_env": "QWEN_API_KEY"},
    "gpt": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "key_env": "OPENAI_API_KEY"},
}
TEMPLATES = {
    "translate": "将以下内容翻译为英文：{text}",
    "weekly": "把以下工作记录整理成周报，分【本周完成】【风险】【下周计划】：{text}",
    "support": "你是电商客服，仅依据商品资料回答，礼貌简洁：{text}",
}

app = FastAPI(title="Multi-Model Chat App")

def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS messages "
                 "(id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT, model TEXT, ts REAL)")
    return conn

class ChatRequest(BaseModel):
    model: str = "deepseek"
    session_id: str = "default"
    message: str
    template: str | None = None

def history(session_id, limit=20):
    with db() as conn:
        rows = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
                            (session_id, limit)).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def stream_llm(req: ChatRequest):
    prompt = TEMPLATES.get(req.template, "{text}").format(text=req.message) if req.template else req.message
    msgs = history(req.session_id) + [{"role": "user", "content": prompt}]
    cfg = MODELS.get(req.model) or MODELS["deepseek"]
    key = os.environ.get(cfg["key_env"])
    with db() as conn:
        conn.execute("INSERT INTO messages(session_id, role, content, model, ts) VALUES(?,?,?,?,?)",
                     (req.session_id, "user", prompt, req.model, time.time()))
    if not key:  # Mock 模式：逐字流式回显
        reply = f"[mock:{req.model}] 已收到：{prompt[:50]}…（配置 {cfg['key_env']} 后接入真实模型）"
        full = []
        for ch in reply:
            full.append(ch)
            yield f"data: {json.dumps({'delta': ch}, ensure_ascii=False)}\n\n"
            time.sleep(0.02)
        text = "".join(full)
    else:
        import requests
        r = requests.post(f"{cfg['base_url']}/chat/completions", stream=True, timeout=60, headers={
            "Authorization": f"Bearer {key}"}, json={"model": cfg["model"], "messages": msgs, "stream": True})
        text = []
        for line in r.iter_lines():
            if line and line.startswith(b"data: ") and line != b"data: [DONE]":
                delta = json.loads(line[6:])["choices"][0]["delta"].get("content", "")
                if delta:
                    text.append(delta)
                    yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
        text = "".join(text)
    with db() as conn:
        conn.execute("INSERT INTO messages(session_id, role, content, model, ts) VALUES(?,?,?,?,?)",
                     (req.session_id, "assistant", text, req.model, time.time()))
    yield "data: [DONE]\n\n"

@app.post("/api/chat")
def chat(req: ChatRequest):
    if req.model not in MODELS:
        raise HTTPException(400, f"未知模型: {req.model}")
    return StreamingResponse(stream_llm(req), media_type="text/event-stream")

@app.get("/api/sessions/{sid}/history")
def get_history(sid: str):
    return {"session_id": sid, "messages": history(sid)}

@app.get("/api/models")
def list_models():
    return [{"name": n, "model": c["model"], "available": bool(os.environ.get(c["key_env"]))} for n, c in MODELS.items()]

@app.get("/api/templates")
def list_templates():
    return TEMPLATES
