import os
import sys
import subprocess
import re

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from PIL import Image, ImageFilter, ImageDraw, ImageFont
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

load_dotenv()
API_KEY = os.getenv("ELEVENLABS_API_KEY")
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
YTDLP_PATH = r"C:\Python312\Scripts\yt-dlp.EXE"

TEMP_DIR = "temp_lustre"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs("output", exist_ok=True)

def get_audio_duration(file_path):
    cmd = [FFMPEG_PATH, "-i", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in res.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
    return 10.0

def generate_voice(text, out_path, voice_id="JBFqnCBsd6RMkjVDRZzb"):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        print(f"Áudio já existente: {out_path}")
        return out_path
    
    print(f"Sintetizando narração: {out_path} ({len(text)} chars)...")
    client = ElevenLabs(api_key=API_KEY)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.2, use_speaker_boost=True)
    )
    with open(out_path, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)
    return out_path

def download_full_album_audio(url, out_path):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000000:
        print(f"Áudio completo já existente: {out_path}")
        return out_path
    
    print(f"Baixando áudio completo do álbum via yt-dlp: {url} -> {out_path}...")
    cmd = [
        YTDLP_PATH,
        "--ffmpeg-location", r"C:\ffmpeg\bin",
        "-f", "bestaudio/best",
        "-x", "--audio-format", "mp3",
        "--audio-quality", "192k",
        "-o", out_path,
        "--force-overwrites",
        url
    ]
    subprocess.run(cmd, check=True)
    return out_path

def cut_local_sample(source_file, start_sec, duration_sec, out_path):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        print(f"Sample já existente: {out_path}")
        return out_path
    
    print(f"Cortando sample local: {start_sec}s (+{duration_sec}s) -> {out_path}")
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", str(start_sec),
        "-i", source_file,
        "-t", str(duration_sec),
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_path
    ]
    subprocess.run(cmd, check=True)
    return out_path

def create_vertical_slide(fg_path, out_path, header="ONE-MAN BAND SPOTLIGHT", subheader="NACHTZEIT - ALL INSTRUMENTS & SYNTHS", now_playing=None, is_intro=False, is_outro=False):
    W, H = 1080, 1920
    fg = Image.open(fg_path).convert("RGB")
    
    # Fundo vertical desfocado e escurecido
    bg = fg.copy().resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=55))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.58)
    
    # Imagem central
    target_size = 940
    fg_resized = fg.resize((target_size, target_size), Image.Resampling.LANCZOS)
    pos_x = (W - target_size) // 2
    pos_y = (H - target_size) // 2 - 35
    bg.paste(fg_resized, (pos_x, pos_y))
    
    draw = ImageDraw.Draw(bg)
    draw.rectangle([pos_x, pos_y, pos_x + target_size, pos_y + target_size], outline=(120, 120, 120), width=3)
    
    try:
        font_header = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 28)
        font_band = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 46)
        font_album = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 32)
        font_now_single = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
        font_now_label = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 26)
        font_now_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 32)
    except Exception:
        font_header = font_sub = font_band = font_album = font_now_single = font_now_label = font_now_title = ImageFont.load_default()

    # Header Badge
    badge_w, badge_h = 760, 80
    badge_x = (W - badge_w) // 2
    badge_y = 160
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=20, fill=(15, 15, 15), outline=(90, 90, 90), width=2)
    draw.text((W // 2, badge_y + 40), header, font=font_header, fill=(240, 240, 240), anchor="mm")
    draw.text((W // 2, badge_y + 120), subheader, font=font_sub, fill=(190, 190, 190), anchor="mm")
    
    # Rodapé
    footer_y = pos_y + target_size + 50
    if is_intro:
        box_w, box_h = 860, 125
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=22, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
        draw.text((W // 2, footer_y + 42), "LUSTRE", font=font_band, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, footer_y + 88), "A GLIMPSE OF GLORY (2009)", font=font_album, fill=(200, 200, 200), anchor="mm")
    elif now_playing:
        full_text = f"NOW PLAYING: {now_playing.upper()}"
        bbox = draw.textbbox((0, 0), full_text, font=font_now_single)
        text_width = bbox[2] - bbox[0]
        
        if text_width > 800 or len(now_playing) > 28:
            box_w, box_h = 880, 120
            bx = (W - box_w) // 2
            draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
            draw.text((W // 2, footer_y + 36), "NOW PLAYING", font=font_now_label, fill=(190, 190, 190), anchor="mm")
            t_bbox = draw.textbbox((0, 0), now_playing.upper(), font=font_now_title)
            if (t_bbox[2] - t_bbox[0]) > 830:
                font_now_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 26)
            draw.text((W // 2, footer_y + 80), now_playing.upper(), font=font_now_title, fill=(255, 255, 255), anchor="mm")
        else:
            box_w, box_h = 860, 95
            bx = (W - box_w) // 2
            draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
            draw.text((W // 2, footer_y + 48), full_text, font=font_now_single, fill=(255, 255, 255), anchor="mm")
    elif is_outro:
        box_w, box_h = 860, 95
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(120, 120, 120), width=2)
        draw.text((W // 2, footer_y + 48), "SWEDISH AMBIENT BLACK METAL • 2008 - PRESENT", font=font_now_single, fill=(220, 220, 220), anchor="mm")

    bg.save(out_path, quality=95)
    return out_path

def build_perfect_ducked_audio(voice_file, music_file, out_file, solo_duration=10.0):
    t_voice = get_audio_duration(voice_file)
    t_up_end = t_voice + 1.2
    t_high_end = t_up_end + solo_duration
    t_down_end = t_high_end + 1.5
    t_fade_end = t_down_end + 1.5
    total_dur = t_fade_end

    vol_expr = (
        f"if(lt(t, {t_voice:.2f}), 0.08, "
        f"if(lt(t, {t_up_end:.2f}), 0.08 + (t - {t_voice:.2f}) * 0.533, "
        f"if(lt(t, {t_high_end:.2f}), 0.72, "
        f"if(lt(t, {t_down_end:.2f}), 0.72 - (t - {t_high_end:.2f}) * 0.427, "
        f"if(lt(t, {t_fade_end:.2f}), 0.08 * (1 - (t - {t_down_end:.2f}) / 1.5), 0.0)))))"
    )

    pad_needed = total_dur - t_voice
    filter_complex = (
        f"[0:a]volume=1.35,apad=pad_dur={pad_needed:.2f}[narr];"
        f"[1:a]atrim=0:{total_dur:.2f},volume='{vol_expr}':eval=frame,afade=t=in:ss=0:d=1.0,apad=pad_dur=2.0[mus];"
        f"[narr][mus]amix=inputs=2:duration=first:normalize=0[aout]"
    )

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", voice_file,
        "-i", music_file,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-t", str(total_dur),
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_file
    ]
    subprocess.run(cmd, check=True)
    return out_file, total_dur

def build_outro_audio(voice_file, ambient_music_file, out_file):
    t_voice = get_audio_duration(voice_file)
    total_dur = t_voice + 1.5

    filter_complex = (
        f"[0:a]volume=1.35,apad=pad_dur=1.5[narr];"
        f"[1:a]atrim=0:{total_dur:.2f},volume=0.08,afade=t=in:ss=0:d=1.5,afade=t=out:st={total_dur-1.5:.2f}:d=1.5[mus];"
        f"[narr][mus]amix=inputs=2:duration=first:normalize=0[aout]"
    )

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", voice_file,
        "-i", ambient_music_file,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-t", str(total_dur),
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_file
    ]
    subprocess.run(cmd, check=True)
    return out_file, total_dur

def run():
    print("\n=======================================================")
    print("PRODUZINDO EPISÓDIO #6: LUSTRE - A GLIMPSE OF GLORY")
    print("=======================================================")

    full_album_url = "https://www.youtube.com/watch?v=Z8dZo62TfPQ"
    cover = "assets/lustre/album_cover_square.jpg"

    # 1. Download de áudio e corte de amostras
    print("\n--- Processando Áudio Completo e Trechos Musicais ---")
    full_audio_file = f"{TEMP_DIR}/full_album.mp3"
    download_full_album_audio(full_album_url, full_audio_file)
    s1 = cut_local_sample(full_audio_file, 80, 60, f"{TEMP_DIR}/sample1_mighty_sight.mp3")
    s2 = cut_local_sample(full_audio_file, 1020, 60, f"{TEMP_DIR}/sample2_lunar_light.mp3")
    s3 = cut_local_sample(full_audio_file, 1680, 60, f"{TEMP_DIR}/sample3_amongst_trees.mp3")
    s_amb = cut_local_sample(full_audio_file, 2040, 50, f"{TEMP_DIR}/sample_ambient.mp3")

    # 2. Narração ElevenLabs
    print("\n--- Gerando Narração ElevenLabs ---")
    v_intro = generate_voice(
        "Founded in 2008 in Östersund, Sweden, Lustre forged a mesmerizing union between atmospheric black metal and hypnotic ambient keyboards.",
        f"{TEMP_DIR}/intro.mp3"
    )
    v_t1 = generate_voice(
        "Behind every cosmic synthesizer and mournful guitar pulse was one solitary artist: Nachtzeit. In 2009, he unveiled his debut masterpiece, A Glimpse of Glory. Here is 'This Mighty Sight'.",
        f"{TEMP_DIR}/track1.mp3"
    )
    v_t2 = generate_voice(
        "With 'Lunar Light', glacial synth melodies float effortlessly above slow, rhythmic distortions, transporting the listener into starlit Swedish skies.",
        f"{TEMP_DIR}/track2.mp3"
    )
    v_t3 = generate_voice(
        "'Amongst the Trees' deepens this hypnotic trance, stripping music down to pure emotional texture and transcendent solitude.",
        f"{TEMP_DIR}/track3.mp3"
    )
    v_outro = generate_voice(
        "Nachtzeit crafted a timeless sanctuary of celestial calm, defining ambient black metal for over a decade. Experience the glory of isolation.",
        f"{TEMP_DIR}/outro.mp3"
    )

    # 3. Gerando Slides Verticais
    print("\n--- Gerando Slides Verticais ---")
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_intro.jpg", is_intro=True)
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_track1.jpg", header="A GLIMPSE OF GLORY", subheader="LUSTRE (2009)", now_playing="This Mighty Sight")
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_track2.jpg", header="A GLIMPSE OF GLORY", subheader="LUSTRE (2009)", now_playing="Lunar Light")
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_track3.jpg", header="A GLIMPSE OF GLORY", subheader="LUSTRE (2009)", now_playing="Amongst the Trees")
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_outro.jpg", header="ONE-MAN BAND SPOTLIGHT", subheader="LUSTRE • NACHTZEIT", is_outro=True)

    # 4. Mixagem com Ducking Perfeito
    print("\n--- Mixando Áudio com Ducking Perfeito ---")
    intro_dur = get_audio_duration(v_intro) + 0.3
    intro_audio = f"{TEMP_DIR}/intro_padded.mp3"
    subprocess.run([
        FFMPEG_PATH, "-y", "-i", v_intro,
        "-af", "volume=1.35,apad=pad_dur=0.3",
        "-c:a", "libmp3lame", "-b:a", "192k",
        intro_audio
    ], check=True)

    t1_audio, t1_dur = build_perfect_ducked_audio(v_t1, s1, f"{TEMP_DIR}/t1.mp3", solo_duration=10.0)
    t2_audio, t2_dur = build_perfect_ducked_audio(v_t2, s2, f"{TEMP_DIR}/t2.mp3", solo_duration=10.0)
    t3_audio, t3_dur = build_perfect_ducked_audio(v_t3, s3, f"{TEMP_DIR}/t3.mp3", solo_duration=10.0)
    outro_audio, outro_dur = build_outro_audio(v_outro, s_amb, f"{TEMP_DIR}/outro_ducked.mp3")

    SEGMENTS = [
        {"img": f"{TEMP_DIR}/slide_intro.jpg", "audio": intro_audio, "dur": intro_dur},
        {"img": f"{TEMP_DIR}/slide_track1.jpg", "audio": t1_audio, "dur": t1_dur},
        {"img": f"{TEMP_DIR}/slide_track2.jpg", "audio": t2_audio, "dur": t2_dur},
        {"img": f"{TEMP_DIR}/slide_track3.jpg", "audio": t3_audio, "dur": t3_dur},
        {"img": f"{TEMP_DIR}/slide_outro.jpg", "audio": outro_audio, "dur": outro_dur},
    ]

    # 5. Renderização de Vídeo
    print("\n--- Renderizando Segmentos em Vídeo ---")
    clip_list_file = f"{TEMP_DIR}/clips.txt"
    clip_files = []

    for idx, seg in enumerate(SEGMENTS):
        clip_path = f"{TEMP_DIR}/clip_{idx:02d}.mp4"
        dur = seg["dur"]
        cmd = [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-i", seg["img"],
            "-i", seg["audio"],
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(dur),
            clip_path
        ]
        print(f"Renderizando segmento {idx+1}/{len(SEGMENTS)} ({dur:.1f}s)...")
        subprocess.run(cmd, check=True)
        clip_files.append(clip_path)

    with open(clip_list_file, "w", encoding="utf-8") as f:
        for c in clip_files:
            abs_c = os.path.abspath(c).replace("\\", "/")
            f.write(f"file '{abs_c}'\n")

    final_output = "output/06_Lustre_Shorts_9x16.mp4"
    print(f"\nConcatenando todos os clipes em: {final_output}")
    cmd_concat = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", clip_list_file,
        "-c", "copy",
        final_output
    ]
    subprocess.run(cmd_concat, check=True)

    # 6. Salvar Metadados do Post
    post_info_file = "output/06_Lustre_post_info.txt"
    post_content = f"""=== TÍTULO (Copiar e colar) ===
#6 - Lustre | One-Man Band Spotlight #Shorts


=== DESCRIÇÃO (Copiar e colar) ===
Founded in 2008 in Östersund, Sweden, Lustre pioneered a unique realm where atmospheric black metal merges seamlessly with celestial ambient soundscapes.

Behind every synth layer, guitar melody, and hypnotic drum loop was Nachtzeit (Henrik Sunding). Working in solitude, he composed and produced his landmark 2009 debut album "A Glimpse of Glory".

Nachtzeit's transcendent minimalism and starlit Nordic sorrow remain a defining monument in ambient black metal.

🎧 Featured tracks in this video:
01. This Mighty Sight
02. Lunar Light
03. Amongst the Trees

💿 Listen to the full album on YouTube:
{full_album_url}

Subscribe for more retrospective spotlights on iconic One-Man Bands!

#shorts #blackmetal #atmosphericblackmetal #ambientblackmetal #onemanband #lustre #nachtzeit #aglimpseofglory #swedishblackmetal #dungeonsynth #metal #undergroundmetal


=== TIKTOK (Legenda curta) ===
#6 - Lustre | One-Man Band Spotlight 🇸🇪 Nachtzeit recorded every instrument alone on "A Glimpse of Glory" (2009).

Full Album: {full_album_url}

#blackmetal #atmosphericblackmetal #ambientblackmetal #onemanband #lustre #nachtzeit #metalhead #undergroundmetal #shorts
"""
    with open(post_info_file, "w", encoding="utf-8") as f:
        f.write(post_content)

    total_sec = sum(s["dur"] for s in SEGMENTS)
    print(f"\n=======================================================")
    print(f"SUCESSO! EPISÓDIO #6 GERADO EM: {final_output}")
    print(f"Metadados salvos em: {post_info_file}")
    print(f"Duração Total: {int(total_sec // 60)}m {int(total_sec % 60)}s ({total_sec:.1f} segundos)")
    print(f"Tamanho: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"=======================================================\n")

if __name__ == "__main__":
    run()
