# Mochi CLI

AI-powered POV history video production agent. A cat named Mochi time-travels through ancient Japan and China.

## Workflow

```
mochi produce "The Great Fire of Meireki 1657" -c japan -f long
```

```
Topic → Script (Gemini) → Images (Imagen 3) → Voice (ElevenLabs) → Clips (Veo/Higgsfield) → Final Video (ffmpeg)
```

## Commands

| Command | What it does |
|---------|-------------|
| `mochi script <topic> -c japan` | Generate a script with scene breakdowns |
| `mochi images <script.json>` | Generate scene images from script |
| `mochi voice <script.json>` | Generate Mochi's voiceover |
| `mochi clips <script.json> -e veo` | Generate video clips from images |
| `mochi assemble <script.json>` | Stitch clips + voice into final video |
| `mochi produce <topic> -c japan -f long` | Full pipeline, one command |
| `mochi status` | Show project status and config |

## Setup

```bash
# Clone
git clone https://github.com/shiki4709/neko-history.git
cd neko-history

# Install
pip install -e .

# Configure
cp config/settings.example.yaml config/settings.yaml
# Edit config/settings.yaml with your API keys

# Install ffmpeg (required for assembly)
brew install ffmpeg

# Run
mochi status
mochi script "Samurai cat in Edo period" -c japan -f short
```

## API Keys Needed

| Service | Cost | What for |
|---------|------|----------|
| Google AI Studio | Free | Scripts (Gemini) + images (Imagen 3) + video (Veo 3.1) |
| ElevenLabs | $5/mo | Mochi's voice |
| Higgsfield | $15-34/mo | Higher quality video clips (optional, Veo is free) |

## Project Structure

```
neko-history/
├── src/mochi/
│   ├── cli.py              # CLI entry point
│   ├── config.py           # Config loader
│   ├── models/script.py    # Data models
│   └── services/
│       ├── script_writer.py  # Gemini script generation
│       ├── image_gen.py      # Imagen 3 scene images
│       ├── voice.py          # ElevenLabs TTS
│       ├── video_gen.py      # Veo/Higgsfield clips
│       ├── assembler.py      # ffmpeg stitching
│       └── publisher.py      # YouTube/TikTok/IG upload
├── assets/character/         # Mochi reference images
├── config/                   # API keys (gitignored)
├── data/                     # Topic database, sample scripts
└── output/{japan,china}/     # Generated videos
```

## The Character

**Mochi** — a realistic orange tabby cat. Dramatic survivor personality. Overreacts to everything. Judges historical figures. Gets distracted by food. Time-travels through Asian history and narrates what he sees.
