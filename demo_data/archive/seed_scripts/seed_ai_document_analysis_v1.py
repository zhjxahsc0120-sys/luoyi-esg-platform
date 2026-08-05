"""生成 ESG-AI-DATA-001 三份罗宜高速解析测试数据。"""

from __future__ import annotations

from ai_document_analysis.service import MySQLAnalysisRepository, TEST_FILES, analyze_document


def main() -> None:
    repository = MySQLAnalysisRepository()
    created = []
    for file_id, (file_name, _, _) in TEST_FILES.items():
        result = analyze_document({"fileId": file_id, "fileName": file_name}, repository=repository)
        created.append(
            {
                "analysis_id": result["analysis_id"],
                "source_file_id": result["source_file_id"],
                "file_name": result["file_name"],
                "document_type": result["document"]["type"],
                "period": result["document"]["period"],
            }
        )
    for item in created:
        print(item)
    print(f"[OK] 已生成 {len(created)} 份罗宜高速 AI 解析测试数据；全部标记为不参与首页指标统计。")


if __name__ == "__main__":
    main()
