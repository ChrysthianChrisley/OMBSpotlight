import os
import sys
import subprocess
from dotenv import load_dotenv
from PIL import Image, ImageFilter, ImageDraw, ImageFont

load_dotenv()

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
os.makedirs("temp_shorts", exist_ok=True)
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

def create_vertical_slide(fg_path, out_path, header="ONE-MAN BAND SPOTLIGHT", subheader="ABYSSIC HATE (AUSTRALIA)", now_playing=None):
    W, H = 1080, 1920
    fg = Image.open(fg_path).convert("RGB")
    
    # 1. Fundo vertical desfocado e escurecido preenchendo a tela toda
    bg = fg.copy().resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=55))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.55)
    
    # 2. Imagem central quadrada nítida (940x940)
    target_size = 940
    fg_resized = fg.resize((target_size, target_size), Image.Resampling.LANCZOS)
    pos_x = (W - target_size) // 2
    pos_y = (H - target_size) // 2 - 30
    bg.paste(fg_resized, (pos_x, pos_y))
    
    draw = ImageDraw.Draw(bg)
    draw.rectangle([pos_x, pos_y, pos_x + target_size, pos_y + target_size], outline=(120, 120, 120), width=3)
    
    # Fontes
    try:
        font_header = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 30)
        font_now = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 42)
    except Exception:
        font_header = font_sub = font_now = ImageFont.load_default()

    # 3. Topo estilizado (Header Badge)
    badge_w, badge_h = 740, 80
    badge_x = (W - badge_w) // 2
    badge_y = 170
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=20, fill=(15, 15, 15), outline=(90, 90, 90), width=2)
    draw.text((W // 2, badge_y + 40), header, font=font_header, fill=(240, 240, 240), anchor="mm")
    
    draw.text((W // 2, badge_y + 125), subheader, font=font_sub, fill=(190, 190, 190), anchor="mm")
    
    # 4. Rodapé (Now Playing / Info)
    footer_y = pos_y + target_size + 65
    if now_playing:
        box_w = 860
        box_h = 95
        bx = (W - box_w) // 2
        draw.rounded_rectangle([bx, footer_y, bx + box_w, footer_y + box_h], radius=20, fill=(15, 15, 15), outline=(130, 130, 130), width=2)
        draw.text((W // 2, footer_y + 48), f"NOW PLAYING: {now_playing.upper()}", font=font_now, fill=(255, 255, 255), anchor="mm")
    else:
        draw.text((W // 2, footer_y + 48), "ALBUM: SUICIDAL EMOTIONS (2000)", font=font_now, fill=(210, 210, 210), anchor="mm")

    bg.save(out_path, quality=95)
    return out_path

def build_ducked_audio(voice_file, music_file, out_file, solo_duration=12.0):
    """
    Mistura narração e música com efeito Ducking/Swell:
    - normalize=0 no amix para NÃO atenuar a voz pela metade!
    - Narração com volume amplificado (1.3) para ficar bem nítida e alta.
    - Música bem sutil (volume=0.08) durante a fala para não competir com a voz.
    - Quando a voz termina: a música sobe suavemente para volume=0.72.
    """
    t_voice = get_audio_duration(voice_file)
    total_dur = t_voice + solo_duration
    
    # Rampa de subida de 1.0s após a voz terminar
    filter_complex = (
        f"[0:a]volume=1.30,apad=pad_dur={solo_duration:.2f}[narr];"
        f"[1:a]atrim=0:{total_dur:.2f},"
        f"volume='if(lt(t, {t_voice:.2f}), 0.08, min(0.72, 0.08 + (t-{t_voice:.2f})*0.64))':eval=frame,"
        f"afade=t=in:ss=0:d=1.0,afade=t=out:st={total_dur-1.8:.2f}:d=1.8[mus];"
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

def assemble_shorts():
    print("\n--- Montando Slides Verticais ---")
    cover_blurred = "assets/suicidal_emotions_blurred.jpg"
    shane = "assets/shane_rout.jpg"
    
    create_vertical_slide(shane, "temp_shorts/slide_intro.jpg", header="ONE-MAN BAND SPOTLIGHT", subheader="SHANE ROUT - ALL INSTRUMENTS & VOCALS")
    create_vertical_slide(cover_blurred, "temp_shorts/slide_sample1.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Depression")
    create_vertical_slide(cover_blurred, "temp_shorts/slide_sample2.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Betrayed")
    create_vertical_slide(cover_blurred, "temp_shorts/slide_sample3.jpg", header="SUICIDAL EMOTIONS (2000)", subheader="ABYSSIC HATE", now_playing="Depression")
    create_vertical_slide(cover_blurred, "temp_shorts/slide_outro.jpg", header="ONE-MAN BAND MONUMENT", subheader="ABYSSIC HATE - SUICIDAL EMOTIONS")

    print("\n--- Processando Áudio com Ducking (Música de Fundo + Aumento de Volume ao Parar de Falar) ---")
    
    # 1. Segmento 1: Introdução Shane Rout
    intro_audio = "temp_shorts/s01_intro.mp3"
    intro_dur = get_audio_duration(intro_audio)
    
    # 2. Segmento 2: NOW PLAYING DEPRESSION (Ducking)
    track1_audio, track1_dur = build_ducked_audio(
        "temp_shorts/s02_intro_sample1.mp3",
        "temp/sample1.mp3",
        "temp_shorts/audio_ducked_track1.mp3",
        solo_duration=11.5
    )
    
    # 3. Segmento 3: NOW PLAYING BETRAYED (Ducking)
    track2_audio, track2_dur = build_ducked_audio(
        "temp_shorts/s04_intro_sample2.mp3",
        "temp/sample2.mp3",
        "temp_shorts/audio_ducked_track2.mp3",
        solo_duration=11.5
    )
    
    # 4. Segmento 4: NOW PLAYING DEPRESSION II (Ducking)
    track3_audio, track3_dur = build_ducked_audio(
        "temp_shorts/s06_intro_sample3.mp3",
        "temp/sample3.mp3",
        "temp_shorts/audio_ducked_track3.mp3",
        solo_duration=11.5
    )
    
    # 5. Segmento 5: Conclusão
    outro_audio = "temp_shorts/s08_outro.mp3"
    outro_dur = get_audio_duration(outro_audio)
    
    SEGMENTS = [
        {"img": "temp_shorts/slide_intro.jpg", "audio": intro_audio, "dur": intro_dur},
        {"img": "temp_shorts/slide_sample1.jpg", "audio": track1_audio, "dur": track1_dur},
        {"img": "temp_shorts/slide_sample2.jpg", "audio": track2_audio, "dur": track2_dur},
        {"img": "temp_shorts/slide_sample3.jpg", "audio": track3_audio, "dur": track3_dur},
        {"img": "temp_shorts/slide_outro.jpg", "audio": outro_audio, "dur": outro_dur},
    ]

    print("\n--- Renderizando Clipes Verticais ---")
    clip_list_file = "temp_shorts/clips_ducked.txt"
    clip_files = []
    
    for idx, seg in enumerate(SEGMENTS):
        clip_path = f"temp_shorts/ducked_clip_{idx:02d}.mp4"
        dur = seg["dur"]
        
        # Para os segmentos 0 e 4 (apenas fala), amplifica para 1.30 igual aos demais
        af_opts = ["-af", "volume=1.30,aformat=channel_layouts=stereo"] if idx in (0, 4) else ["-af", "aformat=channel_layouts=stereo"]
        
        cmd = [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-i", seg["img"],
            "-i", seg["audio"],
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            *af_opts,
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
    print(f"\nConcatenando clipes no vídeo final: {final_output}")
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
    print(f"SUCESSO! VÍDEO COM DUCKING GERADO EM: {final_output}")
    print(f"Duração Total: {int(total_sec // 60)}m {int(total_sec % 60)}s ({total_sec:.1f} segundos)")
    print(f"Tamanho: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"=======================================================\n")

if __name__ == "__main__":
    assemble_shorts()
