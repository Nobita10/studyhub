
"""
StudyHub - YouTube Video Sync Script
চলে প্রতিদিন GitHub Actions-এ। কোনো API key লাগে না।
yt-dlp দিয়ে video fetch → keyword দিয়ে categorize → videos.json update
"""

import json
import subprocess
import os
import re
from datetime import datetime, timezone

# ───────────────────────────────────────────
# KEYWORD DICTIONARY (Bangla + English)
# নতুন keyword যোগ করতে চাইলে এখানে add করো
# ───────────────────────────────────────────

SUBJECT_KEYWORDS = {
    "physics": [
        "পদার্থ", "physics", "phy", "আলো", "তরঙ্গ", "শব্দ",
        "গতি", "বল", "ত্বরণ", "মহাকর্ষ", "তাপ", "বিদ্যুৎ",
        "চুম্বক", "নিউটন", "কাজ", "ক্ষমতা", "শক্তি", "চাপ",
        "ঘনত্ব", "প্লবতা", "বর্তনী", "রোধ", "ধারক", "কোয়ান্টাম"
    ],
    "chemistry": [
        "রসায়ন", "chemistry", "chem", "পর্যায়", "মৌল", "যৌগ",
        "বন্ধন", "জৈব", "অজৈব", "তড়িৎ", "বিশ্লেষণ", "বিক্রিয়া",
        "অম্ল", "ক্ষার", "লবণ", "মোল", "গ্যাস", "দ্রবণ",
        "হাইড্রোকার্বন", "পলিমার", "এস্টার"
    ],
    "biology": [
        "জীব", "biology", "bio", "কোষ", "জেনেটিক্স", "ডিএনএ",
        "উদ্ভিদ", "প্রাণী", "শ্বসন", "সালোকসংশ্লেষণ", "হরমোন",
        "বিবর্তন", "বাস্তুতন্ত্র", "ভাইরাস", "ব্যাকটেরিয়া",
        "ছত্রাক", "পরিপাক", "রক্ত", "হৃদয়", "স্নায়ু"
    ],
    "higher_math": [
        "উচ্চতর গণিত", "higher math", "hmath", "বীজগণিত", "ক্যালকুলাস",
        "ম্যাট্রিক্স", "ত্রিকোণমিতি", "জ্যামিতি", "সংখ্যাতত্ত্ব",
        "অনুক্রম", "ধারা", "লিমিট", "অন্তরকলন", "যোগজীকরণ",
        "দ্বিপদ", "ভেক্টর", "স্থানাঙ্ক", "বৃত্ত", "উপবৃত্ত"
    ],
    "ict": [
        "আইসিটি", "ict", "তথ্য", "প্রযুক্তি", "প্রোগ্রামিং",
        "database", "ডেটাবেস", "নেটওয়ার্ক", "সাইবার", "html",
        "c programming", "সংখ্যা পদ্ধতি", "কৃত্রিম বুদ্ধিমত্তা"
    ],
    "english": [
        "english", "grammar", "writing", "reading", "prose",
        "poem", "poetry", "comprehension", "composition"
    ],
    "bangla": [
        "বাংলা", "bangla", "সাহিত্য", "ব্যাকরণ", "রচনা",
        "গদ্য", "পদ্য", "উপন্যাস", "কবিতা", "ছোটগল্প"
    ],
    "economics": [
        "অর্থনীতি", "economics", "eco", "চাহিদা", "যোগান",
        "বাজার", "জিডিপি", "মুদ্রাস্ফীতি", "ব্যাংক"
    ],
    "accounting": [
        "হিসাববিজ্ঞান", "accounting", "acc", "জাবেদা", "খতিয়ান",
        "রেওয়ামিল", "আর্থিক বিবরণী", "নগদ প্রবাহ"
    ],
    "civics": [
        "পৌরনীতি", "civics", "সংবিধান", "সরকার", "রাষ্ট্র",
        "নাগরিক", "গণতন্ত্র", "নির্বাচন"
    ],
    "history": [
        "ইতিহাস", "history", "মুক্তিযুদ্ধ", "বাংলাদেশ", "সভ্যতা",
        "ঔপনিবেশিক", "মোগল", "ব্রিটিশ"
    ]
}

CHAPTER_KEYWORDS = {
    # Physics chapters
    "ভৌত রাশি ও পরিমাপ": ["পরিমাপ", "একক", "মাত্রা", "ভৌত রাশি"],
    "গতিবিদ্যা": ["গতি", "বেগ", "ত্বরণ", "স্থানচ্যুতি", "গতিবিদ্যা"],
    "নিউটনের সূত্র": ["নিউটন", "বল", "ঘর্ষণ", "ভরবেগ"],
    "কাজ ক্ষমতা শক্তি": ["কাজ", "ক্ষমতা", "শক্তি", "সংরক্ষণ"],
    "মহাকর্ষ": ["মহাকর্ষ", "অভিকর্ষ", "কেপলার", "মহাকর্ষীয়"],
    "পদার্থের গাঠনিক ধর্ম": ["স্থিতিস্থাপকতা", "পৃষ্ঠটান", "সান্দ্রতা", "গাঠনিক"],
    "পর্যাবৃত্ত গতি": ["পর্যাবৃত্ত", "সরল দোলন", "দোলক", "স্পন্দন"],
    "তরঙ্গ": ["তরঙ্গ", "কম্পন", "তরঙ্গদৈর্ঘ্য", "বিস্তার"],
    "আলো": ["আলো", "প্রতিফলন", "প্রতিসরণ", "লেন্স", "দর্পণ"],
    "তাপগতিবিদ্যা": ["তাপ", "তাপমাত্রা", "তাপগতি", "এন্ট্রপি"],
    "বিদ্যুৎ": ["বিদ্যুৎ", "বিভব", "তড়িৎ", "বর্তনী", "রোধ"],
    "চুম্বকত্ব": ["চুম্বক", "চৌম্বক", "ফ্যারাডে", "আবেশ"],
    "আধুনিক পদার্থবিজ্ঞান": ["কোয়ান্টাম", "ফোটন", "আপেক্ষিকতা", "পরমাণু"],

    # Chemistry chapters
    "পর্যায় সারণি": ["পর্যায়", "মৌল", "গ্রুপ", "পিরিয়ড"],
    "রাসায়নিক বন্ধন": ["বন্ধন", "আয়নিক", "সমযোজী", "ধাতব"],
    "জৈব রসায়ন": ["জৈব", "হাইড্রোকার্বন", "অ্যালকেন", "অ্যালকিন"],
    "তড়িৎ রসায়ন": ["তড়িৎ বিশ্লেষণ", "তড়িৎ রসায়ন", "কোষ"],

    # Biology chapters
    "কোষ ও এর গঠন": ["কোষ", "নিউক্লিয়াস", "মাইটোকন্ড্রিয়া", "ক্লোরোপ্লাস্ট"],
    "জেনেটিক্স": ["জেনেটিক্স", "ডিএনএ", "জিন", "ক্রোমোজোম", "মিউটেশন"],
    "সালোকসংশ্লেষণ": ["সালোকসংশ্লেষণ", "ক্লোরোফিল", "ফটোসিন্থেসিস"],
    "শ্বসন": ["শ্বসন", "গ্লাইকোলাইসিস", "ক্রেবস", "এটিপি"],
}

HSC_KEYWORDS = [
    "hsc", "এইচএসসি", "উচ্চ মাধ্যমিক", "একাদশ", "দ্বাদশ",
    "class 11", "class 12", "২০২৫", "২০২৬", "২০২৭"
]


def load_channels():
    """channels.json পড়ো"""
    path = os.path.join(os.path.dirname(__file__), "..", "channels.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["channels"]


def load_existing_videos():
    """আগের videos.json পড়ো (থাকলে)"""
    path = os.path.join(os.path.dirname(__file__), "..", "videos.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"subjects": {}, "uncategorized": [], "last_updated": "", "total_videos": 0}


def fetch_channel_videos(channel_url):
    """yt-dlp দিয়ে channel-এর সব video metadata নিয়ে আসো"""
    print(f"  Fetching: {channel_url}")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        "--playlist-end", "200",   # প্রথমবার ২০০টা, পরে বাড়াতে পারো
        channel_url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                videos.append({
                    "id": data.get("id", ""),
                    "title": data.get("title", ""),
                    "duration": format_duration(data.get("duration", 0)),
                    "thumbnail": data.get("thumbnail", f"https://i.ytimg.com/vi/{data.get('id','')}/hqdefault.jpg"),
                    "published": data.get("upload_date", "")[:10] if data.get("upload_date") else "",
                    "playlist": data.get("playlist_title", "") or data.get("playlist", ""),
                })
            except json.JSONDecodeError:
                continue
        print(f"  ✓ {len(videos)} videos found")
        return videos
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return []


def format_duration(seconds):
    """seconds → MM:SS বা HH:MM:SS"""
    if not seconds:
        return ""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def detect_subject(title, playlist_name=""):
    """Step 1: playlist → Step 2: keyword → Step 3: uncategorized"""
    text = (title + " " + playlist_name).lower()

    # Step 1: Playlist name দিয়ে বোঝার চেষ্টা
    if playlist_name:
        for subject, keywords in SUBJECT_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in playlist_name.lower():
                    return subject

    # Step 2: Title keyword matching
    for subject, keywords in SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return subject

    return None  # uncategorized


def detect_chapter(title, subject):
    """Title দেখে chapter বোঝো"""
    text = title.lower()
    for chapter, keywords in CHAPTER_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return chapter
    return "সাধারণ"  # default chapter


def is_hsc_related(title):
    """HSC related কিনা check করো"""
    text = title.lower()
    for kw in HSC_KEYWORDS:
        if kw.lower() in text:
            return True
    return True  # doubt হলে include করো, filter করা যাবে পরে


def build_videos_json(channels):
    """সব channel process করে videos.json বানাও"""
    existing = load_existing_videos()
    
    # Existing video IDs collect করো (duplicate এড়াতে)
    existing_ids = set()
    for subj in existing.get("subjects", {}).values():
        for ch in subj.get("chapters", {}).values():
            for v in ch.get("videos", []):
                existing_ids.add(v["id"])
    for v in existing.get("uncategorized", []):
        existing_ids.add(v["id"])

    new_count = 0
    subjects = existing.get("subjects", {})
    uncategorized = existing.get("uncategorized", [])

    for channel_info in sorted(channels, key=lambda x: x.get("priority", 99)):
        print(f"\n📺 Processing: {channel_info['name']}")
        videos = fetch_channel_videos(channel_info["url"])

        for video in videos:
            if not video["id"] or video["id"] in existing_ids:
                continue  # Skip duplicates

            existing_ids.add(video["id"])
            new_count += 1

            subject = detect_subject(video["title"], video.get("playlist", ""))
            
            video_entry = {
                "id": video["id"],
                "title": video["title"],
                "channel": channel_info["name"],
                "duration": video["duration"],
                "thumbnail": video["thumbnail"],
                "published": video["published"],
            }

            if subject:
                chapter = detect_chapter(video["title"], subject)
                
                # Subject initialize
                if subject not in subjects:
                    subjects[subject] = {"chapters": {}}
                if chapter not in subjects[subject]["chapters"]:
                    subjects[subject]["chapters"][chapter] = {"videos": []}
                
                subjects[subject]["chapters"][chapter]["videos"].append(video_entry)
            else:
                uncategorized.append(video_entry)

    # Total count
    total = sum(
        len(ch["videos"])
        for subj in subjects.values()
        for ch in subj["chapters"].values()
    ) + len(uncategorized)

    result = {
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_videos": total,
        "new_this_run": new_count,
        "subjects": subjects,
        "uncategorized": uncategorized
    }

    # Save করো
    out_path = os.path.join(os.path.dirname(__file__), "..", "videos.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! {new_count} new videos added. Total: {total}")
    return result


if __name__ == "__main__":
    print("🚀 StudyHub Sync Starting...")
    channels = load_channels()
    print(f"📋 {len(channels)} channels to process")
    build_videos_json(channels)
