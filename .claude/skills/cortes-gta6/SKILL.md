---
name: cortes-gta6
description: Gera cortes verticais (9:16) virais de lives/vídeos de GTA 6 a partir de um link. Use quando o usuário enviar um link de vídeo (YouTube, Twitch, Kick etc.) e pedir cortes, shorts, reels ou TikToks de GTA 6 — baixa o vídeo, transcreve com Whisper, escolhe os melhores momentos e renderiza split-screen (facecam + gameplay) com legendas palavra por palavra.
allowed-tools: Bash, Read, Write
---

# Cortes GTA 6

Transforma um vídeo/live de GTA 6 em 3 a 5 cortes verticais prontos para TikTok, YouTube Shorts e Reels.

Formato final de cada corte (`1080x1920`, 9:16):

| Área | Tamanho | Conteúdo |
|---|---|---|
| Terço superior | `1080x614` | Zoom recortado na facecam do streamer |
| Dois terços inferiores | `1080x1306` | Gameplay de GTA 6 centralizada |
| Legenda | sobre o terço inferior | Palavra por palavra, CAIXA ALTA, Arial Black 82, amarelo `&H0000E6FF`, contorno preto grosso |

Todos os arquivos de trabalho ficam em `./workspace_cortes/` e os vídeos finais em `./cortes_prontos/`.

## Pré-requisitos

Antes de começar, confira se as ferramentas estão instaladas:

```bash
command -v ffmpeg ffprobe yt-dlp whisper
```

Se alguma estiver faltando, pare e mostre ao usuário as instruções do `README.md` na raiz do repositório.

## Fluxo de trabalho (quando o usuário enviar um link)

### a) Baixar o vídeo (até 1080p, MP4)

```bash
mkdir -p ./workspace_cortes ./cortes_prontos
yt-dlp \
  -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/bv*[height<=1080]+ba/b" \
  --merge-output-format mp4 \
  -o "./workspace_cortes/source.mp4" \
  "<LINK_DO_VIDEO>"
```

Se `source.mp4` já existir de um link anterior, apague a pasta `./workspace_cortes/` antes (confirme com o usuário se ela tiver conteúdo de outro vídeo).

Confira resolução e duração:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height:format=duration -of default=nw=1 ./workspace_cortes/source.mp4
```

### b) Transcrever com Whisper

```bash
whisper ./workspace_cortes/source.mp4 \
  --language pt --model small \
  --word_timestamps True \
  --output_format json \
  --output_dir ./workspace_cortes
```

Isso gera `./workspace_cortes/source.json` com `segments[].words[]` (`word`, `start`, `end`). Vídeos longos demoram; rode em segundo plano se precisar e avise o usuário.

### c) Escolher de 3 a 5 momentos

Leia o JSON (use `python3` para resumir os segmentos com timestamps em vez de abrir o arquivo inteiro se ele for grande):

```bash
python3 -c "
import json
d = json.load(open('./workspace_cortes/source.json', encoding='utf-8'))
for s in d['segments']:
    print(f\"{s['start']:8.1f}-{s['end']:8.1f} | {s['text'].strip()}\")
" > ./workspace_cortes/transcricao.txt
```

Procure **3 a 5** trechos com:

- momentos engraçados, zoeira, piadas, risadas (`kkkk`, "mano", "não acredito");
- reações intensas: gritos, sustos, palavrões, "MEU DEUS", silêncio seguido de explosão;
- destaques de GTA 6: perseguições, mortes absurdas, bugs, descobertas do mapa, missões épicas, Lucia/Jason, Vice City.

Regras de cada corte:

- duração **entre 30 s e 55 s**;
- começar um pouco antes do gancho (1–3 s) e terminar logo após o desfecho/punchline — nunca no meio de uma frase;
- sem sobreposição entre cortes.

Salve a seleção em `./workspace_cortes/cortes.json`:

```json
[
  {"inicio": 312.4, "fim": 356.0, "nome": "perseguicao-policia", "motivo": "Fuga absurda com reação gritando"},
  {"inicio": "00:21:05", "fim": "00:21:47", "nome": "bug-carro-voando"}
]
```

`inicio`/`fim` aceitam segundos ou `HH:MM:SS(.ms)`. `nome` vira o nome do arquivo (sem acentos/espaços).

### d) Localizar a facecam

Extraia um frame de exemplo:

```bash
ffmpeg -y -ss 00:05:00 -i ./workspace_cortes/source.mp4 -vframes 1 ./workspace_cortes/frame.jpg
```

(Se o vídeo tiver menos de 5 minutos, use um tempo dentro de um dos cortes escolhidos.)

Abra `./workspace_cortes/frame.jpg` com a ferramenta **Read** e inspecione a imagem para achar a webcam do streamer. Defina as coordenadas no formato do filtro `crop` do FFmpeg, **em pixels da resolução original** do vídeo (a do `ffprobe`):

```
w:h:x:y   →  largura:altura:x_canto_superior_esquerdo:y_canto_superior_esquerdo
```

Dicas:

- Recorte só a câmera, sem bordas/overlay. A proporção ideal é próxima de `1080:614` (~1.76); o script completa o resto com zoom/crop central.
- Para confirmar, gere uma prévia do recorte e abra com Read:
  ```bash
  ffmpeg -y -ss 00:05:00 -i ./workspace_cortes/source.mp4 -vframes 1 -vf "crop=W:H:X:Y" ./workspace_cortes/cam_check.jpg
  ```
  Ajuste até a câmera ficar bem enquadrada.
- Se o vídeo não tiver facecam, avise o usuário e pergunte qual área usar no topo (ou use `--cam` apontando para um trecho interessante do HUD/gameplay).

### e) Gerar os cortes

```bash
python3 .claude/skills/cortes-gta6/scripts/gerar_cortes.py \
  --video ./workspace_cortes/source.mp4 \
  --transcricao ./workspace_cortes/source.json \
  --cortes-json ./workspace_cortes/cortes.json \
  --cam "W:H:X:Y" \
  --saida ./cortes_prontos/
```

Também é possível passar os intervalos direto na linha de comando: `--cortes 312.4-356 00:21:05-00:21:47`.

Opções úteis: `--crf 20` (qualidade), `--preset medium`, `--fontsdir <pasta>` (se a Arial Black não estiver instalada no sistema), `--manter-ass` (guarda o `.ass` de cada corte).

Depois de gerar, extraia um frame do primeiro corte e abra com Read para conferir o layout (câmera em cima, gameplay embaixo, legenda amarela legível):

```bash
ffmpeg -y -ss 5 -i ./cortes_prontos/<arquivo>.mp4 -vframes 1 ./workspace_cortes/preview.jpg
```

### f) Entregar ao usuário

Liste os arquivos em `./cortes_prontos/` e, para cada corte, apresente:

- arquivo, intervalo original (`HH:MM:SS → HH:MM:SS`) e duração;
- resumo de 1 linha do que acontece;
- **3 sugestões de título viral** (curtos, com gancho, em PT-BR, ex.: "ELE NÃO ESPERAVA ISSO NO GTA 6 😭");
- **hashtags** para TikTok/Shorts, misturando amplas e de nicho, ex.: `#gta6 #gtavi #gta #vicecity #gameplay #cortes #humor #shorts #fyp #viral`.

Formato sugerido:

```
1. cortes_prontos/01_perseguicao-policia.mp4  (00:05:12 → 00:05:56, 44s)
   O que rola: ...
   Títulos:
   - ...
   - ...
   - ...
   Hashtags: #gta6 #...
```
