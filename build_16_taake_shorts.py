import os
import sys
import subprocess
import json
import re

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from PIL import Image, ImageFilter, ImageDraw, ImageFont
import edge_tts
import asyncio

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
YTDLP_PATH = r"C:\Python312\Scripts\yt-dlp.EXE"

TEMP_DIR = "temp_taake"
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

def generate_voice(text, out_path):
    clean_text = re.sub(r'\[.*?\]', '', text).strip()
    raw_path = out_path.replace(".mp3", "_raw.mp3")
    
    print(f"Sintetizando narração via Edge-TTS (ChristopherNeural): {out_path}...")
    communicate = edge_tts.Communicate(clean_text, voice="en-US-ChristopherNeural", rate="-3%", pitch="-2Hz")
    asyncio.run(communicate.save(raw_path))
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", raw_path,
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_path
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(raw_path):
        try:
            os.remove(raw_path)
        except Exception:
            pass
    print(f"✅ Narração salva em 48kHz: {out_path}")
    return out_path

def download_full_album_audio(url, out_path):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000000:
        print(f"Áudio completo já existente: {out_path}")
        return out_path
    
    print(f"Baixando áudio completo via yt-dlp: {url} -> {out_path}...")
    cmd = [
        YTDLP_PATH,
        "--ffmpeg-location", r"C:\ffmpeg\bin",
        "--extractor-args", "youtube:player_client=android,web",
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
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_path
    ]
    subprocess.run(cmd, check=True)
    return out_path

def create_vertical_slide(fg_path, out_path, header="ONE-MAN BAND SPOTLIGHT", subheader="HOEST - ALL INSTRUMENTS, VOCALS & COMPOSITION", now_playing=None, is_intro=False, is_outro=False):
    W, H = 1080, 1920
    fg = Image.open(fg_path).convert("RGB")
    
    # Fundo vertical desfocado e escurecido
    bg = fg.copy().resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=55))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.60)
    
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
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 26)
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
        draw.text((W // 2, footer_y + 42), "TAAKE", font=font_band, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, footer_y + 88), "STRIDENS HUS (2014)", font=font_album, fill=(200, 200, 200), anchor="mm")
    elif now_playing:
        full_text = f"NOW PLAYING: {now_playing.upper()}"
        bbox = draw.textbbox((0, 0), full_text, font=font_now_single)
        text_width = bbox[2] - bbox[0]
        
        if text_width > 800 or len(now_playing) > 26:
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
        draw.text((W // 2, footer_y + 48), "TRUE NORWEGIAN BLACK METAL • BERGEN", font=font_now_single, fill=(220, 220, 220), anchor="mm")

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
        "-ar", "48000",
        "-ac", "2",
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
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_file
    ]
    subprocess.run(cmd, check=True)
    return out_file, total_dur

def add_to_upload_queue(item):
    q_file = "upload_queue.json"
    queue = []
    if os.path.exists(q_file):
        try:
            with open(q_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            queue = []
    queue = [q for q in queue if q.get("title") != item.get("title")]
    queue.append(item)
    queue.sort(key=lambda x: x.get("id", 0))
    with open(q_file, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    print(f"Vídeo adicionado à fila de pendências: {item.get('title')}")

def run():
    print("\n=======================================================")
    print("PRODUZINDO EPISÓDIO #16: TAAKE - STRIDENS HUS")
    print("=======================================================")

    full_album_url = "https://www.youtube.com/watch?v=Fz-iAUUpnp0"
    cover = "assets/taake/album_cover_square.jpg"

    # 1. Download de áudio e corte de amostras
    print("\n--- Processando Áudio Completo e Trechos Musicais ---")
    full_audio_file = f"{TEMP_DIR}/full_album.mp3"
    download_full_album_audio(full_album_url, full_audio_file)
    
    # 1. Gamle Norig (0 - 357): sample at 50s
    # 2. Orm (357 - 760): sample at 400s
    # 3. Det fins en prins (760 - 1248): sample at 810s
    # Ambient outro: Kongsgaard bestaar (1934 - 2269): sample at 1950s
    s1 = cut_local_sample(full_audio_file, 50, 60, f"{TEMP_DIR}/sample1_gamle_norig.mp3")
    s2 = cut_local_sample(full_audio_file, 400, 60, f"{TEMP_DIR}/sample2_orm.mp3")
    s3 = cut_local_sample(full_audio_file, 810, 60, f"{TEMP_DIR}/sample3_prins.mp3")
    s_amb = cut_local_sample(full_audio_file, 1950, 50, f"{TEMP_DIR}/sample_ambient.mp3")

    # 2. Narração Consistente (Edge-TTS ChristopherNeural em 48kHz)
    print("\n--- Gerando Narração Consistente ---")
    v_intro = generate_voice(
        "Founded in 1993 in Bergen, Norway, Taake stands as an uncontested titan of True Norwegian Black Metal, helmed exclusively by visionary mastermind Hoest.",
        f"{TEMP_DIR}/intro.mp3"
    )
    v_t1 = generate_voice(
        "Hoest writes, arranges, and performs every ferocious instrument and raspy vocal decree in complete isolation. In 2014, he released 'Stridens hus'. Here is 'Gamle Norig'.",
        f"{TEMP_DIR}/track1.mp3"
    )
    v_t2 = generate_voice(
        "With 'Orm', blistering cold tremolo picking and intricate rhythmic dynamics forge the unmistakable, razor-sharp Helnorsk Svartmetall signature.",
        f"{TEMP_DIR}/track2.mp3"
    )
    v_t3 = generate_voice(
        "'Det fins en prins' showcases Hoest's legendary songwriting brilliance, blending ferocious Nordic aggression with dark, melodic melancholy.",
        f"{TEMP_DIR}/track3.mp3"
    )
    v_outro = generate_voice(
        "For over three decades, Hoest has defended the pure flame of Norwegian black metal without compromise. Taake remains unstoppable.",
        f"{TEMP_DIR}/outro.mp3"
    )

    # 3. Gerando Slides Verticais
    print("\n--- Gerando Slides Verticais ---")
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_intro.jpg", is_intro=True)
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_track1.jpg", header="STRIDENS HUS", subheader="TAAKE (2014)", now_playing="Gamle Norig")
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_track2.jpg", header="STRIDENS HUS", subheader="TAAKE (2014)", now_playing="Orm")
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_track3.jpg", header="STRIDENS HUS", subheader="TAAKE (2014)", now_playing="Det fins en prins")
    create_vertical_slide(cover, f"{TEMP_DIR}/slide_outro.jpg", header="ONE-MAN BAND SPOTLIGHT", subheader="TAAKE • HOEST", is_outro=True)

    # 4. Mixagem com Ducking Perfeito (48kHz Stereo)
    print("\n--- Mixando Áudio com Ducking Perfeito ---")
    intro_dur = get_audio_duration(v_intro) + 0.3
    intro_audio = f"{TEMP_DIR}/intro_padded.mp3"
    subprocess.run([
        FFMPEG_PATH, "-y", "-i", v_intro,
        "-af", "volume=1.35,apad=pad_dur=0.3",
        "-ar", "48000", "-ac", "2",
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

    # 5. Renderização de Vídeo com Áudio Unificado (48000 Hz, Stereo)
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
            "-ar", "48000", "-ac", "2",
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

    final_output = "output/16_Taake_Shorts_9x16.mp4"
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
    post_info_file = "output/16_Taake_post_info.txt"
    title_text = "#16 - Taake | One-Man Band Spotlight #Shorts"
    post_content = f"""=== TÍTULO (Copiar e colar) ===
{title_text}


=== DESCRIÇÃO (Copiar e colar) ===
Founded in 1993 in Bergen, Norway, Taake stands as one of the most revered and steadfast pillars of True Norwegian Black Metal.

Behind the moniker is solitary mastermind Hoest (Ørjan Stedjeberg). Operating with relentless autonomy, he writes, performs, and records every cold riff, blasting drum tempo, and venomous vocal decree himself, releasing the acclaimed 2014 album "Stridens hus".

🎧 Featured tracks in this video:
01. Gamle Norig
02. Orm
03. Det fins en prins

💿 Listen to the full album on YouTube:
{full_album_url}

Subscribe for more retrospective spotlights on iconic One-Man Bands!

#shorts #blackmetal #norwegianblackmetal #taake #hoest #stridenshus #trueblackmetal #onemanband #metal #undergroundmetal


=== TIKTOK (Legenda curta) ===
#16 - Taake | One-Man Band Spotlight 🇳🇴 Hoest recorded every instrument alone on "Stridens hus" (2014).

Full Album: {full_album_url}

#blackmetal #taake #hoest #onemanband #norwegianblackmetal #metalhead #undergroundmetal #shorts
"""
    with open(post_info_file, "w", encoding="utf-8") as f:
        f.write(post_content)

    # 7. Adicionar à fila de pendências
    add_to_upload_queue({
        "id": 16,
        "band": "Taake",
        "file_path": final_output,
        "title": title_text,
        "info_file": post_info_file,
        "status": "pending",
        "video_url": None,
        "tags": ["shorts", "blackmetal", "norwegianblackmetal", "taake", "hoest", "onemanband"]
    })

    total_sec = sum(s["dur"] for s in SEGMENTS)
    print(f"\n=======================================================")
    print(f"SUCESSO! EPISÓDIO #16 GERADO EM: {final_output}")
    print(f"Metadados salvos em: {post_info_file}")
    print(f"Duração Total: {int(total_sec // 60)}m {int(total_sec % 60)}s ({total_sec:.1f} segundos)")
    print(f"Tamanho: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"=======================================================\n")

if __name__ == "__main__":
    run()
