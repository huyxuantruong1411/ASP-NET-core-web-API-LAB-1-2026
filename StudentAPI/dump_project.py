import os
import json

OUTPUT_FILE = "aspnet_project_dump.txt"

# === 1. Quy tắc bỏ qua ===
def should_ignore_dir(dirname: str) -> bool:
    """Bỏ qua các thư mục nặng hoặc không quan trọng."""
    ignore_dirs = {
        "bin", "obj", ".vs", "node_modules", ".git", ".idea", ".vscode",
        "packages", "dist", "logs", "__pycache__"
    }
    return dirname in ignore_dirs or dirname.startswith(".")

def should_ignore_file(filename: str) -> bool:
    """Bỏ qua các file không cần thiết."""
    ignore_exts = {
        ".dll", ".exe", ".pdb", ".log", ".tmp", ".cache"
    }
    if filename.lower().endswith(tuple(ignore_exts)):
        return True
    return False

def is_interesting_file(filename: str) -> bool:
    """Chỉ chọn file quan trọng để đọc nội dung."""
    interesting_exts = {
        ".cs", ".cshtml", ".json", ".js", ".css", ".xml",
        ".config", ".csproj", ".sln", ".md"
    }
    return filename.lower().endswith(tuple(interesting_exts))

# === 2. Tạo cây thư mục (Tree + Markdown) ===
def build_tree(root_dir: str, prefix: str = "") -> str:
    """Tạo cây thư mục giống lệnh `tree`."""
    entries = []
    with os.scandir(root_dir) as it:
        for entry in sorted(it, key=lambda e: e.name.lower()):
            if entry.is_dir() and not should_ignore_dir(entry.name):
                entries.append(entry)
            elif entry.is_file() and not should_ignore_file(entry.name):
                entries.append(entry)

    lines = []
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        if entry.is_dir():
            lines.append(prefix + connector + entry.name + "/")
            extension = "    " if i == len(entries) - 1 else "│   "
            lines.extend(build_tree(entry.path, prefix + extension).splitlines())
        else:
            lines.append(prefix + connector + entry.name)
    return "\n".join(lines)

def build_markdown_tree(root_dir: str, indent: int = 0) -> str:
    """Cây thư mục dạng Markdown."""
    lines = []
    entries = []
    with os.scandir(root_dir) as it:
        for entry in sorted(it, key=lambda e: e.name.lower()):
            if entry.is_dir() and not should_ignore_dir(entry.name):
                entries.append(entry)
            elif entry.is_file() and not should_ignore_file(entry.name):
                entries.append(entry)

    for entry in entries:
        prefix = "  " * indent
        if entry.is_dir():
            lines.append(f"{prefix}- **{entry.name}/**")
            lines.append(build_markdown_tree(entry.path, indent + 1))
        else:
            lines.append(f"{prefix}- {entry.name}")
    return "\n".join(lines)

def build_json_structure(root_dir: str) -> dict:
    """Cây thư mục dạng JSON."""
    structure = {"name": os.path.basename(root_dir), "type": "folder", "children": []}
    try:
        entries = []
        with os.scandir(root_dir) as it:
            for entry in sorted(it, key=lambda e: e.name.lower()):
                if entry.is_dir() and not should_ignore_dir(entry.name):
                    entries.append(build_json_structure(entry.path))
                elif entry.is_file() and not should_ignore_file(entry.name):
                    entries.append({"name": entry.name, "type": "file"})
        structure["children"] = entries
    except PermissionError:
        pass
    return structure

# === 3. Đọc nội dung code ===
def dump_code_content(root_dir: str, out):
    """Xuất toàn bộ nội dung code quan trọng ra file."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Lọc thư mục
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
        rel_path = os.path.relpath(dirpath, root_dir)
        if rel_path == ".":
            rel_path = ""

        out.write(f"\n=== Folder: {rel_path or root_dir} ===\n")

        for filename in filenames:
            if should_ignore_file(filename) or not is_interesting_file(filename):
                continue
            file_path = os.path.join(dirpath, filename)
            out.write(f"\n--- File: {file_path} ---\n")
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    out.write(content + "\n")
            except Exception as e:
                out.write(f"[Lỗi đọc file: {e}]\n")

# === 4. Hàm chính ===
def dump_project(root_dir: str, output_file: str):
    with open(output_file, "w", encoding="utf-8") as out:
        # 4.1 Xuất cây thư mục
        out.write("=== Project Tree ===\n")
        out.write(root_dir + "/\n")
        out.write(build_tree(root_dir))
        out.write("\n\n")

        # 4.2 Xuất Markdown Tree
        out.write("=== Project Tree (Markdown) ===\n")
        out.write("# Project Structure\n")
        out.write(build_markdown_tree(root_dir))
        out.write("\n\n")

        # 4.3 Xuất JSON Tree
        out.write("=== Project Tree (JSON) ===\n")
        json_structure = build_json_structure(root_dir)
        out.write(json.dumps(json_structure, indent=2, ensure_ascii=False))
        out.write("\n\n")

        # 4.4 Xuất nội dung code
        out.write("=== Project Files Content ===\n")
        dump_code_content(root_dir, out)

if __name__ == "__main__":
    current_dir = os.getcwd()
    dump_project(current_dir, OUTPUT_FILE)
    print(f"✅ Đã xuất project ASP.NET Core MVC vào {OUTPUT_FILE}")
