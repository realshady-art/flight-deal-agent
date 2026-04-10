# 区域 → 机场映射

多数航班 API 不直接支持「北美」「西欧」这类大区作为单一查询实体。此处用 **一个 YAML 文件 = 一块逻辑区域**，内部维护 **IATA 机场列表**。

复制 `example_europe.yaml` 为新文件，修改 `id` 与 `airports`，并在 `config/config.yaml` 里把 `target_region_id` 指过去。
