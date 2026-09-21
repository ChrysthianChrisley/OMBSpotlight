import os
import sys
import time
import json
import re
import glob
from datetime import datetime

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.abspath("tiktok_session")
HISTORY_FILE = "tiktok_history.json"
OUTPUT_DIR = "output"
TIKTOK_LOGIN_URL = "https://www.tiktok.com/login"
TIKTOK_STUDIO_URL = "https://www.tiktok.com/tiktokstudio/upload"
MAX_VIDEOS_PER_DAY = 2
DELAY_BETWEEN_VIDEOS = 90  # segundos de intervalo seguro entre vídeos no mesmo dia

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_today_uploads(history):
    today = datetime.now().strftime("%Y-%m-%d")
    return [item for item in history if item.get("uploaded_at", "").startswith(today)]

def get_all_episodes():
    episodes = []
    info_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*_post_info.txt")))
    for f in info_files:
        filename = os.path.basename(f)
        match_id = re.match(r"^(\d+)_", filename)
        if not match_id:
            continue
        ep_id = int(match_id.group(1))
        
        # Encontrar mp4 correspondente
        mp4_pattern = os.path.join(OUTPUT_DIR, f"{ep_id:02d}_*Shorts_9x16.mp4")
        mp4_files = glob.glob(mp4_pattern)
        if not mp4_files:
            # Fallback sem zero à esquerda
            mp4_files = glob.glob(os.path.join(OUTPUT_DIR, f"*{filename.split('_post_info')[0]}*.mp4"))
        
        if not mp4_files:
            continue
        
        mp4_path = mp4_files[0].replace("\\", "/")
        
        # Extrair título e legenda do TikTok
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
        
        match_caption = re.search(r'===\s*TIKTOK\s*\(Legenda curta\)\s*===\s*\n(.*)', content, re.DOTALL)
        if match_caption:
            caption = match_caption.group(1).strip()
        else:
            caption = f"#{ep_id} - One-Man Band Spotlight #shorts #blackmetal #onemanband"
        
        # Extrair nome da banda do título
        match_band = re.search(r'#\d+\s*-\s*([^|]+)\|', content)
        band = match_band.group(1).strip() if match_band else filename.replace("_post_info.txt", "")
        
        episodes.append({
            "id": ep_id,
            "band": band,
            "video_file": mp4_path,
            "info_file": f.replace("\\", "/"),
            "caption": caption
        })
        
    episodes.sort(key=lambda x: x["id"])
    return episodes

def show_status():
    print("\n=======================================================")
    print("📊 STATUS DE PUBLICAÇÕES NO TIKTOK (@onemanbands)")
    print("=======================================================")
    
    history = load_history()
    uploaded_ids = {item["id"]: item for item in history}
    all_episodes = get_all_episodes()
    today_uploads = get_today_uploads(history)
    
    print(f"Total de episódios no acervo: {len(all_episodes)}")
    print(f"Episódios já postados: {len(uploaded_ids)}")
    print(f"Episódios pendentes: {len(all_episodes) - len(uploaded_ids)}")
    print(f"Envios realizados hoje ({datetime.now().strftime('%d/%m/%Y')}): {len(today_uploads)} / {MAX_VIDEOS_PER_DAY}")
    
    if len(today_uploads) >= MAX_VIDEOS_PER_DAY:
        print("🛡️ Trava Anti-Shadowban: ATIVA (limite diário de 2 vídeos atingido).")
    else:
        print(f"✨ Vagas de envio disponíveis para hoje: {MAX_VIDEOS_PER_DAY - len(today_uploads)}")
        
    print("\n--- Lista dos Episódios ---")
    for ep in all_episodes:
        if ep["id"] in uploaded_ids:
            up = uploaded_ids[ep["id"]]
            print(f"  [✅ POSTADO] #{ep['id']:02d} - {ep['band']} (em {up.get('uploaded_at', 'N/D')})")
        else:
            print(f"  [⏳ PENDENTE] #{ep['id']:02d} - {ep['band']}")
    print("=======================================================\n")

def login_tiktok():
    print("\n=======================================================")
    print("🔑 CONECTAR CONTA TIKTOK: @onemanbands")
    print("=======================================================")
    print("Abrindo o navegador para autenticação...")
    print("Dica: No app do TikTok no celular, abra Perfil > Configurações > Código QR para escanear e entrar em 5 segundos!\n")
    
    os.makedirs(SESSION_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            channel="msedge",
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        page.goto(TIKTOK_LOGIN_URL, timeout=60000)
        
        print("-------------------------------------------------------")
        print("Quando você tiver concluído o login com sucesso no navegador:")
        input("👉 Pressione [ENTER] aqui no terminal para confirmar e salvar...")
        print("-------------------------------------------------------")
        
        # Testar acesso ao Studio
        print("Verificando acesso ao TikTok Studio...")
        page.goto(TIKTOK_STUDIO_URL, timeout=60000)
        page.wait_for_timeout(4000)
        
        current_url = page.url
        if "login" in current_url:
            print("⚠️ Aviso: Parece que o login ainda não foi concluído. Tente novamente.")
        else:
            print("🎉 SUCESSO! A sessão da conta @onemanbands foi salva com sucesso em 'tiktok_session/'.")
            print("Agora você pode rodar 'enviar_tiktok.bat' para enviar os vídeos automaticamente!")
            
        browser_context.close()

def upload_videos(force=False):
    history = load_history()
    uploaded_ids = {item["id"] for item in history}
    all_episodes = get_all_episodes()
    pending = [ep for ep in all_episodes if ep["id"] not in uploaded_ids]
    
    if not pending:
        print("\n🎉 Todos os 17 episódios da série já foram enviados com sucesso para o TikTok!")
        return

    today_uploads = get_today_uploads(history)
    today_count = len(today_uploads)
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    print("\n=======================================================")
    print(f"🚀 INICIANDO UPLOAD PARA O TIKTOK (@onemanbands)")
    print("=======================================================")
    print(f"Data de hoje: {today_str}")
    print(f"Envios já realizados hoje: {today_count} / {MAX_VIDEOS_PER_DAY}")
    
    if today_count >= MAX_VIDEOS_PER_DAY and not force:
        print("\n🛡️ PROTEÇÃO ANTI-SHADOWBAN ATIVADA:")
        print(f"Você já enviou {today_count} vídeos hoje ({today_str}).")
        print("Para proteger o alcance da conta nova @onemanbands e evitar filtros de spam,")
        print("o próximo envio deve ser feito amanhã!")
        print("\n(Se você realmente quiser forçar o envio de mais um vídeo agora, execute: python tiktok_uploader.py --upload --force)")
        print("=======================================================\n")
        return

    slots_available = (MAX_VIDEOS_PER_DAY - today_count) if not force else len(pending)
    to_upload = pending[:slots_available]
    
    print(f"Vídeos programados para envio agora: {len(to_upload)}")
    for item in to_upload:
        print(f" - #{item['id']:02d}: {item['band']}")
    print("-------------------------------------------------------\n")
    
    if not os.path.exists(SESSION_DIR):
        print("❌ Erro: Nenhuma sessão encontrada. Execute 'conectar_tiktok.bat' primeiro para fazer o login.")
        return

    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            channel="msedge",
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        
        for idx, ep in enumerate(to_upload):
            ep_id = ep["id"]
            band = ep["band"]
            video_file = os.path.abspath(ep["video_file"])
            caption = ep["caption"]
            
            print(f"\n[{idx+1}/{len(to_upload)}] Enviando #{ep_id:02d} - {band}...")
            print(f"Arquivo: {video_file}")
            print(f"Legenda ({len(caption)} caracteres):\n{caption}\n")
            
            # Navegar para página de upload
            page.goto(TIKTOK_STUDIO_URL, timeout=60000)
            page.wait_for_timeout(3000)
            
            if "login" in page.url:
                print("❌ Sessão expirada ou não logada. Por favor, execute 'conectar_tiktok.bat' novamente.")
                browser_context.close()
                return

            # Localizar input de arquivo
            print("Selecionando arquivo de vídeo...")
            file_input = None
            try:
                # Primeiro tentar na página principal
                inputs = page.locator('input[type="file"]')
                if inputs.count() > 0:
                    file_input = inputs.first
                else:
                    # Tentar dentro de iframes
                    for frame in page.frames:
                        f_inputs = frame.locator('input[type="file"]')
                        if f_inputs.count() > 0:
                            file_input = f_inputs.first
                            break
            except Exception as e:
                print(f"Aviso ao buscar input de arquivo: {e}")
                
            if not file_input:
                print("❌ Não foi possível localizar o campo de upload de vídeo na página do TikTok.")
                print("Tente atualizar a página ou verificar o navegador.")
                continue

            file_input.set_input_files(video_file)
            print("Carregando vídeo... Aguardando a interface de postagem...")
            page.wait_for_timeout(6000)
            
            # Localizar o campo de legenda
            print("Preenchendo legenda e hashtags...")
            caption_box = None
            selectors = [
                'div[contenteditable="true"]',
                'div.public-DraftEditor-content',
                'div[class*="DraftEditor-editorContainer"] div[contenteditable]',
                'div[class*="caption-editor"] [contenteditable="true"]',
                'div[data-placeholder]'
            ]
            
            for sel in selectors:
                loc = page.locator(sel)
                if loc.count() > 0:
                    caption_box = loc.first
                    break
                    
            if caption_box:
                try:
                    caption_box.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.wait_for_timeout(500)
                    
                    # Digitar de forma natural
                    page.keyboard.type(caption, delay=20)
                    print("✅ Legenda inserida com sucesso!")
                except Exception as e:
                    print(f"Aviso ao preencher legenda: {e}")
            else:
                print("⚠️ Campo de legenda não identificado automaticamente; verifique o navegador.")

            # Aguardar o upload concluir (procurar indicação de 100% ou botão habilitado)
            print("Aguardando confirmação de processamento do vídeo...")
            page.wait_for_timeout(10000)
            
            # Procurar o botão Publicar / Post
            post_button = None
            button_selectors = [
                'button:has-text("Publicar")',
                'button:has-text("Post")',
                'button.btn-post',
                'button[class*="button-post"]',
                'button[class*="primary"]:has-text("Post")'
            ]
            
            for b_sel in button_selectors:
                btn = page.locator(b_sel)
                if btn.count() > 0:
                    post_button = btn.first
                    break
                    
            if post_button:
                print("Clicando no botão de publicação...")
                try:
                    post_button.wait_for(state="visible", timeout=60000)
                    post_button.click()
                    print("Aguardando confirmação de envio...")
                    page.wait_for_timeout(8000)
                    
                    # Gravar no histórico
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    history.append({
                        "id": ep_id,
                        "band": band,
                        "video_file": ep["video_file"],
                        "info_file": ep["info_file"],
                        "caption": caption,
                        "uploaded_at": now_str,
                        "status": "uploaded"
                    })
                    save_history(history)
                    print(f"🎉 SUCESSO! Episódio #{ep_id:02d} ({band}) publicado e registrado em 'tiktok_history.json'!")
                except Exception as e:
                    print(f"Erro ao clicar em publicar: {e}")
            else:
                print("⚠️ Botão de publicação não encontrado automaticamente.")
                input("Pressione [ENTER] no terminal após clicar em 'Publicar' manualmente no navegador...")
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                history.append({
                    "id": ep_id,
                    "band": band,
                    "video_file": ep["video_file"],
                    "info_file": ep["info_file"],
                    "caption": caption,
                    "uploaded_at": now_str,
                    "status": "uploaded"
                })
                save_history(history)
                print(f"Episódio #{ep_id:02d} registrado com sucesso!")

            # Se ainda houver outro vídeo para postar hoje, aguardar o intervalo seguro
            if idx < len(to_upload) - 1:
                print(f"\n⏳ Intervalo de proteção anti-spam: Aguardando {DELAY_BETWEEN_VIDEOS} segundos antes do próximo vídeo...")
                time.sleep(DELAY_BETWEEN_VIDEOS)
                
        browser_context.close()
        print("\n=======================================================")
        print("Envio diário concluído com sucesso!")
        print("=======================================================\n")

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--login" in args:
        login_tiktok()
    elif "--status" in args:
        show_status()
    elif "--upload" in args:
        force_flag = "--force" in args
        upload_videos(force=force_flag)
    else:
        print("Uso:")
        print("  python tiktok_uploader.py --login    (Conectar sua conta TikTok)")
        print("  python tiktok_uploader.py --status   (Ver status de postagens e fila)")
        print("  python tiktok_uploader.py --upload   (Enviar os vídeos permitidos hoje)")
        print("  python tiktok_uploader.py --upload --force  (Forçar envio ignorando limite diário)")
        show_status()
