# 罗宜高速 ESG 数据上传工作台交付包说明 V1.0

本文件为根目录《罗宜高速ESG数据上传工作台_交付包说明_V1.0.md》的文档区副本索引。

完整交付说明请查看：

```text
罗宜高速ESG数据上传工作台_交付包说明_V1.0.md
```

## 快速摘要

### 访问地址

| 页面 | 地址 |
| --- | --- |
| 领导层 ESG 看板首页 | `http://localhost:5174/#/` |
| 数据填报与上传工作台 | `http://localhost:5174/#/workspace` |

### 后端 API

```text
http://127.0.0.1:8765
```

### 后端启动

```powershell
powershell -ExecutionPolicy Bypass -File server/start_backend.ps1
```

### 前端启动

```powershell
npm run dev -- --host 127.0.0.1 --port 5174
```

### 最小验收

```powershell
$env:PYTHONIOENCODING='utf-8'
python server/workspace_acceptance_test.py
npm run check
npm run build
```

### 当前状态

```text
可演示：是
可联调：是
可阶段验收：是
可直接生产上线：否
```

### 主要完成能力

- P01-P05 工作台页面；
- S01 任务办理弹窗；
- 真实文件上传；
- 智能入库规则抽取；
- 哈希去重；
- 确认入库并关联任务；
- 审核通过；
- 审核退回；
- 补正再提交；
- 资料中心详情、版本、关联任务；
- 跨页面状态刷新；
- MySQL-first 后端；
- SQLite fallback；
- 自动化回归脚本。

### 主要未完成生产化能力

- 真实 OCR / 大模型解析；
- 登录鉴权和权限；
- 文件在线预览、下载、版本回滚；
- 审核意见动态输入；
- 生产部署、安全审计、日志体系；
- 浏览器端到端自动化。

