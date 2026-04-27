# Mochi CLI

AI-powered POV history video production agent. A cat named Mochi time-travels through ancient Japan and China.

Based on [this workflow](https://www.youtube.com/watch?v=F2dyaOk-deQ).

## Workflow

```
mochi produce "The Great Fire of Meireki 1657" -c japan -f long
```

```
Topic → Script (GPT-4o) → Image prompts (Nano Banana 2) → Video prompts (Kling 3.0) → Stitch (ffmpeg)
```

## How It Works

| Step | Tool | What happens |
|------|------|-------------|
| `mochi script` | GPT-4o | Generates scene-by-scene script with image + video prompts |
| `mochi images` | Higgsfield (Nano Banana 2) | Prints prompts to paste — generates scene images (9:16, 2K) |
| `mochi clips` | Higgsfield (Kling 3.0) | Prints prompts to paste — generates video with dialogue (audio ON, 1080p) |
| `mochi assemble` | ffmpeg | Stitches clips + adds top label overlay |
| `mochi produce` | All of the above | Full pipeline |

Kling 3.0 generates the voice/dialogue directly — no separate TTS needed.

## Setup

```bash
git clone https://github.com/shiki4709/neko-history.git
cd neko-history
pip install -e .
brew install ffmpeg
export OPENAI_API_KEY="your-key"
```

## Tools Needed

| Tool | Cost | What for |
|------|------|----------|
| OpenAI API (GPT-4o) | Pay-per-use (~$0.05/script) | Script generation |
| Higgsfield | $15-34/mo | Images (Nano Banana 2) + Video (Kling 3.0) |
| ffmpeg | Free | Stitch clips |
| DaVinci Resolve | Free | Captions (optional) |
| Instagram Edits app | Free | Final polish (optional) |

## Higgsfield Settings

| Setting | Value |
|---------|-------|
| Image model | Nano Banana 2 |
| Image aspect ratio | 9:16 |
| Image resolution | 2K |
| Video model | Kling 3.0 |
| Enhanced | **OFF** |
| Audio | **ON** |
| Video resolution | 1080p |
| Video duration | 10-15 seconds |
| Multi-shot | Custom (up to 5 shots per generation) |

## The Character

**Mochi** — a realistic orange tabby cat. Dramatic survivor personality. Overreacts to everything, then plays it cool. Time-travels through ancient Japan and China.
