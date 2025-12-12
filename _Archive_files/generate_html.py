#!/usr/bin/env python3
import os
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_title_from_file(path: str):
    """从 html 文件中提取 <title> 内容，没有就返回 None"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None

def main():
    files = []
    for name in os.listdir(BASE_DIR):
        if not name.lower().endswith(".html"):
            continue
        if name.lower() == "index.html":
            continue
        full_path = os.path.join(BASE_DIR, name)
        if os.path.isfile(full_path):
            title = get_title_from_file(full_path) or name
            files.append((name, title))

    files.sort(key=lambda x: x[0])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"fr\">",
        "<head>",
        "  <meta charset=\"UTF-8\" />",
        "  <title>French Learning Index - fr.awtza.com</title>",
        "  <style>",
        "    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;",
        "           max-width: 900px; margin: 2rem auto; padding: 0 1rem; }",
        "    h1 { margin-bottom: 0.5rem; }",
        "    .subtitle { color: #666; margin-bottom: 1.5rem; }",
        "    ul { list-style: none; padding-left: 0; }",
        "    li { margin: 0.5rem 0; }",
        "    a { text-decoration: none; color: inherit; }",
        "    .card { padding: 0.75rem 1rem; border-radius: 0.5rem;",
        "            border: 1px solid #ddd; transition: box-shadow 0.2s, transform 0.1s; }",
        "    .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-1px); }",
        "    .filename { font-size: 0.85rem; color: #999; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>📚 Bruce 的法语学习首页</h1>",
        f"  <div class=\"subtitle\">自动生成目录 · 最后更新：{now}</div>",
        "  <ul>",
    ]

    if not files:
        html_parts.append("    <li>目前还没有单元页面，请添加一些 .html 文件。</li>")
    else:
        for fname, title in files:
            html_parts.append("    <li>")
            html_parts.append(f"      <a href=\"{fname}\">")
            html_parts.append("        <div class=\"card\">")
            html_parts.append(f"          <div>{title}</div>")
            html_parts.append(f"          <div class=\"filename\">{fname}</div>")
            html_parts.append("        </div>")
            html_parts.append("      </a>")
            html_parts.append("    </li>")

    html_parts += [
        "  </ul>",
        "</body>",
        "</html>",
    ]

    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    print(f"Generated {index_path} with {len(files)} entries.")

if __name__ == "__main__":
    main()
