import os
from google.cloud import texttospeech
from pydub import AudioSegment
from pathlib import Path
from typing import Any, Dict, List

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\11796\OneDrive\桌面\Web Dev\dns-credit-08cf1716327e.json"

OUTPUT_DIR = "audio"

client = texttospeech.TextToSpeechClient()

# 男声（服务员）
SERVEUR_VOICE = texttospeech.VoiceSelectionParams(
    language_code="fr-FR",
    name="fr-FR-Wavenet-D"  # 如果不可用，可以改成你项目里可用的 fr-FR 声音
)

# 女声（顾客 + 词汇表）
CLIENT_VOICE = texttospeech.VoiceSelectionParams(
    language_code="fr-FR",
    name="fr-FR-Wavenet-E"
)

AUDIO_CONFIG = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=0.85,
)

# -----------------------------
# 对话部分：id, 文本, 角色, 场景id
# -----------------------------
DIALOGUE_LINES = [
    ("d001", "Bonjour, bienvenue !", "serveur", "sec1"),
    ("d002", "Vous avez une réservation ?", "serveur", "sec1"),
    ("d003", "Oui, nous avons une réservation au nom de.", "client", "sec1"),
    ("d004", "Non, nous n’avons pas de réservation.", "client", "sec1"),
    ("d005", "Vous êtes combien ?", "serveur", "sec1"),
    ("d006", "Nous sommes deux.", "client", "sec1"),
    ("d007", "Suivez-moi, s’il vous plaît.", "serveur", "sec1"),
    ("d008", "Vous préférez être à l’intérieur ou en terrasse ?", "serveur", "sec1"),
    ("d009", "Est-ce qu’on peut avoir une table près de la fenêtre ?", "client", "sec1"),
    ("d010", "Bien sûr, installez-vous.", "serveur", "sec1"),

    ("d011", "Voici la carte.", "serveur", "sec2"),
    ("d012", "Je vous laisse quelques minutes.", "serveur", "sec2"),
    ("d013", "Vous avez des questions sur la carte ?", "serveur", "sec2"),
    ("d014", "Vous voulez un conseil ?", "serveur", "sec2"),
    ("d015", "Qu’est-ce que vous recommandez ?", "client", "sec2"),
    ("d016", "Le plat du jour, c’est le poisson grillé.", "serveur", "sec2"),
    ("d017", "C’est un plat assez épicé, ça vous va ?", "serveur", "sec2"),
    ("d018", "Oui, ça me va.", "client", "sec2"),
    ("d019", "Je préfère quelque chose de moins épicé.", "client", "sec2"),

    ("d020", "Qu’est-ce que vous voulez boire ?", "serveur", "sec3"),
    ("d021", "Vous voulez commencer par une boisson ?", "serveur", "sec3"),
    ("d022", "De l’eau plate ou gazeuse ?", "serveur", "sec3"),
    ("d023", "Une carafe d’eau, s’il vous plaît.", "client", "sec3"),
    ("d024", "Vous voulez du vin avec votre repas ?", "serveur", "sec3"),
    ("d025", "Je vais prendre un verre de vin rouge.", "client", "sec3"),
    ("d026", "Je vais prendre une bière, s’il vous plaît.", "client", "sec3"),

    ("d027", "Vous avez choisi ?", "serveur", "sec4"),
    ("d028", "Je peux prendre votre commande ?", "serveur", "sec4"),
    ("d029", "Oui, c’est bon.", "client", "sec4"),
    ("d030", "Pas encore, encore quelques minutes, s’il vous plaît.", "client", "sec4"),
    ("d031", "Qu’est-ce que vous prenez comme entrée ?", "serveur", "sec4"),
    ("d032", "Comme entrée, je vais prendre la soupe du jour.", "client", "sec4"),
    ("d033", "Et comme plat principal ?", "serveur", "sec4"),
    ("d034", "Comme plat principal, je vais prendre le poulet rôti.", "client", "sec4"),
    ("d035", "Vous voulez un dessert ?", "serveur", "sec4"),
    ("d036", "Oui, je vais prendre une crème brûlée.", "client", "sec4"),
    ("d037", "Non, merci.", "client", "sec4"),

    ("d038", "Avec ça, vous voulez des frites ou de la salade ?", "serveur", "sec5"),
    ("d039", "Des frites, s’il vous plaît.", "client", "sec5"),
    ("d040", "Et la cuisson du steak ? Saignant, à point ou bien cuit ?", "serveur", "sec5"),
    ("d041", "À point, s’il vous plaît.", "client", "sec5"),
    ("d042", "Vous voulez du pain avec ça ?", "serveur", "sec5"),
    ("d043", "Oui, s’il vous plaît.", "client", "sec5"),
    ("d044", "Non merci.", "client", "sec5"),

    ("d045", "Vous avez des allergies ?", "serveur", "sec6"),
    ("d046", "Oui, je suis allergique aux noix.", "client", "sec6"),
    ("d047", "D’accord, je vais le signaler en cuisine.", "serveur", "sec6"),
    ("d048", "Vous mangez de la viande ?", "serveur", "sec6"),
    ("d049", "Je ne mange pas de porc.", "client", "sec6"),
    ("d050", "Je ne mange pas de produits laitiers.", "client", "sec6"),
    ("d051", "Est-ce que ce plat contient du lait ?", "client", "sec6"),
    ("d052", "Est-ce que ce plat contient du gluten ?", "client", "sec6"),

    ("d053", "Tout se passe bien ?", "serveur", "sec7"),
    ("d054", "Ça vous plaît ?", "serveur", "sec7"),
    ("d055", "Oui, c’est très bon.", "client", "sec7"),
    ("d056", "C’est un peu trop salé.", "client", "sec7"),
    ("d057", "Je vous rapporte un peu d’eau ?", "serveur", "sec7"),
    ("d058", "Oui, merci.", "client", "sec7"),
    ("d059", "Non merci.", "client", "sec7"),

    ("d060", "L’addition, s’il vous plaît.", "client", "sec8"),
    ("d061", "Je vous apporte l’addition tout de suite.", "serveur", "sec8"),
    ("d062", "Vous payez ensemble ou séparément ?", "serveur", "sec8"),
    ("d063", "On va payer séparément, s’il vous plaît.", "client", "sec8"),
    ("d064", "Vous payez par carte ou en espèces ?", "serveur", "sec8"),
    ("d065", "Par carte, s’il vous plaît.", "client", "sec8"),
    ("d066", "En espèces.", "client", "sec8"),
    ("d067", "Je reviens avec la machine.", "serveur", "sec8"),
    ("d068", "C’était bon ?", "serveur", "sec8"),
    ("d069", "Oui, c’était délicieux, merci.", "client", "sec8"),

    ("d070", "Merci, bonne soirée !", "serveur", "sec9"),
    ("d071", "Merci, au revoir.", "client", "sec9"),
]

# -----------------------------
# 词汇表：id, 文本, 角色(统一女声), section='vocab'
# -----------------------------
VOCAB_LINES = [
    ("v001", "un restaurant", "client", "vocab"),
    ("v002", "un serveur", "client", "vocab"),
    ("v003", "une serveuse", "client", "vocab"),
    ("v004", "la carte", "client", "vocab"),
    ("v005", "le menu", "client", "vocab"),
    ("v006", "l’addition", "client", "vocab"),
    ("v007", "une réservation", "client", "vocab"),
    ("v008", "une entrée", "client", "vocab"),
    ("v009", "un plat principal", "client", "vocab"),
    ("v010", "un dessert", "client", "vocab"),
    ("v011", "une soupe", "client", "vocab"),
    ("v012", "une salade", "client", "vocab"),
    ("v013", "du poulet", "client", "vocab"),
    ("v014", "du bœuf", "client", "vocab"),
    ("v015", "du poisson", "client", "vocab"),
    ("v016", "du riz", "client", "vocab"),
    ("v017", "des pâtes", "client", "vocab"),
    ("v018", "des légumes", "client", "vocab"),
    ("v019", "des frites", "client", "vocab"),
    ("v020", "du fromage", "client", "vocab"),
    ("v021", "du pain", "client", "vocab"),
    ("v022", "de l’eau plate", "client", "vocab"),
    ("v023", "de l’eau gazeuse", "client", "vocab"),
    ("v024", "du vin rouge", "client", "vocab"),
    ("v025", "du vin blanc", "client", "vocab"),
    ("v026", "une bière", "client", "vocab"),
    ("v027", "un café", "client", "vocab"),
    ("v028", "un thé", "client", "vocab"),
    ("v029", "un jus d’orange", "client", "vocab"),
]

ALL_LINES = DIALOGUE_LINES + VOCAB_LINES


def synthesize_line(text: str, role: str) -> bytes:
    """调用 Google TTS，按角色选择男女声，返回 MP3 bytes。"""
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = SERVEUR_VOICE if role == "serveur" else CLIENT_VOICE
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=AUDIO_CONFIG,
    )
    return response.audio_content


def generate_individual_files():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for line_id, text, role, section in ALL_LINES:
        out_path = os.path.join(OUTPUT_DIR, f"{line_id}.mp3")
        # if os.path.exists(out_path):
        #     print(f"[SKIP] {out_path} already exists")
        #     continue
        print(f"[TTS] {line_id} ({role}) -> {out_path}")
        audio_bytes = synthesize_line(text, role)
        with open(out_path, "wb") as f:
            f.write(audio_bytes)


def build_sections_and_global():
    # 按 section 聚合
    sections = {}
    for line_id, text, role, section in ALL_LINES:
        sections.setdefault(section, []).append(line_id)

    # 为每个 section 合并一个 mp3
    for section_id, line_ids in sections.items():
        print(f"[MERGE] Building {section_id}_all.mp3")
        combined = AudioSegment.silent(duration=200)  # 开头空 200ms
        for line_id in line_ids:
            path = os.path.join(OUTPUT_DIR, f"{line_id}.mp3")
            audio = AudioSegment.from_file(path, format="mp3")
            # 每句后加 400ms 空白
            combined += audio + AudioSegment.silent(duration=400)
        out_path = os.path.join(OUTPUT_DIR, f"{section_id}_all.mp3")
        combined.export(out_path, format="mp3")

    # 为词汇表单独建立 vocab_all.mp3（其实已经由上面的 section='vocab' 生成）
    # 这里不需要额外处理，只是确保存在
    vocab_path = os.path.join(OUTPUT_DIR, "vocab_all.mp3")
    if not os.path.exists(vocab_path) and "vocab" in sections:
        print("[INFO] vocab_all.mp3 not found, but 'vocab' section exists (should have been created).")

    # 再拼一个 global：所有 section 串起来（对话 + 词汇）
    print("[MERGE] Building all_dialogues.mp3")
    all_combined = AudioSegment.silent(duration=200)
    for section_id in sorted(sections.keys()):  # sec1..sec9 + vocab
        sec_path = os.path.join(OUTPUT_DIR, f"{section_id}_all.mp3")
        sec_audio = AudioSegment.from_file(sec_path, format="mp3")
        # 每个 section 之间 800ms 空白
        all_combined += sec_audio + AudioSegment.silent(duration=800)
    all_path = os.path.join(OUTPUT_DIR, "all_dialogues.mp3")
    all_combined.export(all_path, format="mp3")


def main():
    generate_individual_files()
    build_sections_and_global()
    print("[DONE] 所有单句 / 分节 / 词汇表 / 汇总音频已生成到 'audio/' 目录。")


if __name__ == "__main__":
    main()
