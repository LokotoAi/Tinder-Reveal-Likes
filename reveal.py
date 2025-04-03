import json
import os
import tempfile
import webbrowser
from pathlib import Path
from datetime import datetime
import subprocess

def extract_profiles_from_har(har_path: str):
    with open(har_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)

    entries = har_data['log']['entries']
    teasers, core = [], []

    for entry in entries:
        url = entry['request']['url']
        content = entry['response']['content']
        if 'text' in content and 'application/json' in content.get('mimeType', ''):
            try:
                data = json.loads(content['text'])
                if 'teasers' in url:
                    teasers.append(data)
                elif 'core' in url:
                    core.append(data)
            except:
                continue

    return teasers, core

def parse_teasers(teasers):
    results = []
    if not teasers:
        return results
    for item in teasers[0].get("data", {}).get("results", []):
        user = item.get("user", {})
        photo = user.get("photos", [{}])[0].get("url", "")
        results.append({"id": user.get("_id", ""), "photo": photo})
    return results

def parse_core(core_data):
    profiles = []
    for core in core_data:
        for item in core.get("data", {}).get("results", []):
            if item.get("type") != "user":
                continue
            user = item.get("user", {})
            user_id = user.get("_id", "")
            name = user.get("name", "")
            birth_date = user.get("birth_date", "")
            bio = user.get("bio", "")
            city = user.get("city", {}).get("name", "")
            age = ""
            if birth_date:
                try:
                    birth = datetime.strptime(birth_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    today = datetime.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                except:
                    pass
            photos = []
            for photo in user.get("photos", []):
                processed = photo.get("processedFiles", [])
                if processed:
                    largest = max(processed, key=lambda x: x.get("width", 0))
                    photos.append(largest["url"])
            profiles.append({
                "id": user_id,
                "name": name,
                "age": age,
                "bio": bio,
                "city": city,
                "photos": photos
            })
    return profiles

def generate_html(teasers, core_profiles, out_path):
    html = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">
    <title>Tinder likes</title><style>
    body { margin: 0; font-family: Arial; background: #1e1e1e; color: #f0f0f0; display: flex; }
    .fixed { width: 40%; position: fixed; top: 0; bottom: 0; left: 0; overflow-y: auto; padding: 20px; border-right: 2px solid #333; }
    .scrollable { margin-left: 40%; width: 60%; padding: 20px; height: 100vh; overflow-y: scroll; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #444; padding: 8px; text-align: left; vertical-align: top; }
    th { background-color: #333; }
    .photos-row td { text-align: center; }
    img { max-width: 100px; border-radius: 10px; margin: 5px; transition: transform 0.2s; }
    img:hover { transform: scale(1.1); }
    a { text-decoration: none; }
    </style></head><body>
    <div class="fixed"><h2>Your likes (blurred)</h2><table><tr><th>ID</th><th>Photo</th></tr>"""

    for t in teasers:
        html += f'<tr><td>{t["id"]}</td><td><a href="{t["photo"]}" target="_blank"><img src="{t["photo"]}"></a></td></tr>'

    html += "</table></div><div class='scrollable'><h2>Potencial likes</h2><table><tr><th>ID</th><th>Name</th><th>Age</th><th>City</th><th>Profile description</th></tr>"

    for p in core_profiles:
        html += f'<tr><td>{p["id"]}</td><td>{p["name"]}</td><td>{p["age"]}</td><td>{p["city"]}</td><td>{p["bio"]}</td></tr>'
        html += f'<tr class="photos-row"><td colspan="5">' + "".join(
            [f'<a href="{url}" target="_blank"><img src="{url}"></a>' for url in p["photos"]]
        ) + '</td></tr>'

    html += "</table></div></body></html>"
    Path(out_path).write_text(html, encoding='utf-8')

def run():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    har_file_path = os.path.join(script_dir, "tinder.com.har")

    if not os.path.exists(har_file_path):
        print("[!] File tinder.com.har not found in scrip directory:", har_file_path)
        return

    teasers_data, core_data = extract_profiles_from_har(har_file_path)
    teasers = parse_teasers(teasers_data)
    core_profiles = parse_core(core_data)

    output_file = os.path.join(tempfile.gettempdir(), "tinder_likes.html")
    generate_html(teasers, core_profiles, output_file)
    print("[*] HTML ready:", output_file)

    subprocess.run(['start', 'chrome', output_file], shell=True)

if __name__ == "__main__":
    run()
