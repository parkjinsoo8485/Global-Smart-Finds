import requests
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

urls = {
    "sample_air_duster.jpg": "https://ae-pic-a1.aliexpressimages.com/kf/S2c0e812543d54832be0f8ef0fbaec3bfj.jpg",
    "sample_stirring_mug.jpg": "https://ae-pic-a1.aliexpressimages.com/kf/S3e43ee16a34444e3966580f4f9547d2fq.jpg"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for name, url in urls.items():
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 5000:
            out_file = data_dir / name
            with open(out_file, "wb") as f:
                f.write(r.content)
            print(f"SUCCESS: {name} ({len(r.content)} bytes)")
        else:
            print(f"FAIL status {r.status_code} for {name}")
    except Exception as e:
        print(f"ERROR: {e}")

