# 罗宜高速 ESG 智能入库真实文件上传补充说明 V0.2

本说明补充 `POST /api/workspace/files/upload` 的真实文件上传能力。原 JSON 元数据上传仍保留，用于 mock / 自动化测试兼容；新增 multipart 上传用于前端 P03 “选择文件上传”真实链路。

## 1. 接口

```http
POST /api/workspace/files/upload
```

## 2. 支持的请求形式

### 2.1 multipart/form-data（真实文件上传）

字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file | File | 是 | 上传文件，支持 PDF、Word、Excel、图片、压缩包等 |
| uploaderId | string/number | 否 | 上传人 ID，默认 10001 |
| uploaderName | string | 否 | 上传人名称，默认“项目管理员” |

后端处理：

1. 读取文件字节；
2. 计算真实 `sha256Hash`；
3. 写入 `server/storage/uploads/202607/`；
4. 将 `storagePath`、`fileSize`、`mimeType`、`sha256Hash` 写入 `file_asset`；
5. 返回 `fileId`，供后续发起解析。

### 2.2 application/json（兼容旧 mock）

```json
{
  "originalName": "2026年7月水保监测月报.pdf",
  "fileSize": 2048000,
  "mimeType": "application/pdf",
  "uploaderId": 10001,
  "uploaderName": "项目管理员"
}
```

## 3. 返回

```json
{
  "fileId": 900100,
  "fileCode": "FILE-202607-900100",
  "originalName": "2026年7月水保监测月报.pdf",
  "fileSize": 2048000,
  "storagePath": "storage/uploads/202607/uuid_2026年7月水保监测月报.pdf",
  "sha256Hash": "真实文件SHA256",
  "duplicateStatus": "UNKNOWN",
  "parseStatus": "PENDING"
}
```

## 4. 后续链路

```text
multipart 文件上传
→ file_asset
→ POST /api/workspace/files/{fileId}/parse
→ ai_parse_job
→ ai_parse_field_result
→ task_match_candidate
→ POST /api/workspace/parse-jobs/{jobId}/confirm
→ document_record / document_version / document_task_relation
```

## 5. 自动化验证

新增测试：

```powershell
python server/multipart_upload_test.py
```

验证内容：

- 真实文件字节不丢失；
- 文件落盘；
- `file_asset` 返回真实 `fileSize` / `storagePath` / `sha256Hash`；
- 上传后可继续创建解析任务。
