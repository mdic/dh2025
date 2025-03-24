import csv
import re
from yt_dlp import YoutubeDL
from youtube_comment_downloader import *
import os

downloader = YoutubeCommentDownloader()
# CSV input filename
csv_filename = "./youtube_links.csv"

# Regex pattern to match English subtitles (e.g., 'en', 'en-US', 'en-GB', 'en-randomID')
english_sub_regex = re.compile(r"^en(-\w+)*$", re.IGNORECASE)

# Read CSV and collect all links
with open(csv_filename, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter="\t")
    all_links = [link.strip()
                 for row in reader for link in row if link.strip()]

# Process each video
for url in all_links:
    try:

        print(f"\nProcessing: {url}")

        # First, extract info
        with YoutubeDL({'skip_download': True, 'quiet': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
        # Extract matching English subtitle languages
        if os.path.exists(f"{info_dict['id']}.jsonl"):
            continue
        else:
            available_subtitles = info_dict.get('subtitles', {})
            available_auto_subtitles = info_dict.get('automatic_captions', {})

            # Filter subtitles using regex (find all valid English ones)
            english_subs = sorted(
                [lang for lang in available_subtitles if english_sub_regex.match(
                    lang)],
                # Prioritize 'en' over other English variants
                key=lambda x: (x != 'en', x)
            )
            # english_subs = [lang for lang in available_subtitles if english_sub_regex.match(lang)]
            # english_auto_subs = [lang for lang in available_auto_subtitles if english_sub_regex.match(lang)]
            english_auto_subs = sorted(
                [lang for lang in available_auto_subtitles if english_sub_regex.match(
                    lang)],
                key=lambda x: (x != 'en', x)
            )

            # If manual subs exist, download them; otherwise, fall back to auto subs
            selected_subs = english_subs if english_subs else english_auto_subs

            if not selected_subs:
                print(f"No English subtitles available for {url}. Skipping.")
                continue

            print(
                f"Downloading subtitles for {url} (Languages: {selected_subs})")

            # Dynamically set subtitle language for yt_dlp
            ydl_opts = {
                'skip_download': True,
                "writeinfojson": True,
                'writesubtitles': True,
                # Only allow auto if no manual subs
                'writeautomaticsub': False if english_subs else True,
                # Use exact language codes found
                'subtitleslangs': [selected_subs[0]],
                'subtitlesformat': 'srv3',  # Use srv3 format
                'outtmpl': '%(id)s.%(ext)s',  # Output filename format
                'quiet': False
            }

            # Download subtitles
            # with YoutubeDL(ydl_opts) as ydl:
            #     ydl.download([url])

            with open(f"{info_dict['id']}.jsonl", "a") as f:
                print(f"Saving comments to {info_dict['id']}.jsonl")
                for comment in downloader.get_comments_from_url(url):
                    json.dump(comment, f, ensure_ascii=False)
                    f.write("\n")

    except Exception as e:
        print(f"Error processing {url}: {e}")

print("\nAll subtitle downloads completed.")
