if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    from super_agent.utils.path_utils import get_project_root
    import os
    import subprocess
    import threading

    # 加载环境变量
    env_file_path = os.path.join(get_project_root(), "config.env")
    print("环境变量的路径：", env_file_path)
    load_dotenv(dotenv_path=env_file_path, override=True)  # 加载环境变量

    # 显示所有加载的环境变量（仅显示config.env中定义的变量）
    print("已加载的环境变量：")
    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                value = os.environ.get(key)
                print(f"{key} = {value}")

    # 导入settings并显示
    from super_agent.settings import settings
    print("配置:", settings)

    # 启动 super_agent/agents/ 目录下的命令（假设为 main.py）
    def run_agents():
        # 这里假设 agents 目录下有 main.py 作为入口
        agents_path = os.path.join(get_project_root(), "super_agent", "agents", "__main__.py")
        if os.path.exists(agents_path):
            print("启动 agents 服务：", agents_path)
            subprocess.run(["uv", "run", agents_path])
        else:
            print("未找到 agents/main.py，未启动 agents 服务。")
    
     # 启动 super-agent/super_agent_ui 前端
    def run_ui():
        # 进入前端目录并执行 pnpm dev
        ui_path = os.path.join(get_project_root(), "super_agent_ui")
        print("启动 ui 服务：", ui_path)
        # 先进入目录，再执行 pnpm dev
        subprocess.run(["pnpm", "dev"], cwd=ui_path)

    # 使用线程同时启动后端 agents 和前端 ui
    agents_thread = threading.Thread(target=run_agents)
    ui_thread = threading.Thread(target=run_ui)
    agents_thread.start()
    ui_thread.start()

    # 启动主 FastAPI 服务
    uvicorn.run("super_agent.__main__:app", host="0.0.0.0", port=8000, reload=True)
