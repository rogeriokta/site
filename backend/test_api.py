"""Teste rápido da API - executa com python test_api.py"""
import requests
import json

BASE = "http://127.0.0.1:8000"

# Health
h = requests.get(f"{BASE}/api/health")
print(f"Health: {h.status_code} - {h.json()}")

# Login
login = requests.post(f"{BASE}/api/auth/login", json={
    "username": "admin", "password": "admin123"
})
print(f"Login: {login.status_code}")
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload
with open("test_card.png", "rb") as f:
    up = requests.post(
        f"{BASE}/api/corrections/upload",
        headers=headers,
        files={"file": ("test_card.png", f, "image/png")},
        data={
            "student_name": "Maria Teste",
            "student_id": "2026002",
            "class_name": "1o Periodo CCO",
            "discipline": "Matematica",
        },
    )
print(f"Upload: {up.status_code}")
cid = up.json()["id"]

# Process with gabarito
gabarito = json.dumps({
    "1": "A", "2": "B", "3": "C", "4": "D", "5": "E",
    "6": "A", "7": "B", "8": "C", "9": "D", "10": "E",
})
proc = requests.post(
    f"{BASE}/api/corrections/{cid}/process",
    headers=headers,
    data={"gabarito": gabarito},
)
print(f"Process: {proc.status_code}")
pj = proc.json()
print(f"  score={pj.get('score')} questions={pj.get('total_questions')} correct={pj.get('correct_answers')} confidence={pj.get('confidence')}")

# Result
res = requests.get(f"{BASE}/api/corrections/{cid}/result", headers=headers)
rj = res.json()
print(f"Result: {res.status_code}")
print(f"  score={rj.get('score')} details_count={len(rj.get('details', []))}")

print("\n=== Fim do teste ===")
