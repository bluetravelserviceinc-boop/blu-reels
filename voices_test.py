"""Genera muestras del mismo texto con las voces en español de Kokoro, más una mezcla."""
import os
import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline

TEXTO = ("Hola, soy Blu, la maleta de Blue Travel. ¿Sueñas con el Caribe? "
         "Cancún y Punta Cana te esperan. Escríbenos por WhatsApp.")

os.makedirs("salida", exist_ok=True)
pipe = KPipeline(lang_code="e")


def sintetizar(voz, nombre, velocidad=1.0):
    trozos = []
    for r in pipe(TEXTO, voice=voz, speed=velocidad):
        audio = r.audio if hasattr(r, "audio") else r[2]
        trozos.append(torch.as_tensor(audio))
    onda = torch.cat(trozos).numpy().astype(np.float32)
    sf.write(f"salida/{nombre}.wav", onda, 24000)
    print("listo:", nombre, f"{len(onda) / 24000:.1f}s")


for voz in ("ef_dora", "em_alex", "em_santa"):
    try:
        sintetizar(voz, voz)
    except Exception as e:
        print("fallo", voz, e)

try:
    mezcla = (pipe.load_voice("ef_dora") + pipe.load_voice("em_alex")) / 2
    sintetizar(mezcla, "mezcla_dora_alex")
except Exception as e:
    print("fallo la mezcla:", e)
