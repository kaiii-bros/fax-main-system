"""FAX Main Web - API menu dinamis.

Daftar website dan tautan dukungan (Saweria, Sociabuzz, dll.) dibaca dari
sites.json, lalu dikirim ke halaman lewat GET /api/menu. Untuk menambah, mengubah, atau menyembunyikan menu,
cukup edit sites.json (tidak perlu menyentuh HTML).
"""
import json
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

BASE = Path(__file__).resolve().parent
app = Flask(__name__)

LABEL_STATUS = {"live": "Siap dipakai", "soon": "Segera hadir"}


def url_aman(url):
    """Hanya izinkan http(s) atau alamat internal (diawali satu '/')."""
    if not isinstance(url, str):
        return False
    if url.startswith(("https://", "http://")):
        return True
    return url.startswith("/") and not url.startswith("//")


def muat_menu():
    with open(BASE / "sites.json", encoding="utf-8") as f:
        data = json.load(f)

    menu = []
    for mentah in data.get("menu", []):
        if not isinstance(mentah, dict) or not mentah.get("aktif", True):
            continue  # "aktif": false -> menu disembunyikan

        judul = str(mentah.get("judul", "")).strip()
        if not judul:
            continue

        status = mentah.get("status", "live")
        if status not in LABEL_STATUS:
            status = "soon"

        url = mentah.get("url", "")
        if status == "live" and not url_aman(url):
            status = "soon"  # link kosong/rusak tidak dibuat bisa diklik

        menu.append({
            "no": len(menu) + 1,
            "judul": judul,
            "deskripsi": str(mentah.get("deskripsi", "")).strip(),
            "url": url if status == "live" else "",
            "status": status,
            "label": str(mentah.get("label") or LABEL_STATUS[status]),
        })
    dukungan = []
    for mentah in data.get("dukungan", []):
        if not isinstance(mentah, dict) or not mentah.get("aktif", True):
            continue
        nama = str(mentah.get("nama", "")).strip()
        url = mentah.get("url", "")
        if nama and isinstance(url, str) and url.startswith(("https://", "http://")):
            dukungan.append({"nama": nama, "url": url})

    return {"menu": menu, "dukungan": dukungan}


@app.get("/api/menu")
def api_menu():
    try:
        isi = muat_menu()
    except (OSError, ValueError):
        return jsonify({"error": "sites.json tidak bisa dibaca"}), 500
    resp = jsonify(isi)
    resp.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=300"
    return resp


@app.get("/")
def beranda():
    # Cadangan untuk pengujian lokal. Di Vercel, public/index.html
    # disajikan langsung oleh CDN.
    return send_from_directory(BASE / "public", "index.html")
