import tkinter as tk
from tkinter import ttk
import anasayfa
import requests
import json
from pathlib import Path

url = "http://127.0.0.1:8000/"
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
APP_LOG_FILE = LOG_DIR / "app.log"


def uygulama_logla(seviye, olay, detay):
    kayit = {
        "level": seviye,
        "event": olay,
        "detail": detay,
    }
    try:
        with APP_LOG_FILE.open("a", encoding="utf-8") as log_dosyasi:
            log_dosyasi.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    except OSError as hata:
        print("log yazılamadı", hata)


def setup_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=8)
    style.configure("TLabel", font=("Segoe UI", 10))
    style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
    style.configure("TEntry", padding=6)
    style.configure("Card.TFrame", background="#ffffff")


def sorgu(kullanıcı, sifre):
    print("istek gönderiliyor")
    data = {
    "username": kullanıcı,
    "password": sifre
    }
    data["username"] = kullanıcı
    data["password"] = sifre

    try:
        cevap = requests.post(url+"login", json=data, timeout=5)

        print(cevap.status_code)
        uygulama_logla("info", "login_request", f"{kullanıcı} -> {cevap.status_code}")
        try:
            sonuc = cevap.json()
        except ValueError:
            print("Sunucudan geçersiz JSON geldi")
            uygulama_logla("error", "login_bad_json", kullanıcı)
            return

        print(sonuc)

        if cevap.status_code == 200 and sonuc.get("status") == "success":
            with open("token.json","w", encoding="utf-8") as jsn:
                print("token yazılıyor")
                json.dump(sonuc, jsn, ensure_ascii=False, indent=4)
            print("Giriş başarılı")
            uygulama_logla("info", "login_success", kullanıcı)
            pencere.destroy()
            anasayfa.app()
        else:
            print("Giriş başarısız" if cevap.status_code == 200 else "Server hatası")
            uygulama_logla("warning", "login_fail", kullanıcı)

    except requests.exceptions.RequestException as e:
        print("Bağlantı hatası:", e)
        uygulama_logla("error", "login_http_error", str(e))

def kaydet_post(kullanıcı,sifre,tekrar,mail):
    print("Kayıt")
    data_2 = {
    "username": kullanıcı,
    "password": sifre,
    "password2": tekrar,
    "mail": mail
    }

    try:
        durum = requests.post(url+"singup",json=data_2, timeout=5)
        print(durum.status_code)
        uygulama_logla("info", "signup_request", f"{kullanıcı} -> {durum.status_code}")
        try:
            sonuc = durum.json()
        except ValueError:
            print("Sunucudan geçersiz JSON geldi")
            uygulama_logla("error", "signup_bad_json", kullanıcı)
            return

        print(sonuc)
        if durum.status_code == 200:
            if sonuc.get("status") == "success":
                print("başarılı")
                uygulama_logla("info", "signup_success", kullanıcı)
            else:
                print("Giriş başarısız")
                uygulama_logla("warning", "signup_fail", kullanıcı)
        else:
            print("Server hatası")
            uygulama_logla("warning", "signup_server_error", kullanıcı)

    except requests.exceptions.RequestException as e:
        print("Bağlantı hatası:", e)
        uygulama_logla("error", "signup_http_error", str(e))

def kayıt_panel():
    print("Kayıt yapılıyor")

    alt_pencere = tk.Toplevel(pencere)
    alt_pencere.title("Kayıt ol")
    alt_pencere.geometry("420x360")
    alt_pencere.resizable(False, False)
    alt_pencere.configure(bg="#f3f7fb")
    alt_pencere.transient(pencere)
    alt_pencere.lift()
    alt_pencere.focus_force()
    alt_pencere.update_idletasks()
    alt_pencere.deiconify()

    def geridon():
        print("geri dönüldü")
        alt_pencere.destroy()

    card = ttk.Frame(alt_pencere, style="Card.TFrame", padding=18)
    card.pack(fill="both", expand=True, padx=16, pady=16)

    label_3 = ttk.Label(card, text="Kayıt Ol", style="Header.TLabel")
    label_3.pack(pady=(0, 16))

    form_frame = ttk.Frame(card)
    form_frame.pack(fill="x", expand=True)

    ttk.Label(form_frame, text="Kullanıcı adı").grid(row=0, column=0, sticky="w", pady=4)
    entry_2 = ttk.Entry(form_frame)
    entry_2.grid(row=1, column=0, sticky="ew", pady=4)

    ttk.Label(form_frame, text="Şifre").grid(row=2, column=0, sticky="w", pady=4)
    entry_3 = ttk.Entry(form_frame, show="*")
    entry_3.grid(row=3, column=0, sticky="ew", pady=4)

    ttk.Label(form_frame, text="Şifreyi tekrarla").grid(row=4, column=0, sticky="w", pady=4)
    entry_4 = ttk.Entry(form_frame, show="*")
    entry_4.grid(row=5, column=0, sticky="ew", pady=4)

    ttk.Label(form_frame, text="Mail").grid(row=6, column=0, sticky="w", pady=4)
    entry_5 = ttk.Entry(form_frame)
    entry_5.grid(row=7, column=0, sticky="ew", pady=4)

    form_frame.columnconfigure(0, weight=1)
    action_frame = ttk.Frame(card)
    action_frame.pack(fill="x", pady=(16, 0))

    ttk.Button(action_frame, text="Geri", command=geridon, style="Accent.TButton").pack(side="left", fill="x", expand=True, padx=(0, 8))
    ttk.Button(
        action_frame,
        text="Kayıt Ol",
        command=lambda: kaydet_post(entry_2.get(), entry_3.get(), entry_4.get(), entry_5.get()),
        style="Accent.TButton",
    ).pack(side="left", fill="x", expand=True)

    alt_pencere.protocol("WM_DELETE_WINDOW", geridon)


pencere = tk.Tk()

pencere.title("Giriş")

pencere.geometry("420x320")

pencere.resizable(False, False)

pencere.configure(bg="#f3f7fb")
setup_style(pencere)

card_frame = ttk.Frame(pencere, style="Card.TFrame", padding=20)
card_frame.place(relx=0.5, rely=0.5, anchor="center")

label_0 = ttk.Label(card_frame, text="Giriş", style="Header.TLabel")
label_0.pack(pady=(0, 16))

label_1 = ttk.Label(card_frame, text="Kullanıcı Adı")
label_1.pack(anchor="w")
entry_0 = ttk.Entry(card_frame)
entry_0.pack(fill="x", pady=4)

label_2 = ttk.Label(card_frame, text="Şifre")
label_2.pack(anchor="w", pady=(12, 0))
entry_1 = ttk.Entry(card_frame, show="*")
entry_1.pack(fill="x", pady=4)

button_frame = ttk.Frame(card_frame)
button_frame.pack(fill="x", pady=(18, 0))

ttk.Button(button_frame, text="Giriş", command=lambda: sorgu(entry_0.get(), entry_1.get()), style="Accent.TButton").pack(side="left", fill="x", expand=True, padx=(0, 8))
ttk.Button(button_frame, text="Kayıt Ol", command=kayıt_panel, style="Accent.TButton").pack(side="left", fill="x", expand=True)

pencere.mainloop()
