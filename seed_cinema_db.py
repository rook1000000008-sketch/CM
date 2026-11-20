import urllib.request
import urllib.parse
import json
import random
import hashlib

FIREBASE_URL = "https://cinemamanager-209-default-rtdb.asia-southeast1.firebasedatabase.app/cinema_manager/talents.json"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

ROLE_QUERIES = {
    "ACT": "wd:Q33999",    # Actor / Actress
    "SCR": "wd:Q28389",    # Screenwriter
    "DOP": "wd:Q222344",   # Cinematographer
    "EDT": "wd:Q7042855",  # Film Editor
    "CMP": "wd:Q1415090"   # Film Score Composer
}

ALL_GENRES = [
    "Drama", "Comedy / Satire", "Action / Stunt", "Sci-Fi",
    "Crime / Thriller", "Romance", "Horror / Psychological",
    "Historical / Biopic", "Musical / Dance", "Mystery / Neo-Noir",
    "Fantasy / Adventure", "Animation / Voice"
]

def fetch_wikidata_people(role_code, qid, limit=100):
    sparql = f"""
    SELECT DISTINCT ?person ?personLabel ?genderLabel ?countryLabel ?desc WHERE {{
      ?person wdt:P31 wd:Q5;
              wdt:P106 {qid};
              wdt:P166 ?award.
      ?award wdt:P31/wdt:P279* wd:Q19020.
      OPTIONAL {{ ?person wdt:P21 ?gender. }}
      OPTIONAL {{ ?person wdt:P27 ?country. }}
      OPTIONAL {{
        ?person schema:description ?desc.
        FILTER(LANG(?desc) = "en")
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT {limit}
    """
    url = f"{WIKIDATA_SPARQL}?query={urllib.parse.quote(sparql)}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "CinemaManagerBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    results = {}
    for row in data["results"]["bindings"]:
        name = row.get("personLabel", {}).get("value", "")
        if not name or name.startswith("Q"):
            continue
        raw_gender = row.get("genderLabel", {}).get("value", "").lower()
        gender = "F" if "female" in raw_gender else "M"
        nation = row.get("countryLabel", {}).get("value", "Global")
        desc = row.get("desc", {}).get("value", f"Acclaimed {role_code} in world cinema")

        uid = f"{role_code.lower()}_{hashlib.md5(name.encode()).hexdigest()[:10]}"
        base_stat = random.randint(17, 20)
        results[uid] = {
            "id": uid,
            "name": name,
            "gender": gender,
            "role": role_code,
            "nation": nation,
            "age": random.randint(28, 68),
            "s1": base_stat,
            "s2": random.randint(15, 20),
            "s3": random.randint(16, 20),
            "s4": random.randint(15, 20),
            "ego": random.randint(6, 14),
            "fee": round(random.uniform(6.0, 18.0) if role_code == "ACT" else random.uniform(3.5, 8.5), 1),
            "awards": random.randint(1, 3),
            "genres": random.sample(ALL_GENRES, 3),
            "bio": desc
        }
    return results

def upload_to_firebase(payload):
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(FIREBASE_URL, data=data_bytes, method="PATCH")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status

if __name__ == "__main__":
    all_talents = {}
    for role, qid in ROLE_QUERIES.items():
        print(f"กำลังดูดรายชื่อตำแหน่ง {role} จาก Wikidata...")
        people = fetch_wikidata_people(role, qid, limit=100)
        print(f"  -> ได้มา {len(people)} คน")
        all_talents.update(people)

    print(f"กำลังอัปโหลดทั้งหมด {len(all_talents)} คนขึ้น Firebase...")
    status = upload_to_firebase(all_talents)
    print(f"สำเร็จ! HTTP Status: {status}")
