"""
StudyHub - YouTube Video Sync Script
Method 1: YouTube RSS Feed (fast, reliable, no scraping)
Method 2: yt-dlp fallback (যদি RSS কাজ না করে)
কোনো API key লাগে না
"""

import json
import subprocess
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════
# SUBJECT KEYWORDS
# ═══════════════════════════════════════════════════════════════

SUBJECT_KEYWORDS = {
    "physics": [
        "পদার্থ", "পদার্থবিজ্ঞান", "physics", "phy",
        "ভৌত রাশি", "গতিবিদ্যা", "নিউটন", "মহাকর্ষ",
        "তরঙ্গ", "শব্দ", "তাপ", "বিদ্যুৎ", "আলো",
        "চুম্বক", "কোয়ান্টাম", "নিউক্লিয়", "সেমিকন্ডাক্টর",
        "ভেক্টর", "বল", "ক্ষমতা", "শক্তি", "চাপ",
        "পর্যাবৃত্ত", "দোলক", "স্থিতিস্থাপক",
    ],
    "chemistry": [
        "রসায়ন", "রাসায়নিক", "chemistry", "chem",
        "মোল", "পর্যায় সারণি", "বন্ধন", "জৈব",
        "অম্ল", "ক্ষার", "লবণ", "তড়িৎ রসায়ন",
        "হাইড্রোকার্বন", "পলিমার", "গ্যাসের সূত্র",
        "দ্রবণ", "বিক্রিয়া", "এস্টার", "অ্যালকোহল",
    ],
    "biology": [
        "জীব", "জীববিজ্ঞান", "biology", "bio",
        "কোষ", "ডিএনএ", "জেনেটিক্স", "সালোকসংশ্লেষণ",
        "শ্বসন", "উদ্ভিদ", "প্রাণী", "ভাইরাস",
        "ব্যাকটেরিয়া", "হরমোন", "বিবর্তন",
        "ব্রায়োফাইটা", "জীবপ্রযুক্তি", "মানব শারীর",
    ],
    "higher_math": [
        "উচ্চতর গণিত", "higher math", "গণিত", "math",
        "ম্যাট্রিক্স", "ত্রিকোণমিতি",
        "বৃত্ত", "উপবৃত্ত", "অন্তরকলন", "যোগজীকরণ",
        "অনুক্রম", "ধারা", "দ্বিপদ", "সম্ভাবনা",
    ],
    "ict": [
        "আইসিটি", "ict", "তথ্য প্রযুক্তি",
        "সংখ্যা পদ্ধতি", "বাইনারি", "লজিক গেট",
        "প্রোগ্রামিং", "ডেটাবেস", "নেটওয়ার্ক", "html",
    ],
    "english": [
        "english", "grammar", "composition",
        "prose", "poem", "comprehension",
    ],
    "bangla": [
        "বাংলা", "সাহিত্য", "ব্যাকরণ",
        "গদ্য", "পদ্য", "রচনা", "কবিতা",
    ],
    "economics": [
        "অর্থনীতি", "economics",
        "চাহিদা", "যোগান", "জিডিপি", "বাজেট",
    ],
    "accounting": [
        "হিসাববিজ্ঞান", "accounting",
        "জাবেদা", "খতিয়ান", "রেওয়ামিল",
    ],
    "civics": [
        "পৌরনীতি", "civics", "সংবিধান", "গণতন্ত্র",
    ],
    "history": [
        "ইতিহাস", "history", "মুক্তিযুদ্ধ", "১৯৭১",
    ],
}

CHAPTER_KEYWORDS = {
    # Physics
    "ভৌত রাশি ও পরিমাপ": ["ভৌত রাশি", "পরিমাপ", "একক", "মাত্রা", "SI unit"],
    "ভেক্টর": ["ভেক্টর", "vector", "লব্ধি", "উপাংশ", "ডট গুণফল"],
    "গতিবিদ্যা": ["গতিবিদ্যা", "বেগ", "ত্বরণ", "গতি সমীকরণ", "প্রজেক্টাইল"],
    "নিউটনের গতিসূত্র": ["নিউটন", "গতিসূত্র", "ঘর্ষণ", "ভরবেগ", "জড়তা"],
    "কাজ ক্ষমতা ও শক্তি": ["কাজ", "ক্ষমতা", "শক্তি", "গতিশক্তি", "বিভবশক্তি"],
    "মহাকর্ষ": ["মহাকর্ষ", "অভিকর্ষ", "কেপলার", "উপগ্রহ", "মুক্তিবেগ"],
    "পদার্থের গাঠনিক ধর্ম": ["গাঠনিক", "স্থিতিস্থাপক", "পৃষ্ঠটান", "সান্দ্রতা"],
    "পর্যাবৃত্ত গতি": ["পর্যাবৃত্ত", "সরল দোলন", "দোলক", "SHM", "পর্যায়কাল"],
    "তরঙ্গ ও শব্দ": ["তরঙ্গ", "শব্দ", "তরঙ্গদৈর্ঘ্য", "ডপলার", "অনুরণন"],
    "আলো": ["আলো", "প্রতিফলন", "প্রতিসরণ", "লেন্স", "দর্পণ", "ব্যতিচার"],
    "তাপগতিবিদ্যা": ["তাপ", "তাপমাত্রা", "তাপগতি", "কার্নো", "এন্ট্রপি"],
    "স্থির বিদ্যুৎ": ["স্থির বিদ্যুৎ", "কুলম্ব", "বিভব", "ধারক", "ক্যাপাসিটর"],
    "চল বিদ্যুৎ": ["চল বিদ্যুৎ", "রোধ", "ওহম", "বর্তনী", "কির্শফ"],
    "চুম্বকত্ব ও আবেশ": ["চুম্বক", "ফ্যারাডে", "আবেশ", "ট্রান্সফর্মার"],
    "আধুনিক পদার্থবিজ্ঞান": ["আধুনিক", "কোয়ান্টাম", "ফটোইলেকট্রিক", "ডি ব্রগলি"],
    "পরমাণুর মডেল": ["পরমাণু", "বোর", "রাদারফোর্ড", "ইলেকট্রন বিন্যাস"],
    "নিউক্লিয়ার পদার্থবিজ্ঞান": ["নিউক্লিয়", "তেজস্ক্রিয়", "ফিশন", "ফিউশন"],
    "সেমিকন্ডাক্টর": ["সেমিকন্ডাক্টর", "ট্রানজিস্টর", "ডায়োড"],
    # Chemistry
    "গুণগত রসায়ন": ["পরমাণুর গঠন", "ইলেকট্রন বিন্যাস", "অরবিটাল"],
    "মোল ও রাসায়নিক গণনা": ["মোল", "মোলার", "আণবিক ভর", "সীমাবদ্ধ বিকারক"],
    "রাসায়নিক পরিবর্তন": ["বিক্রিয়ার হার", "সাম্যাবস্থা", "অনুঘটক"],
    "পর্যায় সারণি": ["পর্যায় সারণি", "গ্রুপ", "পিরিয়ড", "হ্যালোজেন"],
    "রাসায়নিক বন্ধন": ["রাসায়নিক বন্ধন", "আয়নিক", "সমযোজী", "সংকরায়ন"],
    "অম্ল ক্ষার ও লবণ": ["অম্ল", "ক্ষার", "লবণ", "pH", "টাইট্রেশন"],
    "তড়িৎ রসায়ন": ["তড়িৎ রসায়ন", "ইলেক্ট্রোলাইসিস", "গ্যালভানিক"],
    "জৈব রসায়ন": ["জৈব", "হাইড্রোকার্বন", "অ্যালকেন", "অ্যালকিন", "বেনজিন"],
    "গ্যাসের ধর্ম": ["গ্যাসের সূত্র", "বয়েল", "চার্লস", "আদর্শ গ্যাস"],
    "পলিমার ও শিল্প রসায়ন": ["পলিমার", "প্লাস্টিক", "নাইলন", "শিল্প রসায়ন"],
    # Biology
    "কোষ ও এর গঠন": ["কোষ", "নিউক্লিয়াস", "মাইটোকন্ড্রিয়া", "ক্লোরোপ্লাস্ট"],
    "কোষ বিভাজন": ["কোষ বিভাজন", "মাইটোসিস", "মিয়োসিস", "ক্রোমোজোম"],
    "জীবের শ্রেণিবিন্যাস": ["শ্রেণিবিন্যাস", "ট্যাক্সোনমি", "দ্বিপদ নামকরণ"],
    "ভাইরাস ও ব্যাকটেরিয়া": ["ভাইরাস", "ব্যাকটেরিয়া", "অণুজীব"],
    "ছত্রাক ও শৈবাল": ["ছত্রাক", "ফাঙ্গাস", "শৈবাল", "মাশরুম"],
    "ব্রায়োফাইটা": ["ব্রায়োফাইটা", "মস", "লিভারওয়ার্ট", "হ্যাপ্লয়েড"],
    "টেরিডোফাইটা": ["টেরিডোফাইটা", "ফার্ন", "ভাস্কুলার"],
    "নগ্নবীজী ও আবৃতবীজী": ["নগ্নবীজী", "আবৃতবীজী", "একবীজপত্রী", "দ্বিবীজপত্রী"],
    "সালোকসংশ্লেষণ": ["সালোকসংশ্লেষণ", "ফটোসিন্থেসিস", "ক্লোরোফিল", "ক্যালভিন"],
    "শ্বসন": ["শ্বসন", "গ্লাইকোলাইসিস", "ক্রেবস চক্র", "এটিপি"],
    "জেনেটিক্স": ["জেনেটিক্স", "ডিএনএ", "আরএনএ", "জিন", "মেন্ডেল"],
    "মানব শারীরতত্ত্ব": ["মানব শারীর", "পরিপাক", "রক্ত সংবহন", "হৃদয়"],
    "বিবর্তন": ["বিবর্তন", "ডারউইন", "প্রাকৃতিক নির্বাচন"],
    "জীবপ্রযুক্তি": ["জীবপ্রযুক্তি", "বায়োটেকনোলজি", "ক্লোনিং", "টিস্যু কালচার"],
    # Higher Math
    "ম্যাট্রিক্স ও নির্ণায়ক": ["ম্যাট্রিক্স", "নির্ণায়ক", "ক্রামার"],
    "সরল রেখা": ["সরল রেখা", "রেখার সমীকরণ", "ঢাল"],
    "বৃত্ত": ["বৃত্ত", "বৃত্তের সমীকরণ", "স্পর্শক"],
    "কনিক সেকশন": ["উপবৃত্ত", "অধিবৃত্ত", "পরাবৃত্ত", "কনিক"],
    "ত্রিকোণমিতি": ["ত্রিকোণমিতি", "সাইন", "কোসাইন", "ট্যানজেন্ট"],
    "অনুক্রম ও ধারা": ["অনুক্রম", "ধারা", "সমান্তর", "গুণোত্তর", "AP", "GP"],
    "দ্বিপদ বিস্তার": ["দ্বিপদ", "বাইনোমিয়াল", "প্যাসকেল"],
    "অন্তরকলন": ["অন্তরকলন", "ডেরিভেটিভ", "differentiation", "চেইন রুল"],
    "যোগজীকরণ": ["যোগজীকরণ", "integration", "নির্দিষ্ট যোগজ"],
    "বিন্যাস সমাবেশ ও সম্ভাবনা": ["বিন্যাস", "সমাবেশ", "সম্ভাবনা", "probability"],
    # ICT
    "তথ্য প্রযুক্তি বিশ্ব": ["বিশ্বগ্রাম", "ই-কমার্স", "ভার্চুয়াল", "রোবটিক্স"],
    "কমিউনিকেশন সিস্টেম": ["নেটওয়ার্ক", "টপোলজি", "ফাইবার অপটিক", "ওয়াইফাই"],
    "সংখ্যা পদ্ধতি": ["সংখ্যা পদ্ধতি", "বাইনারি", "অক্টাল", "হেক্সাডেসিমাল"],
    "ওয়েব ডিজাইন": ["ওয়েব ডিজাইন", "html", "css", "ওয়েবপেজ"],
    "প্রোগ্রামিং": ["প্রোগ্রামিং", "c programming", "অ্যালগরিদম", "ফ্লোচার্ট"],
    "ডেটাবেস": ["ডেটাবেস", "database", "SQL", "রিলেশনাল"],
}


# ═══════════════════════════════════════════════════════════════
# FETCH METHODS
# ═══════════════════════════════════════════════════════════════

def get_channel_id_from_url(channel_url):
    """yt-dlp দিয়ে channel ID বের করো"""
    cmd = [
        "yt-dlp", "--print", "channel_id",
        "--playlist-items", "1",
        "--no-warnings", "--quiet",
        channel_url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        lines = result.stdout.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("UC") and len(line) > 10:
                return line
    except Exception as e:
        print(f"  Channel ID error: {e}")
    return None


def fetch_via_rss(channel_id, channel_name):
    """YouTube RSS Feed — latest 15 videos, fast ও reliable"""
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    print(f"  RSS → {rss_url}")
    try:
        req = urllib.request.Request(
            rss_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; StudyHub/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_content = response.read()

        root = ET.fromstring(xml_content)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
        }

        videos = []
        for entry in root.findall("atom:entry", ns):
            vid_id_el = entry.find("yt:videoId", ns)
            title_el = entry.find("atom:title", ns)
            published_el = entry.find("atom:published", ns)
            if vid_id_el is None or title_el is None:
                continue
            vid_id = vid_id_el.text or ""
            videos.append({
                "id": vid_id,
                "title": title_el.text or "",
                "duration": "",
                "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                "published": (published_el.text or "")[:10] if published_el is not None else "",
                "playlist": "",
            })
        print(f"  ✓ RSS: {len(videos)} videos")
        return videos
    except Exception as e:
        print(f"  ✗ RSS failed: {e}")
        return []


def fetch_via_ytdlp(channel_url, channel_name):
    """yt-dlp fallback — stderr দেখাবে debugging এর জন্য"""
    print(f"  yt-dlp → {channel_url}")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--ignore-errors",
        "--no-warnings",
        "--playlist-end", "100",
        channel_url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0 and result.stderr:
            print(f"  stderr: {result.stderr[:200]}")

        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get("_type") == "playlist":
                    continue
                vid_id = data.get("id", "")
                if not vid_id:
                    continue
                videos.append({
                    "id": vid_id,
                    "title": data.get("title", ""),
                    "duration": format_duration(data.get("duration", 0)),
                    "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                    "published": (data.get("upload_date", "") or "")[:10],
                    "playlist": data.get("playlist_title", "") or "",
                })
            except json.JSONDecodeError:
                continue
        print(f"  ✓ yt-dlp: {len(videos)} videos")
        return videos
    except Exception as e:
        print(f"  ✗ yt-dlp failed: {e}")
        return []


def fetch_channel_videos(channel_info):
    """Smart fetch: RSS → yt-dlp"""
    name = channel_info["name"]
    url = channel_info["url"]

    # Channel ID আগে থেকে দেওয়া থাকলে সরাসরি RSS
    channel_id = channel_info.get("channel_id", "")
    if channel_id:
        videos = fetch_via_rss(channel_id, name)
        if videos:
            return videos

    # URL থেকে channel ID বের করো
    print(f"  Getting channel ID...")
    channel_id = get_channel_id_from_url(url)
    if channel_id:
        print(f"  ID: {channel_id}")
        videos = fetch_via_rss(channel_id, name)
        if videos:
            return videos

    # yt-dlp fallback
    return fetch_via_ytdlp(url, name)


# ═══════════════════════════════════════════════════════════════
# CATEGORIZATION
# ═══════════════════════════════════════════════════════════════

def detect_subject(title, playlist_name=""):
    combined = (playlist_name + " " + title).lower()
    for subject, keywords in SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                return subject
    return None


def detect_chapter(title, playlist_name, subject):
    combined = (playlist_name + " " + title).lower()
    for chapter, keywords in CHAPTER_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                return chapter
    return "সাধারণ"


def format_duration(seconds):
    if not seconds:
        return ""
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    s = int(seconds) % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def load_channels():
    path = os.path.join(os.path.dirname(__file__), "..", "channels.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["channels"]


def load_existing_videos():
    path = os.path.join(os.path.dirname(__file__), "..", "videos.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                pass
    return {"subjects": {}, "uncategorized": [], "last_updated": "", "total_videos": 0}


def build_videos_json(channels):
    existing = load_existing_videos()

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
        print(f"\n📺 {channel_info['name']}")
        videos = fetch_channel_videos(channel_info)

        for video in videos:
            if not video["id"] or video["id"] in existing_ids:
                continue
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
                chapter = detect_chapter(
                    video["title"], video.get("playlist", ""), subject
                )
                if subject not in subjects:
                    subjects[subject] = {"chapters": {}}
                if chapter not in subjects[subject]["chapters"]:
                    subjects[subject]["chapters"][chapter] = {"videos": []}
                subjects[subject]["chapters"][chapter]["videos"].append(video_entry)
            else:
                uncategorized.append(video_entry)

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
        "uncategorized": uncategorized,
    }

    out_path = os.path.join(os.path.dirname(__file__), "..", "videos.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! New: {new_count} | Total: {total} | Uncategorized: {len(uncategorized)}")


if __name__ == "__main__":
    print("🚀 StudyHub Sync Starting...")
    channels = load_channels()
    print(f"📋 {len(channels)} channels")
    build_videos_json(channels)
