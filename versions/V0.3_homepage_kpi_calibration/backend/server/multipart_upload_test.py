from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8765"
SERVER_DIR = Path(__file__).resolve().parent


def post_multipart_upload(filename: str, content: bytes, mime_type: str = "application/pdf") -> dict:
    boundary = "----LuoyiEsgBoundary202607"
    parts = [
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8")
        + content
        + b"\r\n",
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="uploaderId"\r\n\r\n'
        "10001\r\n".encode("utf-8"),
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="uploaderName"\r\n\r\n'
        "项目管理员\r\n".encode("utf-8"),
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    req = Request(
        f"{BASE_URL}/api/workspace/files/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(path: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    content = b"%PDF-1.4\n% luoyi esg multipart upload smoke test\n%%EOF\n"
    original_name = "\u6c34\u4fdd\u76d1\u6d4b\u6708\u62a5_2026-07_multipart.pdf"
    uploaded = post_multipart_upload(original_name, content)

    assert_true(uploaded.get("fileId") is not None, "upload response missing fileId")
    assert_true(uploaded.get("originalName") == original_name, "upload response originalName mismatch")
    assert_true(uploaded.get("fileSize") == len(content), "upload response fileSize mismatch")
    assert_true(uploaded.get("sha256Hash"), "upload response missing sha256Hash")
    storage_path = uploaded.get("storagePath") or ""
    assert_true(storage_path.startswith("storage/uploads/202607/"), "storagePath is not an upload path")
    assert_true((SERVER_DIR / storage_path).exists(), "uploaded file was not written to disk")

    parse_job = post_json(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
    assert_true(parse_job.get("jobStatus") == "WAIT_CONFIRM", "parse job was not created")

    print("✅ multipart 上传测试通过：真实文件已落盘、写入 file_asset，并可创建解析任务。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ multipart 上传测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
