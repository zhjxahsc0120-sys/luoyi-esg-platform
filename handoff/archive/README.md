# Codex ↔ Trae 本机交接工作流

这个目录用于减少手工复制粘贴。

## 固定文件

| 文件 | 用途 |
|---|---|
| `NEXT_FOR_TRAE.md` | Codex 写给 Trae 的下一步任务书 |
| `TRAE_DONE_REPORT.md` | Trae 完成后写回的报告 |
| `TRAE_REPORT_TEMPLATE.md` | Trae 回报模板 |
| `handoff_status.json` | 当前交接状态 |

## 推荐使用方式

### 1. Codex 出任务

Codex 将下一步任务写入：

```text
_handoff/NEXT_FOR_TRAE.md
```

### 2. 给 Trae 的固定提示

以后可以不用复制完整任务书，只给 Trae 这句话：

```text
请读取项目根目录 _handoff/NEXT_FOR_TRAE.md，严格按其中任务执行；完成后把结果写入 _handoff/TRAE_DONE_REPORT.md。
```

### 3. Trae 完成后

Trae 将报告写入：

```text
_handoff/TRAE_DONE_REPORT.md
```

### 4. Codex 校核

用户只需对 Codex 说：

```text
读取 Trae 回报并校核
```

Codex 直接读取 `_handoff/TRAE_DONE_REPORT.md`，不需要用户复制报告。

## 注意

- Trae 如果不能主动读取文件，需要在 Trae 对话中明确给出上述固定提示。
- Codex 不会直接控制 Trae UI；这是本机文件交接，不是跨工具远程控制。
- 前端样式类任务仍建议 Trae 执行；数据库、后端、接口、测试由 Codex 继续执行。
