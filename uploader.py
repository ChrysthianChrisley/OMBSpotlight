import os
import sys
import pickle
import json
from datetime import datetime

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

CREDENTIALS_DIR = r"C:\Users\cytch\Documents\GitHub\AutomatizarUploadYT\credentials"
CLIENT_SECRETS_FILE = os.path.join(CREDENTIALS_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "token.pickle")

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Aviso ao carregar token existente: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Atualizando token de acesso do YouTube...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Não foi possível atualizar token: {e}")
                creds = None

        if not creds or not creds.valid:
            print("Autenticando via client_secrets.json...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print("Autenticação salva com sucesso!")

    return build('youtube', 'v3', credentials=creds)

def add_video_to_playlist(youtube, video_id, playlist_name="One Man Bands"):
    try:
        request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
        response = request.execute()
        target_playlist_id = None
        for item in response.get("items", []):
            title = item.get("snippet", {}).get("title", "")
            if playlist_name.lower() in title.lower():
                target_playlist_id = item.get("id")
                break

        if not target_playlist_id:
            print(f"Playlist '{playlist_name}' não encontrada. Criando nova playlist...")
            create_req = youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {"title": playlist_name, "description": "One-Man Band Spotlight Series"},
                    "status": {"privacyStatus": "unlisted"}
                }
            )
            created_res = create_req.execute()
            target_playlist_id = created_res.get("id")

        body = {
            "snippet": {
                "playlistId": target_playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id}
            }
        }
        youtube.playlistItems().insert(part="snippet", body=body).execute()
        print(f"Vídeo adicionado à playlist '{playlist_name}' (ID: {target_playlist_id})!")
        return True
    except Exception as e:
        print(f"Aviso ao adicionar à playlist: {e}")
        return False

def upload_short(file_path, title, description, tags=None, privacy_status="unlisted"):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {file_path}")

    print(f"\nIniciando upload de: {file_path}")
    print(f"Título: {title}")
    print(f"Privacidade: {privacy_status}")

    youtube = get_authenticated_service()

    if tags is None:
        tags = ["shorts", "blackmetal", "dsbm", "onemanband", "metal", "undergroundmetal"]

    body = {
        'snippet': {
            'title': title[:100],
            'description': description,
            'tags': tags,
            'categoryId': '10' # Music
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=1024*1024*8, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progresso: {int(status.progress() * 100)}%")

    video_id = response.get('id')
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\n✅ Upload concluído com sucesso!")
    print(f"🔗 Link do Vídeo: {video_url}")

    add_video_to_playlist(youtube, video_id, playlist_name="One Man Bands")
    return video_url

from datetime import datetime

QUEUE_FILE = "upload_queue.json"
HISTORY_FILE = "uploaded_history.json"

def get_description_from_info(info_file):
    if not os.path.exists(info_file):
        return "One-Man Band Spotlight Series."
    with open(info_file, "r", encoding="utf-8") as f:
        content = f.read()
    if "=== DESCRIÇÃO (Copiar e colar) ===" in content:
        desc = content.split("=== DESCRIÇÃO (Copiar e colar) ===")[1].split("=== TIKTOK")[0].strip()
        return desc
    return content

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

def process_upload_queue():
    if not os.path.exists(QUEUE_FILE):
        print(f"Fila {QUEUE_FILE} não encontrada!")
        return

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = json.load(f)

    # Considera pendente se status for 'pending' ou se simplesmente estiver na lista de pendências
    pending = [item for item in queue if item.get("status", "pending") == "pending"]
    if not pending:
        print("🎉 Não há vídeos pendentes na fila de upload! Todos já foram enviados.")
        return

    print(f"\n=======================================================")
    print(f"📋 PROCESSANDO FILA DE UPLOAD DO YOUTUBE ({len(pending)} pendentes)")
    print(f"=======================================================")

    history = load_history()
    remaining_queue = list(queue)

    for item in list(pending):
        file_path = item.get("file_path")
        title = item.get("title")
        info_file = item.get("info_file")
        tags = item.get("tags", ["shorts", "blackmetal", "dsbm", "onemanband", "metal"])

        if not os.path.exists(file_path):
            print(f"⚠️ Arquivo de vídeo não encontrado para '{title}': {file_path}. Pulando...")
            continue

        desc = get_description_from_info(info_file)

        print(f"\nTentando upload de: {title}")
        print(f"Arquivo: {file_path}")

        try:
            url = upload_short(file_path, title, desc, tags=tags, privacy_status="unlisted")
            
            # Adiciona ao histórico com timestamp
            item_uploaded = dict(item)
            item_uploaded["status"] = "uploaded"
            item_uploaded["video_url"] = url
            item_uploaded["uploaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history.append(item_uploaded)
            save_history(history)

            # Remove da lista de pendências
            remaining_queue = [q for q in remaining_queue if q.get("title") != title and q.get("file_path") != file_path]
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(remaining_queue, f, indent=2, ensure_ascii=False)

            print(f"✅ {title} enviado e REMOVIDO da fila de pendências! Salvo no histórico -> {url}")

        except HttpError as e:
            if "quotaExceeded" in str(e) or (hasattr(e, 'resp') and e.resp.status in [403, 429]):
                print(f"\n🛑 AVISO DE QUOTA DA API DO YOUTUBE:")
                print(f"O limite de quota diária da API do YouTube foi atingido!")
                print(f"O vídeo '{title}' e os próximos permanecem salvos na lista de pendências.")
                print(f"Basta dar 2 cliques em 'enviar_pendencias.bat' quando a quota reestabelecer.")
            else:
                print(f"❌ Erro HTTP ao enviar vídeo: {e}")
            break
        except Exception as e:
            print(f"❌ Erro inesperado durante o upload: {e}")
            break

    print(f"\nProcessamento concluído. Itens restantes na fila: {len(remaining_queue)}.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--upload-1":
        video_file = "output/Abyssic_Hate_Shorts_9x16.mp4"
        title = "#1 - Abyssic Hate | One-Man Band Spotlight #Shorts"
        desc = get_description_from_info("output/post_info.txt")
        upload_short(video_file, title, desc, privacy_status="unlisted")
    elif len(sys.argv) > 1 and sys.argv[1] == "--upload-pending":
        process_upload_queue()
    else:
        print("Uso:")
        print("  python uploader.py --upload-pending   (Envia todos os vídeos pendentes da fila)")
        print("  python uploader.py --upload-1         (Envia apenas o vídeo #1)")

