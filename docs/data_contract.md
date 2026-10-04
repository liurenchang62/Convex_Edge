# Point-in-Time 数据契约

ConvexEdge 的所有研究表必须显式区分以下时间：

- `event_time`：价格区间开始、财报期结束或经济事件发生的时间。
- `source_time`：数据供应商记录的原始时间。
- `available_time`：该信息最早能够被策略使用的时间。
- `as_of_time`：策略作出预测或交易决定的时间。

基本约束是 `available_time <= as_of_time`。违反该约束的记录不得被静默删除或回填，管线必须直接失败。

## 行情 K 线

IBKR 日内历史数据使用 `formatDate=2` 请求 epoch 秒，并统一转换为 UTC。IBKR 返回的是区间起点；例如 5 分钟 K 线在起点后 5 分钟才完整可用。因此：

```text
available_time = event_time + bar_size
```

当前实现只接收已经完成的 K 线。实时未完成 K 线必须进入单独的数据类型，不得混入历史训练样本。

IBKR 日线即使设置 `formatDate=2`，实际仍返回 `YYYYMMDD`。原始层将其保存为 `session_date`，不会虚构具体收盘时间。日线特征标记为下一实际观测交易日可用；精确交易时刻将在升级到支持 `historicalSchedule` 的官方 API 后补齐。

## 财报和宏观数据

财报所属季度不是可用时间。`available_time` 必须使用真实公告时间，并考虑盘前、盘后和交易日边界。宏观数据应使用首次发布时间；修订值必须作为新版本记录，不能覆盖历史首次发布值。

## 标签

前瞻收益标签包含 `label_start_time` 和 `label_end_time`。训练样本的特征必须在 `label_start_time` 前可用；模型训练、标准化和参数选择不能访问测试期标签。

## 原始数据保存

原始响应应以追加方式保存，并记录供应商、请求参数、抓取时间和数据版本。原始层不可就地修改；清洗和派生结果进入独立层。账户编号、订单信息、API 凭据和个人报表不得提交 Git。

当前快照格式为 `data.parquet` 加 `manifest.json`。Manifest 记录行数、列名、生成时间、请求元数据和数据文件 SHA-256。加载前必须验证行数、模式和校验和。
