# 区域 → 机场映射

多数航班 API 不直接支持「北美」「西欧」这类大区作为单一查询实体。此处用 **一个 YAML 文件 = 一块逻辑区域**，内部维护 **IATA 机场列表**。

复制 `example_europe.yaml` 为新文件，修改 `id` 与 `airports`，并在 `config/config.yaml` 里把 `target_region_id` 指过去。

如果希望出发地也按一个区域池来轮询，可在配置里使用 `origin_region_id`，例如：

```yaml
origin_region_id: "us_ca_major"
target_region_id: "us_ca_major"
```

仓库已附带一份 `us_ca_major.yaml`，用于美国 + 加拿大主要机场。
