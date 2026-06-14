"""
批量更新端口：80XX → 90XX
P01: 8080 → 9001
P02: 8081 → 9002
P04: 8001 → 9004
P05: 8002 → 9005
"""
import os
import re

PROJECT_ROOT = r"D:\Codex-project\Agent_Ultimate_System"

# 端口映射：旧端口 -> 新端口
PORT_MAP = {
    "8080": "9001",
    "8081": "9002",
    "8001": "9004",
    "8002": "9005",
}

# 需要修改的文件列表（从扫描结果中提取）
FILES_TO_UPDATE = [
    # P01
    r"01_企业管理基座系统\backend\src\main\resources\application.yml",
    r"01_企业管理基座系统\README.md",
    # P02
    r"02_政企物流智能化转化\backend\src\main\resources\application.yml",
    r"02_政企物流智能化转化\README.md",
    r"02_政企物流智能化转化\docker-compose.yml",
    # P04
    r"04_医疗智能问诊基础RAG\backend\.env",
    r"04_医疗智能问诊基础RAG\backend\start.bat",
    r"04_医疗智能问诊基础RAG\backend\app\config.py",
    # P05
    r"05_企业级高级RAG知识库\backend\.env",
    r"05_企业级高级RAG知识库\backend\app\config.py",
    # P06
    r"06_Agent智能体合流总管\README.md",
    r"06_Agent智能体合流总管\start-all.bat",
    r"06_Agent智能体合流总管\当前完成情况.md",
    r"06_Agent智能体合流总管\docs\架构图.md",
    r"06_Agent智能体合流总管\docs\部署文档.md",
    r"06_Agent智能体合流总管\docs\项目三接入指南.md",
    r"06_Agent智能体合流总管\openapi\project1-tools.json",
    r"06_Agent智能体合流总管\openapi\project2-tools.json",
    r"06_Agent智能体合流总管\openapi\project4-medical-rag.json",
    r"06_Agent智能体合流总管\openapi\project5-rag.json",
    r"06_Agent智能体合流总管\scripts\dify_setup.py",
    r"06_Agent智能体合流总管\scripts\import_tools2.py",
    r"06_Agent智能体合流总管\tests\agent_demo.py",
    r"06_Agent智能体合流总管\workflow\chatflow-design.md",
]


def update_file(filepath, replacements):
    """Replace ports in a file, return number of changes"""
    if not os.path.exists(filepath):
        return 0, f"NOT FOUND: {filepath}"

    # Try different encodings
    content = None
    for enc in ["utf-8", "utf-8-sig", "gbk", "latin-1"]:
        try:
            with open(filepath, "r", encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        return 0, f"DECODE ERROR: {filepath}"

    original = content
    changes = []

    for old_port, new_port in replacements:
        # Count occurrences before replacement
        count = content.count(old_port)
        if count > 0:
            content = content.replace(old_port, new_port)
            changes.append(f"{old_port}->{new_port} ({count}x)")

    if content == original:
        return 0, f"NO CHANGE: {os.path.basename(filepath)}"

    # Write back with same encoding
    for enc in ["utf-8", "utf-8-sig"]:
        try:
            with open(filepath, "w", encoding=enc) as f:
                f.write(content)
            break
        except UnicodeError:
            continue

    return 1, f"UPDATED: {os.path.basename(filepath)} [{', '.join(changes)}]"


def main():
    print("=" * 60)
    print("端口批量更新: 80XX → 90XX")
    print("=" * 60)
    print()
    print("映射规则:")
    for old, new in PORT_MAP.items():
        print(f"  {old} → {new}")
    print()

    total_updated = 0
    total_skipped = 0

    for rel_path in FILES_TO_UPDATE:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        count, msg = update_file(full_path, PORT_MAP.items())
        if count > 0:
            print(f"  {msg}")
            total_updated += 1
        else:
            print(f"  {msg}")
            total_skipped += 1

    # Also update P01 start/stop bat files
    bat_files = [
        r"01_企业管理基座系统\启动系统.bat",
        r"01_企业管理基座系统\停止系统.bat",
    ]
    for rel in bat_files:
        full = os.path.join(PROJECT_ROOT, rel)
        count, msg = update_file(full, PORT_MAP.items())
        if count > 0:
            print(f"  {msg}")
            total_updated += 1

    print(f"\n总计: {total_updated} 个文件已更新, {total_skipped} 个无需修改")

    # Verify
    print("\n" + "=" * 60)
    print("验证更新结果")
    print("=" * 60)
    for rel_path in FILES_TO_UPDATE[:10]:  # Check first 10
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            remaining = []
            for old in PORT_MAP.keys():
                if old in content:
                    remaining.append(old)
            status = "CLEAN" if not remaining else f"STILL HAS: {remaining}"
            print(f"  {os.path.basename(full_path)}: {status}")


if __name__ == "__main__":
    main()
