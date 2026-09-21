import os
import sys
import subprocess
import json
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from PIL import Image, ImageFilter

load_dotenv()

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
YTDLP_PATH = r"C:\Python312\Scripts\yt-dlp.EXE"
YT_URL = "https://www.youtube.com/watch?v=bWph7PoODuw"

os.makedirs("temp", exist_ok=True)
os.makedirs("output", exist_ok=True)

# 1. Narration Segments
SECTIONS = [
    {
        "id": "01_intro",
        "type": "narr",
        "text": (
            "Founded in 1993 in Australia, Abyssic Hate stands as one of the darkest "
            "and most influential one-man band projects in the history of underground black metal. "
            "Behind the entire vision was a single mastermind: Shane Rout. "
            "Operating in complete isolation, he wrote, performed, and recorded every instrument and vocal line himself. "
            "In the year 2000, he unleashed the project's defining masterpiece: the seminal album, Suicidal Emotions."
        ),
        "visual": "intro_shane"
    },
    {
        "id": "02_intro_sample1",
        "type": "narr",
        "text": (
            "The journey begins with Depression: Part One. "
            "Driven by a hypnotic, sorrowful guitar loop that repeats over a deliberate, slow beat, "
            "this track became the blueprint for atmospheric despair. Listen to how the melody builds."
        ),
        "visual": "cover_track1"
    },
    {
        "id": "03_sample1",
        "type": "music",
        "file": "temp/sample1.mp3",
        "download_range": "*00:45-01:03", # 18s
        "title": "01. Depression - Part I",
        "visual": "cover_track1"
    },
    {
        "id": "04_intro_sample2",
        "type": "narr",
        "text": (
            "While much of the album is slow and suffocating, the second track, Betrayed, shifts the momentum. "
            "It hits with a faster tempo, abrasive aggression, and a driving melancholic riff that captures pure anguish."
        ),
        "visual": "cover_track2"
    },
    {
        "id": "05_sample2",
        "type": "music",
        "file": "temp/sample2.mp3",
        "download_range": "*12:45-13:03", # 18s
        "title": "02. Betrayed",
        "visual": "cover_track2"
    },
    {
        "id": "06_intro_sample3",
        "type": "narr",
        "text": (
            "Then comes Depression: Part Two, marking the darkest emotional climax of the record. "
            "Anchored by a heavy, plodding bassline, it gives way to Shane Rout's torturous, agonized vocals, "
            "laying bare the sheer desolation at the heart of the project."
        ),
        "visual": "cover_track3"
    },
    {
        "id": "07_sample3",
        "type": "music",
        "file": "temp/sample3.mp3",
        "download_range": "*25:15-25:33", # 18s
        "title": "03. Depression - Part II",
        "visual": "cover_track3"
    },
    {
        "id": "08_outro",
        "type": "narr",
        "text": (
            "Decades later, Suicidal Emotions remains a monumental achievement, "
            "proving just how haunting and timeless a solitary artistic vision can truly be."
        ),
        "visual": "cover_outro"
    }
]

def download_samples():
    print("\n--- Verificando / Baixando Amostras Musicais do YouTube ---")
    for sec in SECTIONS:
        if sec["type"] == "music":
            dest = sec["file"]
            if os.path.exists(dest) and os.path.getsize(dest) > 10000:
                print(f"Sample já existe: {dest}")
                continue
            print(f"Baixando {sec['title']} ({sec['download_range']})...")
            cmd = [
                YTDLP_PATH,
                "--ffmpeg-location", FFMPEG_PATH,
                "--download-sections", sec["download_range"],
                "-x", "--audio-format", "mp3",
                "-o", dest.replace(".mp3", ".%(ext)s"),
                YT_URL
            ]
            subprocess.run(cmd, check=True)

def generate_narrations():
    print("\n--- Gerando Locuções com ElevenLabs ---")
    api_key = os.getenv("ELEVENLABS_API_KEY")
    client = ElevenLabs(api_key=api_key)
    
    # ID da voz Adam ou George (voz profunda e limpa para narração)
    voice_id = "JBFqnCBsd6RMkjVDRZzb" # George / Deep male voice
    
    for sec in SECTIONS:
        if sec["type"] == "narr":
            out_file = f"temp/{sec['id']}.mp3"
            sec["audio_file"] = out_file
            if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
                print(f"Locução já gerada: {out_file}")
                continue
            print(f"Gerando áudio para: {sec['id']}...")
            audio_stream = client.text_to_speech.convert(
                voice_id=voice_id,
                text=sec["text"],
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.55,
                    similarity_boost=0.75,
                    style=0.15,
                    use_speaker_boost=True
                )
            )
            with open(out_file, "wb") as f:
                for chunk in audio_stream:
                    f.write(chunk)
            print(f"Salvo: {out_file} ({os.path.getsize(out_file)} bytes)")

def get_audio_duration(file_path):
    cmd = [
        FFMPEG_PATH, "-i", file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in res.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
    return 10.0

def create_16x9_backdrop(fg_path, out_path, title_text=None, subtitle_text=None):
    """Cria imagem 1920x1080 com fundo desfocado da própria arte e primeiro plano centralizado nítido"""
    from PIL import ImageDraw, ImageFont
    
    W, H = 1920, 1080
    fg = Image.open(fg_path).convert("RGB")
    
    # Fundo 16:9 desfocado e escurecido
    bg = fg.copy().resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
    # Escurece um pouco o fundo para destacar o centro
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.4)
    
    # Redimensiona imagem principal para caber na altura (ex: 880px de altura)
    target_h = 880
    aspect = fg.width / fg.height
    target_w = int(target_h * aspect)
    fg_resized = fg.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Cola no centro
    pos_x = (W - target_w) // 2
    pos_y = (H - target_h) // 2
    bg.paste(fg_resized, (pos_x, pos_y))
    
    # Borda sutil de destaque
    draw = ImageDraw.Draw(bg)
    draw.rectangle([pos_x, pos_y, pos_x + target_w, pos_y + target_h], outline=(80, 80, 80), width=3)
    
    # Se houver textos de overlay
    if title_text:
        # Faixa inferior elegante
        draw.rectangle([0, H - 90, W, H], fill=(10, 10, 10))
        draw.line([0, H - 90, W, H - 90], fill=(60, 60, 60), width=2)
        # Escreve o texto com fonte padrão ou truetype
        draw.text((W // 2, H - 55), title_text, fill=(230, 230, 230), anchor="mm")
    
    bg.save(out_path, quality=95)
    return out_path

def prepare_visuals():
    print("\n--- Preparando Telas 16:9 (1920x1080) ---")
    cover_blurred = "assets/suicidal_emotions_blurred.jpg"
    shane = "assets/shane_rout.jpg"
    logo = "assets/abyssic_hate_logo.jpg"
    
    create_16x9_backdrop(logo, "temp/slide_logo.jpg", "ABYSSIC HATE (AUSTRALIA - 1993)")
    create_16x9_backdrop(shane, "temp/slide_shane.jpg", "SHANE ROUT - THE SOLE MASTERMIND")
    create_16x9_backdrop(cover_blurred, "temp/slide_album.jpg", "ABYSSIC HATE - SUICIDAL EMOTIONS (2000)")
    create_16x9_backdrop(cover_blurred, "temp/slide_track1.jpg", "NOW PLAYING: 01. DEPRESSION - PART I")
    create_16x9_backdrop(cover_blurred, "temp/slide_track2.jpg", "NOW PLAYING: 02. BETRAYED")
    create_16x9_backdrop(cover_blurred, "temp/slide_track3.jpg", "NOW PLAYING: 03. DEPRESSION - PART II")
    create_16x9_backdrop(cover_blurred, "temp/slide_outro.jpg", "A MONUMENT OF DEPRESSIVE BLACK METAL")

def render_video():
    print("\n--- Renderizando Clipes e Montando Vídeo Final ---")
    clip_list_file = "temp/clips.txt"
    clip_files = []
    
    for idx, sec in enumerate(SECTIONS):
        clip_path = f"temp/clip_{idx:02d}.mp4"
        
        # Define áudio
        if sec["type"] == "narr":
            audio_in = sec.get("audio_file", f"temp/{sec['id']}.mp3")
            # Fade out leve no áudio no fim
            is_music = False
        else:
            audio_in = sec["file"]
            is_music = True
            
        dur = get_audio_duration(audio_in)
        
        # Define imagem de fundo
        vis = sec["visual"]
        if vis == "intro_shane":
            img_in = "temp/slide_shane.jpg"
        elif vis == "cover_track1":
            img_in = "temp/slide_track1.jpg"
        elif vis == "cover_track2":
            img_in = "temp/slide_track2.jpg"
        elif vis == "cover_track3":
            img_in = "temp/slide_track3.jpg"
        elif vis == "cover_outro":
            img_in = "temp/slide_outro.jpg"
        else:
            img_in = "temp/slide_album.jpg"
            
        # Para trechos musicais, aplica fade in de 1s e fade out de 1.5s
        if is_music:
            af_filter = f"afade=t=in:ss=0:d=1.0,afade=t=out:st={dur-1.5:.2f}:d=1.5"
        else:
            af_filter = "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo"
            
        cmd = [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-i", img_in,
            "-i", audio_in,
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080",
            "-af", af_filter,
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(dur),
            clip_path
        ]
        print(f"Renderizando segmento {idx+1}/{len(SECTIONS)} ({dur:.1f}s)...")
        subprocess.run(cmd, check=True)
        clip_files.append(clip_path)

    # Concatena todos os segmentos
    with open(clip_list_file, "w", encoding="utf-8") as f:
        for c in clip_files:
            abs_c = os.path.abspath(c).replace("\\", "/")
            f.write(f"file '{abs_c}'\n")

    final_output = "output/Abyssic_Hate_Suicidal_Emotions.mp4"
    print(f"\nJuntando todos os segmentos em: {final_output}")
    cmd_concat = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", clip_list_file,
        "-c", "copy",
        final_output
    ]
    subprocess.run(cmd_concat, check=True)
    print(f"\n=======================================================")
    print(f"SUCESSO! VÍDEO COMPLETO GERADO EM: {final_output}")
    print(f"Tamanho: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"=======================================================\n")

if __name__ == "__main__":
    download_samples()
    generate_narrations()
    prepare_visuals()
    render_video()
