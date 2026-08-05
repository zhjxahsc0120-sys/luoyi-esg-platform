#### 2.7.3 核验与月度/季度

| 状态 | 是否进入**正式** E04 KPI |
|------|---------------------------|
| `verification_status = VERIFIED`（季度复核通过或等价已核验） | **可以**（且须 effective） |
| `verification_status = PENDING`（含月度暂算） | **默认不进入正式 KPI**；可进入「月度暂算视图」或演示/平台测算视图 |
| `REJECTED` | 不进入 |

须在 UI/API 区分：

- **月度暂算**（`MONTHLY_PROVISIONAL`）  
- **季度已核验**（`QUARTERLY_VERIFIED`）  

不得只写「实施任务单再定」而不在设计稿冻结上述默认。