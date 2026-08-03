# Multi-Model Chat App · 多模型对话应用

> 个人开源对标 LobeChat / Open WebUI 的轻量级多模型对话后端。

## 核心特性

- **多模型切换**：DeepSeek / 通义千问 / GPT 统一适配层，OpenAI 兼容协议
- **SSE 流式输出**：`/api/chat` 逐 token 推送
- **会话记忆管理**：SQLite 持久化，支持多会话与历史回放
- **Prompt 模板库**：内置翻译 / 周报 / 客服等模板，可自定义扩展
- **插件系统**：函数注册 + 模型自主选择调用
- **Mock 模式**：无 API Key 也可完整体验全部接口（本地演示/联调）

## 快速开始

```bash
pip install -r requirements.txt
uvicorn chat_server:app --port 8300

# 多模型对话（SSE）
curl -N -X POST localhost:8300/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek","session_id":"s1","message":"用一句话介绍RAG"}'

# 历史回放
curl localhost:8300/api/sessions/s1/history
```

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/chat | 对话（SSE 流式） |
| GET | /api/sessions/{sid}/history | 会话历史 |
| GET | /api/models | 模型列表 |
| GET | /api/templates | Prompt 模板库 |

## 技术栈

Python 3.10+ / FastAPI / SQLite / SSE；可选 DeepSeek·通义千问·GPT API。

## 路线图

- [x] 多模型切换与 SSE 流式
- [x] 会话记忆与 SQLite 持久化
- [x] Prompt 模板库与插件注册
- [ ] Web 前端界面
- [ ] 私有化部署一键脚本

## License

MIT
