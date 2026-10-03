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

## 当前安全边界

- 数据测试保持 TWS 只读 API。
- 订单测试默认仅使用 `whatIf=True`。
- 未获得对应权限时，Level 2 策略只允许研究和回测，不进入真实执行。
- 任何真实订单必须经过标的白名单、数量上限、风险预算、人工确认和订单回读。

