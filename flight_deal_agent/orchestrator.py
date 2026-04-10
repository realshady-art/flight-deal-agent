from __future__ import annotations

from dataclasses import dataclass

from flight_deal_agent.settings import AppConfig


@dataclass(frozen=True)
class SearchTask:
    """一轮运行中的最小查询单元（占位；后续可扩展为具体 API 参数）。"""

    origin: str
    destination: str


def plan_tasks(config: AppConfig, destination_airports: list[str]) -> list[SearchTask]:
    """根据出发地与区域机场池生成本轮任务列表（尚未做预算截断与分级轮询）。"""
    tasks: list[SearchTask] = []
    for origin in config.origin_airports:
        for dest in destination_airports:
            if origin == dest:
                continue
            tasks.append(SearchTask(origin=origin, destination=dest))
    return tasks
