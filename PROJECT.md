# Neko History — POV History Through a Cat's Eyes

## Concept
AI-generated POV history videos featuring a cat character who "time travels" to historical Asian events. Two channels:
- **Channel 1:** Cat in Old Japan (Edo, Sengoku, Heian, Meiji)
- **Channel 2:** Cat in Ancient China (Tang, Song, Ming, Qing)

English narration. Deadpan/sarcastic cat personality. Educational + comedic tone.

## Revenue Target
$5,000/month combined across both channels.

## Revenue Strategy
| Stream | When It Kicks In | Expected |
|--------|-----------------|----------|
| YouTube long-form ads | After YPP (1K subs + 4K watch hours) | $2K-8K/mo at scale |
| Sponsorships | After 20-50K subs | $500-2K per video |
| Affiliate links (books, courses) | Day 1 | $100-500/mo |
| TikTok Creator Fund | After 10K followers | $500-2K/mo |
| Merch (cat character) | After brand is established | $500-2K/mo |

## Content Format

### Short-form (60-90 sec) — Daily
- TikTok + Instagram Reels + YouTube Shorts
- Single scene, one historical moment
- Hook → scene → punchline/fact
- Purpose: audience growth funnel

### Long-form (8-15 min) — 2-3x/week
- YouTube main channel
- Multiple scenes stitched together
- Deep dive into a period/event
- Purpose: where the ad revenue lives

---

# Automated Production Pipeline

## Overview
```
[Topic Selection] → [Script Gen] → [Voice Gen] → [Video Gen] → [Stitch + Edit] → [Publish]
     Claude            Claude API     ElevenLabs     Seedance/Kling    ffmpeg        Multi-platform API
```

## Phase 1: Foundation (Week 1-2)

### 1.1 Character Design
- [ ] Design the cat character (calico? tabby? lucky cat style?)
- [ ] Generate 8-10 reference images in different poses/angles using Midjourney
- [ ] Lock character identity for video generation consistency
- [ ] Name the cat, define personality traits and catchphrases
- [ ] Create channel branding (logo, banner, color palette)

### 1.2 Voice Identity
- [ ] Clone or select a voice on ElevenLabs for the cat narrator
- [ ] Decide tone: deadpan sarcastic? curious explorer? dramatic storyteller?
- [ ] Test voice with sample scripts, iterate until it feels right
- [ ] Save voice_id for pipeline automation

### 1.3 Accounts & API Keys
- [ ] Create YouTube channels (x2: Japan + China)
- [ ] Create TikTok accounts (x2)
- [ ] Create Instagram accounts (x2)
- [ ] Sign up for API access:
  - Claude API (script generation)
  - ElevenLabs API (voice)
  - Seedance 2.0 via fal.ai or BytePlus (video generation)
  - Kling API via PiAPI (backup video gen)
  - YouTube Data API v3 (upload)
  - TikTok Content Posting API
  - Instagram Graph API (Reels upload)

## Phase 2: Pipeline Build (Week 2-4)

### 2.1 Script Generator (`scripts/generate_script.py`)
- Input: historical topic, format (short/long), channel (japan/china)
- Uses Claude API to generate:
  - Hook line (first 3 seconds caption)
  - Narration script (cat's voice)
  - Scene descriptions (for video generation prompts)
  - Historical facts to include
  - Hashtags and caption
- Output: structured JSON with all components

### 2.2 Voice Generator (`scripts/generate_voice.py`)
- Input: narration text from script
- Uses ElevenLabs API (Multilingual v2 model)
- Output: .mp3 narration file
- Handles: timing, pacing, emotional markers

### 2.3 Video Generator (`scripts/generate_video.py`)
- Input: scene descriptions from script + character reference images
- Uses Seedance 2.0 API (primary) or Kling 3.0 API (fallback)
- Generates: individual scene clips (5-8 seconds each)
- Prompt formula: "handheld POV, [cat character ref], hyper-realistic [historical setting], cinematic atmosphere, [specific scene action]"
- Output: multiple .mp4 clip files per video

### 2.4 Video Assembler (`scripts/assemble_video.py`)
- Input: voice .mp3 + video clips .mp4 + captions
- Uses ffmpeg to:
  - Stitch clips in sequence
  - Overlay narration audio
  - Add captions/subtitles (burned in for Shorts/Reels)
  - Add background ambient audio
  - Add intro/outro branding
- Output: final .mp4 ready to upload

### 2.5 Publisher (`scripts/publish.py`)
- Input: final .mp4 + metadata (title, description, tags, hashtags)
- Uploads to all platforms via their APIs:
  - YouTube (Shorts or long-form, scheduled)
  - TikTok (with platform-specific caption)
  - Instagram Reels (via Graph API)
- Handles: scheduling, rate limits, error retries
- Logs: upload status, URLs, publish times

### 2.6 Orchestrator (`scripts/pipeline.py`)
- Master script that chains all steps
- Input: topic + format
- Runs: script → voice → video → assemble → publish
- Error handling at each stage
- Saves all artifacts to organized output directory
- Can run in batch mode (generate N videos at once)

## Phase 3: Content Library (Week 3-5)

### 3.1 Topic Database (`data/topics.json`)
Pre-researched topics organized by:
- Channel (japan / china)
- Era (e.g., edo, sengoku, tang, ming)
- Category (daily_life, battle, culture, food, fashion, disaster, invention)
- Viral potential score (1-5)
- Difficulty to visualize (1-5)

### 3.2 Initial Content Plan — Japan Channel
| # | Topic | Era | Hook |
|---|-------|-----|------|
| 1 | A day as a cat in Edo-period Tokyo | Edo | "POV: You're a stray cat in 1800s Tokyo" |
| 2 | Watching samurai commit seppuku | Sengoku | "POV: Your owner just lost a battle" |
| 3 | The Great Fire of Meireki (1657) | Edo | "POV: You smell smoke and it's not the kitchen" |
| 4 | Cat cafes origin — cats on ships | Various | "POV: You're a ship cat on a trade vessel to Japan" |
| 5 | Ninja training from a cat's perspective | Sengoku | "POV: The humans think they're stealthy" |
| 6 | Hiroshima morning, Aug 6 1945 | Showa | "POV: It's a normal morning in Hiroshima" |
| 7 | Arrival of Perry's Black Ships | Bakumatsu | "POV: There's a giant metal thing in the harbor" |
| 8 | Life in a geisha house | Edo | "POV: You live in Kyoto's fanciest tea house" |
| 9 | The 47 Ronin revenge | Edo | "POV: Your owner's been planning something for 2 years" |
| 10 | Earthquake and tsunami (1923) | Taisho | "POV: The ground won't stop shaking" |

### 3.3 Initial Content Plan — China Channel
| # | Topic | Era | Hook |
|---|-------|-----|------|
| 1 | Walking the Great Wall during construction | Qin | "POV: They've been building this wall for 10 years" |
| 2 | A day in Chang'an (Tang Dynasty) | Tang | "POV: You live in the world's largest city" |
| 3 | Zheng He's treasure fleet departure | Ming | "POV: That ship is bigger than your entire village" |
| 4 | The fall of the last emperor | Qing | "POV: The palace just got very quiet" |
| 5 | Silk Road market day | Han/Tang | "POV: You've never seen so many different humans" |
| 6 | Terracotta Army burial | Qin | "POV: They're burying 8,000 statues and you don't know why" |
| 7 | Invention of gunpowder (accidental) | Tang | "POV: The alchemist just blew up the lab again" |
| 8 | Mongol invasion | Song | "POV: The horses keep getting closer" |
| 9 | Chinese New Year in the Forbidden City | Ming | "POV: The fireworks are MUCH louder up close" |
| 10 | Opium War — British ships arrive | Qing | "POV: Strange ships and the humans look worried" |

## Phase 4: Launch & Growth (Week 4-8)

### 4.1 Launch Strategy
- Pre-produce 10 Shorts per channel before launch
- Post daily Shorts for first 30 days (use scheduler)
- Start long-form after first 500 subscribers
- Cross-promote Japan ↔ China channels
- Engage with history and cat communities

### 4.2 Posting Schedule
| Day | Japan Channel | China Channel |
|-----|--------------|---------------|
| Mon | Short + Long-form | Short |
| Tue | Short | Short + Long-form |
| Wed | Short | Short |
| Thu | Short + Long-form | Short |
| Fri | Short | Short + Long-form |
| Sat | Short | Short |
| Sun | Short | Short |

### 4.3 Growth Tactics
- Comment on popular history channels
- Reddit posts in r/history, r/japan, r/china, r/cats
- Collab with other AI/history creators
- Trending historical events (anniversaries, new discoveries)
- "Part 2" cliffhangers to drive subscriptions

---

# Cost Breakdown

## Monthly Fixed Costs
| Service | Plan | Cost/mo |
|---------|------|---------|
| Claude API | Pay-per-use | ~$20 |
| ElevenLabs | Starter | $5 |
| Seedance 2.0 (fal.ai) | Pay-per-use | ~$30-60 |
| Kling (backup) | Pro | $26 |
| Midjourney | Basic | $10 |
| Upload-Post or similar | Scheduling | $10-20 |
| **Total** | | **~$100-140/mo** |

## Per-Video Cost (Short-form, 60 sec)
| Component | Cost |
|-----------|------|
| Script (Claude API) | $0.05 |
| Voice (ElevenLabs) | $0.10 |
| Video gen (Seedance, ~12 clips) | $0.60-1.20 |
| Ambient audio | $0 (royalty-free) |
| **Total per Short** | **~$0.75-1.35** |

## Per-Video Cost (Long-form, 10 min)
| Component | Cost |
|-----------|------|
| Script (Claude API) | $0.15 |
| Voice (ElevenLabs) | $0.50 |
| Video gen (Seedance, ~60 clips) | $3.00-6.00 |
| Ambient audio | $0 |
| **Total per Long-form** | **~$3.65-6.65** |

## Monthly Production Cost (at full schedule)
- 14 Shorts/week × 4 = 56 Shorts → $42-76
- 4 Long-forms/week × 4 = 16 Long-forms → $58-106
- **Total production: ~$100-180/mo**
- **Total with tools: ~$200-320/mo**

---

# Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Language | Python 3.12+ | Best API ecosystem, ffmpeg bindings |
| Script gen | Claude API (Sonnet) | Best creative writing for cost |
| Voice | ElevenLabs API | Best TTS quality, voice cloning |
| Video gen (primary) | Seedance 2.0 via fal.ai | Cheapest per-second, best physics |
| Video gen (backup) | Kling 3.0 via PiAPI | Proven quality, good character consistency |
| Character images | Midjourney | Best aesthetic quality |
| Video assembly | ffmpeg (via python-ffmpeg) | Industry standard, free |
| Captions | whisper or manual from script | Sync with narration |
| Upload | YouTube Data API v3, TikTok API, IG Graph API | Direct platform APIs |
| Scheduling | Upload-Post.com or custom | Multi-platform scheduling |
| Storage | Local + S3 (optional) | Archive all assets |
| Orchestration | Python + cron or n8n | Batch pipeline runs |

---

# Success Metrics

| Metric | Month 1 | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|---------|----------|
| Subscribers (per ch) | 500 | 5K | 25K | 100K |
| Monthly views | 50K | 500K | 2M | 5M+ |
| Revenue | $0 | $200 | $1.5K | $5K+ |
| Videos produced | 80 | 240 | 480 | 960 |
| Cost | $300 | $300 | $300 | $300 |

---

# Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| YouTube flags AI content | Demonetization | Label as AI, add educational value, narration |
| Character inconsistency | Brand confusion | Lock reference images, test heavily in Phase 1 |
| Copycat channels | Audience split | Move fast, build brand loyalty, unique cat personality |
| API price increases | Higher costs | Multi-provider setup, budget alerts |
| Historical inaccuracy backlash | Reputation damage | Fact-check scripts, add disclaimers |
| Content fatigue | Declining views | Rotate eras, introduce special episodes, audience polls |
