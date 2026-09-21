import os
import sys
import re
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

# Carrega variáveis do arquivo .env
load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")

def get_client():
    if not API_KEY:
        raise ValueError("Chave ELEVENLABS_API_KEY não encontrada no arquivo .env!")
    return ElevenLabs(api_key=API_KEY)

def list_voices():
    """Lista as vozes disponíveis na sua conta (padrão e clonadas)"""
    client = get_client()
    response = client.voices.get_all()
    print("\n=== VOZES DISPONÍVEIS NA SUA CONTA ===")
    for v in response.voices:
        category = getattr(v, "category", "default")
        print(f"Nome: {v.name:<20} | ID: {v.voice_id} | Categoria: {category}")
    print("======================================\n")

def generate_narration(text, output_file="narracao.mp3", voice_id="JBFqnCBsd6RMkjVDRZzb", stability=0.5, similarity=0.75):
    """
    Gera áudio a partir de um texto usando o modelo eleven_multilingual_v2.
    
    Parâmetros:
    - text: Texto do script a ser narrado.
    - output_file: Caminho do arquivo .mp3 de saída.
    - voice_id: ID da voz escolhida (padrão: George / Multilingual).
    - stability: Estabilidade da voz (0.0 a 1.0). Valores menores dão mais emoção/variação.
    - similarity: Aderência à voz original (0.0 a 1.0).
    """
    # Remove marcadores de direção como [PLAY SAMPLE ...] para não serem lidos
    clean_text = re.sub(r'\[.*?\]', '', text).strip()
    
    print(f"Gerando narração com ElevenLabs...")
    print(f"Tamanho do texto limpo: {len(clean_text)} caracteres")
    
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=clean_text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=stability,
            similarity_boost=similarity,
            style=0.2,
            use_speaker_boost=True
        )
    )

    # Cria pasta de destino caso não exista
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    print(f"Sucesso! Áudio salvo em: {output_file}")
    return output_file

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list-voices":
        list_voices()
    else:
        # Se passar o caminho de um arquivo txt como argumento, lê o arquivo
        script_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("scripts", "abyssic_hate.txt")
        
        if os.path.isfile(script_path):
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()
            out_file = os.path.splitext(os.path.basename(script_path))[0] + ".mp3"
            generate_narration(content, output_file=out_file)
        else:
            exemplo = (
                "Founded in 1993 in Australia, Abyssic Hate stands as one of the darkest "
                "and most influential one-man band projects in black metal."
            )
            generate_narration(exemplo, output_file="teste_narracao.mp3")
