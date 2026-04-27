# Mochi CLI

AI-powered POV history video production agent. A cat named Mochi time-travels through ancient Japan and China.

Based on [this workflow](https://www.youtube.com/watch?v=F2dyaOk-deQ).

## Workflow

```
mochi produce "The Great Fire of Meireki 1657" -c japan -f long
```

```
Topic → ChatGPT (script) → Nano Banana 2 (images) → Kling 3.0 (video+audio) → ffmpeg (stitch)
```

**No API keys required.** Everything is copy-paste into web UIs.

## Commands

| Step | Command | What it does |
|------|---------|-------------|
| 1 | `mochi script <topic> -c japan` | Generates a prompt to paste into ChatGPT |
| 2 | `mochi load-script response.json -c japan` | Loads ChatGPT's JSON response |
| 3 | `mochi images script.json` | Prints prompts for Higgsfield Nano Banana 2 |
| 4 | `mochi clips script.json` | Prints prompts for Higgsfield Kling 3.0 |
| 5 | `mochi assemble script.json` | Stitches clips + adds top label (ffmpeg) |

## Setup

```bash
git clone https://github.com/shiki4709/neko-history.git
cd neko-history
pip install -e .
brew install ffmpeg
```

## Tools Needed

| Tool | Cost | What for |
|------|------|----------|
| ChatGPT | Free | Script generation (paste prompt into website) |
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
