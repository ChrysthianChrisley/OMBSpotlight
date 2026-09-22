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

TEMP_DIR = "temp_decalius"
OUTPUT_DIR = "output"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


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


def download_section_audio(url, section_str, out_path):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 50000:
        print(f"Trecho de áudio já existente: {out_path}")
        return out_path
    
    print(f"Baixando trecho via yt-dlp: {url} ({section_str}) -> {out_path}...")
    cmd = [
        YTDLP_PATH,
        "--ffmpeg-location", r"C:\ffmpeg\bin",
        "--download-sections", f"*{section_str}",
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


def resample_and_cut(source_file, start_offset, duration_sec, out_path):
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", str(start_offset),
        "-i", source_file,
        "-t", str(duration_sec),
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_path
    ]
    subprocess.run(cmd, check=True)
    return out_path


def create_vertical_slide(fg_path, out_path, header="ONE-MAN BAND SPOTLIGHT", subheader="BRAULIO AVELAR - 100% RECORDED SOLO", now_playing=None, album_label=None, is_intro=False, is_outro=False):
    W, H = 1080, 1920
    fg = Image.open(fg_path).convert("RGB")
    
    # Fundo vertical desfocado e escurecido
    bg = fg.copy().resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=55))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.55)
    
    # Imagem central perfeitamente quadrada
    target_size = 940
    fg_resized = fg.resize((target_size, target_size), Image.Resampling.LANCZOS)
    pos_x = (W - target_size) // 2
    pos_y = (H - target_size) // 2 - 35
    bg.paste(fg_resized, (pos_x, pos_y))
    
    draw = ImageDraw.Draw(bg)
    draw.rectangle([pos_x, pos_y, pos_x + target_size, pos_y + target_size], outline=(140, 140, 140), width=3)
    
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
    badge_w, badge_h = 780, 80
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
        draw.text((W // 2, footer_y + 42), "DECALIUS", font=font_band, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, footer_y + 88), "DEHUMANIZING LONELINESS (2023)", font=font_album, fill=(200, 200, 200), anchor="mm")
    elif now_playing:
        box_w, box_h = 880, 120
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
        draw.text((W // 2, footer_y + 36), "NOW PLAYING", font=font_now_label, fill=(190, 190, 190), anchor="mm")
        
        display_title = now_playing.upper()
        t_bbox = draw.textbbox((0, 0), display_title, font=font_now_title)
        if (t_bbox[2] - t_bbox[0]) > 830:
            font_title_fit = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 26)
        else:
            font_title_fit = font_now_title
            
        draw.text((W // 2, footer_y + 80), display_title, font=font_title_fit, fill=(255, 255, 255), anchor="mm")
    elif is_outro:
        box_w, box_h = 860, 95
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(120, 120, 120), width=2)
        draw.text((W // 2, footer_y + 48), "DEPRESSIVE BLACK METAL • SEATTLE, USA", font=font_now_single, fill=(220, 220, 220), anchor="mm")

    bg.save(out_path, quality=95)
    return out_path


def build_ducked_audio(voice_file, music_file, out_file, solo_duration=9.0):
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
    total_dur = t_voice + 2.0

    filter_complex = (
        f"[0:a]volume=1.35,apad=pad_dur=2.0[narr];"
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


def combine_two_voices(v1, v2, pause_sec, out_path):
    filter_complex = (
        f"[0:a][1:a]concat=n=2:v=0:a=1[aout]"
    )
    # Criar silêncio intermediário
    silence = f"{TEMP_DIR}/silence_{pause_sec}s.mp3"
    subprocess.run([
        FFMPEG_PATH, "-y",
        "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
        "-t", str(pause_sec),
        "-c:a", "libmp3lame", "-b:a", "192k",
        silence
    ], check=True)
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", v1,
        "-i", silence,
        "-i", v2,
        "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[aout]",
        "-map", "[aout]",
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_path
    ]
    subprocess.run(cmd, check=True)
    return out_path


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
    print("PRODUZINDO EPISÓDIO #18: DECALIUS - SPOTLIGHT SHORTS")
    print("=======================================================")

    url_dehumanizing = "https://www.youtube.com/watch?v=AKn-DKsdwiM"
    url_isolated = "https://www.youtube.com/watch?v=b0uYE8cfEI4"
    url_hated = "https://www.youtube.com/watch?v=WXqXQdBqHIk"

    cover_dehumanizing = "temp_decalius/square_dehumanizing.jpg"
    cover_isolated = "temp_decalius/clean_cover_isolated.jpg"
    cover_hated = "temp_decalius/square_hated.jpg"

    # 1. Download de Áudio dos 4 Trechos
    print("\n--- 1. Baixando Trechos Musicais Específicos via yt-dlp ---")
    raw1 = download_section_audio(url_dehumanizing, "2247-2315", f"{TEMP_DIR}/raw_excluded.mp3")
    raw2 = download_section_audio(url_dehumanizing, "2627-2690", f"{TEMP_DIR}/raw_miserable.mp3")
    raw3 = download_section_audio(url_isolated, "3427-3485", f"{TEMP_DIR}/raw_isolated.mp3")
    raw4 = download_section_audio(url_hated, "349-410", f"{TEMP_DIR}/raw_unfair.mp3")

    # Resample e corte limpo (garantindo 48kHz stereo)
    s1 = resample_and_cut(raw1, 0, 55, f"{TEMP_DIR}/music_excluded.mp3")
    s2 = resample_and_cut(raw2, 0, 45, f"{TEMP_DIR}/music_miserable.mp3")
    s3 = resample_and_cut(raw3, 0, 45, f"{TEMP_DIR}/music_isolated.mp3")
    s4 = resample_and_cut(raw4, 0, 45, f"{TEMP_DIR}/music_unfair.mp3")
    s_amb = resample_and_cut(raw1, 0, 30, f"{TEMP_DIR}/music_ambient.mp3")

    # 2. Narração Consistente (Edge-TTS ChristopherNeural em 48kHz)
    print("\n--- 2. Gerando Narração em Inglês ---")
    v_intro = generate_voice(
        "Originating from Seattle, Decalius has surged as one of the most hypnotic and emotionally devastating forces in modern Depressive Black Metal, created entirely solo by visionary Braulio Avelar Rodriguez.",
        f"{TEMP_DIR}/voice_intro.mp3"
    )
    v_t1 = generate_voice(
        "First up is the iconic Excluded from Humanity. Driven by slow-burning, melancholic guitar leads and a repetitive, trance-inducing groove, this masterpiece transforms raw existential despair into hauntingly beautiful black metal.",
        f"{TEMP_DIR}/voice_track1.mp3"
    )
    v_t2 = generate_voice(
        "Next is his most streamed track, A Miserable Life. Featuring piercing, agonized vocals and a somber, weeping bassline, it strips away all pretension for pure, unfiltered emotional catharsis.",
        f"{TEMP_DIR}/voice_track2.mp3"
    )
    v_t3 = generate_voice(
        "Stepping back into his seminal 2021 release, here is the crushing title track Isolated from Life. With suffocating lo-fi grit and mournful chord progressions, it captures total solitary desolation.",
        f"{TEMP_DIR}/voice_track3.mp3"
    )
    v_t4 = generate_voice(
        "That same bleak elegance fuels his acclaimed EP Hated by Life Itself, featuring the deeply poignant and melodic track Unfair.",
        f"{TEMP_DIR}/voice_track4.mp3"
    )
    v_outro = generate_voice(
        "Braulio Avelar proves that a solitary artist can channel immense emotional weight into unforgettable art. Experience the complete Decalius discography right here on the One Man Bands channel.",
        f"{TEMP_DIR}/voice_outro.mp3"
    )

    # Combinar v_intro + v_t1 para o primeiro bloco
    v_block1 = combine_two_voices(v_intro, v_t1, 0.4, f"{TEMP_DIR}/voice_block1.mp3")

    # 3. Mixagem de Áudio com Ducking Preciso
    print("\n--- 3. Mixando Áudio com Curvas de Ducking ---")
    # Bloco 1: Intro + Excluded from Humanity (solo de 9.0s)
    a_b1, dur_b1 = build_ducked_audio(v_block1, s1, f"{TEMP_DIR}/mixed_b1.mp3", solo_duration=9.0)
    # Bloco 2: A Miserable Life (solo de 8.0s)
    a_b2, dur_b2 = build_ducked_audio(v_t2, s2, f"{TEMP_DIR}/mixed_b2.mp3", solo_duration=8.0)
    # Bloco 3: Isolated from Life (solo de 8.0s)
    a_b3, dur_b3 = build_ducked_audio(v_t3, s3, f"{TEMP_DIR}/mixed_b3.mp3", solo_duration=8.0)
    # Bloco 4: Unfair... (solo de 8.0s)
    a_b4, dur_b4 = build_ducked_audio(v_t4, s4, f"{TEMP_DIR}/mixed_b4.mp3", solo_duration=8.0)
    # Bloco 5: Outro
    a_b5, dur_b5 = build_outro_audio(v_outro, s_amb, f"{TEMP_DIR}/mixed_b5.mp3")

    # 4. Gerando Slides Verticais
    print("\n--- 4. Criando Slides Visuais em 1080x1920 ---")
    slide_intro = create_vertical_slide(cover_dehumanizing, f"{TEMP_DIR}/slide_intro.jpg", is_intro=True)
    slide_excluded = create_vertical_slide(cover_dehumanizing, f"{TEMP_DIR}/slide_excluded.jpg", now_playing="Excluded from Humanity")
    slide_miserable = create_vertical_slide(cover_dehumanizing, f"{TEMP_DIR}/slide_miserable.jpg", now_playing="A Miserable Life...")
    slide_isolated = create_vertical_slide(cover_isolated, f"{TEMP_DIR}/slide_isolated.jpg", now_playing="Isolated from Life")
    slide_unfair = create_vertical_slide(cover_hated, f"{TEMP_DIR}/slide_unfair.jpg", now_playing="Unfair...")
    slide_outro = create_vertical_slide(cover_dehumanizing, f"{TEMP_DIR}/slide_outro.jpg", is_outro=True)

    # Para o Bloco 1, dividir visualmente entre Intro (duração de v_intro) e Excluded
    t_v_intro = get_audio_duration(v_intro)
    dur_b1_sub1 = t_v_intro + 0.2
    dur_b1_sub2 = dur_b1 - dur_b1_sub1

    # Cortar áudio do bloco 1 nas duas partes
    a_b1_part1 = f"{TEMP_DIR}/a_b1_part1.mp3"
    a_b1_part2 = f"{TEMP_DIR}/a_b1_part2.mp3"
    resample_and_cut(a_b1, 0, dur_b1_sub1, a_b1_part1)
    resample_and_cut(a_b1, dur_b1_sub1, dur_b1_sub2, a_b1_part2)

    CLIPS = [
        {"img": slide_intro, "audio": a_b1_part1, "dur": dur_b1_sub1, "name": "Intro (Braulio Avelar)"},
        {"img": slide_excluded, "audio": a_b1_part2, "dur": dur_b1_sub2, "name": "Track 1: Excluded from Humanity"},
        {"img": slide_miserable, "audio": a_b2, "dur": dur_b2, "name": "Track 2: A Miserable Life..."},
        {"img": slide_isolated, "audio": a_b3, "dur": dur_b3, "name": "Track 3: Isolated from Life"},
        {"img": slide_unfair, "audio": a_b4, "dur": dur_b4, "name": "Track 4: Unfair..."},
        {"img": slide_outro, "audio": a_b5, "dur": dur_b5, "name": "Outro"}
    ]

    # 5. Renderização de Vídeo com Áudio Unificado
    print("\n--- 5. Renderizando Segmentos em Vídeo (1080x1920 @ 60fps) ---")
    clip_list_file = f"{TEMP_DIR}/clips.txt"
    clip_files = []

    for idx, seg in enumerate(CLIPS):
        clip_path = f"{TEMP_DIR}/clip_{idx:02d}.mp4"
        dur = seg["dur"]
        cmd = [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-i", seg["img"],
            "-i", seg["audio"],
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            "-r", "60",
            "-ar", "48000", "-ac", "2",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(dur),
            clip_path
        ]
        print(f"Renderizando segmento {idx+1}/{len(CLIPS)}: {seg['name']} ({dur:.1f}s)...")
        subprocess.run(cmd, check=True)
        clip_files.append(clip_path)

    with open(clip_list_file, "w", encoding="utf-8") as f:
        for c in clip_files:
            abs_c = os.path.abspath(c).replace("\\", "/")
            f.write(f"file '{abs_c}'\n")

    final_output = "output/18_Decalius_Shorts_9x16.mp4"
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
    post_info_file = "output/18_Decalius_post_info.txt"
    title_text = "#18 - Decalius | One-Man Band Spotlight #Shorts"
    post_content = f"""=== TÍTULO (Copiar e colar) ===
{title_text}


=== DESCRIÇÃO (Copiar e colar) ===
Originating from Seattle, Decalius has surged as one of the most hypnotic, poignant, and emotionally devastating forces in modern Depressive Black Metal (DSBM).

Behind every note is sole visionary Braulio Avelar Rodriguez. Working in complete solitude, Rodriguez writes, records, performs, and mixes every instrument and agonizing vocal line one hundred percent alone.

Featured tracks in this spotlight:
01. Excluded from Humanity (from 'Dehumanizing Loneliness')
02. A Miserable Life... (from 'Dehumanizing Loneliness')
03. Isolated from Life (from 'Isolated from Life')
04. Unfair... (from 'Hated by Life Itself' [EP])

🎧 Listen to the full albums on the One Man Bands channel:
- Dehumanizing Loneliness: {url_dehumanizing}
- Isolated from Life (Remaster): {url_isolated}
- Hated by Life Itself [EP]: {url_hated}

Subscribe to One Man Bands for more deep-dive spotlights into legendary solitary metal masterminds!

#shorts #blackmetal #dsbm #decalius #depressiveblackmetal #atmosphericblackmetal #onemanband #undergroundmetal #metalhead #blackgaze


=== TIKTOK (Legenda curta) ===
#18 - Decalius | One-Man Band Spotlight 🇺🇸 Braulio Avelar recorded 100% solo across his discography.

Full Albums: {url_dehumanizing}

#dsbm #blackmetal #decalius #depressiveblackmetal #onemanband #metal #atmosphericblackmetal #shorts
"""
    with open(post_info_file, "w", encoding="utf-8") as f:
        f.write(post_content)

    # 7. Adicionar à fila de pendências
    add_to_upload_queue({
        "id": 18,
        "band": "Decalius",
        "file_path": final_output,
        "title": title_text,
        "info_file": post_info_file,
        "status": "pending",
        "video_url": None,
        "tags": ["shorts", "blackmetal", "dsbm", "decalius", "depressiveblackmetal", "atmosphericblackmetal", "onemanband"]
    })

    total_sec = sum(s["dur"] for s in CLIPS)
    print(f"\n=======================================================")
    print(f"🎉 SUCESSO! EPISÓDIO #18 GERADO EM: {final_output}")
    print(f"Metadados salvos em: {post_info_file}")
    print(f"Duração Total: {int(total_sec // 60)}m {int(total_sec % 60)}s ({total_sec:.1f} segundos)")
    print(f"Tamanho: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"=======================================================\n")


if __name__ == "__main__":
    run()
