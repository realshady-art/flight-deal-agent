# flight-deal-agent

按 **目的地区域** 监控 **往返** 特价航班的后端程序。  
定时触发 → 采集报价 → 落库 → 规则筛选 → 通知 + 汇总。  
本地可用，也预留了 API 和调度器供日后部署到服务器。

---

## 现状（v0.2）

| 模块 | 状态 |
|------|------|
| 配置 YAML + 区域机场池 | 可用 |
| CLI（run-once / serve / check-config） | 可用 |
| Amadeus Self-Service 采集器 | 可用（需免费注册获取 key） |
| Stub 采集器（离线测试） | 可用 |
| SQLite 落库 + 历史查询 | 可用 |
| 策略：绝对阈值 + 历史中位数 + 通知冷却 | 可用 |
| 通知：stdout | 可用 |
| 通知：Telegram / Email | 预留接口 |
| APScheduler 定时调度 | 可用 |
| FastAPI（未来前端接口） | 可用 |
| pytest 测试 (31 cases) | 全部通过 |

---

## 快速开始

**环境**：Python 3.9+

```bash
git clone https://github.com/realshady-art/flight-deal-agent.git
cd flight-deal-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e ".[dev]"
```

### 1. 准备配置

```bash
cp config/config.example.yaml config/config.yaml
cp .env.example .env
# 编辑 config/config.yaml 修改出发机场、区域等
# 编辑 .env 填入 Amadeus API Key（或保持 provider: stub 离线测试）
```

### 2. 校验配置

```bash
python -m flight_deal_agent check-config
```

### 3. 跑一轮

```bash
python -m flight_deal_agent run-once
```

### 4. 启动 API + 定时调度

```bash
python -m flight_deal_agent serve
# 默认 http://127.0.0.1:8000，每小时自动扫一次
# --no-scheduler 仅启动 API 不自动扫
```

### 5. 跑测试

```bash
pytest -v
```

---

## Amadeus 免费层

注册 [Amadeus for Developers](https://developers.amadeus.com) 获取 `client_id` 和 `client_secret`，写入 `.env`。

- **测试环境**（默认）：缓存数据，不消耗生产配额。
- **生产环境**：每月免费 2000 次 Flight Offers Search。

在 `config.yaml` 中把 `collector.provider` 改为 `amadeus`，`amadeus.test_mode` 设为 `true`（测试）或 `false`（生产）。

---

## 项目结构

```text
flight-deal-agent/
├── config/
│   └── config.example.yaml     # 主配置模板
├── data/
│   └── regions/                 # 区域 → IATA 机场池
├── flight_deal_agent/
│   ├── cli.py                   # 命令行入口
│   ├── runner.py                # run-once 编排
│   ├── settings.py              # 配置加载
│   ├── models.py                # 数据模型（Pydantic）
│   ├── orchestrator.py          # 任务规划 + 日期采样
│   ├── collector.py             # 采集（stub / Amadeus）
│   ├── storage.py               # SQLite 存储 + 历史统计
│   ├── analyst.py               # 特价判断规则
│   ├── notifier.py              # 通知（stdout / 预留）
│   ├── scheduler.py             # APScheduler 定时
│   └── api.py                   # FastAPI（前端预留）
├── tests/                       # pytest（31 cases）
├── pyproject.toml
└── README.md
```

---

## API 端点（供前端 / 调试）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 + 调度器状态 |
| GET | `/api/deals` | 最近通知过的 deal |
| GET | `/api/quotes` | 最近采集的报价 |
| GET | `/api/runs` | 运行日志 |
| POST | `/api/run` | 手动触发一轮 |
| GET | `/api/config` | 当前配置（脱敏） |
| GET | `/api/scheduler/status` | 调度器状态 |
| POST | `/api/scheduler/start` | 启动调度 |
| POST | `/api/scheduler/stop` | 停止调度 |

---

## 后续开发

1. 接入 Telegram / Email 通知渠道
2. 前端 Web UI 对接 FastAPI
3. 更多数据源 adapter
4. 部署到云服务器 + Clockwork / cron

---

## 免责声明

票价以供应商实际下单页为准；本工具仅用于技术学习与个人监控。使用第三方 API 时请遵守其服务条款。
