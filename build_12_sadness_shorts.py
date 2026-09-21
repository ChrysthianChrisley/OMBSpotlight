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

TEMP_DIR = "temp_sadness"
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

def create_vertical_slide(fg_path, out_path, header="ONE-MAN BAND SPOTLIGHT", subheader="DAMIÁN ANTÓN OJEDA • SADNESS", now_playing=None, is_intro=False, is_outro=False):
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
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 26)
        font_band = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 46)
        font_album = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 32)
        font_now_single = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
        font_now_label = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 26)
        font_now_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 32)
    except Exception:
        font_header = font_sub = font_band = font_album = font_now_single = font_now_label = font_now_title = ImageFont.load_default()

    # Header Badge
    badge_w, badge_h = 820, 80
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
        draw.text((W // 2, footer_y + 42), "SADNESS", font=font_band, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, footer_y + 88), "DAMIÁN ANTÓN OJEDA (2014 - PRESENT)", font=font_album, fill=(200, 200, 200), anchor="mm")
    elif now_playing:
        full_text = f"NOW PLAYING: {now_playing.upper()}"
        bbox = draw.textbbox((0, 0), full_text, font=font_now_single)
        text_width = bbox[2] - bbox[0]
        
        if text_width > 800 or len(now_playing) > 25:
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
        draw.text((W // 2, footer_y + 48), "ATMOSPHERIC BLACK METAL • BLACKGAZE", font=font_now_single, fill=(220, 220, 220), anchor="mm")

    bg.save(out_path, quality=95)
    return out_path

def build_perfect_ducked_audio(voice_file, music_file, out_file, solo_duration=12.0):
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
    print("PRODUZINDO EPISÓDIO #12: SADNESS (SPECIAL EXTENDED EDITION)")
    print("=======================================================")

    url_somewhere = "https://www.youtube.com/watch?v=jAUzyQDyFcg"
    url_ep = "https://www.youtube.com/watch?v=nl0IaMvXr8s"
    url_oldsongs = "https://www.youtube.com/watch?v=LqLppMB0saY"

    cover_somewhere = "assets/sadness/cover_somewhere_hires.jpg"
    cover_ep = "assets/sadness/cover_ep_hires.jpg"
    cover_oldsongs = "assets/sadness/cover_oldsongs_hires.jpg"

    # 1. Downloads de Áudio
    print("\n--- Baixando Áudios Originais ---")
    audio_somewhere = f"{TEMP_DIR}/full_somewhere.mp3"
    audio_ep = f"{TEMP_DIR}/full_ep.mp3"
    audio_oldsongs = f"{TEMP_DIR}/full_oldsongs.mp3"

    download_full_album_audio(url_somewhere, audio_somewhere)
    download_full_album_audio(url_ep, audio_ep)
    download_full_album_audio(url_oldsongs, audio_oldsongs)

    # 2. Corte de Amostras
    # Track 1: Kiss in October (from Somewhere: 1080 - 1885) -> sample at 1180s
    # Track 2: Her (from Somewhere: 1885 - 2654) -> sample at 1980s
    # Track 3: I Can't Say Goodbye (from EP: 1239 - 2221) -> sample at 1350s
    # Track 4: In January (from Old Songs: 5494 - 6161) -> sample at 5550s (01:32:30)
    # Ambient Outro: from Era La Tuya (start 0 to 80s)
    s1 = cut_local_sample(audio_somewhere, 1180, 60, f"{TEMP_DIR}/sample1_kiss_in_october.mp3")
    s2 = cut_local_sample(audio_somewhere, 1980, 60, f"{TEMP_DIR}/sample2_her.mp3")
    s3 = cut_local_sample(audio_ep, 1350, 60, f"{TEMP_DIR}/sample3_cant_say_goodbye.mp3")
    s4 = cut_local_sample(audio_oldsongs, 5550, 60, f"{TEMP_DIR}/sample4_in_january.mp3")
    s_amb = cut_local_sample(audio_somewhere, 40, 50, f"{TEMP_DIR}/sample_ambient.mp3")

    # 3. Narração Consistente e Roteiro Especial
    print("\n--- Gerando Narrações em 48kHz ---")
    v_intro = generate_voice(
        "Founded in 2014, Sadness is the crown jewel of modern atmospheric black metal and emotional blackgaze, crafted in total solitude by Mexican-American mastermind Damián Antón Ojeda.",
        f"{TEMP_DIR}/intro.mp3"
    )
    v_t1 = generate_voice(
        "With his 2014 breakthrough opus 'Somewhere Along Our Memory', Damián captured pure nostalgia and longing. Here is the iconic masterpiece 'Kiss in October'.",
        f"{TEMP_DIR}/track1.mp3"
    )
    v_t2 = generate_voice(
        "Beyond Sadness, Damián is legendary for his vast creative cosmos, including enigmatic conlang black metal project Trhä, DSBM entity Left Alone, and Life. Here is the breathtaking 'Her'.",
        f"{TEMP_DIR}/track2.mp3"
    )
    v_t3 = generate_voice(
        "In 2021, the enigmatic EP 'Underscores' revealed ethereal shoegaze textures colliding with soaring post-black metal shrieks. Here is 'I Can't Say Goodbye'.",
        f"{TEMP_DIR}/track3.mp3"
    )
    v_t4 = generate_voice(
        "From the cherished archival compilation 'old songs 2014', 'In January' radiates lo-fi winter melancholy and fragile warmth recorded at the very dawn of Sadness.",
        f"{TEMP_DIR}/track4.mp3"
    )
    v_outro = generate_voice(
        "Writing, recording, and mixing dozens of legendary albums entirely on his own, Damián Antón Ojeda remains an unmatched force of solitary emotion.",
        f"{TEMP_DIR}/outro.mp3"
    )

    # 4. Gerando Slides Verticais
    print("\n--- Gerando Slides Verticais ---")
    create_vertical_slide(cover_somewhere, f"{TEMP_DIR}/slide_intro.jpg", is_intro=True)
    create_vertical_slide(cover_somewhere, f"{TEMP_DIR}/slide_track1.jpg", header="SOMEWHERE ALONG OUR MEMORY", subheader="SADNESS (2014)", now_playing="Kiss in October")
    create_vertical_slide(cover_somewhere, f"{TEMP_DIR}/slide_track2.jpg", header="TRHÄ • LEFT ALONE... • LIFE", subheader="THE MULTI-PROJECT VISION OF DAMIÁN", now_playing="Her")
    create_vertical_slide(cover_ep, f"{TEMP_DIR}/slide_track3.jpg", header="_____ (EP)", subheader="SADNESS (2021)", now_playing="I Can't Say Goodbye")
    create_vertical_slide(cover_oldsongs, f"{TEMP_DIR}/slide_track4.jpg", header="OLD SONGS 2014", subheader="SADNESS (2022)", now_playing="In January")
    create_vertical_slide(cover_somewhere, f"{TEMP_DIR}/slide_outro.jpg", header="ONE-MAN BAND SPOTLIGHT", subheader="SADNESS • DAMIÁN ANTÓN OJEDA", is_outro=True)

    # 5. Mixagem com Ducking Perfeito (Solo duration = 12s para experiência cinematográfica)
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

    t1_audio, t1_dur = build_perfect_ducked_audio(v_t1, s1, f"{TEMP_DIR}/t1.mp3", solo_duration=12.0)
    t2_audio, t2_dur = build_perfect_ducked_audio(v_t2, s2, f"{TEMP_DIR}/t2.mp3", solo_duration=12.0)
    t3_audio, t3_dur = build_perfect_ducked_audio(v_t3, s3, f"{TEMP_DIR}/t3.mp3", solo_duration=12.0)
    t4_audio, t4_dur = build_perfect_ducked_audio(v_t4, s4, f"{TEMP_DIR}/t4.mp3", solo_duration=12.0)
    outro_audio, outro_dur = build_outro_audio(v_outro, s_amb, f"{TEMP_DIR}/outro_ducked.mp3")

    SEGMENTS = [
        {"img": f"{TEMP_DIR}/slide_intro.jpg", "audio": intro_audio, "dur": intro_dur},
        {"img": f"{TEMP_DIR}/slide_track1.jpg", "audio": t1_audio, "dur": t1_dur},
        {"img": f"{TEMP_DIR}/slide_track2.jpg", "audio": t2_audio, "dur": t2_dur},
        {"img": f"{TEMP_DIR}/slide_track3.jpg", "audio": t3_audio, "dur": t3_dur},
        {"img": f"{TEMP_DIR}/slide_track4.jpg", "audio": t4_audio, "dur": t4_dur},
        {"img": f"{TEMP_DIR}/slide_outro.jpg", "audio": outro_audio, "dur": outro_dur},
    ]

    # 6. Renderização de Vídeo com Áudio Unificado (48000 Hz Stereo)
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

    final_output = "output/12_Sadness_Shorts_9x16.mp4"
    print(f"\nConcatenando todos os clipes em: {final_output}")
    cmd_concat = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", clip_list_file,
        "-c", "copy",
        final_output
    ]
    subprocess.run(cmd_concat, check=True)

    # 7. Salvar Metadados do Post
    post_info_file = "output/12_Sadness_post_info.txt"
    title_text = "#12 - Sadness | One-Man Band Spotlight #Shorts"
    post_content = f"""=== TÍTULO (Copiar e colar) ===
{title_text}


=== DESCRIÇÃO (Copiar e colar) ===
Founded in 2014, Sadness stands as the crown jewel of atmospheric black metal and blackgaze, crafted in complete solitude by prolific mastermind Damián Antón Ojeda.

Operating under boundless creative independence, Damián writes, performs, records, and mixes every instrument and vocal line himself. In addition to Sadness, he has created an entire legendary musical universe, including conlang black metal project Trhä, DSBM entity Left Alone..., and Life.

This special extended edition explores four of his most iconic songs across his discography.

🎧 Featured tracks in this video:
01. Kiss in October (Somewhere Along Our Memory - 2014)
02. Her (Somewhere Along Our Memory - 2014)
03. I Can't Say Goodbye (_____ - 2021)
04. In January (old songs 2014 - 2022)

💿 Listen to the featured releases on YouTube:
Somewhere Along Our Memory: {url_somewhere}
_____ [EP]: {url_ep}
old songs 2014: {url_oldsongs}

Subscribe for more retrospective spotlights on iconic One-Man Bands!

#shorts #blackmetal #blackgaze #postblackmetal #sadness #damianantonojeda #trha #leftalone #dsbm #shoegaze #atmosphericblackmetal #onemanband #undergroundmetal


=== TIKTOK (Legenda curta) ===
#12 - Sadness | One-Man Band Spotlight 🇺🇸 Damián Antón Ojeda recorded every instrument alone across Sadness, Trhä, and Left Alone.

Full Album: {url_somewhere}

#blackmetal #blackgaze #onemanband #sadness #trha #metalhead #undergroundmetal #shorts
"""
    with open(post_info_file, "w", encoding="utf-8") as f:
        f.write(post_content)

    # 8. Adicionar à fila de pendências
    add_to_upload_queue({
        "id": 12,
        "band": "Sadness",
        "file_path": final_output,
        "title": title_text,
        "info_file": post_info_file,
        "status": "pending",
        "video_url": None,
        "tags": ["shorts", "blackmetal", "blackgaze", "postblackmetal", "sadness", "damianantonojeda", "trha", "onemanband"]
    })

    total_sec = sum(s["dur"] for s in SEGMENTS)
    print(f"\n=======================================================")
    print(f"SUCESSO! EPISÓDIO #12 GERADO EM: {final_output}")
    print(f"Metadados salvos em: {post_info_file}")
    print(f"Duração Total: {int(total_sec // 60)}m {int(total_sec % 60)}s ({total_sec:.1f} segundos)")
    print(f"Tamanho: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"=======================================================\n")

if __name__ == "__main__":
    run()
