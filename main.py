import subprocess
import multiprocessing
import time

def start_service(cmd, name):
    try:
        print(f"正在启动{name}...")
        # 使用subprocess.Popen启动服务，不阻塞主进程
        process = subprocess.Popen(cmd, shell=True)
        print(f"{name} 启动成功，进程ID: {process.pid}")
        return process
    except Exception as e:
        print(f"{name} 启动失败: {e}")
        return None

def service_worker(cmd, name):
    process = start_service(cmd, name)
    if process:
        process.wait()  # 保持子进程运行

def main():
    services = [
        ("uv run super_agent --run mcp-server --transport sse", "MCP服务"),
        ("uv run super_agent/agents/ --agent-card super_agent/agent_cards/orchestrator_agent.json --port 10101", "Orchestrator 代理"),
        ("uv run super_agent/agents/ --agent-card super_agent/agent_cards/planner_agent.json --port 10102", "Planner 代理"),
        ("uv run super_agent/agents/ --agent-card super_agent/agent_cards/air_ticketing_agent.json --port 10103", "Airline Ticketing Agent"),
        ("uv run super_agent/agents/ --agent-card super_agent/agent_cards/hotel_booking_agent.json --port 10104", "Hotel Reservations Agent"),
        ("uv run super_agent/agents/ --agent-card super_agent/agent_cards/car_rental_agent.json --port 10105", "Car Rental Reservations Agent")
    ]

    processes = []
    for cmd, name in services:
        p = multiprocessing.Process(target=service_worker, args=(cmd, name))
        p.start()
        processes.append(p)

    # 等待所有子进程启动
    time.sleep(2)
    print("所有服务已启动。请检查各服务日志以确认运行状态。")

    # 保持主进程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止所有服务...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        print("所有服务已停止。")

if __name__ == "__main__":
    main()
