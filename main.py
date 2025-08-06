if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    from super_agent.utils.path_utils import get_project_root
    import os
    env_file_path = os.path.join(get_project_root(),"config.env")
    print("环境变量的路径：",env_file_path)
    load_dotenv(dotenv_path="")  # 加载环境变量
    uvicorn.run("super_agent.__main__:app", host="0.0.0.0", port=8000, reload=True)
