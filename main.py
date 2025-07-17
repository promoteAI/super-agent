import subprocess
import sys
import time

def start_service(cmd, name):
    try:
        print(f"正在启动{name}...")
        # 使用subprocess.Popen启动服务，保持进程不阻塞
        subprocess.Popen(cmd, shell=True)
        print(f"{name} 启动成功。")
    except Exception as e:
        print(f"{name} 启动失败: {e}")

def main():
    # 启动mcp服务
    start_service("uv run super_agent --run mcp-server --transport sse", "MCP服务")

    # 启动 Orchestrator 代理
    start_service("uv run super_agent/agents/ --agent-card super_agent/agent_cards/orchestrator_agent.json --port 10101", "Orchestrator 代理")

    # 启动 Planner 代理
    start_service("uv run super_agent/agents/ --agent-card super_agent/agent_cards/planner_agent.json --port 10102", "Planner 代理")

    # 启动 Airline Ticketing Agent
    start_service("uv run super_agent/agents/ --agent-card super_agent/agent_cards/air_ticketing_agent.json --port 10103", "Airline Ticketing Agent")

    # 启动 Hotel Reservations Agent
    start_service("uv run super_agent/agents/ --agent-card super_agent/agent_cards/hotel_booking_agent.json --port 10104", "Hotel Reservations Agent")

    # 启动 Car Rental Reservations Agent
    start_service("uv run super_agent/agents/ --agent-card super_agent/agent_cards/car_rental_agent.json --port 10105", "Car Rental Reservations Agent")

    print("所有服务已启动。请检查各服务日志以确认运行状态。")

if __name__ == "__main__":
    main()
