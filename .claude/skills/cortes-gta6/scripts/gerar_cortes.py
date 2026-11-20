#!/usr/bin/env python3
"""
Gera cortes verticais 1080x1920 (9:16) em split-screen a partir de um vídeo de GTA 6.

Layout (sem legendas queimadas — o corte sai limpo):
  - Terço superior   (1080x614):  zoom recortado na facecam do streamer (--cam w:h:x:y)
  - Dois terços inf. (1080x1306): gameplay centralizada

Exemplos:
  python3 gerar_cortes.py --video source.mp4 \
      --cortes 690-765 00:16:09-00:17:35 --cam 480:270:1420:790 --saida ./cortes_prontos/

  python3 gerar_cortes.py --video source.mp4 \
      --cortes-json cortes.json --cam 480:270:1420:790 --saida ./cortes_prontos/

Formato do --cortes-json:
  [{"inicio": 690, "fim": 765, "nome": "transito"}, {"inicio": "00:16:09", "fim": "00:17:35"}]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass

LARGURA = 1080
ALTURA = 1920
ALTURA_CAM = 614
ALTURA_GAME = ALTURA - ALTURA_CAM  # 1306

DURACAO_MIN = 70.0
DURACAO_MAX = 90.0


@dataclass
class Corte:
    inicio: float
    fim: float
    nome: str

    @property
    def duracao(self) -> float:
        return self.fim - self.inicio


# --------------------------------------------------------------------------- utilidades


def parse_tempo(valor) -> float:
    """Aceita segundos (int/float/str) ou HH:MM:SS(.ms) / MM:SS."""
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace(",", ".")
    if ":" not in texto:
        return float(texto)
    segundos = 0.0
    for p in (float(p) for p in texto.split(":")):
        segundos = segundos * 60 + p
    return segundos


def formatar_hms(segundos: float) -> str:
    segundos = max(0.0, segundos)
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = segundos % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto[:60] or "corte"


def parse_intervalo(texto: str) -> tuple[float, float]:
    """'690-765' ou '00:16:09-00:17:35' -> (inicio, fim)"""
    m = re.fullmatch(r"\s*([0-9:.,]+)\s*-\s*([0-9:.,]+)\s*", texto)
    if not m:
        raise ValueError(f"Intervalo inválido: {texto!r} (use INICIO-FIM)")
    return parse_tempo(m.group(1)), parse_tempo(m.group(2))


def parse_cam(texto: str) -> tuple[int, int, int, int]:
    partes = re.split(r"[:x,\s]+", texto.strip())
    if len(partes) != 4:
        raise ValueError(f"--cam inválido: {texto!r} (use w:h:x:y)")
    w, h, x, y = (int(round(float(p))) for p in partes)
    if w <= 0 or h <= 0 or x < 0 or y < 0:
        raise ValueError(f"--cam inválido: {texto!r}")
    return w, h, x, y


def dimensoes_video(caminho: str) -> tuple[int, int, float]:
    saida = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "json", caminho,
        ],
        check=True, capture_output=True, text=True,
    ).stdout
    dados = json.loads(saida)
    stream = dados["streams"][0]
    duracao = float(dados.get("format", {}).get("duration") or 0)
    return int(stream["width"]), int(stream["height"]), duracao


def tem_audio(caminho: str) -> bool:
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", caminho],
        capture_output=True, text=True,
    ).stdout
    return bool(saida.strip())


# --------------------------------------------------------------------------- render


def montar_filtro(cam: tuple[int, int, int, int]) -> str:
    w, h, x, y = cam
    topo = (
        f"[0:v]crop={w}:{h}:{x}:{y},"
        f"scale={LARGURA}:{ALTURA_CAM}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={LARGURA}:{ALTURA_CAM},setsar=1[cam]"
    )
    base = (
        f"[0:v]scale=-2:{ALTURA_GAME}:flags=lanczos,"
        f"crop={LARGURA}:{ALTURA_GAME}:(iw-{LARGURA})/2:0,setsar=1[game]"
    )
    return f"{topo};{base};[cam][game]vstack=inputs=2,format=yuv420p[v]"


def renderizar(args, corte: Corte, indice: int, cam, audio: bool) -> str:
    os.makedirs(args.saida, exist_ok=True)
    nome_arquivo = f"{indice:02d}_{slug(corte.nome)}.mp4"
    destino = os.path.abspath(os.path.join(args.saida, nome_arquivo))

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-y",
        "-ss", f"{corte.inicio:.3f}", "-t", f"{corte.duracao:.3f}", "-i", os.path.abspath(args.video),
        "-filter_complex", montar_filtro(cam),
        "-map", "[v]",
    ]
    if audio:
        cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += [
        "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
        "-profile:v", "high", "-movflags", "+faststart",
        destino,
    ]
    print(f"\n[{indice}] {nome_arquivo}  {formatar_hms(corte.inicio)} -> {formatar_hms(corte.fim)} "
          f"({corte.duracao:.1f}s)")
    subprocess.run(cmd, check=True)
    return destino


# --------------------------------------------------------------------------- main


def carregar_cortes(args) -> list[Corte]:
    cortes: list[Corte] = []
    if args.cortes_json:
        with open(args.cortes_json, encoding="utf-8") as f:
            itens = json.load(f)
        for i, item in enumerate(itens, 1):
            cortes.append(Corte(
                inicio=parse_tempo(item["inicio"]),
                fim=parse_tempo(item["fim"]),
                nome=str(item.get("nome") or item.get("titulo") or f"corte-{i}"),
            ))
    for texto in args.cortes or []:
        ini, fim = parse_intervalo(texto)
        cortes.append(Corte(ini, fim, f"corte-{len(cortes) + 1}"))
    return cortes


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera cortes verticais 9:16 (facecam + gameplay) de GTA 6.")
    ap.add_argument("--video", required=True, help="Vídeo de origem (ex.: ./workspace_cortes/source.mp4)")
    ap.add_argument("--cortes", nargs="*", help="Intervalos INICIO-FIM (segundos ou HH:MM:SS)")
    ap.add_argument("--cortes-json", help="Arquivo JSON com [{inicio, fim, nome}]")
    ap.add_argument("--cam", required=True, help="Recorte da facecam no vídeo original: w:h:x:y")
    ap.add_argument("--saida", default="./cortes_prontos/", help="Pasta de saída")
    ap.add_argument("--crf", type=int, default=20, help="Qualidade x264 (menor = melhor). Padrão: 20")
    ap.add_argument("--preset", default="medium", help="Preset x264. Padrão: medium")
    args = ap.parse_args()

    for ferramenta in ("ffmpeg", "ffprobe"):
        if not shutil.which(ferramenta):
            print(f"Erro: '{ferramenta}' não encontrado no PATH.", file=sys.stderr)
            return 1
    if not os.path.isfile(args.video):
        print(f"Erro: arquivo não encontrado: {args.video}", file=sys.stderr)
        return 1

    try:
        cam = parse_cam(args.cam)
        cortes = carregar_cortes(args)
    except (ValueError, KeyError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    if not cortes:
        print("Erro: informe --cortes e/ou --cortes-json.", file=sys.stderr)
        return 1

    largura, altura, duracao_total = dimensoes_video(args.video)
    w, h, x, y = cam
    if x + w > largura or y + h > altura:
        print(f"Erro: --cam {args.cam} sai do quadro do vídeo ({largura}x{altura}).", file=sys.stderr)
        return 1

    validos: list[Corte] = []
    for c in cortes:
        if duracao_total and c.fim > duracao_total:
            c.fim = duracao_total
        if c.fim <= c.inicio:
            print(f"Aviso: corte '{c.nome}' ignorado (fim <= início).", file=sys.stderr)
            continue
        if not (DURACAO_MIN <= c.duracao <= DURACAO_MAX):
            print(f"Aviso: corte '{c.nome}' tem {c.duracao:.1f}s (regra: {DURACAO_MIN:.0f}-{DURACAO_MAX:.0f}s).",
                  file=sys.stderr)
        validos.append(c)

    audio = tem_audio(args.video)

    gerados = []
    for i, c in enumerate(validos, 1):
        try:
            gerados.append((renderizar(args, c, i, cam, audio), c))
        except subprocess.CalledProcessError as e:
            print(f"Erro ao renderizar '{c.nome}': ffmpeg saiu com código {e.returncode}", file=sys.stderr)

    print("\nCortes prontos:")
    for caminho, c in gerados:
        print(f"  {caminho}  ({formatar_hms(c.inicio)} -> {formatar_hms(c.fim)}, {c.duracao:.1f}s)")
    return 0 if len(gerados) == len(validos) else 2


if __name__ == "__main__":
    sys.exit(main())
