#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          VOIDFACTS USA - FULL AUTOMATION SYSTEM             ║
║   Research → Script → AI Images → Voiceover → Video → Upload ║
║              100% FREE | UNLIMITED | FOREVER                 ║
╚══════════════════════════════════════════════════════════════╝

HOW TO RUN:
  python main.py once       → Run once immediately (for testing)
  python main.py schedule   → Run on auto-schedule (6:30AM + 11:30PM IST)
  python main.py            → Same as schedule
"""

import os, sys, json, time, asyncio, requests, random
import textwrap, re, shutil
from datetime import datetime
from pathlib import Path
import numpy as np

# ================================================================
#  CONFIGURATION — SET YOUR API KEYS HERE OR IN ENVIRONMENT
# ================================================================
GEMINI_API_KEY    = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_KEY_HERE")
YOUTUBE_CREDS_JSON = os.environ.get("YOUTUBE_CREDENTIALS", "")   # JSON string
OUTPUT_BASE_DIR   = "outputs"

# TTS voice — deep male US English (Edge TTS)
TTS_VOICE         = "en-US-GuyNeural"
TTS_RATE          = "+5%"    # slightly faster
TTS_VOLUME        = "+25%"

# Video settings
IMG_WIDTH, IMG_HEIGHT = 1080, 1920   # 9:16 Shorts

# Dark fact niches to rotate through
TOPICS = [
    "black holes event horizon mysteries",
    "deep sea creatures unknown species",
    "ancient civilizations lost technology",
    "quantum entanglement mind bending facts",
    "human brain unsolved mysteries neuroscience",
    "dark matter dark energy universe",
    "extreme space phenomena neutron stars",
    "time dilation Einstein relativity",
    "multiverse parallel dimensions theory",
    "unexplained historical events mysteries",
    "volcanic eruptions extreme geology",
    "DNA genetics recent discoveries",
]

# ================================================================
#  STEP 1 — RESEARCH TRENDING TOPIC
# ================================================================
def research_topic():
    """Pick a topic and fetch Wikipedia summary for context."""
    import wikipedia
    wikipedia.set_lang("en")

    topic = random.choice(TOPICS)
    print(f"  📌 Topic: {topic}")

    try:
        results = wikipedia.search(topic, results=3)
        if results:
            try:
                page = wikipedia.page(results[0], auto_suggest=False)
                return {
                    "topic": topic,
                    "title": page.title,
                    "content": page.summary[:1500],
                }
            except Exception:
                pass
    except Exception:
        pass

    return {"topic": topic, "title": topic, "content": ""}


# ================================================================
#  STEP 2 — GENERATE SCRIPT USING GEMINI (FREE TIER)
# ================================================================
def generate_script(topic_data: dict) -> dict:
    """Call Gemini 1.5 Flash (free) to write the full video script."""
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    prompt = f"""You are writing a script for a YouTube Shorts dark facts channel called VoidFacts.
Topic: {topic_data['topic']}
Wikipedia reference: {topic_data['content'][:600]}

Create a ~45 second script. Rules:
- English only, dark/mysterious/mind-blowing tone
- Hook must be shocking (start with "What if...", "Scientists discovered...", or "Did you know...")
- 5 short facts — each 1-2 sentences max (easy to speak in 7-8 seconds)
- Strong conclusion

For each fact also write an image_prompt for AI image generation (cinematic dark style).

Return ONLY valid JSON — no markdown, no backticks:
{{
  "title": "SEO YouTube title max 95 characters",
  "description": "Professional SEO description 400-500 words, multiple paragraphs with keywords",
  "hashtags": "#VoidFacts #DarkFacts #Space #Science #Mystery #Shorts #Facts #MindBlowing #Universe #Unknown",
  "hook": "hook sentence here",
  "facts": [
    {{"text": "fact 1 sentence.", "image_prompt": "cinematic dark dramatic space nebula glowing stars volumetric light"}},
    {{"text": "fact 2 sentence.", "image_prompt": "ancient ruins dark mysterious fog torch light cinematic"}},
    {{"text": "fact 3 sentence.", "image_prompt": "deep dark ocean bioluminescent creatures abyss cinematic"}},
    {{"text": "fact 4 sentence.", "image_prompt": "quantum particles energy glow dark background cinematic"}},
    {{"text": "fact 5 sentence.", "image_prompt": "massive black hole accretion disk glowing cinematic dark"}}
  ],
  "conclusion": "powerful concluding sentence here."
}}"""

    resp = model.generate_content(prompt)
    raw = resp.text.strip()
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON block
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse Gemini response:\n{raw[:300]}")


# ================================================================
#  STEP 3 — GENERATE AI IMAGES (Pollinations.ai — COMPLETELY FREE)
# ================================================================
def generate_image(prompt: str, index: int, output_dir: str) -> str:
    """Use Pollinations.ai — no API key, no cost, unlimited."""

    enhanced = (
        f"cinematic dark dramatic {prompt}, "
        "4K ultra detailed, moody dark atmosphere, volumetric god rays, "
        "photorealistic, vertical portrait 9:16"
    )
    seed = random.randint(1000, 99999)
    encoded = requests.utils.quote(enhanced)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={IMG_WIDTH}&height={IMG_HEIGHT}&nologo=true&seed={seed}"
    )

    for attempt in range(3):
        try:
            r = requests.get(url, timeout=90)
            if r.status_code == 200 and len(r.content) > 5000:
                path = f"{output_dir}/img_{index}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                print(f"    ✅ Image {index} generated ({len(r.content)//1024} KB)")
                return path
        except Exception as e:
            print(f"    ⚠️  Image attempt {attempt+1} failed: {e}")
            time.sleep(3)

    print(f"    ⚠️  Using fallback dark image for index {index}")
    return _fallback_image(index, output_dir)


def _fallback_image(index: int, output_dir: str) -> str:
    """Create a dark gradient fallback image with stars."""
    from PIL import Image, ImageDraw

    img_arr = np.zeros((IMG_HEIGHT, IMG_WIDTH, 3), dtype=np.uint8)
    for y in range(IMG_HEIGHT):
        t = y / IMG_HEIGHT
        img_arr[y, :] = [int(3 + t * 12), int(0 + t * 8), int(15 + t * 45)]

    img = Image.fromarray(img_arr)
    draw = ImageDraw.Draw(img)

    # Scatter stars
    rng = random.Random(index * 777)
    for _ in range(300):
        x, y = rng.randint(0, IMG_WIDTH - 1), rng.randint(0, IMG_HEIGHT - 1)
        b = rng.randint(120, 255)
        r_size = rng.randint(0, 1)
        draw.ellipse([x - r_size, y - r_size, x + r_size, y + r_size], fill=(b, b, b))

    path = f"{output_dir}/img_{index}.jpg"
    img.save(path, quality=92)
    return path


# ================================================================
#  STEP 4 — GENERATE VOICEOVER (Microsoft Edge TTS — FREE)
# ================================================================
async def _tts_async(text: str, path: str):
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME)
    await communicate.save(path)


def generate_voiceover(text: str, path: str):
    import edge_tts
    asyncio.run(_tts_async(text, path))


def _tts_async_factory(text, path):
    """Create coroutine — needed for asyncio.run in some environments."""
    import edge_tts
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME)
    return communicate.save(path)


def generate_all_voiceovers(script_data: dict, output_dir: str) -> dict:
    """Generate all audio files and return paths."""
    import edge_tts

    async def _all():
        tasks = []
        paths = {}

        paths["hook"]       = f"{output_dir}/audio_hook.mp3"
        paths["conclusion"] = f"{output_dir}/audio_conclusion.mp3"
        tasks.append(edge_tts.Communicate(script_data["hook"],       TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME).save(paths["hook"]))
        tasks.append(edge_tts.Communicate(script_data["conclusion"], TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME).save(paths["conclusion"]))

        for i, fact in enumerate(script_data["facts"]):
            p = f"{output_dir}/audio_fact_{i}.mp3"
            paths[f"fact_{i}"] = p
            tasks.append(edge_tts.Communicate(fact["text"], TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME).save(p))

        await asyncio.gather(*tasks)
        return paths

    return asyncio.run(_all())


# ================================================================
#  STEP 5 — ADD TEXT OVERLAY TO IMAGES
# ================================================================
def _add_text_overlay(img_path: str, title_text: str, body_text: str, out_path: str) -> str:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(img_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # Dark gradient at bottom for text readability
    for y in range(IMG_HEIGHT - 600, IMG_HEIGHT):
        alpha = int(200 * (y - (IMG_HEIGHT - 600)) / 600)
        od.line([(0, y), (IMG_WIDTH, y)], fill=(0, 0, 0, alpha))

    # Merge
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Load fonts — fallback to default if not available
    def load_font(size, bold=False):
        font_paths = [
            f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans-{'Bold' if bold else ''}.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
        for fp in font_paths:
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
        return ImageFont.load_default()

    font_brand = load_font(55, bold=True)
    font_body  = load_font(52, bold=False)

    # Brand name top
    draw.text((IMG_WIDTH // 2, 90), "⚡ VOID FACTS",
              font=font_brand, fill=(255, 210, 0), anchor="mm",
              stroke_width=3, stroke_fill=(0, 0, 0))

    # Body text bottom
    wrapped = textwrap.wrap(body_text, width=28)
    y_start = IMG_HEIGHT - (len(wrapped) * 68) - 100
    for i, line in enumerate(wrapped):
        draw.text((IMG_WIDTH // 2, y_start + i * 65), line,
                  font=font_body, fill=(255, 255, 255), anchor="mm",
                  stroke_width=2, stroke_fill=(0, 0, 0))

    img.save(out_path, quality=94)
    return out_path


# ================================================================
#  STEP 6 — ASSEMBLE VIDEO (MoviePy — FREE)
# ================================================================
def assemble_video(script_data: dict, images: list, audio_paths: dict, output_dir: str) -> str:
    """Combine images + audio into final MP4."""
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

    clips = []
    segments = [
        ("hook",       script_data["hook"],       images[0]),
        ("fact_0",     script_data["facts"][0]["text"], images[0]),
        ("fact_1",     script_data["facts"][1]["text"], images[0]),
        ("fact_2",     script_data["facts"][2]["text"], images[1]),
        ("fact_3",     script_data["facts"][3]["text"], images[1]),
        ("fact_4",     script_data["facts"][4]["text"], images[1]),
        ("conclusion", script_data["conclusion"], images[1]),
    ]

    for idx, (key, text, img_path) in enumerate(segments):
        audio = AudioFileClip(audio_paths[key])
        dur = audio.duration

        frame = _add_text_overlay(img_path, "VOID FACTS", text, f"{output_dir}/frame_{idx}.jpg")
        clip = ImageClip(frame).set_duration(dur).set_audio(audio)
        clip = clip.fadein(0.3).fadeout(0.3)
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")

    out_path = f"{output_dir}/VOIDFACTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    final.write_videofile(
        out_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=f"{output_dir}/_tmp_audio.m4a",
        remove_temp=True,
        preset="ultrafast",
        logger=None,
    )
    print(f"    ✅ Video saved: {out_path}")
    return out_path


# ================================================================
#  STEP 7 — UPLOAD TO YOUTUBE (Data API v3 — FREE, ~6 videos/day)
# ================================================================
def upload_to_youtube(video_path: str, script_data: dict) -> str:
    """Upload completed video to YouTube and return URL."""
    import google.oauth2.credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    if not YOUTUBE_CREDS_JSON:
        print("    ⚠️  YOUTUBE_CREDENTIALS not set — skipping upload.")
        return "(not uploaded)"

    creds_dict = json.loads(YOUTUBE_CREDS_JSON)
    creds = google.oauth2.credentials.Credentials(
        token          = creds_dict.get("token", ""),
        refresh_token  = creds_dict["refresh_token"],
        token_uri      = "https://oauth2.googleapis.com/token",
        client_id      = creds_dict["client_id"],
        client_secret  = creds_dict["client_secret"],
    )

    youtube = build("youtube", "v3", credentials=creds)

    title       = script_data["title"][:100]
    description = (script_data["description"][:4800] +
                   f"\n\n{script_data['hashtags']}")
    tags = [t.lstrip("#") for t in script_data["hashtags"].split() if t.startswith("#")]

    body = {
        "snippet": {
            "title":           title,
            "description":     description,
            "tags":            tags,
            "categoryId":      "28",   # Science & Technology
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        },
    }

    media   = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1 * 1024 * 1024)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"    📤 Uploading... {pct}%", end="\r")

    vid_id = response["id"]
    url = f"https://youtube.com/shorts/{vid_id}"
    print(f"\n    ✅ Uploaded → {url}")
    return url


# ================================================================
#  MASTER PIPELINE
# ================================================================
def run_once():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(OUTPUT_BASE_DIR, ts)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    log_path = f"{out_dir}/run.log"

    def log(msg):
        print(msg)
        with open(log_path, "a") as lf:
            lf.write(msg + "\n")

    log(f"\n{'='*60}")
    log(f"  🚀 VoidFacts Automation Started — {datetime.now()}")
    log(f"{'='*60}")

    try:
        # 1. Research
        log("\n📚 Step 1/7 — Researching topic...")
        topic = research_topic()

        # 2. Script
        log("\n✍️  Step 2/7 — Generating script (Gemini)...")
        script = generate_script(topic)
        with open(f"{out_dir}/script.json", "w") as f:
            json.dump(script, f, indent=2)
        log(f"  Title: {script['title']}")

        # 3. Images (Image 1 → parts 1-3, Image 2 → parts 4-5)
        log("\n🎨 Step 3/7 — Generating AI images (Pollinations.ai)...")
        img1 = generate_image(script["facts"][0]["image_prompt"], 1, out_dir)
        img2 = generate_image(script["facts"][3]["image_prompt"], 2, out_dir)
        images = [img1, img2]   # img1 for first 3 clips, img2 for last 4

        # 4. Voiceovers
        log("\n🎙️  Step 4/7 — Generating voiceovers (Edge TTS)...")
        audio_paths = generate_all_voiceovers(script, out_dir)
        log(f"  ✅ {len(audio_paths)} audio files generated")

        # 5. Assemble video
        log("\n🎬 Step 5/7 — Assembling video (MoviePy)...")
        video_path = assemble_video(script, images, audio_paths, out_dir)

        # 6. Save metadata
        log("\n📄 Step 6/7 — Saving metadata...")
        metadata = {
            "timestamp":   ts,
            "title":       script["title"],
            "description": script["description"],
            "hashtags":    script["hashtags"],
            "video_path":  video_path,
        }
        with open(f"{out_dir}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # 7. Upload
        log("\n📤 Step 7/7 — Uploading to YouTube...")
        url = upload_to_youtube(video_path, script)

        log(f"\n{'='*60}")
        log(f"  🎉 SUCCESS!  Video URL: {url}")
        log(f"  📁 Files at: {out_dir}/")
        log(f"{'='*60}\n")

    except Exception as e:
        import traceback
        log(f"\n❌ FAILED: {e}")
        log(traceback.format_exc())


# ================================================================
#  SCHEDULER — runs at 6:30 AM IST (01:00 UTC) + 11:30 PM IST (18:00 UTC)
# ================================================================
def run_scheduler():
    import schedule

    # IST = UTC + 5:30
    # 6:30 AM IST  = 1:00 AM UTC
    # 11:30 PM IST = 6:00 PM UTC
    schedule.every().day.at("01:00").do(run_once)
    schedule.every().day.at("18:00").do(run_once)

    print("⏰ Scheduler active!")
    print("   → 6:30 AM IST  (01:00 UTC)")
    print("   → 11:30 PM IST (18:00 UTC)")
    print("Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


# ================================================================
#  ENTRY POINT
# ================================================================
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "schedule"

    if mode == "once":
        run_once()
    elif mode in ("schedule", ""):
        run_scheduler()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python main.py [once|schedule]")
