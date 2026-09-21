import os
import subprocess
from PIL import Image, ImageFilter, ImageDraw, ImageFont

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
os.makedirs("temp_xasthur", exist_ok=True)
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

def create_vertical_slide(fg_path, out_path, header="ONE-MAN BAND SPOTLIGHT", subheader="MALEFIC - ALL INSTRUMENTS & VOCALS", now_playing=None, is_intro=False, is_outro=False):
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

    # 3. Topo estilizado (Header Badge)
    badge_w, badge_h = 760, 80
    badge_x = (W - badge_w) // 2
    badge_y = 160
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=20, fill=(15, 15, 15), outline=(90, 90, 90), width=2)
    draw.text((W // 2, badge_y + 40), header, font=font_header, fill=(240, 240, 240), anchor="mm")
    draw.text((W // 2, badge_y + 120), subheader, font=font_sub, fill=(190, 190, 190), anchor="mm")
    
    # 4. Rodapé
    footer_y = pos_y + target_size + 50
    if is_intro:
        box_w, box_h = 860, 125
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=22, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
        draw.text((W // 2, footer_y + 42), "XASTHUR", font=font_band, fill=(255, 255, 255), anchor="mm")
        draw.text((W // 2, footer_y + 88), "THE FUNERAL OF BEING (2003)", font=font_album, fill=(200, 200, 200), anchor="mm")
    elif now_playing:
        full_text = f"NOW PLAYING: {now_playing.upper()}"
        # Medir comprimento do texto para decidir se precisa de 2 linhas
        bbox = draw.textbbox((0, 0), full_text, font=font_now_single)
        text_width = bbox[2] - bbox[0]
        
        if text_width > 800 or len(now_playing) > 28:
            # Layout em 2 linhas: título cabe confortavelmente dentro da barra
            box_w, box_h = 880, 120
            bx = (W - box_w) // 2
            draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
            draw.text((W // 2, footer_y + 36), "NOW PLAYING", font=font_now_label, fill=(190, 190, 190), anchor="mm")
            # Se mesmo na segunda linha for muito comprido, ajusta fonte
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
        draw.text((W // 2, footer_y + 48), "DSBM PIONEER • 1995 - PRESENT", font=font_now_single, fill=(220, 220, 220), anchor="mm")

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
    print("\n--- 1. Gerando Slides Verticais de Xasthur ---")
    cover = "assets/xasthur/album_cover.jpg"
    malefic = "assets/xasthur/malefic_photo.jpg"

    create_vertical_slide(malefic, "temp_xasthur/slide_intro.jpg", is_intro=True)
    create_vertical_slide(cover, "temp_xasthur/slide_track1.jpg", header="THE FUNERAL OF BEING", subheader="XASTHUR (2003)", now_playing="The Awakening to the Unknown Perception of Evil")
    create_vertical_slide(cover, "temp_xasthur/slide_track2.jpg", header="THE FUNERAL OF BEING", subheader="XASTHUR (2003)", now_playing="Tyrant of Nightmares")
    create_vertical_slide(cover, "temp_xasthur/slide_track3.jpg", header="THE FUNERAL OF BEING", subheader="XASTHUR (2003)", now_playing="Sigils Made of Flesh and Trees")
    create_vertical_slide(malefic, "temp_xasthur/slide_outro.jpg", header="ONE-MAN BAND SPOTLIGHT", subheader="XASTHUR • MALEFIC", is_outro=True)

    print("\n--- 2. Processando Áudio com Ducking Perfeito ---")
    intro_voice = "temp_xasthur/intro.mp3"
    intro_dur = get_audio_duration(intro_voice) + 0.3
    intro_audio = "temp_xasthur/intro_padded.mp3"
    subprocess.run([
        FFMPEG_PATH, "-y", "-i", intro_voice,
        "-af", "volume=1.35,apad=pad_dur=0.3",
        "-c:a", "libmp3lame", "-b:a", "192k",
        intro_audio
    ], check=True)

    t1_audio, t1_dur = build_perfect_ducked_audio(
        "temp_xasthur/track1.mp3",
        "temp_xasthur/sample1_awakening.mp3",
        "temp_xasthur/t1.mp3",
        solo_duration=10.0
    )

    t2_audio, t2_dur = build_perfect_ducked_audio(
        "temp_xasthur/track2.mp3",
        "temp_xasthur/sample2_tyrant.mp3",
        "temp_xasthur/t2.mp3",
        solo_duration=10.0
    )

    t3_audio, t3_dur = build_perfect_ducked_audio(
        "temp_xasthur/track3.mp3",
        "temp_xasthur/sample3_sigils.mp3",
        "temp_xasthur/t3.mp3",
        solo_duration=10.0
    )

    outro_audio, outro_dur = build_outro_audio(
        "temp_xasthur/outro.mp3",
        "temp_xasthur/sample_ambient.mp3",
        "temp_xasthur/outro_ducked.mp3"
    )

    SEGMENTS = [
        {"img": "temp_xasthur/slide_intro.jpg", "audio": intro_audio, "dur": intro_dur},
        {"img": "temp_xasthur/slide_track1.jpg", "audio": t1_audio, "dur": t1_dur},
        {"img": "temp_xasthur/slide_track2.jpg", "audio": t2_audio, "dur": t2_dur},
        {"img": "temp_xasthur/slide_track3.jpg", "audio": t3_audio, "dur": t3_dur},
        {"img": "temp_xasthur/slide_outro.jpg", "audio": outro_audio, "dur": outro_dur},
    ]

    print("\n--- 3. Renderizando Segmentos em Vídeo ---")
    clip_list_file = "temp_xasthur/clips.txt"
    clip_files = []

    for idx, seg in enumerate(SEGMENTS):
        clip_path = f"temp_xasthur/clip_{idx:02d}.mp4"
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

    final_output = "output/03_Xasthur_Shorts_9x16.mp4"
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
    print(f"SUCESSO! EPISÓDIO #3 GERADO EM: {final_output}")
    print(f"Duração Total: {int(total_sec // 60)}m {int(total_sec % 60)}s ({total_sec:.1f} segundos)")
    print(f"Tamanho: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"=======================================================\n")

if __name__ == "__main__":
    run()
