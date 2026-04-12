# flight-deal-agent

按 **目的地区域** 监控 **往返** 特价航班的后端程序。  
定时触发 → 采集报价 → 落库 → 规则筛选 → 通知 + 汇总。  
本地可用，也预留了 API 和调度器供日后部署到服务器。

**仓库**：https://github.com/realshady-art/flight-deal-agent  

---

## 项目进度（移交说明）

**当前版本**：v0.2.1（以 `flight_deal_agent/__init__.py` 与 `pyproject.toml` 为准）

**已完成（可在另一台机器上直接 clone验证）**

- 后端流水线：`run-once` = 规划任务 → 采集（stub / Amadeus / SearchApi）→ SQLite 落库 → 策略筛选 → stdout 通知 → 运行日志。
- **Amadeus**：OAuth2 + Flight Inspiration（扫目的地）+ Flight Offers Search（补漏/复核思路在 `collector.py`）；免费层需自行注册密钥。
- **SearchApi**：Google Flights 搜索已接入 `searchapi` provider，适合当前 MVP。
- **配置**：YAML + `data/regions/*.yaml` 机场池；`python-dotenv` 自动加载根目录 `.env`。
- **命令**：`run-once`、`serve`（FastAPI + APScheduler）、`check-config`、`verify-amadeus`（`--oauth-only` 可选）。
- **HTTP API**：健康检查、deals/quotes/runs、手动触发、调度器启停、脱敏配置（见下文 API 表）。
- **测试**：`pytest` 全量应通过（当前约 35+ 条，以本机 `pytest -v` 为准）。

**未完成 / 未接入**

- 前端 UI（仅 REST 预留）。
- Telegram / Email通知（`notifier.py` 仅占位）。
- 第二数据源、生产环境配额与成本监控、告警运维面板。
- 与 Clockwork 等外部调度器的正式对接文档（当前可用系统 cron 或自带 `serve` 内调度）。

---

## 现状（v0.2.1）功能一览

| 模块 | 状态 |
|------|------|
| 配置 YAML + 区域机场池 | 可用 |
| CLI（run-once / serve / check-config / verify-amadeus） | 可用 |
| 自动加载根目录 `.env`（python-dotenv） | 可用 |
| Amadeus Self-Service 采集器 | 可用（需免费注册获取 key） |
| SearchApi Google Flights 采集器 | 可用（需 SearchApi key） |
| Stub 采集器（离线测试） | 可用 |
| SQLite 落库 + 历史查询 | 可用 |
| 策略：绝对阈值 + 历史中位数 + 通知冷却 | 可用 |
| 通知：stdout | 可用 |
| 通知：Telegram / Email | 预留接口 |
| APScheduler 定时调度 | 可用 |
| FastAPI（未来前端接口） | 可用 |
| pytest | 全部通过（移交后请在目标机执行 `pytest -v` 复核） |

---

## 待办事项（TODO / Backlog）

按优先级大致排序，供下一台机器上的同事继续开发。

| 优先级 | 事项 | 说明 |
|--------|------|------|
| P0 | 配置 SearchApi / Amadeus 密钥 | SearchApi 更适合当前 MVP；密钥只放 `.env`，勿提交仓库。 |
| P1 | 根据配额调 `request_budget_per_run` 与调度间隔 | 避免超额；现已支持 `scheduler.interval_hours` / `interval_minutes`，但全量航线仍受预算限制。 |
| P1 | 实现 Telegram或邮件通知 | 改 `notifier.py`，配置项可扩到 `config.yaml` 的 `alerts`。 |
| P2 | Flight Offers **二次复核**策略细化 | Inspiration 为缓存价；文档已建议命中后再 Offers，可按 deal 阈值触发复核以减 API 次数。 |
| P2 | 前端 | 对接现有 FastAPI（`/api/*`），或新增鉴权（Token / Cookie）。 |
| P2 | 服务器部署 | systemd / Docker、`127.0.0.1` 反代、HTTPS、日志轮转；`.env` 权限 `600`。 |
| P3 | 多用户 / 多配置 | 当前单配置文件；若产品化需租户模型与 DB 迁移。 |
| P3 | 更多 collector adapter | 在 `collector.py` 或拆分子包，保持 `provider` 枚举一致。 |

---

## 下一步：在新机器 / 服务器上怎么做**1. 拉代码与环境**

```bash
git clone https://github.com/realshady-art/flight-deal-agent.git
cd flight-deal-agent
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip && pip install -e ".[dev]"
pytest -v    # 确认测试通过
```

**2. 配置（二选一或并存）**

- **仅验证流水线、不调外网**：`cp config/config.example.yaml config/config.yaml`，保持 `collector.provider: stub`。
- **真实询价（SearchApi）**：`cp .env.example .env`，填入 `SEARCHAPI_API_KEY`；`cp config/config.searchapi.example.yaml config/config.yaml`。
- **真实询价（Amadeus）**：`cp .env.example .env`，填入 Amadeus；`cp config/config.amadeus.example.yaml config/config.yaml`；改出发地、区域、阈值。
- **美国 + 加拿大 10 分钟监控模板**：`cp config/config.us_ca.amadeus.example.yaml config/config.yaml`，再按你的配额与阈值微调。

**3. 验证 Amadeus（有密钥后）**

```bash
python -m flight_deal_agent verify-amadeus
# 或仅测 OAuth2：python -m flight_deal_agent verify-amadeus --oauth-only
python -m flight_deal_agent check-config
python -m flight_deal_agent run-once
```

**4. 常驻服务（服务器）**

```bash
python -m flight_deal_agent serve
# 监听地址与端口见 config.yaml → api.host / api.port；默认 127.0.0.1:8000
# 仅 API、不用内置调度：python -m flight_deal_agent serve --no-scheduler
# 也可用系统 cron 每小时：python -m flight_deal_agent run-once -c /path/to/config.yaml
```

**5. 移交检查清单（建议打勾）**

- [ ] `pytest -v` 全绿  
- [ ] `verify-amadeus` 通过（若使用 Amadeus）  
- [ ] `config/config.yaml` 与 `data/regions/*` 已按业务改好  
- [ ] `.env` 已在目标机创建且权限安全  
- [ ] SQLite 路径 `storage.sqlite_path` 在磁盘上有写权限、已考虑备份  
- [ ] 若公网暴露 API：已加反向代理 + TLS + 访问控制（当前 API **无鉴权**）

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

**离线（stub，不调外网）**

```bash
cp config/config.example.yaml config/config.yaml
python -m flight_deal_agent run-once
```

**接 SearchApi（当前更适合跑 MVP）**

```bash
cp .env.example .env
# 在 https://www.searchapi.io 注册 → Dashboard → API Keys → 把 key 填入 .env
cp config/config.searchapi.example.yaml config/config.yaml
python -m flight_deal_agent check-config
python -m flight_deal_agent run-once
```

**接 Amadeus（备用）**

```bash
cp .env.example .env
# 在 https://developers.amadeus.com 注册 → 创建 App → 把 API Key / Secret 填入 .env
cp config/config.amadeus.example.yaml config/config.yaml
# 按需改出发机场、区域、阈值等
python -m flight_deal_agent verify-amadeus          # OAuth2 + Inspiration 探测
# 或: python -m flight_deal_agent verify-amadeus --oauth-only   # 只测登录，省一次业务请求
python -m flight_deal_agent check-config
python -m flight_deal_agent run-once
```

程序启动时会自动从**项目根目录**和**当前工作目录**加载 `.env`，无需手动 export。

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
# 默认 http://127.0.0.1:8000，按 config.yaml 里的 interval 自动扫
# --no-scheduler 仅启动 API 不自动扫
```

### 5. 跑测试

```bash
pytest -v
```

---

## Amadeus 免费层

注册 [Amadeus for Developers](https://developers.amadeus.com) 获取 `client_id` 和 `client_secret`，写入 `.env`。

- **测试环境**（`amadeus.test_mode: true`）：`test.api.amadeus.com`，多为缓存/样例数据，适合联调。
- **生产环境**（`false`）：真实票价；每月有免费调用额度（以官网说明为准）。

在 `config.yaml` 中设置 `collector.provider: amadeus`。模板见 `config/config.amadeus.example.yaml`。

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
│   ├── collector.py             # 采集（stub / Amadeus / SearchApi）
│   ├── storage.py               # SQLite 存储 + 历史统计
│   ├── analyst.py               # 特价判断规则
│   ├── notifier.py              # 通知（stdout / 预留）
│   ├── scheduler.py             # APScheduler 定时
│   └── api.py                   # FastAPI（前端预留）
├── tests/                       # pytest（条数以 pytest收集为准）
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

## 美国 + 加拿大监控说明

如果你的目标是“每 10 分钟扫一次美国 + 加拿大主要航线，只在明显便宜时提醒”，当前仓库已经能直接配置到这一层：

- `origin_region_id: "us_ca_major"` + `target_region_id: "us_ca_major"`：把出发地和目的地都限制在美国/加拿大主要机场池
- `scheduler.interval_minutes: 10`：10 分钟级调度
- `thresholds.below_median_pct`：只在明显低于历史中位价时提醒

但有一个边界要明确：

- 当前 orchestrator 仍然受 `collector.request_budget_per_run` 限制
- 所以它是“按预算轮询主要航线”，不是“无限制穷举北美所有机场对”
- 这层是故意保留的，不然免费额度会很快耗尽

---

## 免责声明

票价以供应商实际下单页为准；本工具仅用于技术学习与个人监控。使用第三方 API 时请遵守其服务条款。
