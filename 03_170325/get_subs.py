from yt_dlp import YoutubeDL
import csv
import re

# print(help(YoutubeDL))
video_url = "https://youtu.be/cwZb2mqId0A?si=kwB1YMKrTqVCt1kl"
csv_filename = "./youtube_links.csv"

english_sub_regex = re.compile(r'^en(-\w+)*$', re.IGNORECASE)

ydl_opts = {
    "skip_download": True,
    "quiet": True,
    "writesubtitles": True,
    "writeautomaticsub": False,
    "subtitleslangs": ["en"],
    "subtitlesformat": "srv3",
    "outtmpl": "%(id)s.%(ext)s",
}

with open(csv_filename, newline='',  encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter="\t")
    all_links = [link.strip()
                 for row in reader for link in row if link.strip()]


with YoutubeDL(ydl_opts) as ydl:
    for video_url in all_links:
        print(video_url)
        try:
            print(f"Getting {video_url}")
            info_dict = ydl.extract_info(video_url, download=False)
            subtitles = {
                lang: files for lang, files in info_dict.get('subtitles', {}).items()
                if english_sub_regex.match(lang)
            }
            auto_subtitles = {
                lang: files for lang, files in info_dict.get('automatic_captions', {}).items()
                if english_sub_regex.match(lang)
            }

            if subtitles:
                print(f"Downloading manual subtitles for {video_url} (Languages: {list(subtitles.keys())})")
                ydl.params['writeautomaticsub'] = False  # Ensure only manual subs are downloaded
            elif auto_subtitles:
                print(f"No manual subtitles found. Downloading auto captions for {video_url} (Languages: {list(auto_subtitles.keys())})")
                ydl.params['writeautomaticsub'] = True  # Allow auto captions if no manual subs
            else:
                print(f"No English subtitles available for {video_url}. Skipping.")
                continue

            ydl.download([video_url])
        except Exception as e:
            print(f"Error getting {video_url} coz {e}")

print("Subtitle download completed.")
