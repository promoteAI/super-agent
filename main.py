if __name__ == "__main__":
    import uvicorn
    uvicorn.run("super_agent.__main__:app", host="0.0.0.0", port=8000, reload=True)
