
#!/usr/bin/env python3
import os
from collections import defaultdict

from bs4 import BeautifulSoup
from gtts import gTTS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "restaurant.html")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

os.makedirs(AUDIO_DIR, exist_ok=True)

def text_to_speech(text: str, out_path: str, lang: str = "fr"):
    """将给定文本转换为 mp3 音频"""
    text = " ".join(text.split())
    if not text:
        return
    print(f"[TTS] {out_path} ← {text[:40]}...")
    tts = gTTS(text=text, lang=lang)
    tts.save(out_path)

def main():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    phrases = soup.select("span.fr-phrase")

    # 存储：按 section / role / 全部 来组合文本
    section_texts = defaultdict(list)   # section -> [text1, text2, ...]
    role_texts = defaultdict(list)      # role(client/server) -> [text...]
    all_texts = []

    for span in phrases:
        tts_id = span.get("data-tts-id")
        role = span.get("data-role", "unknown")
        section = span.get("data-section", "default")

        if not tts_id:
            continue

        text = span.get_text(strip=True)
        if not text:
            continue

        # 1) 单句音频
        file_name = f"restaurant_{tts_id}.mp3"
        out_path = os.path.join(AUDIO_DIR, file_name)
        text_to_speech(text, out_path)

        # 收集汇总文本
        section_texts[section].append(text)
        role_texts[role].append(text)
        all_texts.append(text)

    # 2) 每节汇总音频
    for section, texts in section_texts.items():
        joined = " ".join(texts)
        out_path = os.path.join(AUDIO_DIR, f"restaurant_section_{section}.mp3")
        text_to_speech(joined, out_path)

    # 3) 按角色汇总音频（顾客 / 服务员）
    for role, texts in role_texts.items():
        joined = " ".join(texts)
        out_path = os.path.join(AUDIO_DIR, f"restaurant_role_{role}.mp3")
        text_to_speech(joined, out_path)

    # 4) 所有台词汇总
    if all_texts:
        joined = " ".join(all_texts)
        out_path = os.path.join(AUDIO_DIR, "restaurant_all.mp3")
        text_to_speech(joined, out_path)

    print("✅ 音频生成完成。请在浏览器中打开 restaurant.html 测试播放。")

if __name__ == "__main__":
    main()
