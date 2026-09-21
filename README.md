# 🎸 OMBSpotlight: One-Man Band Spotlight

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Audio%2FVideo%20Pipeline-007808?style=flat-square&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![YouTube](https://img.shields.io/badge/YouTube-Data%20API%20v3-FF0000?style=flat-square&logo=youtube&logoColor=white)](https://developers.google.com/youtube/v3)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Edge-TTS](https://img.shields.io/badge/TTS-Edge--TTS%2048kHz-blueviolet?style=flat-square)](https://github.com/rany2/edge-tts)

**OMBSpotlight** é um pipeline automatizado de produção de vídeos verticais (1080x1920, 9:16) para **YouTube Shorts** e **TikTok**, dedicado a homenagear e contar a história dos projetos mais icônicos do formato **One-Man Band** no Metal Extremo subterrâneo (Black Metal, DSBM, Post-Black Metal, Blackgaze, Ambient e Dungeon Synth).

O sistema orquestra download de áudio via yt-dlp, corte cirúrgico de amostras, síntese de narração neural com ducking de volume, renderização gráfica com efeitos de desfoque gaussiano no Pillow/FFmpeg, e publicação automática no YouTube com gerenciamento inteligente de quotas diárias.

---

## 📺 Catálogo da Série (Episódios #1 ao #17)

Todos os 17 episódios da primeira temporada estão gravados, renderizados e publicados:

| # | Projeto | País | Mente Criativa | Álbum Destacado | YouTube Shorts |
| :---: | :--- | :---: | :--- | :--- | :---: |
| **#1** | **Abyssic Hate** | 🇦🇺 Austrália | Shane Rout | *Suicidal Emotions* (2000) | [Assistir #Shorts](https://www.youtube.com/watch?v=TzGSjWNrGO4) |
| **#2** | **Leviathan** | 🇺🇸 EUA | Wrest (Jef Whitehead) | *The Tenth Sub Level of Suicide* (2003) | [Assistir #Shorts](https://www.youtube.com/watch?v=XSbHYo3fFVs) |
| **#3** | **Xasthur** | 🇺🇸 EUA | Malefic (Scott Conner) | *Subliminal Genocide* (2006) | [Assistir #Shorts](https://www.youtube.com/watch?v=fTSBR7_uC_w) |
| **#4** | **Trist** | 🇨🇿 Chéquia | Jan Kunc | *Zrcadlení Melancholie* (2007) | [Assistir #Shorts](https://www.youtube.com/watch?v=5TbUAmvClEw) |
| **#5** | **Panopticon** | 🇺🇸 EUA | Austin Lunn | *Kentucky* (2012) | [Assistir #Shorts](https://www.youtube.com/watch?v=XnBBoyUJW2Q) |
| **#6** | **Lustre** | 🇸🇪 Suécia | Nachtzeit (Henrik Sunding) | *Wonder* (2013) | [Assistir #Shorts](https://www.youtube.com/watch?v=j36eeJUGbEI) |
| **#7** | **Herbstregen** | 🇦🇹 Áustria | Herbstregen | *Herbstregen* (2013) | [Assistir #Shorts](https://www.youtube.com/watch?v=bO-q3tXhSWA) |
| **#8** | **Bilskirnir** | 🇩🇪 Alemanha | Widar | *Wotansvolk* (2007) | [Assistir #Shorts](https://www.youtube.com/watch?v=bjzaYbOjcHU) |
| **#9** | **Violet Cold** | 🇦🇿 Azerbaijão | Emin Guliyev | *Anomie* (2017) | [Assistir #Shorts](https://www.youtube.com/watch?v=gS4JE857-XY) |
| **#10** | **Mizmor** | 🇺🇸 EUA | A.L.N. (Liam Neighbors) | *Yodh* (2016) | [Assistir #Shorts](https://www.youtube.com/watch?v=aCKFhM_qRNQ) |
| **#11** | **Nihilistium** | 🇩🇪 Alemanha | Mortemiis | *Nihilistium* (2018) | [Assistir #Shorts](https://www.youtube.com/watch?v=bi-ILZx3q-8) |
| **#12** | **Sadness** *(Especial)* | 🇺🇸 EUA | Damián Antón Ojeda | *Somewhere Along Our Memory* (2020) + Trhä | [Assistir #Shorts](https://www.youtube.com/watch?v=Q1W4qrc8Fqo) |
| **#13** | **Grausamkeit** | 🇩🇪 Alemanha | B.S.o.D. (Andreas Bettinger) | *Pink Green 666* (1999) | [Assistir #Shorts](https://www.youtube.com/watch?v=spGoPnfKczo) |
| **#14** | **Woods of Desolation** | 🇦🇺 Austrália | D. (Dolor) | *Torn Beyond Reason* (2011) | [Assistir #Shorts](https://www.youtube.com/watch?v=_aPWbzpeskY) |
| **#15** | **Funesto** | 🇧🇷 Brasil | Funebre (Sergio França) | *Depressivos Hinos Suicidas* (2007) | [Assistir #Shorts](https://www.youtube.com/watch?v=WsleftvFgBg) |
| **#16** | **Taake** | 🇳🇴 Noruega | Hoest (Ørjan Stedjeberg) | *Stridens Hus* (2014) | [Assistir #Shorts](https://www.youtube.com/watch?v=hGij6lMNb5I) |
| **#17** | **Sacred Son** | 🇬🇧 Reino Unido | Dane Cross | *Sacred Son* (100% Solo Debut - 2017) | [Assistir #Shorts](https://www.youtube.com/watch?v=o986kexNXUw) |

---

## ⚙️ Arquitetura & Recursos Técnicos

### 1. Engenharia de Áudio & Ducking
- **Padronização em 48.000 Hz Stereo (192 kbps):** Todas as fontes de voz (Edge-TTS / ElevenLabs) e os cortes de áudio musical são estritamente convertidos para 48 kHz antes da concatenação, prevenindo qualquer erro de timestamp (`Non-monotonous DTS`).
- **Automação Dinâmica de Volume:**
  - A música de fundo opera em volume atenuado (`0.08`) durante a fala do narrador.
  - Sobe suavemente (`1.2s ramp`) para volume de destaque (`0.72`) durante o solo da música (10-14s).
  - Fade out dinâmico sem pausas ou silêncios mortos na troca de faixas.
- **Voz Neural:** Voz `en-US-ChristopherNeural` (Edge-TTS) configurada a `-3% rate` e `-2Hz pitch`, entregando tom narrativo documentário, consistente e sem limites de quota de caracteres.

### 2. Design Visual (1080x1920)
- **Fundo Cinematográfico:** Fundo vertical derivado da própria capa do álbum com aplicação de desfoque gaussiano de 55px e escurecimento de 60%.
- **Box "NOW PLAYING" Responsivo:** O sistema mede a largura do texto do título da música em pixels. Títulos longos (> 26 caracteres) são automaticamente formatados em duas linhas (*NOW PLAYING* no topo e o título da faixa em destaque abaixo), eliminando qualquer transbordamento.
- **Identidade da Série:** Header badge superior estilizado com os dados do projeto e o mentor responsável.

### 3. Pipeline de Envio Automático & Fila
- **Fila em JSON (`upload_queue.json`):** Vídeos recém-gerados são adicionados automaticamente com metadados completos.
- **Histórico Consolidado (`uploaded_history.json`):** Vídeos postados com sucesso são transferidos da fila de pendências para o histórico com data/hora e URL do YouTube.
- **Envio com 2 Cliques (`enviar_pendencias.bat`):** Script executável em Windows que consome a fila e lida de forma resiliente com pausas por limite de cota da API do YouTube.

---

## 📁 Estrutura do Repositório

```text
OMBSpotlight/
├── assets/                       # Capas de álbuns originais em alta resolução (1200x1200)
│   ├── abyssic_hate/
│   ├── bilskirnir/
│   ├── funesto/
│   ├── grausamkeit/
│   ├── leviathan/
│   ├── lustre/
│   ├── mizmor/
│   ├── nihilistium/
│   ├── panopticon/
│   ├── sacred_son/
│   ├── sadness/
│   ├── taake/
│   ├── trist/
│   ├── violet_cold/
│   ├── woods_of_desolation/
│   └── xasthur/
├── build_08_bilskirnir_shorts.py # Builders individuais por episódio
├── build_09_violet_cold_shorts.py
├── build_10_mizmor_shorts.py
├── ...
├── build_17_sacred_son_shorts.py
├── output/                       # Metadados e textos de publicação dos 17 episódios
│   ├── 01_Abyssic_Hate_post_info.txt
│   ├── ...
│   └── 17_Sacred_Son_post_info.txt
├── enviar_pendencias.bat         # Executável para envio em lote das pendências
├── uploader.py                   # Script de upload via YouTube Data API v3
├── narrator.py                   # Módulo de narração ElevenLabs / TTS
├── upload_queue.json             # Fila de pendências de upload
├── uploaded_history.json         # Histórico de uploads com URLs definitivas
├── requirements.txt              # Dependências do projeto
├── .env.example                  # Template de variáveis de ambiente
├── .gitignore                    # Regras de exclusão de mídias, temporários e credenciais
├── LICENSE                       # Licença MIT
└── README.md
```

---

## 🚀 Como Começar

### Pré-requisitos
- **Python 3.10+**
- **FFmpeg** instalado e adicionado ao `PATH` do sistema ([Guia de Instalação do FFmpeg](https://ffmpeg.org/download.html)).
- Conexão com a internet para download de áudio e síntese de voz.

### 1. Clonar o Repositório
```bash
git clone https://github.com/ChrysthianChrisley/OMBSpotlight.git
cd OMBSpotlight
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente (Opcional)
Copie o arquivo de exemplo e insira suas credenciais caso deseje utilizar ElevenLabs ou rotas personalizadas:
```bash
cp .env.example .env
```

---

## 🛠️ Como Usar

### 1. Gerar um Episódio
Para gerar qualquer episódio, execute seu respectivo builder:
```bash
python build_17_sacred_son_shorts.py
```
O script fará o download do áudio, corte das faixas, síntese de voz, renderização dos clipes 1080x1920, concatenação final e salvará:
- Vídeo: `output/17_Sacred_Son_Shorts_9x16.mp4`
- Metadados: `output/17_Sacred_Son_post_info.txt`
- Registro na fila: `upload_queue.json`

### 2. Enviar para o YouTube
#### No Windows (2 Cliques):
Basta dar dois cliques no arquivo:
👉 `enviar_pendencias.bat`

#### Pelo Terminal:
```bash
python uploader.py --upload-pending
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja [`LICENSE`](LICENSE) para mais informações.
