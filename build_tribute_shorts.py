import os
import subprocess
from PIL import Image, ImageFilter, ImageDraw, ImageFont

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
os.makedirs("temp_tribute", exist_ok=True)
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

def create_vertical_slide(fg_path, out_path, header="ONE-MAN BAND SPOTLIGHT", subheader="ABYSSIC HATE (AUSTRALIA)", now_playing=None, is_tribute=False):
    W, H = 1080, 1920
    fg = Image.open(fg_path).convert("RGB")
    
    # Fundo escurecido e desfocado
    bg = fg.copy().resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=55))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.58)
    
    # Imagem central
    target_size = 940
    fg_resized = fg.resize((target_size, target_size), Image.Resampling.LANCZOS)
    pos_x = (W - target_size) // 2
    pos_y = (H - target_size) // 2 - 30
    bg.paste(fg_resized, (pos_x, pos_y))
    
    draw = ImageDraw.Draw(bg)
    border_color = (180, 150, 100) if is_tribute else (120, 120, 120)
    draw.rectangle([pos_x, pos_y, pos_x + target_size, pos_y + target_size], outline=border_color, width=3)
    
    try:
        font_header = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 30)
        font_now = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 40)
    except Exception:
        font_header = font_sub = font_now = ImageFont.load_default()

    # Header Badge
    badge_w, badge_h = 760, 80
    badge_x = (W - badge_w) // 2
    badge_y = 170
    badge_bg = (25, 20, 15) if is_tribute else (15, 15, 15)
    badge_outline = (140, 110, 60) if is_tribute else (90, 90, 90)
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=20, fill=badge_bg, outline=badge_outline, width=2)
    header_color = (255, 220, 160) if is_tribute else (240, 240, 240)
    draw.text((W // 2, badge_y + 40), header, font=font_header, fill=header_color, anchor="mm")
    
    # Subtítulo
    draw.text((W // 2, badge_y + 125), subheader, font=font_sub, fill=(190, 190, 190), anchor="mm")
    
    # Rodapé
    footer_y = pos_y + target_size + 65
    if now_playing:
        box_w = 860
        box_h = 95
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
        draw.text((W // 2, footer_y + 48), f"NOW PLAYING: {now_playing.upper()}", font=font_now, fill=(255, 255, 255), anchor="mm")
    elif is_tribute:
        box_w = 860
        box_h = 95
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(20, 18, 15), outline=(120, 100, 60), width=2)
        draw.text((W // 2, footer_y + 48), "REST IN PEACE • 1972 - 2026", font=font_now, fill=(240, 210, 160), anchor="mm")
    else:
        draw.text((W // 2, footer_y + 48), "ALBUM: SUICIDAL EMOTIONS (2000)", font=font_now, fill=(210, 210, 210), anchor="mm")

    bg.save(out_path, quality=95)
    return out_path

def build_ducked_audio_smooth(voice_file, music_file, out_file, solo_duration=11.0, fadeout_duration=3.0, post_pause=1.2):
    """
    Mixagem com Ducking, Fade Out longo (3.0s) e pausa de respiro (1.2s):
    - Durante a fala: música no fundo bem sutil (volume=0.07).
    - Fim da fala: música sobe suavemente para volume=0.72 em 1.2s.
    - Toca solo por solo_duration segundos.
    - Fade-out gradual e suave de 3.0s até silêncio total.
    - Pausa de respiro de 1.2s antes do próximo trecho de narração.
    """
    t_voice = get_audio_duration(voice_file)
    music_active_dur = t_voice + solo_duration + fadeout_duration
    total_dur = music_active_dur + post_pause
    
    fade_start = t_voice + solo_duration
    
    # normalize=0 para preservar o volume da voz
    filter_complex = (
        f"[0:a]volume=1.35,apad=pad_dur={solo_duration + fadeout_duration + post_pause:.2f}[narr];"
        f"[1:a]atrim=0:{music_active_dur:.2f},"
        f"volume='if(lt(t, {t_voice:.2f}), 0.07, min(0.72, 0.07 + (t-{t_voice:.2f})*0.55))':eval=frame,"
        f"afade=t=in:ss=0:d=1.2,"
        f"afade=t=out:st={fade_start:.2f}:d={fadeout_duration:.2f},"
        f"apad=pad_dur={post_pause:.2f}[mus];"
        f"[narr][mus]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0[aout]"
    )
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", voice_file,
        "-i", music_file,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_file
    ]
    subprocess.run(cmd, check=True)
    return out_file, total_dur

def build_tribute_audio(voice_file, ambient_music_file, out_file):
    """Áudio para o tributo com fundo solene sutil e fade out respeitoso"""
    t_voice = get_audio_duration(voice_file)
    total_dur = t_voice + 2.5
    
    filter_complex = (
        f"[0:a]volume=1.35,apad=pad_dur=2.5[narr];"
        f"[1:a]atrim=0:{total_dur:.2f},volume=0.06,afade=t=in:ss=0:d=2.0,afade=t=out:st={total_dur-2.0:.2f}:d=2.0[mus];"
        f"[narr][mus]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0[aout]"
    )
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", voice_file,
        "-i", ambient_music_file,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_file
    ]
    subprocess.run(cmd, check=True)
    return out_file, total_dur

def run():
    print("\n--- Montando Slides Verticais ---")
    cover_blurred = "assets/suicidal_emotions_blurred.jpg"
    shane = "assets/shane_rout.jpg"
    
    create_vertical_slide(shane, "temp_tribute/slide_intro.jpg", header="ONE-MAN BAND SPOTLIGHT", subheader="SHANE ROUT - ALL INSTRUMENTS & VOCALS")
    create_vertical_slide(cover_blurred, "temp_tribute/slide_sample1.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Depression")
    create_vertical_slide(cover_blurred, "temp_tribute/slide_sample2.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Betrayed")
    create_vertical_slide(cover_blurred, "temp_tribute/slide_sample3.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Depression")
    create_vertical_slide(shane, "temp_tribute/slide_tribute.jpg", header="IN MEMORIAM: SHANE ROUT", subheader="PIONEER OF DEPRESSIVE BLACK METAL", is_tribute=True)

    print("\n--- Processando Áudio com Transições Suaves e Pausas Naturais ---")
    
    # 1. Intro
    intro_audio = "temp_tribute/s01_intro.mp3"
    intro_dur = get_audio_duration(intro_audio) + 0.8
    intro_padded = "temp_tribute/intro_padded.mp3"
    subprocess.run([
        FFMPEG_PATH, "-y", "-i", intro_audio,
        "-af", "volume=1.35,apad=pad_dur=0.8",
        "-c:a", "libmp3lame", "-b:a", "192k",
        intro_padded
    ], check=True)
    
    # 2. Track 1
    t1_audio, t1_dur = build_ducked_audio_smooth(
        "temp_tribute/s02_intro_sample1.mp3",
        "temp/sample1.mp3",
        "temp_tribute/ducked_t1.mp3",
        solo_duration=11.0,
        fadeout_duration=3.0,
        post_pause=1.2
    )
    
    # 3. Track 2
    t2_audio, t2_dur = build_ducked_audio_smooth(
        "temp_tribute/s04_intro_sample2.mp3",
        "temp/sample2.mp3",
        "temp_tribute/ducked_t2.mp3",
        solo_duration=11.0,
        fadeout_duration=3.0,
        post_pause=1.2
    )
    
    # 4. Track 3
    t3_audio, t3_dur = build_ducked_audio_smooth(
        "temp_tribute/s06_intro_sample3.mp3",
        "temp/sample3.mp3",
        "temp_tribute/ducked_t3.mp3",
        solo_duration=11.0,
        fadeout_duration=3.0,
        post_pause=1.2
    )
    
    # 5. Tributo a Shane Rout
    trib_audio, trib_dur = build_tribute_audio(
        "temp_tribute/s08_tribute.mp3",
        "temp/sample1.mp3",
        "temp_tribute/tribute_ducked.mp3"
    )

    SEGMENTS = [
        {"img": "temp_tribute/slide_intro.jpg", "audio": intro_padded, "dur": intro_dur},
        {"img": "temp_tribute/slide_sample1.jpg", "audio": t1_audio, "dur": t1_dur},
        {"img": "temp_tribute/slide_sample2.jpg", "audio": t2_audio, "dur": t2_dur},
        {"img": "temp_tribute/slide_sample3.jpg", "audio": t3_audio, "dur": t3_dur},
        {"img": "temp_tribute/slide_tribute.jpg", "audio": trib_audio, "dur": trib_dur},
    ]

    print("\n--- Renderizando Clipes Verticais ---")
    clip_list_file = "temp_tribute/clips.txt"
    clip_files = []
    
    for idx, seg in enumerate(SEGMENTS):
        clip_path = f"temp_tribute/clip_{idx:02d}.mp4"
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
    print(f"\nConcatenando no vídeo final: {final_output}")
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
    run()
