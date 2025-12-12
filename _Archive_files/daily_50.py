#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
50 phrases de la vie quotidienne en français

功能：
- 生成 fr_daily_50.html
- 导出 fr_daily_50.csv
- 导出 fr_daily_50.md
- 用 Google Cloud Text-to-Speech 生成法语 mp3（语速偏慢，自然一点）

使用前：
    pip install google-cloud-texttospeech

并确保已经设置好 GCP 凭证，例如：
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-key.json"
"""

from pathlib import Path

# ===== 1. 数据：50 句日常对话 =====

phrases = [
    (1,  "Bonjour !",                                 "你好！（白天打招呼）"),
    (2,  "Salut !",                                    "嗨！ / 你好！（比较随意）"),
    (3,  "Ça va ?",                                    "最近怎么样？ / 还好吗？"),
    (4,  "Ça va bien, merci. Et toi ?",                "我很好，谢谢，你呢？"),
    (5,  "Comment tu t’appelles ?",                    "你叫什么名字？"),
    (6,  "Je m’appelle …",                             "我叫……"),
    (7,  "Enchanté.",                                  "幸会。（男生说）"),
    (8,  "Tu viens d’où ?",                            "你来自哪里？"),
    (9,  "Je viens de Chine.",                         "我来自中国。"),
    (10, "Tu habites où maintenant ?",                 "你现在住在哪里？"),
    (11, "J’habite à Vancouver.",                      "我住在温哥华。"),
    (12, "Qu’est-ce que tu fais dans la vie ?",        "你是做什么工作的？ / 你平时做什么？"),
    (13, "Je suis étudiant.",                          "我是学生。（男）"),
    (14, "Je suis étudiante.",                         "我是学生。（女）"),
    (15, "Je travaille dans l’informatique.",          "我在 IT 行业工作。"),
    (16, "Tu parles quelles langues ?",                "你会说哪些语言？"),
    (17, "Je parle chinois, anglais et un peu français.", "我会说中文、英文和一点法语。"),
    (18, "Tu peux répéter, s’il te plaît ?",           "你可以再说一遍吗？（朋友间）"),
    (19, "Tu peux parler plus lentement, s’il te plaît ?", "你可以说慢一点吗？（朋友间）"),
    (20, "Je ne comprends pas.",                       "我不明白。 / 我听不懂。"),
    (21, "Tu peux l’écrire, s’il te plaît ?",          "你可以写下来吗？"),
    (22, "Qu’est-ce que ça veut dire ?",               "这是什么意思？"),
    (23, "Tu es libre ce week-end ?",                  "你这个周末有空吗？"),
    (24, "On se voit quand ?",                         "我们什么时候见面？"),
    (25, "On se voit demain ?",                        "我们明天见面吗？"),
    (26, "À quelle heure ?",                           "几点？ / 什么时间？"),
    (27, "Où on se retrouve ?",                        "我们在哪里见面？ / 在哪儿碰头？"),
    (28, "Ça te va ?",                                 "这样可以吗？ / 合适吗？"),
    (29, "Pas de problème.",                           "没问题。"),
    (30, "Merci beaucoup.",                            "非常感谢。"),
    (31, "De rien.",                                   "不客气。"),
    (32, "Excuse-moi.",                                "不好意思。（朋友间）"),
    (33, "Pardon, je suis en retard.",                 "不好意思，我迟到了。"),
    (34, "Ce n’est pas grave.",                        "没关系。 / 不要紧。"),
    (35, "J’aime beaucoup cette ville.",               "我很喜欢这座城市。"),
    (36, "Il fait beau aujourd’hui.",                  "今天天气很好。"),
    (37, "J’ai faim.",                                 "我饿了。"),
    (38, "J’ai soif.",                                 "我渴了。"),
    (39, "Je suis fatigué.",                           "我累了。（男）"),
    (40, "Je suis fatiguée.",                          "我累了。（女）"),
    (41, "J’ai besoin de dormir.",                     "我需要睡觉了。"),
    (42, "On y va ?",                                  "我们走吗？ / 出发吗？"),
    (43, "Attends une minute, s’il te plaît.",         "等一下，拜托。（等我一下）"),
    (44, "Tu peux m’aider ?",                          "你能帮我一下吗？"),
    (45, "Comment on dit ça en français ?",            "这个用法语怎么说？"),
    (46, "Je dois y aller.",                           "我得走了。"),
    (47, "À tout à l’heure !",                         "一会儿见！"),
    (48, "À demain !",                                 "明天见！"),
    (49, "Bonne journée !",                            "祝你今天愉快！"),
    (50, "Bonne soirée !",                             "祝你晚上愉快！"),
]

# ===== 2. 生成 HTML（结构和之前一样，还是用浏览器 TTS） =====

HTML_HEAD = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Français – 50 phrases de la vie quotidienne</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background-color: #f7f7f7;
            margin: 0;
            padding: 0;
        }
        header {
            background: linear-gradient(135deg, #ffb347, #ffcc33);
            padding: 1.2rem 1.5rem;
            color: #222;
            text-align: center;
        }
        header h1 {
            margin: 0;
            font-size: 1.6rem;
        }
        header p {
            margin: 0.3rem 0 0;
            font-size: 0.9rem;
        }
        main {
            max-width: 900px;
            margin: 0 auto;
            padding: 1.2rem 1rem 2rem;
        }
        .tips {
            background: #fff;
            border-radius: 0.8rem;
            padding: 0.8rem 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            font-size: 0.9rem;
            line-height: 1.4;
        }
        .phrase {
            background: #fff;
            border-radius: 0.9rem;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 0.8rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .num {
            font-weight: 600;
            font-size: 0.85rem;
            color: #ff9800;
            width: 2.2rem;
            text-align: center;
        }
        .text {
            flex: 1;
        }
        .fr {
            font-weight: 600;
            margin-bottom: 0.15rem;
        }
        .zh {
            font-size: 0.9rem;
            color: #555;
        }
        .speak-btn {
            border: none;
            border-radius: 999px;
            padding: 0.4rem 0.65rem;
            cursor: pointer;
            font-size: 0.9rem;
            background: #ff9800;
            color: #fff;
            flex-shrink: 0;
        }
        .speak-btn:hover {
            opacity: 0.9;
        }
        footer {
            text-align: center;
            font-size: 0.8rem;
            color: #888;
            padding: 1rem 0 1.5rem;
        }
    </style>
</head>
<body>
    <header>
        <h1>50 phrases de la vie quotidienne</h1>
        <p>日常对话常用 50 句 · Cliquez sur ▶️ pour 听法语发音</p>
    </header>
    <main>
        <section class="tips">
            <strong>使用方法：</strong>先看<b>法语句子</b>再对照<b>中文意思</b>，
            最后点右边的<b>▶️</b>跟读。语速比正常略慢，适合初学者。
        </section>
"""

HTML_TAIL = """
    </main>
    <footer>
        Français · Vie quotidienne · AWTZA
    </footer>
    <script>
        function speak(text) {
            if (!("speechSynthesis" in window)) {
                alert("Votre navigateur ne supporte pas la synthèse vocale.");
                return;
            }
            const u = new SpeechSynthesisUtterance(text);
            u.lang = "fr-FR";
            u.rate = 0.85;  // 比正常略慢
            u.pitch = 1.0;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
        }
    </script>
</body>
</html>
"""

def build_html_body() -> str:
    blocks = []
    for num, fr, zh in phrases:
        block = f'''        <div class="phrase" id="p{num}" data-fr="{fr}">
            <div class="num">{num:02d}</div>
            <div class="text">
                <div class="fr">{fr}</div>
                <div class="zh">{zh}</div>
            </div>
            <button class="speak-btn" onclick="speak(this.closest('.phrase').dataset.fr)">▶️</button>
        </div>'''
        blocks.append(block)
    return "\n\n".join(blocks)

def export_html(path: Path = Path("fr_daily_50.html")):
    html = HTML_HEAD + build_html_body() + HTML_TAIL
    path.write_text(html, encoding="utf-8")
    print(f"[OK] 生成 HTML: {path}")


# ===== 3. 导出 CSV（给 Notion 用） =====

def export_csv(path: Path = Path("fr_daily_50.csv")):
    import csv
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Français", "中文"])
        for num, fr, zh in phrases:
            writer.writerow([num, fr, zh])
    print(f"[OK] 导出 CSV: {path}")


# ===== 4. 导出 Markdown（可以直接粘到 Notion 页面） =====

def export_md(path: Path = Path("fr_daily_50.md")):
    lines = []
    for num, fr, zh in phrases:
        lines.append(f"## {num:02d} {fr}")
        lines.append(zh)
        lines.append("")  # 空行
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 导出 Markdown: {path}")


# ===== 5. 用 Google Cloud Text-to-Speech 生成 mp3 =====

def generate_tts_google(output_dir: Path = Path("audio"),
                         speaking_rate: float = 0.85,
                         voice_name: str | None = "fr-FR-Wavenet-D"):
    """
    用 Google Cloud Text-to-Speech 为每个法语句子生成一个 mp3 文件。

    需要：
        pip install google-cloud-texttospeech
    并配置好 GCP 凭证（GOOGLE_APPLICATION_CREDENTIALS 等）。

    参数：
        output_dir: 输出目录（默认 audio/）
        speaking_rate: 语速，1.0 为正常，可以略微调慢，比如 0.85
        voice_name: 具体的 voice 名字，None 则让 Google 自动选
                    常用示例：fr-FR-Wavenet-B / fr-FR-Wavenet-D 等
    """
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    output_dir.mkdir(parents=True, exist_ok=True)

    for num, fr, _ in phrases:
        filename = output_dir / f"{num:02d}.mp3"

        synthesis_input = texttospeech.SynthesisInput(text=fr)

        if voice_name:
            voice = texttospeech.VoiceSelectionParams(
                language_code="fr-FR",
                name=voice_name,
            )
        else:
            voice = texttospeech.VoiceSelectionParams(
                language_code="fr-FR"
            )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        filename.write_bytes(response.audio_content)
        print(f"[TTS] 生成 {filename}")

    print("[OK] 所有 mp3 已生成。")


# ===== main =====

def main():
    export_html()
    export_csv()
    export_md()
    # 如果想同时生成 Google TTS mp3，取消下一行注释：
    generate_tts_google()

if __name__ == "__main__":
    main()
