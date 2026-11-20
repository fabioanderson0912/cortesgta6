# Cortes GTA 6

Skill do Claude Code (`.claude/skills/cortes-gta6/`) que transforma um link de live/vídeo de GTA 6 em 3 a 5 cortes verticais (1080x1920, 9:16) de 70 a 90 segundos, prontos para TikTok, YouTube Shorts e Reels. Os cortes saem limpos, sem legendas queimadas:

- **Terço superior (1080x614):** zoom na facecam do streamer
- **Dois terços inferiores (1080x1306):** gameplay centralizada

## Como usar

Abra o Claude Code na raiz deste repositório e envie o link do vídeo, por exemplo:

```
/cortes-gta6 https://www.youtube.com/watch?v=XXXXXXXX
```

(ou só "faz cortes desse vídeo: <link>"). O Claude baixa o vídeo, escolhe os momentos, encontra a webcam e gera os arquivos em `./cortes_prontos/`, com sugestões de títulos e hashtags.

Para rodar o script manualmente:

```bash
python3 .claude/skills/cortes-gta6/scripts/gerar_cortes.py \
  --video ./workspace_cortes/source.mp4 \
  --cortes 690-765 00:16:09-00:17:35 \
  --cam 480:270:1420:790 \
  --saida ./cortes_prontos/
```

`--cam` é o recorte da webcam no vídeo original, no formato `largura:altura:x:y`. Rode com `--help` para ver todas as opções.

## Instalação das dependências

Você precisa de **Python 3.9+**, **FFmpeg** e **yt-dlp**.

### 1. FFmpeg

O FFmpeg precisa ter suporte a `libx264`. As versões dos gerenciadores abaixo já trazem.

**Windows** (PowerShell):

```powershell
winget install Gyan.FFmpeg
```

**macOS** ([Homebrew](https://brew.sh)):

```bash
brew install ffmpeg
```

**Ubuntu/Debian:**

```bash
sudo apt update && sudo apt install -y ffmpeg
```

Teste:

```bash
ffmpeg -version
```

### 2. yt-dlp

```bash
python3 -m pip install -U yt-dlp
```

(Também dá para usar `brew install yt-dlp` ou `winget install yt-dlp`.) Mantenha o yt-dlp atualizado: os sites mudam com frequência e versões antigas param de baixar.

## Estrutura

```
.claude/skills/cortes-gta6/
├── SKILL.md                 # fluxo de trabalho seguido pelo Claude
└── scripts/
    └── gerar_cortes.py      # renderização 9:16 com FFmpeg
workspace_cortes/            # arquivos temporários (vídeo, frames)
cortes_prontos/              # cortes finais
```
