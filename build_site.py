#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os, re, json, csv, datetime, hashlib, html
from pathlib import Path
from typing import Any, Dict, List

# ===== 路径配置 =====
ROOT = Path(__file__).parent
JSON_DIR = ROOT / "lessons_json"
LESSON_HTML_DIR = ROOT / "lessons"
AUDIO_DIR = ROOT / "audio"
EXPORT_DIR = ROOT / "exports"
ASSETS_DIR = ROOT / "assets"

STYLE_CSS = ASSETS_DIR / "style.css"
INDEX_HTML = ROOT / "index.html"

# ===== Google TTS 配置 =====
# 推荐在 PowerShell 里设置环境变量：
#   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\...\key.json"
# 如果你想写死路径就取消注释下面这一行并改成你的路径：
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\11796\OneDrive\桌面\Web Dev\dns-credit-08cf1716327e.json"

TTS_VOICE_NAME = "fr-FR-Wavenet-D"
TTS_SPEAKING_RATE = 0.85
MAX_TTS_CHARS = 3800


# ----------------- 通用工具 -----------------

def e(text: str) -> str:
    """HTML text escape"""
    return html.escape(text or "", quote=False)

def ea(text: str) -> str:
    """HTML attribute escape (quote=True)"""
    return html.escape(text or "", quote=True)

def safe_slug(text: str) -> str:
    t = (text or "").strip().lower()
    t2 = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if not t2:
        t2 = "w-" + hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:10]
    return t2[:60]

def chunk_text(text: str, max_chars: int = MAX_TTS_CHARS) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    parts = re.split(r"(?<=[\.\!\?\n])\s+", text)
    chunks: List[str] = []
    buf = ""
    for p in parts:
        p = (p or "").strip()
        if not p:
            continue
        if len(buf) + len(p) + 1 <= max_chars:
            buf = (buf + " " + p).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)

    final: List[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            for i in range(0, len(c), max_chars):
                final.append(c[i:i+max_chars])
    return final

def details_zh(zh: str) -> str:
    zh = (zh or "").strip()
    if not zh:
        return ""
    # ✅ summary 保持 “--”
    return f"""
      <details class="zh">
        <summary>--</summary>
        <div class="zh-text">{e(zh)}</div>
      </details>
    """

def pick_sentences(lesson: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    兼容多种字段名：
    - sentences (推荐)
    - phrases
    - pharse / pharses (常见拼写错误)
    返回列表里只保留有 fr 的条目（没 fr 就跳过）
    """
    candidates = []
    for key in ("sentences", "phrases", "pharse", "pharses"):
        v = lesson.get(key)
        if isinstance(v, list) and v:
            candidates = v
            break

    out: List[Dict[str, Any]] = []
    for it in candidates:
        if not isinstance(it, dict):
            continue
        fr = (it.get("fr") or it.get("phrase") or it.get("pharse") or "").strip()
        # ✅ 没有 phrase/fr 就跳过
        if not fr:
            continue
        out.append({
            "fr": fr,
            "zh": (it.get("zh") or it.get("cn") or "").strip(),
            "words": it.get("words") if isinstance(it.get("words"), list) else []
        })
    return out

def pick_passage(lesson: Dict[str, Any]) -> Dict[str, str]:
    p = lesson.get("passage")
    if not isinstance(p, dict):
        return {}
    fr = (p.get("fr") or "").strip()
    if not fr:
        return {}
    return {"fr": fr, "zh": (p.get("zh") or "").strip()}


def load_all_json() -> List[Dict[str, Any]]:
    lessons: List[Dict[str, Any]] = []
    if not JSON_DIR.exists():
        print(f"[WARN] JSON_DIR not found: {JSON_DIR}")
        return lessons

    for p in sorted(JSON_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as ex:
            print(f"[ERROR] JSON parse failed: {p} -> {ex!r}")
            continue

        data.setdefault("id", p.stem)
        data.setdefault("title", data["id"])
        data.setdefault("title_zh", "")
        data.setdefault("description", "")
        data.setdefault("description_zh", "")

        # 统一抽取（兼容错字段名）
        data["_sentences"] = pick_sentences(data)
        data["_passage"] = pick_passage(data)

        # 词汇：兼容 vocab / vocab_nouns / vocab_verbs / nouns / verbs
        vocab: List[Dict[str, str]] = []
        if isinstance(data.get("vocab"), list):
            vocab += [x for x in data["vocab"] if isinstance(x, dict)]
        if isinstance(data.get("vocab_nouns"), list):
            vocab += [x for x in data["vocab_nouns"] if isinstance(x, dict)]
        if isinstance(data.get("vocab_verbs"), list):
            vocab += [x for x in data["vocab_verbs"] if isinstance(x, dict)]
        if isinstance(data.get("nouns"), list):
            vocab += [x for x in data["nouns"] if isinstance(x, dict)]
        if isinstance(data.get("verbs"), list):
            vocab += [x for x in data["verbs"] if isinstance(x, dict)]

        # 清洗 + 去重
        seen = set()
        vocab2: List[Dict[str, str]] = []
        for w in vocab:
            fr = (w.get("fr") or "").strip()
            if not fr:
                continue
            k = fr.lower()
            if k in seen:
                continue
            seen.add(k)
            vocab2.append({"fr": fr, "zh": (w.get("zh") or "").strip()})
        data["_vocab"] = vocab2

        lessons.append(data)

    return lessons


# ----------------- Google Cloud TTS -----------------

def tts_client():
    from google.cloud import texttospeech
    return texttospeech.TextToSpeechClient()

def synthesize_mp3(client, text: str, out_path: Path):
    from google.cloud import texttospeech
    out_path.parent.mkdir(parents=True, exist_ok=True)

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="fr-FR", name=TTS_VOICE_NAME)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=TTS_SPEAKING_RATE
    )
    resp = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    out_path.write_bytes(resp.audio_content)

def ensure_tts_segments(client, text: str, out_dir: Path, stem: str) -> List[str]:
    segs = chunk_text(text)
    rel: List[str] = []
    for i, seg in enumerate(segs, start=1):
        fname = f"{stem}_{i:02d}.mp3"
        outp = out_dir / fname
        if not outp.exists():
            synthesize_mp3(client, seg, outp)
            print(f"[TTS] {outp}")
        rel.append(fname)
    return rel


# ----------------- 导出 -----------------

def export_md(lesson: Dict[str, Any]):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    p = EXPORT_DIR / f"{lesson['id']}.md"

    lines = [f"# {lesson.get('title','')}", lesson.get("title_zh",""), ""]
    passage = lesson["_passage"]
    if passage.get("fr"):
        lines += ["## Passage", passage["fr"], ""]
        if passage.get("zh"):
            lines += [f"> {passage['zh']}", ""]

    sentences = lesson["_sentences"]
    if sentences:
        lines.append("## Sentences")
        for i, s in enumerate(sentences, start=1):
            lines.append(f"### {i:02d} {s['fr']}")
            if s.get("zh"):
                lines.append(s["zh"])
            lines.append("")

    vocab = lesson["_vocab"]
    if vocab:
        lines.append("## Vocab")
        for w in vocab:
            lines.append(f"- **{w['fr']}** — {w.get('zh','')}")

    p.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] MD  {p}")

def export_csv(lesson: Dict[str, Any]):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    p = EXPORT_DIR / f"{lesson['id']}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type", "#", "fr", "zh"])
        passage = lesson["_passage"]
        if passage.get("fr"):
            w.writerow(["passage", "", passage.get("fr",""), passage.get("zh","")])
        for i, s in enumerate(lesson["_sentences"], start=1):
            w.writerow(["sentence", i, s.get("fr",""), s.get("zh","")])
        for i, v in enumerate(lesson["_vocab"], start=1):
            w.writerow(["vocab", i, v.get("fr",""), v.get("zh","")])
    print(f"[OK] CSV {p}")

def export_xlsx(lesson: Dict[str, Any]):
    try:
        from openpyxl import Workbook
    except ImportError:
        print("[WARN] openpyxl not installed, skip xlsx. (python -m pip install openpyxl)")
        return

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    p = EXPORT_DIR / f"{lesson['id']}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "Sentences" # type: ignore
    ws.append(["#", "Français", "中文"]) # type: ignore
    for i, s in enumerate(lesson["_sentences"], start=1):
        ws.append([i, s.get("fr",""), s.get("zh","")]) # type: ignore

    ws2 = wb.create_sheet("Vocab")
    ws2.append(["#", "Mot", "中文"])
    for i, v in enumerate(lesson["_vocab"], start=1):
        ws2.append([i, v.get("fr",""), v.get("zh","")])

    wb.save(p)
    print(f"[OK] XLSX {p}")


# ----------------- HTML 生成 -----------------

LESSON_HTML_HEAD = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="../assets/style.css" />
</head>
<body>
  <header class="header">
    <h1>{title}</h1>
    <p>{title_zh}</p>
  </header>

  <main class="container">
    <div class="bar">
      <span class="pill">📄 <a class="link" href="../index.html">Index</a></span>
      <span class="pill">📝 <a class="link" href="../exports/{id}.md">MD</a></span>
      <span class="pill">📑 <a class="link" href="../exports/{id}.csv">CSV</a></span>
      <span class="pill">📊 <a class="link" href="../exports/{id}.xlsx">XLSX</a></span>
    </div>
"""

LESSON_HTML_TAIL = """
    <div class="footer">Français · Lesson · AWTZA</div>
  </main>

  <script>
    let passageQueue = [];
    let passageIndex = 0;
    const passageAudio = new Audio();

    function playPassage(queue){
      passageQueue = queue || [];
      passageIndex = 0;
      if (!passageQueue.length) return;
      passageAudio.src = passageQueue[0];
      passageAudio.currentTime = 0;
      passageAudio.play();
    }

    passageAudio.addEventListener("ended", () => {
      passageIndex += 1;
      if (passageIndex < passageQueue.length){
        passageAudio.src = passageQueue[passageIndex];
        passageAudio.currentTime = 0;
        passageAudio.play();
      }
    });

    const globalAudio = new Audio();

    function speakFallback(text){
      if (!("speechSynthesis" in window)) {
        alert("Browser TTS not supported.");
        return;
      }
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "fr-FR";
      u.rate = 0.85;
      u.pitch = 1.0;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    }

    function playFromDataset(el){
      const text = el.dataset.fr || "";
      const src = el.dataset.audio || "";
      if (!src){
        speakFallback(text);
        return;
      }
      try{
        globalAudio.pause();
        globalAudio.src = src;
        globalAudio.currentTime = 0;
        globalAudio.play().catch(() => speakFallback(text));
      }catch(e){
        speakFallback(text);
      }
    }
  </script>
</body>
</html>
"""

def generate_lesson_page(lesson: Dict[str, Any], passage_srcs: List[str]) -> str:
    lid = lesson["id"]
    title = lesson.get("title", lid)
    title_zh = lesson.get("title_zh", "")

    out = [LESSON_HTML_HEAD.format(title=e(title), title_zh=e(title_zh), id=ea(lid))]

    # Passage（没有就跳过）
    passage = lesson["_passage"]
    if passage.get("fr"):
        queue_js = "[" + ",".join([f"\"../audio/{lid}/{ea(s)}\"" for s in passage_srcs]) + "]"
        out.append(f"""
    <section class="card pad col-12">
      <div class="section-title">
        <h2>📖 Passage</h2>
        <div class="hint">整篇朗读（分段 mp3 自动顺序播放）</div>
      </div>
      <div class="actions">
        <button class="btn" onclick='playPassage({queue_js})'>▶️ Play passage</button>
        <span class="pill">Segments: {len(passage_srcs)}</span>
      </div>
      <div class="divider"></div>
      <div class="fr">{e(passage["fr"])}</div>
      {details_zh(passage.get("zh",""))}
    </section>
""")

    # Sentences（每条没 fr 就跳过）
    sentences = lesson["_sentences"]
    if sentences:
        out.append("""
    <section class="card pad col-12">
      <div class="section-title">
        <h2>🧩 Sentences</h2>
        <div class="hint">单句朗读 + 中文折叠</div>
      </div>
      <div class="list">
""")
        for i, s in enumerate(sentences, start=1):
            fr = s["fr"]
            zh = s.get("zh", "")
            src = f"../audio/{lid}/sentences/{i:02d}.mp3"
            out.append(f"""
        <div class="item row" data-fr="{ea(fr)}" data-audio="{ea(src)}">
          <div class="num">{i:02d}</div>
          <div style="flex:1">
            <div class="fr">{e(fr)}</div>
            {details_zh(zh)}
          </div>
          <div class="actions">
            <button class="btn" onclick="playFromDataset(this.closest('.item'))">▶️</button>
          </div>
        </div>
""")
        out.append("""
      </div>
    </section>
""")

    # Vocab（没有就跳过；单词没 fr 就跳过）
    vocab = lesson["_vocab"]
    if vocab:
        out.append("""
    <section class="card pad col-12">
      <div class="section-title">
        <h2>🧠 Vocab</h2>
        <div class="hint">单词朗读 + 中文折叠</div>
      </div>
      <div class="list">
""")
        for w in vocab:
            word = w["fr"]
            zh = w.get("zh", "")
            slug = safe_slug(word)
            src = f"../audio/{lid}/words/{slug}.mp3"
            out.append(f"""
        <div class="item row" data-fr="{ea(word)}" data-audio="{ea(src)}">
          <div class="num">•</div>
          <div style="flex:1">
            <div class="fr">{e(word)}</div>
            {details_zh(zh)}
          </div>
          <div class="actions">
            <button class="btn ghost" onclick="playFromDataset(this.closest('.item'))">🔊</button>
          </div>
        </div>
""")
        out.append("""
      </div>
    </section>
""")

    out.append(LESSON_HTML_TAIL)
    return "".join(out)


# ----------------- Index（根目录） -----------------

def build_index(lessons: List[Dict[str, Any]]):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    items = []
    for ls in lessons:
        lid = ls["id"]
        items.append(f"""
        <a href="lessons/{ea(lid)}.html">
          <div class="item">
            <div class="fr">{e(ls.get("title", lid))}</div>
            <div class="muted">{e(ls.get("title_zh",""))}</div>
            <div class="kv">
              <span><a class="link" href="lessons/{ea(lid)}.html">HTML</a></span>
              <span><a class="link" href="exports/{ea(lid)}.md">MD</a></span>
              <span><a class="link" href="exports/{ea(lid)}.csv">CSV</a></span>
              <span><a class="link" href="exports/{ea(lid)}.xlsx">XLSX</a></span>
              <span class="muted">audio/{e(lid)}/…</span>
            </div>
          </div>
        </a>
        """.rstrip())

    html_index = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>French Learning Index</title>
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body>
  <header class="header">
    <h1>📚 Bruce 的法语学习首页</h1>
    <p>统一模板 + 自动生成 · 最后更新：{now}</p>
  </header>

  <main class="container">
    <div class="card pad">
      <div class="section-title">
        <h2>Leçons</h2>
        <div class="hint">{len(lessons)} lessons</div>
      </div>

      <div class="list">
        {''.join(items)}
      </div>
    </div>

    <div class="footer">Français · AWTZA</div>
  </main>
</body>
</html>
"""
    INDEX_HTML.write_text(html_index, encoding="utf-8")
    print(f"[OK] INDEX {INDEX_HTML}")


# ----------------- 主流程 -----------------

def build_all():
    if not STYLE_CSS.exists():
        raise FileNotFoundError(f"Missing CSS: {STYLE_CSS}")

    LESSON_HTML_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    lessons = load_all_json()
    if not lessons:
        print("[WARN] No json lessons found.")
        return

    # TTS client init
    client = tts_client()

    for lesson in lessons:
        lid = lesson["id"]
        print(f"\n=== BUILD {lid} ===")

        # 1) 导出
        export_md(lesson)
        export_csv(lesson)
        export_xlsx(lesson)

        # 2) 音频：passage / sentences / words
        passage_srcs: List[str] = []
        passage = lesson["_passage"]
        if passage.get("fr"):
            out_dir = AUDIO_DIR / lid
            passage_srcs = ensure_tts_segments(client, passage["fr"], out_dir, "passage")

        # sentences
        for i, s in enumerate(lesson["_sentences"], start=1):
            fr = (s.get("fr") or "").strip()
            if not fr:
                continue
            outp = AUDIO_DIR / lid / "sentences" / f"{i:02d}.mp3"
            if not outp.exists():
                synthesize_mp3(client, fr, outp)
                print(f"[TTS] {outp}")

        # words（只用 _vocab；没 fr 自动跳过）
        seen = set()
        for w in lesson["_vocab"]:
            word = (w.get("fr") or "").strip()
            if not word:
                continue
            k = word.lower()
            if k in seen:
                continue
            seen.add(k)
            slug = safe_slug(word)
            outp = AUDIO_DIR / lid / "words" / f"{slug}.mp3"
            if not outp.exists():
                synthesize_mp3(client, word, outp)
                print(f"[TTS] {outp}")

        # 3) HTML
        html_page = generate_lesson_page(lesson, passage_srcs)
        out_html = LESSON_HTML_DIR / f"{lid}.html"
        out_html.write_text(html_page, encoding="utf-8")
        print(f"[OK] HTML {out_html}")

    # 4) index
    build_index(lessons)


if __name__ == "__main__":
    build_all()
