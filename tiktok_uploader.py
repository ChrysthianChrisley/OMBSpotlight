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
        
        try:
            # Aguarda qualquer redirecionamento pendente do login estabilizar
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            
            current_url = page.url
            print(f"Página após login: {current_url}")
            
            if "login" not in current_url:
                print("\n🎉 SUCESSO! A sessão da conta @onemanbands foi salva com sucesso em 'tiktok_session/'!")
                print("Agora você já pode fechar esta janela e dar 2 cliques em 'enviar_tiktok.bat'!")
            else:
                print("Verificando acesso ao TikTok Studio...")
                try:
                    page.goto(TIKTOK_STUDIO_URL, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(3000)
                    if "login" not in page.url:
                        print("\n🎉 SUCESSO! A sessão da conta @onemanbands foi salva com sucesso em 'tiktok_session/'!")
                        print("Agora você já pode fechar esta janela e dar 2 cliques em 'enviar_tiktok.bat'!")
                    else:
                        print("⚠️ Aviso: Parece que o login ainda não foi concluído. Tente novamente.")
                except Exception as e:
                    print("🎉 SUCESSO! A sessão da conta @onemanbands foi salva localmente!")
                    print("Agora você já pode fechar esta janela e dar 2 cliques em 'enviar_tiktok.bat'!")
        finally:
            try:
                browser_context.close()
            except Exception:
                pass


def dismiss_modals(page):
    """Fecha qualquer modal, popup ou overlay informativo do TikTok Studio (ex: 'Preview your video on your phone')."""
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass

    button_selectors = [
        'button:has-text("Got it")',
        'button:has-text("Entendi")',
        'button:has-text("OK")',
        'button:has-text("Certo")',
        'button:has-text("Done")',
        '.TUXModal-overlay button',
        '[data-floating-ui-portal] button'
    ]
    for sel in button_selectors:
        try:
            btns = page.locator(sel)
            for i in range(btns.count()):
                b = btns.nth(i)
                if b.is_visible():
                    txt = b.inner_text().strip().lower()
                    if txt in ["got it", "entendi", "ok", "certo", "done", "close", "fechar", ""]:
                        print(f"Fechando aviso/popup do TikTok: '{b.inner_text().strip()}'...")
                        b.click(force=True)
                        page.wait_for_timeout(500)
        except Exception:
            pass

    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def upload_videos(force=False, visible=False):
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
    print(f"Modo: {'Visível' if visible else 'Silencioso (Segundo plano)'}")
    
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

    successful_uploads = []
    failed_uploads = []

    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            channel="msedge",
            headless=not visible,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        try:
            page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
            
            for idx, ep in enumerate(to_upload):
                ep_id = ep["id"]
                band = ep["band"]
                video_file = os.path.abspath(ep["video_file"])
                caption = ep["caption"]
                
                print(f"[{idx+1}/{len(to_upload)}] Preparando envio de #{ep_id:02d} - {band}...")
                print(f"Arquivo: {video_file}")
                
                # 1. Navegar para o estúdio de upload
                try:
                    page.goto(TIKTOK_STUDIO_URL, wait_until="domcontentloaded", timeout=60000)
                except Exception:
                    page.wait_for_timeout(2000)
                    page.goto(TIKTOK_STUDIO_URL, wait_until="domcontentloaded", timeout=60000)
                
                # Aguardar estabilização do app React
                page.wait_for_timeout(5000)
                
                if "login" in page.url:
                    print("❌ Sessão expirada ou não logada. Por favor, execute 'conectar_tiktok.bat' novamente.")
                    return

                # 2. Descartar rascunho anterior se houver
                try:
                    discard_btn = page.locator('button:has-text("Discard"), button:has-text("Descartar")')
                    if discard_btn.count() > 0 and discard_btn.first.is_visible():
                        print("Limpando rascunho anterior não finalizado no estúdio...")
                        discard_btn.first.click()
                        page.wait_for_timeout(3000)
                except Exception:
                    pass

                # 3. Localizar input de arquivo (esperando montar no DOM)
                print("Aguardando campo de upload...")
                try:
                    page.wait_for_selector('input[type="file"]', state="attached", timeout=45000)
                except Exception as e:
                    print(f"Aviso ao aguardar campo de arquivo: {e}")

                file_input = None
                inputs = page.locator('input[type="file"]')
                if inputs.count() > 0:
                    file_input = inputs.first
                else:
                    for frame in page.frames:
                        f_inputs = frame.locator('input[type="file"]')
                        if f_inputs.count() > 0:
                            file_input = f_inputs.first
                            break
                            
                if not file_input:
                    print("❌ Não foi possível anexar o arquivo de vídeo. Tentando capturar tela para diagnóstico...")
                    page.screenshot(path=f"debug_error_upload_{ep_id}.png")
                    failed_uploads.append(ep)
                    continue

                print("Enviando arquivo para o TikTok Studio...")
                file_input.set_input_files(video_file)
                page.wait_for_timeout(5000)
                
                # Fechar popups de onboarding que o TikTok exibe ao carregar o vídeo
                dismiss_modals(page)
                
                # 4. Preencher legenda e hashtags
                print("Preenchendo legenda e hashtags...")
                caption_box = page.locator('div[contenteditable="true"], div.public-DraftEditor-content, div[class*="DraftEditor-editorContainer"] div[contenteditable]').first
                try:
                    caption_box.wait_for(state="attached", timeout=30000)
                    caption_box.click(force=True)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.wait_for_timeout(500)
                    page.keyboard.type(caption, delay=15)
                    print("✅ Legenda inserida com sucesso!")
                except Exception as e:
                    print(f"Aviso ao preencher legenda: {e}")

                # Fechar popups que possam ter aparecido
                dismiss_modals(page)

                # 5. Aguardar processamento do vídeo (100% / botão habilitado)
                print("Aguardando upload e processamento do vídeo no servidor do TikTok...")
                post_button = page.locator('button:has-text("Publicar"), button:has-text("Post")').first
                
                is_ready = False
                for _ in range(45):  # até 90 segundos
                    try:
                        if post_button.is_visible() and post_button.is_enabled():
                            is_ready = True
                            break
                    except Exception:
                        pass
                    dismiss_modals(page)
                    page.wait_for_timeout(2000)
                    
                if is_ready:
                    dismiss_modals(page)
                    print("Clicando no botão de publicação...")
                    try:
                        # force=True garante o clique mesmo se houver camada sobreposta
                        post_button.click(force=True)
                        print("Aguardando confirmação do TikTok...")
                        
                        is_posted = False
                        for _ in range(15):  # até 30 segundos
                            page.wait_for_timeout(2000)
                            cur = page.url
                            if "content" in cur or "manage" in cur:
                                is_posted = True
                                break
                            success_indicators = page.locator('button:has-text("Manage your videos"), button:has-text("Upload another video"), button:has-text("Gerenciar seus vídeos"), button:has-text("Carregar outro vídeo"), div:has-text("Your video has been uploaded"), div:has-text("Seu vídeo foi publicado")')
                            if success_indicators.count() > 0 and success_indicators.first.is_visible():
                                is_posted = True
                                break
                            if not post_button.is_visible():
                                is_posted = True
                                break
                                
                        if is_posted:
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
                            successful_uploads.append(ep)
                            print(f"🎉 SUCESSO! Episódio #{ep_id:02d} ({band}) publicado e registrado em 'tiktok_history.json'!")
                        else:
                            print(f"⚠️ Não foi possível confirmar automaticamente a publicação do #{ep_id:02d}. Capturando tela...")
                            page.screenshot(path=f"debug_unconfirmed_{ep_id}.png")
                            failed_uploads.append(ep)
                    except Exception as e:
                        print(f"Erro ao clicar em publicar #{ep_id:02d}: {e}")
                        failed_uploads.append(ep)
                else:
                    print("⚠️ O botão de publicação não ficou pronto a tempo. Capturando tela para diagnóstico...")
                    page.screenshot(path=f"debug_timeout_{ep_id}.png")
                    failed_uploads.append(ep)

                # Se ainda houver outro vídeo para postar hoje, aguardar o intervalo seguro
                if idx < len(to_upload) - 1:
                    print(f"\n⏳ Intervalo de proteção anti-spam: Aguardando {DELAY_BETWEEN_VIDEOS} segundos antes do próximo vídeo...")
                    time.sleep(DELAY_BETWEEN_VIDEOS)
        finally:
            try:
                browser_context.close()
            except Exception:
                pass
                
        print("\n=======================================================")
        if successful_uploads:
            print(f"🎉 Envio concluído! {len(successful_uploads)} vídeo(s) publicado(s) com sucesso hoje:")
            for s in successful_uploads:
                print(f"   ✅ #{s['id']:02d} - {s['band']}")
        if failed_uploads:
            print(f"\n⚠️ Atenção: {len(failed_uploads)} vídeo(s) não foram concluídos:")
            for f in failed_uploads:
                print(f"   ❌ #{f['id']:02d} - {f['band']}")
        if not successful_uploads and not failed_uploads:
            print("Nenhum vídeo pendente para envio hoje.")
        print("=======================================================\n")

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--login" in args:
        login_tiktok()
    elif "--status" in args:
        show_status()
    elif "--upload" in args:
        force_flag = "--force" in args
        visible_flag = "--visible" in args
        upload_videos(force=force_flag, visible=visible_flag)
    else:
        print("Uso:")
        print("  python tiktok_uploader.py --login    (Conectar sua conta TikTok)")
        print("  python tiktok_uploader.py --status   (Ver status de postagens e fila)")
        print("  python tiktok_uploader.py --upload   (Enviar vídeos em modo 100% silencioso)")
        print("  python tiktok_uploader.py --upload --visible  (Enviar com navegador visível na tela)")
        print("  python tiktok_uploader.py --upload --force    (Forçar envio ignorando limite diário)")
        show_status()

