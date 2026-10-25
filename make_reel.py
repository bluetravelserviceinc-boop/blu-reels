#!/usr/bin/env python3
"""Reel generator for Blue Travel: on-screen hook, big captions, and Blu with lip-sync.

usage: make_reel.py --bg clip.mp4 --audio voice.wav --hook "Texto" \
       --lines "Linea 1|Linea 2|Linea 3" --out reel.mp4
Only ffmpeg + python stdlib are needed. Captions are timed by text length across the audio.
"""
import argparse, os, subprocess, wave, struct, math

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
BLU_W, BLU_H = 340, 405


def ass_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def wav_info(path):
    with wave.open(path, "rb") as w:
        n, sr, ch, sw = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    assert sw == 2, "use 16-bit wav"
    vals = struct.unpack("<" + "h" * (len(raw) // 2), raw)
    if ch > 1:
        vals = vals[::ch]
    return vals, sr, n / sr


def speech_windows(vals, sr, step=0.06):
    size = int(sr * step)
    rms = []
    for i in range(0, len(vals) - size, size):
        seg = vals[i:i + size]
        rms.append(math.sqrt(sum(v * v for v in seg) / size))
    if not rms:
        return []
    thr = max(rms) * 0.22
    wins, start = [], None
    for k, r in enumerate(rms):
        t = k * step
        if r > thr and start is None:
            start = t
        elif r <= thr and start is not None:
            wins.append((start, t)); start = None
    if start is not None:
        wins.append((start, len(rms) * step))
    merged = []
    for a, b in wins:
        if merged and a - merged[-1][1] < 0.09:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def build_ass(hook, lines, dur, path):
    total = sum(len(l) for l in lines) or 1
    ev, t = [], 0.3
    span = max(dur - 0.6, 1)
    for l in lines:
        d = span * len(l) / total
        ev.append(f"Dialogue: 0,{ass_time(t)},{ass_time(t + d)},Cap,,0,0,0,,{l}")
        t += d
    hook_end = min(2.4, dur)
    ev.insert(0, f"Dialogue: 1,{ass_time(0)},{ass_time(hook_end)},Hook,,0,0,0,,{{\\fad(180,220)}}{hook}")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,DejaVu Sans,74,&H00FFFFFF,&H00FFFFFF,&H00794B12,&H80000000,1,0,0,0,100,100,0,0,1,7,2,2,60,60,640,1
Style: Hook,DejaVu Sans,98,&H0056C9FA,&H00FFFFFF,&H00794B12,&H80000000,1,0,0,0,100,100,0,0,1,9,3,8,60,60,260,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(ev) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--hook", required=True)
    ap.add_argument("--lines", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    vals, sr, dur = wav_info(a.audio)
    wins = speech_windows(vals, sr)
    lines = [l.strip() for l in a.lines.split("|") if l.strip()]
    work = os.path.dirname(os.path.abspath(a.out))
    ass = os.path.join(work, "captions.ass")
    build_ass(a.hook, lines, dur, ass)

    enable = "+".join(f"between(t,{x:.2f},{y:.2f})" for x, y in wins) or "0"
    x, y = W - BLU_W - 30, H - BLU_H - 120
    graph = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[bg];"
        f"[1:v]scale={BLU_W}:{BLU_H}[bc];[2:v]scale={BLU_W}:{BLU_H}[bo];"
        f"[bg][bc]overlay={x}:{y}[v1];"
        f"[v1][bo]overlay={x}:{y}:enable='{enable}'[v2];"
        f"[v2]subtitles={ass}[v]"
    )
    gfile = os.path.join(work, "graph.txt")
    with open(gfile, "w") as f:
        f.write(graph)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-stream_loop", "-1", "-i", a.bg,
           "-i", os.path.join(HERE, "blu_closed.png"),
           "-i", os.path.join(HERE, "blu_open.png"),
           "-i", a.audio,
           "-filter_complex_script", gfile,
           "-map", "[v]", "-map", "3:a", "-t", f"{dur:.2f}",
           "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(f"ok: {a.out} ({dur:.1f}s, {len(wins)} speech segments)")


if __name__ == "__main__":
    main()
