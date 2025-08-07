# Super Agent

一个智能对话代理系统，包含后端服务和前端UI界面。

## 项目结构

- `super_agent/` - 后端服务
- `super_agent_ui/` - 前端UI界面

## 快速开始

### 1. 启动后端服务

```bash
cd super_agent
uv run main.py

uv run super_agent/agents
```

### 2. 启动前端UI服务

```bash
cd super_agent_ui
pnpm dev
```

### 3. 访问应用

打开浏览器访问 [http://localhost:3000](http://localhost:3000) 开始与智能代理对话。

## 技术栈

- **后端**: Python + UV
- **前端**: React + TypeScript + Vite
- **包管理**: pnpm

## 开发环境要求

- Node.js 18+
- Python 3.10+
- UV (Python包管理器)
- pnpm

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。