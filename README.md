# blu-reels

Generador de Reels para Blue Travel: gancho en pantalla, subtítulos grandes y Blu la maleta con la boca sincronizada al audio.

- `draw_blu.py` dibuja a Blu (`blu_closed.png`, `blu_open.png`).
- `make_reel.py` arma el Reel con ffmpeg a partir de un video de fondo, un audio, el gancho y las frases.
- `voices_test.py` + `.github/workflows/probar-voces.yml` generan muestras de voz con Kokoro (gratis, corre en GitHub Actions).

No guardes claves ni datos de clientes en este repositorio: es público.
