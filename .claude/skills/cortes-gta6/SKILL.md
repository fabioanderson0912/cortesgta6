---
name: cortes-gta6
description: Gera cortes verticais (9:16) virais de lives/vídeos de GTA 6 a partir de um link. Use quando o usuário enviar um link de vídeo (YouTube, Twitch, Kick etc.) e pedir cortes, shorts, reels ou TikToks de GTA 6 — baixa o vídeo, escolhe os melhores momentos (70–90 s) e renderiza split-screen limpo (facecam + gameplay), sem legendas queimadas.
allowed-tools: Bash, Read, Write
---

# Cortes GTA 6

Transforma um vídeo/live de GTA 6 em 3 a 5 cortes verticais prontos para TikTok, YouTube Shorts e Reels.

Formato final de cada corte (`1080x1920`, 9:16), **limpo, sem legendas queimadas**:

| Área | Tamanho | Conteúdo |
|---|---|---|
| Terço superior | `1080x614` | Zoom recortado na facecam do streamer |
| Dois terços inferiores | `1080x1306` | Gameplay de GTA 6 centralizada |

Não use Whisper nem gere arquivos `.ass`/legendas. Todos os arquivos de trabalho ficam em `./workspace_cortes/` e os vídeos finais em `./cortes_prontos/`.

## Pré-requisitos

```bash
command -v ffmpeg ffprobe yt-dlp
```

Se alguma estiver faltando, pare e mostre ao usuário as instruções do `README.md` na raiz do repositório. No Windows, `python3` pode ser só o atalho da Microsoft Store; nesse caso use `python`.

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

### b) Escolher de 3 a 5 momentos

Se o usuário já informou os intervalos, use-os direto e pule para a etapa (c).

Caso contrário, use fontes leves (sem transcrever o áudio localmente):

1. **Legenda automática do YouTube** (quando houver):
   ```bash
   yt-dlp --skip-download --write-auto-sub --sub-lang pt --sub-format vtt \
     -o "./workspace_cortes/legenda" "<LINK_DO_VIDEO>"
   ```
   Leia o `.vtt` gerado procurando reações e falas fortes.
2. **"Mais repetidos" do YouTube** (heatmap), quando disponível:
   ```bash
   yt-dlp -J --skip-download "<LINK_DO_VIDEO>" > ./workspace_cortes/info.json
   ```
   O campo `heatmap` (lista de `start_time`, `end_time`, `value`) aponta os trechos mais assistidos.
3. **Inspeção visual**: monte grades de frames de trechos candidatos e abra com Read para confirmar a ação.

Procure trechos com:

- momentos engraçados, zoeira, piadas, risadas;
- reações intensas: gritos, sustos, palavrões, "MEU DEUS";
- destaques de GTA 6: perseguições, mortes absurdas, bugs, descobertas do mapa, missões épicas, Lucia/Jason, Vice City.

Regras de cada corte:

- duração **entre 70 s e 90 s** (mínimo de 1 min 10 s);
- começar um pouco antes do gancho (1–3 s) e terminar logo após o desfecho/punchline — nunca no meio de uma frase;
- sem sobreposição entre cortes.

Salve a seleção em `./workspace_cortes/cortes.json`:

```json
[
  {"inicio": 690, "fim": 765, "nome": "transito-realista", "motivo": "Streamer surtando no engarrafamento"},
  {"inicio": "00:16:09", "fim": "00:17:35", "nome": "porcos"}
]
```

`inicio`/`fim` aceitam segundos ou `HH:MM:SS(.ms)`. `nome` vira o nome do arquivo (sem acentos/espaços).

### c) Localizar a facecam

Extraia um frame de exemplo:

```bash
ffmpeg -y -ss 00:05:00 -i ./workspace_cortes/source.mp4 -vframes 1 ./workspace_cortes/frame.jpg
```

(Se o vídeo tiver menos de 5 minutos, use um tempo dentro de um dos cortes escolhidos.)

Abra `./workspace_cortes/frame.jpg` com a ferramenta **Read** e ache a webcam do streamer. Defina as coordenadas no formato do filtro `crop` do FFmpeg, **em pixels da resolução original** do vídeo:

```
w:h:x:y   →  largura:altura:x_canto_superior_esquerdo:y_canto_superior_esquerdo
```

Dicas:

- Recorte só a câmera, sem bordas/overlay. A proporção ideal é próxima de `1080:614` (~1.76); o script completa o resto com zoom/crop central.
- Para confirmar, gere uma prévia do recorte e abra com Read:
  ```bash
  ffmpeg -y -ss 00:05:00 -i ./workspace_cortes/source.mp4 -vframes 1 -vf "crop=W:H:X:Y" ./workspace_cortes/cam_check.jpg
  ```
- Se o vídeo não tiver facecam, avise o usuário e pergunte qual área usar no topo.

### d) Gerar os cortes

```bash
python3 .claude/skills/cortes-gta6/scripts/gerar_cortes.py \
  --video ./workspace_cortes/source.mp4 \
  --cortes-json ./workspace_cortes/cortes.json \
  --cam "W:H:X:Y" \
  --saida ./cortes_prontos/
```

Também é possível passar os intervalos direto: `--cortes 690-765 00:16:09-00:17:35`.

Opções: `--crf 20` (qualidade), `--preset medium`. O script avisa se algum corte estiver fora de 70–90 s.

Depois de gerar, extraia um frame do primeiro corte e abra com Read para conferir o layout (câmera em cima, gameplay embaixo):

```bash
ffmpeg -y -ss 5 -i ./cortes_prontos/<arquivo>.mp4 -vframes 1 ./workspace_cortes/preview.jpg
```

### e) Entregar ao usuário

Liste os arquivos em `./cortes_prontos/` e, para cada corte, apresente:

- arquivo, intervalo original (`HH:MM:SS → HH:MM:SS`) e duração;
- resumo de 1 linha do que acontece;
- **3 sugestões de título viral** (curtos, com gancho, em PT-BR, ex.: "ELE NÃO ESPERAVA ISSO NO GTA 6 😭");
- **hashtags** para TikTok/Shorts, misturando amplas e de nicho, ex.: `#gta6 #gtavi #gta #vicecity #gameplay #cortes #humor #shorts #fyp #viral`.

Formato sugerido:

```
1. cortes_prontos/01_transito-realista.mp4  (00:11:30 → 00:12:45, 75s)
   O que rola: ...
   Títulos:
   - ...
   - ...
   - ...
   Hashtags: #gta6 #...
```
