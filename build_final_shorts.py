import os
import subprocess
from PIL import Image, ImageFilter, ImageDraw, ImageFont

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
os.makedirs("temp_final", exist_ok=True)
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

def create_vertical_slide(fg_path, out_path, header="ONE-MAN BAND SPOTLIGHT", subheader="SHANE ROUT - ALL INSTRUMENTS & VOCALS", now_playing=None, is_intro=False, is_tribute=False):
    W, H = 1080, 1920
    fg = Image.open(fg_path).convert("RGB")
    
    # 1. Fundo vertical desfocado e escurecido
    bg = fg.copy().resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=55))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.58)
    
    # 2. Imagem central
    target_size = 940
    fg_resized = fg.resize((target_size, target_size), Image.Resampling.LANCZOS)
    pos_x = (W - target_size) // 2
    pos_y = (H - target_size) // 2 - 35
    bg.paste(fg_resized, (pos_x, pos_y))
    
    draw = ImageDraw.Draw(bg)
    border_color = (180, 150, 100) if is_tribute else (120, 120, 120)
    draw.rectangle([pos_x, pos_y, pos_x + target_size, pos_y + target_size], outline=border_color, width=3)
    
    try:
        font_header = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 28)
        font_band = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 46)
        font_album = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 32)
        font_now = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 42)
    except Exception:
        font_header = font_sub = font_band = font_album = font_now = ImageFont.load_default()

    # 3. Topo estilizado (Header Badge)
    badge_w, badge_h = 760, 80
    badge_x = (W - badge_w) // 2
    badge_y = 160
    badge_bg = (25, 20, 15) if is_tribute else (15, 15, 15)
    badge_outline = (140, 110, 60) if is_tribute else (90, 90, 90)
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=20, fill=badge_bg, outline=badge_outline, width=2)
    header_color = (255, 220, 160) if is_tribute else (240, 240, 240)
    draw.text((W // 2, badge_y + 40), header, font=font_header, fill=header_color, anchor="mm")
    
    # Subtítulo topo
    draw.text((W // 2, badge_y + 120), subheader, font=font_sub, fill=(190, 190, 190), anchor="mm")
    
    # 4. Rodapé
    footer_y = pos_y + target_size + 55
    if is_intro:
        # Nome da banda e nome do álbum logo abaixo
        box_w, box_h = 860, 125
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=22, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
        draw.text((W // 2, footer_y + 42), "ABYSSIC HATE", font=font_band, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, footer_y + 88), "SUICIDAL EMOTIONS (2000)", font=font_album, fill=(200, 200, 200), anchor="mm")
    elif now_playing:
        box_w, box_h = 860, 95
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
        draw.text((W // 2, footer_y + 48), f"NOW PLAYING: {now_playing.upper()}", font=font_now, fill=(255, 255, 255), anchor="mm")
    elif is_tribute:
        box_w, box_h = 860, 95
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(20, 18, 15), outline=(120, 100, 60), width=2)
        draw.text((W // 2, footer_y + 48), "REST IN PEACE • 1972 - 2026", font=font_now, fill=(240, 210, 160), anchor="mm")

    bg.save(out_path, quality=95)
    return out_path

def build_perfect_ducked_audio(voice_file, music_file, out_file, solo_duration=10.0):
    """
    Curva de volume solicitada:
    1. Durante a narração (0 -> t_voice): música bem baixinha ao fundo (volume=0.08).
    2. Ao parar a narração: música sobe suavemente para 0.72 em 1.2s.
    3. Toca no volume alto (0.72) por solo_duration segundos.
    4. O volume vai abaixando suavemente (em 2.0s) de volta até o nível que estava antes (0.08).
    5. Permanece em 0.08 por 1.5s e depois faz 'fade to 0' lentamente (2.0s).
    6. Pausa de respiro de 1.0s de silêncio antes do retorno da narração.
    """
    t_voice = get_audio_duration(voice_file)
    
    t_up_end = t_voice + 1.2
    t_high_end = t_up_end + solo_duration
    t_down_end = t_high_end + 2.0
    t_fade_start = t_down_end + 1.5
    t_fade_end = t_fade_start + 2.0
    
    total_dur = t_fade_end + 1.0 # 1.0s de respiro final
    
    vol_expr = (
        f"if(lt(t, {t_voice:.2f}), 0.08, "
        f"if(lt(t, {t_up_end:.2f}), 0.08 + (t - {t_voice:.2f}) * 0.533, "
        f"if(lt(t, {t_high_end:.2f}), 0.72, "
        f"if(lt(t, {t_down_end:.2f}), 0.72 - (t - {t_high_end:.2f}) * 0.32, "
        f"if(lt(t, {t_fade_start:.2f}), 0.08, "
        f"if(lt(t, {t_fade_end:.2f}), 0.08 * (1 - (t - {t_fade_start:.2f}) / 2.0), 0.0))))))"
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

def build_tribute_audio(voice_file, ambient_music_file, out_file):
    """Música tocando com volume baixo durante toda a narração do in memoriam"""
    t_voice = get_audio_duration(voice_file)
    total_dur = t_voice + 3.0
    
    filter_complex = (
        f"[0:a]volume=1.35,apad=pad_dur=3.0[narr];"
        f"[1:a]atrim=0:{total_dur:.2f},volume=0.08,afade=t=in:ss=0:d=2.0,afade=t=out:st={total_dur-2.5:.2f}:d=2.5[mus];"
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

def build_full_video():
    print("\n--- 1. Gerando Slides Verticais 9:16 (1080x1920) ---")
    cover = "assets/suicidal_emotions_blurred.jpg"
    shane = "assets/shane_rout.jpg"
    
    # Slide de abertura com Nome da Banda e Nome do Álbum logo abaixo
    create_vertical_slide(shane, "temp_final/slide_intro.jpg", is_intro=True)
    
    # 3 Faixas distintas
    create_vertical_slide(cover, "temp_final/slide_track1.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Depression")
    create_vertical_slide(cover, "temp_final/slide_track2.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Betrayed")
    create_vertical_slide(cover, "temp_final/slide_track3.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Despondency")
    
    # Slide Tributo
    create_vertical_slide(shane, "temp_final/slide_tribute.jpg", header="IN MEMORIAM: SHANE ROUT", subheader="PIONEER OF DEPRESSIVE BLACK METAL", is_tribute=True)

    print("\n--- 2. Processando Áudio com Curva Perfeita de Volume ---")
    
    # Intro
    intro_voice = "temp_tribute/s01_intro.mp3"
    intro_dur = get_audio_duration(intro_voice) + 0.8
    intro_audio = "temp_final/intro.mp3"
    subprocess.run([
        FFMPEG_PATH, "-y", "-i", intro_voice,
        "-af", "volume=1.35,apad=pad_dur=0.8",
        "-c:a", "libmp3lame", "-b:a", "192k",
        intro_audio
    ], check=True)
    
    # Track 1: Depression
    t1_audio, t1_dur = build_perfect_ducked_audio(
        "temp_tribute/s02_intro_sample1.mp3",
        "temp/sample1_long.mp3",
        "temp_final/t1.mp3",
        solo_duration=10.0
    )
    
    # Track 2: Betrayed
    t2_audio, t2_dur = build_perfect_ducked_audio(
        "temp_tribute/s04_intro_sample2.mp3",
        "temp/sample2_long.mp3",
        "temp_final/t2.mp3",
        solo_duration=10.0
    )
    
    # Track 3: Despondency
    t3_audio, t3_dur = build_perfect_ducked_audio(
        "temp_tribute/s06_intro_despondency.mp3",
        "temp/sample3_despondency.mp3",
        "temp_final/t3.mp3",
        solo_duration=10.0
    )
    
    # Tributo a Shane Rout (Música de fundo tocando baixo durante a fala)
    trib_audio, trib_dur = build_tribute_audio(
        "temp_tribute/s08_tribute.mp3",
        "temp/sample_ambient_outro.mp3",
        "temp_final/tribute.mp3"
    )

    SEGMENTS = [
        {"img": "temp_final/slide_intro.jpg", "audio": intro_audio, "dur": intro_dur},
        {"img": "temp_final/slide_track1.jpg", "audio": t1_audio, "dur": t1_dur},
        {"img": "temp_final/slide_track2.jpg", "audio": t2_audio, "dur": t2_dur},
        {"img": "temp_final/slide_track3.jpg", "audio": t3_audio, "dur": t3_dur},
        {"img": "temp_final/slide_tribute.jpg", "audio": trib_audio, "dur": trib_dur},
    ]

    print("\n--- 3. Renderizando Segmentos em Vídeo ---")
    clip_list_file = "temp_final/clips.txt"
    clip_files = []
    
    for idx, seg in enumerate(SEGMENTS):
        clip_path = f"temp_final/clip_{idx:02d}.mp4"
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

    final_output = "output/Abyssic_Hate_Shorts_9x16.mp4"
    print(f"\nConcatenando todos os clipes em: {final_output}")
    cmd_concat = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", clip_list_file,
        "-c", "copy",
        final_output
    ]
    subprocess.run(cmd_concat, check=True)
    
    total_sec = sum(s["dur"] for s in SEGMENTS)
    print(f"\n=======================================================")
    print(f"SUCESSO! VÍDEO COMPLETO GERADO EM: {final_output}")
    print(f"Duração Total: {int(total_sec // 60)}m {int(total_sec % 60)}s ({total_sec:.1f} segundos)")
    print(f"Tamanho: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"=======================================================\n")

if __name__ == "__main__":
    build_full_video()
