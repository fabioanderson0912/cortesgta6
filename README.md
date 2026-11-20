# Cortes GTA 6

Skill do Claude Code (`.claude/skills/cortes-gta6/`) que transforma um link de live/vídeo de GTA 6 em 3 a 5 cortes verticais (1080x1920, 9:16) prontos para TikTok, YouTube Shorts e Reels:

- **Terço superior (1080x614):** zoom na facecam do streamer
- **Dois terços inferiores (1080x1306):** gameplay centralizada
- **Legendas dinâmicas:** palavra por palavra, CAIXA ALTA, Arial Black 82, amarelo com contorno preto

## Como usar

Abra o Claude Code na raiz deste repositório e envie o link do vídeo, por exemplo:

```
/cortes-gta6 https://www.youtube.com/watch?v=XXXXXXXX
```

(ou só "faz cortes desse vídeo: <link>"). O Claude baixa o vídeo, transcreve, escolhe os momentos, encontra a webcam e gera os arquivos em `./cortes_prontos/`, com sugestões de títulos e hashtags.

Para rodar o script manualmente:

```bash
python3 .claude/skills/cortes-gta6/scripts/gerar_cortes.py \
  --video ./workspace_cortes/source.mp4 \
  --transcricao ./workspace_cortes/source.json \
  --cortes 312-356 00:21:05-00:21:47 \
  --cam 480:270:1420:790 \
  --saida ./cortes_prontos/
```

`--cam` é o recorte da webcam no vídeo original, no formato `largura:altura:x:y`. Rode com `--help` para ver todas as opções.

## Instalação das dependências

Você precisa de **Python 3.9+**, **FFmpeg**, **yt-dlp** e **openai-whisper**.

### 1. FFmpeg

O FFmpeg precisa ter suporte a `libass` (para as legendas) e `libx264`. As versões dos gerenciadores abaixo já trazem os dois.

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

### 3. openai-whisper

```bash
python3 -m pip install -U openai-whisper
```

O Whisper usa PyTorch. Na primeira execução ele baixa o modelo `small` (~460 MB). Em uma GPU NVIDIA com CUDA a transcrição fica bem mais rápida; para isso, instale antes o PyTorch com CUDA seguindo as instruções de https://pytorch.org/get-started/locally/.

Teste:

```bash
whisper --help
```

> Dica: use um ambiente virtual (`python3 -m venv .venv` e depois `source .venv/bin/activate`; no Windows, `.venv\Scripts\activate`) antes dos `pip install`.

### 4. Fonte Arial Black

As legendas usam **Arial Black**. Ela já vem no Windows e no macOS. No Linux:

```bash
sudo apt install -y ttf-mscorefonts-installer && fc-cache -f
```

Se a fonte não estiver instalada, o FFmpeg usa outra fonte no lugar. Também é possível apontar para uma pasta com o `.ttf` usando `--fontsdir`.

## Estrutura

```
.claude/skills/cortes-gta6/
├── SKILL.md                 # fluxo de trabalho seguido pelo Claude
└── scripts/
    └── gerar_cortes.py      # renderização 9:16 com FFmpeg + legendas .ass
workspace_cortes/            # arquivos temporários (vídeo, transcrição, frames)
cortes_prontos/              # cortes finais
```
