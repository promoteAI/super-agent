## 安装依赖环境
## 启动所有服务
1. 启动mcp服务
```shell
uv run super_agent --run mcp-server --transport sse
```

2. 启动 Orchestrator 代理：
```shell
uv run super_agent/agents/ --agent-card super_agent/agent_cards/orchestrator_agent.json --port 10101
```

3. 启动 Planner 代理：
```shell
uv run super_agent/agents/ --agent-card super_agent/agent_cards/planner_agent.json --port 10102
```

4. 启动 Airline Ticketing Agent：
```shell
uv run super_agent/agents/ --agent-card super_agent/agent_cards/air_ticketing_agent.json --port 10103
```

5. 启动 Hotel Reservations Agent：
```shell
uv run super_agent/agents/ --agent-card super_agent/agent_cards/hotel_booking_agent.json --port 10104
```

6. 启动 Car Rental Reservations Agent：
```shell
uv run super_agent/agents/ --agent-card super_agent/agent_cards/car_rental_agent.json --port 10105
```

# 天气MCP服务

uvx --from git+https://github.com/microagents/mcp-servers.git#subdirectory=mcp-weather-free mcp-weather-free

pip install git+https://github.com/microagents/mcp-servers.git#subdirectory=mcp-weather-free