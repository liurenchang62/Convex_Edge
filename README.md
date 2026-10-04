# ConvexEdge

**Permission-Aware Stock–Option Allocation and Volatility Forecasting**

ConvexEdge 是一个股票—期权联合研究与执行项目。系统预测股票未来收益分布与实际波动率，并结合期权隐含波动率、交易成本、风险预算和账户权限，在股票、现金与期权覆盖层之间进行动态配置。

## 双路径设计

- **Level 1 路径**：股票组合 + Covered Call / Buy Write。该路径能够独立形成完整研究、回测与执行项目。
- **Level 2 路径**：在同一数据、模型和回测框架上增加 Long Call/Put、Protective Put、Debit Spread、Straddle/Strangle 等动作。

Level 2 权限只扩展可执行动作，不是研究项目完成的前提。

## 测试分层

| 目录 | 职责 | 当前阶段 |
|---|---|---|
| `test_data` | TWS 连接、合约、行情、期权链、Greeks、历史数据 | 已建立 |
| `test_features` | 点时特征、收益标签、实现波动率、期权曲面、无泄漏检查 | 验收规范已建立 |
| `test_models` | 收益分布、波动率和状态模型的训练、校准与基准比较 | 验收规范已建立 |
| `test_backtest` | 股票与期权统一事件驱动回测、成本和行权处理 | 验收规范已建立 |
| `test_risk` | 组合约束、Greeks、压力测试、尾部风险和权限约束 | 验收规范已建立 |
| `test_order` | IBKR WHAT-IF 与最小订单执行测试 | 已建立 |

各目录中的 `运行指南.md` 是该层的测试入口和完成标准。建议按上述顺序开发，任何后层不得绕过前层的数据点时性和安全检查。

## 当前实现

- `src/convexedge/data`：point-in-time 校验、as-of 对齐、收益标签、实现波动率和 IBKR K 线规范化。
- `src/convexedge/features.py`：按实际交易序列构建日频特征、多周期标签和下一可用交易日。
- `tests`：确定性单元测试，包括刻意注入未来信息和未完成 K 线。
- `test_features/00_ibkr_pit_smoke.py`：使用真实 IBKR 只读历史行情验证 UTC 与数据契约。
- `docs/data_contract.md`：四时间字段、标签区间和原始数据保存规范。
- `scripts/collect_ibkr_stock_history.py`：采集复权日线并保存不可变快照。
- `scripts/collect_ibkr_option_chain.py`：采集不依赖报价权限的期权链结构。
- `scripts/build_stock_features.py`：从已校验原始快照生成处理层特征数据。

本地验证：

```powershell
python -m pytest -q
python test_features\run_all.py
python test_features\run_all.py --include-live
```

真实数据采集示例：

```powershell
python scripts\collect_ibkr_stock_history.py --symbol AAPL --duration "1 Y"
python scripts\collect_ibkr_option_chain.py --symbol AAPL --exchange SMART
python scripts\build_stock_features.py <原始股票快照目录>
```

`data/raw` 和 `data/processed` 默认不提交 Git。每个快照包含 Parquet 数据和带 SHA-256 的 manifest；相同 ID 不允许覆盖。

## 当前安全边界

- 数据测试保持 TWS 只读 API。
- 订单测试默认仅使用 `whatIf=True`。
- 未获得对应权限时，Level 2 策略只允许研究和回测，不进入真实执行。
- 任何真实订单必须经过标的白名单、数量上限、风险预算、人工确认和订单回读。

