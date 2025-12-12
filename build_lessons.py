#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一体式法语学习内容构建脚本

功能：
- 从 lessons/*.json 读取配置
- 为每个 lesson 生成：
    build/<id>.html      — 带音频播放按钮的网页
    build/<id>.md        — Markdown（可直接丢 Notion）
    build/<id>.csv       — CSV（也可导入 Notion / Excel）
    build/<id>.xlsx      — Excel（需要 openpyxl）
    build/audio/<id>/<nn>.mp3 — Google Cloud TTS 生成的语音
- 生成 build/index.html 作为总目录

依赖：
    python -m pip install google-cloud-texttospeech
    （可选）python -m pip install openpyxl

并配置 GCP 凭证，例如（PowerShell）：
    $env:GOOGLE_APPLICATION_CREDENTIALS="C:\\path\\to\\your-key.json"
"""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any, Dict, List
import datetime
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\11796\OneDrive\桌面\Web Dev\dns-credit-08cf1716327e.json"


BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "lessons"
OUTPUT_DIR = BASE_DIR / "build"
AUDIO_ROOT = OUTPUT_DIR / "audio"


# ========== 工具函数 ==========

def load_lessons() -> List[Dict[str, Any]]:
    """读取 lessons/*.json 并附加一些默认字段。"""
    lessons: List[Dict[str, Any]] = []
    if not CONTENT_DIR.exists():
        print(f"[WARN] lessons 目录不存在: {CONTENT_DIR}")
        return lessons

    for path in sorted(CONTENT_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ERROR] 解析 JSON 失败: {path} -> {e!r}")
            continue

        if "id" not in data:
            data["id"] = path.stem

        data.setdefault("title", data["id"])
        data.setdefault("title_zh", "")
        data.setdefault("description", "")
        data.setdefault("description_zh", "")
        data["_source_path"] = path

        if "sentences" not in data or not isinstance(data["sentences"], list):
            print(f"[WARN] lesson 缺少 sentences 或类型不对，跳过: {path}")
            continue

        lessons.append(data)

    return lessons


# ========== 生成 HTML ==========

HTML_LESSON_TEMPLATE_HEAD = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background-color: #f7f7f7;
            margin: 0;
            padding: 0;
        }}
        header {{
            background: linear-gradient(135deg, #ffb347, #ffcc33);
            padding: 1.2rem 1.5rem;
            color: #222;
            text-align: center;
        }}
        header h1 {{
            margin: 0;
            font-size: 1.6rem;
        }}
        header p {{
            margin: 0.3rem 0 0;
            font-size: 0.9rem;
        }}
        main {{
            max-width: 900px;
            margin: 0 auto;
            padding: 1.2rem 1rem 2rem;
        }}
        .tips {{
            background: #fff;
            border-radius: 0.8rem;
            padding: 0.8rem 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        .phrase {{
            background: #fff;
            border-radius: 0.9rem;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 0.8rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .num {{
            font-weight: 600;
            font-size: 0.85rem;
            color: #ff9800;
            width: 2.2rem;
            text-align: center;
        }}
        .text {{
            flex: 1;
        }}
        .fr {{
            font-weight: 600;
            margin-bottom: 0.15rem;
        }}
        .zh {{
            font-size: 0.9rem;
            color: #555;
        }}
        .speak-btn {{
            border: none;
            border-radius: 999px;
            padding: 0.4rem 0.65rem;
            cursor: pointer;
            font-size: 0.9rem;
            background: #ff9800;
            color: #fff;
            flex-shrink: 0;
        }}
        .speak-btn:hover {{
            opacity: 0.9;
        }}
        footer {{
            text-align: center;
            font-size: 0.8rem;
            color: #888;
            padding: 1rem 0 1.5rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </header>
    <main>
        <section class="tips">
            <strong>使用方法：</strong>先看<b>法语句子</b>再对照<b>中文意思</b>，
            点右边的<b>▶️</b>听音频。优先播放 mp3，失败时用浏览器朗读兜底。
        </section>
"""

HTML_LESSON_TEMPLATE_TAIL = """
    </main>
    <footer>
        Français · AWTZA
    </footer>
    <script>
        const globalAudio = new Audio();

        function speakFallback(text) {
            if (!("speechSynthesis" in window)) {
                alert("Votre navigateur ne supporte pas la synthèse vocale.");
                return;
            }
            const u = new SpeechSynthesisUtterance(text);
            u.lang = "fr-FR";
            u.rate = 0.85;
            u.pitch = 1.0;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
        }

        function playSentence(phraseEl) {
            const text = phraseEl.dataset.fr || "";
            const src = phraseEl.dataset.audio || "";

            if (src) {
                try {
                    globalAudio.pause();
                    globalAudio.src = src;
                    globalAudio.currentTime = 0;
                    globalAudio.play().catch(function() {
                        speakFallback(text);
                    });
                } catch (e) {
                    console.error(e);
                    speakFallback(text);
                }
            } else {
                speakFallback(text);
            }
        }
    </script>
</body>
</html>
"""

def build_lesson_html(lesson: Dict[str, Any]) -> str:
    head = HTML_LESSON_TEMPLATE_HEAD.format(
        title=lesson["title"],
        subtitle=lesson.get("title_zh", "") or lesson["id"],
    )

    blocks: List[str] = []
    sentences = lesson["sentences"]
    lesson_id = lesson["id"]

    for idx, s in enumerate(sentences, start=1):
        fr = s["fr"]
        zh = s.get("zh", "")
        audio_rel = f"audio/{lesson_id}/{idx:02d}.mp3"
        block = f'''        <div class="phrase" id="{lesson_id}_{idx:02d}" data-fr="{fr}" data-audio="{audio_rel}">
            <div class="num">{idx:02d}</div>
            <div class="text">
                <div class="fr">{fr}</div>
                <div class="zh">{zh}</div>
            </div>
            <button class="speak-btn" onclick="playSentence(this.closest('.phrase'))">▶️</button>
        </div>'''
        blocks.append(block)

    body = "\n\n".join(blocks)
    return head + body + HTML_LESSON_TEMPLATE_TAIL


def export_lesson_html(lesson: Dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{lesson['id']}.html"
    html = build_lesson_html(lesson)
    path.write_text(html, encoding="utf-8")
    print(f"[OK] HTML: {path}")
    return path


# ========== 导出 CSV / MD / XLSX ==========

def export_lesson_csv(lesson: Dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{lesson['id']}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Français", "中文"])
        for idx, s in enumerate(lesson["sentences"], start=1):
            writer.writerow([idx, s["fr"], s.get("zh", "")])
    print(f"[OK] CSV: {path}")
    return path


def export_lesson_md(lesson: Dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{lesson['id']}.md"
    lines: List[str] = []
    for idx, s in enumerate(lesson["sentences"], start=1):
        lines.append(f"## {idx:02d} {s['fr']}")
        lines.append(s.get("zh", ""))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] MD:  {path}")
    return path


def export_lesson_xlsx(lesson: Dict[str, Any]) -> Path | None:
    try:
        from openpyxl import Workbook
    except ImportError:
        print("[WARN] 未安装 openpyxl，跳过 XLSX 导出。可以运行：python -m pip install openpyxl")
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{lesson['id']}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "Phrases"
    ws.append(["#", "Français", "中文"])
    for idx, s in enumerate(lesson["sentences"], start=1):
        ws.append([idx, s["fr"], s.get("zh", "")])
    wb.save(path)
    print(f"[OK] XLSX: {path}")
    return path


# ========== Google Cloud TTS ==========

def generate_lesson_tts(lesson: Dict[str, Any],
                        speaking_rate: float = 0.85,
                        voice_name: str | None = "fr-FR-Wavenet-D") -> None:
    """为一个 lesson 生成 mp3。"""
    try:
        from google.cloud import texttospeech
    except ImportError:
        print("[ERROR] 未安装 google-cloud-texttospeech，无法生成 mp3。")
        print("        请先运行：python -m pip install google-cloud-texttospeech")
        return

    try:
        client = texttospeech.TextToSpeechClient()
    except Exception as e:
        print("[ERROR] 创建 TTS 客户端失败（多半是凭证问题）：", repr(e))
        print("        请检查 GOOGLE_APPLICATION_CREDENTIALS 是否设置正确。")
        return

    lesson_id = lesson["id"]
    sentences = lesson["sentences"]
    audio_dir = AUDIO_ROOT / lesson_id
    audio_dir.mkdir(parents=True, exist_ok=True)

    for idx, s in enumerate(sentences, start=1):
        fr_text = s["fr"]
        filename = audio_dir / f"{idx:02d}.mp3"

        # 已存在就跳过，方便重复运行
        if filename.exists():
            print(f"[TTS] 跳过已有文件: {filename.name}")
            continue

        print(f"[TTS] 生成 {lesson_id} 第 {idx:02d} 句 -> {filename.name} : {fr_text}")

        synthesis_input = texttospeech.SynthesisInput(text=fr_text)

        if voice_name:
            voice = texttospeech.VoiceSelectionParams(
                language_code="fr-FR",
                name=voice_name,
            )
        else:
            voice = texttospeech.VoiceSelectionParams(
                language_code="fr-FR",
            )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
        )

        try:
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            filename.write_bytes(response.audio_content)
        except Exception as e:
            print(f"[ERROR] 生成 {lesson_id} 第 {idx:02d} 句失败: {e!r}")
            continue

    print(f"[OK] TTS 完成: {lesson_id}")



# ========== 生成总 index.html（根目录） ==========

# ========== 生成总 index.html（根目录，列出 build 里的所有 HTML） ==========

HTML_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>French Learning Index - fr.awtza.com</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      max-width: 900px;
      margin: 2rem auto;
      padding: 0 1rem;
      background: #f7f7f7;
    }}
    h1 {{
      margin-bottom: 0.5rem;
    }}
    .subtitle {{
      color: #666;
      margin-bottom: 1.5rem;
      font-size: 0.9rem;
    }}
    ul {{
      list-style: none;
      padding-left: 0;
      margin: 0;
    }}
    li {{
      margin: 0.5rem 0;
    }}
    a {{
      text-decoration: none;
      color: inherit;
    }}
    .card {{
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      border: 1px solid #ddd;
      transition: box-shadow 0.2s, transform 0.1s, border-color 0.2s;
      background: #fff;
    }}
    .card:hover {{
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      transform: translateY(-1px);
      border-color: #bbb;
    }}
    .title-line {{
      font-size: 0.98rem;
      margin-bottom: 0.2rem;
    }}
    .title-zh {{
      font-size: 0.9rem;
      color: #555;
      margin-bottom: 0.2rem;
    }}
    .desc {{
      font-size: 0.86rem;
      color: #666;
      margin-bottom: 0.2rem;
    }}
    .filename {{
      font-size: 0.8rem;
      color: #999;
    }}
    .links {{
      margin-top: 0.25rem;
      font-size: 0.8rem;
      color: #666;
    }}
    .links a {{
      color: #1976d2;
      margin-right: 0.5rem;
    }}
    .links a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <h1>📚 Bruce 的法语学习首页</h1>
  <div class="subtitle">自动生成目录 · 最后更新：{last_updated}</div>
  <ul>
{items}
  </ul>
</body>
</html>
"""

def build_index_html(lessons: list[dict[str, Any]]) -> str:
    """
    生成 index.html 内容：
    - 用 lessons 里的元数据（如果有）补充标题/中文/描述
    - 扫描 build/*.html，把所有 HTML 页面都做成卡片
    """
    # 先把 lessons 做成一个快速索引：id -> meta
    lesson_meta: dict[str, dict[str, Any]] = {}
    for lesson in lessons:
        lesson_meta[lesson["id"]] = lesson

    item_lines: list[str] = []

    # 遍历 build 目录下所有 html（排除自身 index.html，如果存在）
    if OUTPUT_DIR.exists():
        html_files = sorted(OUTPUT_DIR.glob("*.html"))
    else:
        html_files = []

    for html_path in html_files:
        if html_path.name.lower() == "index.html":
            # 以前在 build 下生成过 index 的话，这里跳过
            continue

        lid = html_path.stem  # e.g. daily_50
        meta = lesson_meta.get(lid, {})

        title = meta.get("title", lid)
        title_zh = meta.get("title_zh", "")
        desc = meta.get("description_zh") or meta.get("description") or ""

        # 根目录 index 链接指向 build 下的文件
        html_href = f"build/{html_path.name}"

        # 可选链接：只在文件存在时显示
        md_path = OUTPUT_DIR / f"{lid}.md"
        csv_path = OUTPUT_DIR / f"{lid}.csv"
        xlsx_path = OUTPUT_DIR / f"{lid}.xlsx"

        links_parts: list[str] = [f'<a href="{html_href}">HTML</a>']
        if md_path.exists():
            links_parts.append(f'<a href="build/{lid}.md">MD</a>')
        if csv_path.exists():
            links_parts.append(f'<a href="build/{lid}.csv">CSV</a>')
        if xlsx_path.exists():
            links_parts.append(f'<a href="build/{lid}.xlsx">XLSX</a>')

        links_html = " ".join(links_parts)

        block = f"""    <li>
      <a href="{html_href}">
        <div class="card">
          <div class="title-line">{title}</div>
          <div class="title-zh">{title_zh}</div>
          {f'<div class="desc">{desc}</div>' if desc else ''}
          <div class="filename">{html_path.name}</div>
          <div class="links">
            {links_html}
          </div>
        </div>
      </a>
    </li>"""
        item_lines.append(block)

    items_str = "\n".join(item_lines)
    last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html = HTML_INDEX_TEMPLATE.format(last_updated=last_updated, items=items_str)
    return html

def export_index_html(lessons: list[dict[str, Any]]) -> Path:
    """
    把 index.html 生在根目录（脚本所在目录），
    链接指向 build/ 下面的所有 html。
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = BASE_DIR / "index.html"
    html = build_index_html(lessons)
    path.write_text(html, encoding="utf-8")
    print(f"[OK] Index: {path}")
    return path



# ========== main ==========

def build_all():
    lessons = load_lessons()
    if not lessons:
        print("[WARN] 没有找到任何 lessons/*.json")
        return

    for lesson in lessons:
        print(f"\n=== 处理 lesson: {lesson['id']} ===")
        export_lesson_html(lesson)
        export_lesson_md(lesson)
        export_lesson_csv(lesson)
        export_lesson_xlsx(lesson)
        generate_lesson_tts(lesson)

    export_index_html(lessons)


if __name__ == "__main__":
    build_all()
