# flight-deal-agent

按 **目的地区域**（而非单一城市）监控 **往返**特价航班的 **agentic 骨架**：定时触发 → 采集报价 → 落库 → 规则/策略筛选 → 通知与汇总。  
当前仓库为 **starter template**：目录与数据模型已就位，**真实航班 API、二次复核、Clockwork 调度、Telegram 等需自行接入**。

- **仓库**：https://github.com/realshady-art/flight-deal-agent  
- **协议**：MIT

---

## 现状（v0.1 模板）

| 模块 | 状态 |
|------|------|
| 配置（YAML）与区域机场池 | 可用 |
| `run-once` CLI | 可用 |
| 采集器 `stub` | 占位，不请求外网 |
| SQLite 落库 | 基础表结构 + 写入 |
| 策略 / 特价判断 | 占位，始终无 deal |
| 通知 | 仅 `stdout` |
| 小时级调度（Clockwork / cron） | 文档说明，未内置 |

---

## 快速开始

**环境**：Python 3.9+（推荐 3.11+）

```bash
git clone https://github.com/realshady-art/flight-deal-agent.git
cd flight-deal-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# 使用示例配置跑一轮（采集器为 stub，通常 quotes=0）
python -m flight_deal_agent run-once -c config/config.example.yaml

# 演示通知链路（不访问 API）
python -m flight_deal_agent run-once -c config/config.example.yaml --demo-notification
```

本地使用时可将 `config/config.example.yaml` 复制为 `config/config.yaml` 再改参数（勿把密钥写进 YAML，优先环境变量）。

```bash
cp config/config.example.yaml config/config.yaml
```

区域机场列表放在 `data/regions/<region_id>.yaml`，与配置里的 `target_region_id` 对应。

---

## 项目结构（概要）

```text
flight-deal-agent/
├── config/
│   └── config.example.yaml    # 主配置模板
├── data/
│   └── regions/               # 区域 → IATA 机场池
├── flight_deal_agent/
│   ├── cli.py                 # 命令行入口
│   ├── runner.py              # run-once 编排
│   ├── settings.py            # 配置与区域加载
│   ├── orchestrator.py        # 任务规划（OD组合）
│   ├── collector.py           # 采集（stub；后续接 API）
│   ├── storage.py             # SQLite
│   ├── analyst.py             # 特价策略（占位）
│   └── notifier.py            # 通知（占位）
├── pyproject.toml
└── README.md
```

---

## 与「agentic / 调度」的衔接

- **本仓库**：提供可重复执行的 `run-once`，便于被外部调度器调用（HTTP、CLI、cron 均可）。
- **Clockwork（或同类）**：建议注册 **每小时**（或带 jitter）任务，仅调用例如：  
  `python -m flight_deal_agent run-once -c config/config.yaml`  
 失败重试、去重、配额控制可在调度侧或后续在 `runner` 内扩展。

---

## 后续开发建议（路线图）

1. 选定数据源，在 `collector.py`（或 `flight_deal_agent/collectors/`）实现 provider，并遵守条款与配额。  
2. 实现 **explore / indicative → live 复核** 两阶段，再触发实时提醒。  
3. 在 `analyst.py` 接入历史分位数、绝对阈值、再提醒规则（与配置中 `thresholds`、`alerts` 对齐）。  
4. 扩展 `notifier`（Telegram、邮件等）与可选 digest 任务。  
5. 对 `plan_tasks` 做 **请求预算截断** 与分级轮询，避免查询空间爆炸。

---

## 免责声明

票价以供应商/OTA **实际下单页**为准；本工具仅用于技术学习与个人监控，不构成购票或投资建议。使用第三方 API 时请自行审阅服务条款。
