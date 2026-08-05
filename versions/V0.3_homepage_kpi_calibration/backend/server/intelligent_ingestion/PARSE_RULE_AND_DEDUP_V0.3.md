# 罗宜高速 ESG 智能入库解析规则与去重补充说明 V0.3

本说明补充 P03 ESG 智能入库后端能力：解析字段由规则表驱动生成，上传文件按 SHA256 做重复检测。

## 1. 规则表驱动解析

解析任务创建接口：

```http
POST /api/workspace/files/{fileId}/parse
```

当前逻辑：

1. 根据文件名推断资料类型、资料周期、ESG 模块；
2. 读取 `ai_field_mapping_rule`；
3. 合并：
   - `通用资料`规则；
   - 当前资料类型规则，例如 `水保监测月报`；
4. 写入 `ai_parse_field_result`；
5. 前端继续通过 `/fields` 查询抽取结果。

示例：上传 `水保监测月报_2026-07.pdf` 后，会生成：

| fieldKey | 含义 |
| --- | --- |
| document_name | 资料名称 |
| document_type | 资料类型 |
| esg_module | ESG 模块 |
| period | 资料周期 |
| responsible_unit | 责任单位 |
| valid_start_date | 有效期开始 |
| valid_end_date | 有效期结束 |
| monitor_date | 监测日期 |
| dust_exceed_count | 扬尘超标次数 |
| noise_exceed_count | 噪声超标次数 |
| water_protection_issue_count | 水保问题数量 |

## 2. 有效期入库

确认入库接口：

```http
POST /api/workspace/parse-jobs/{jobId}/confirm
```

确认后写入：

- `document_record.valid_start_date`
- `document_record.valid_end_date`

示例：

```text
2026-07 月度资料 → 2026-07-01 ~ 2026-08-31
2026-Q2 季度资料 → 2026-04-01 ~ 2026-06-30
```

## 3. 重复文件检测

真实上传和 JSON 上传都会计算或接收 `sha256Hash`。

上传时：

1. 在 `file_asset` 中按 `sha256_hash` 查找历史文件；
2. 无相同哈希：`duplicateStatus = UNIQUE`；
3. 有相同哈希：`duplicateStatus = DUPLICATE`；
4. 写入 `deduplication_record`，记录 `matched_file_id / matched_document_id`。

上传响应新增字段：

```json
{
  "duplicateStatus": "DUPLICATE",
  "matchedFileId": 900100,
  "matchedDocumentId": 930100
}
```

## 4. 自动化验证

新增测试：

```powershell
python server/parse_rule_dedup_test.py
```

覆盖：

- 首次上传识别为 `UNIQUE`；
- 相同文件二次上传识别为 `DUPLICATE`；
- 规则表生成通用字段和业务字段；
- 有效期字段写入资料主档。
