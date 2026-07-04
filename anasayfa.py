import tkinter as tk #Ekran yapmak için
import json #Json dsyalarını kullanmak için
import requests #Http istekleri için
from tkinter import messagebox #Mesaj kutusu için
from tkinter import ttk
from pathlib import Path

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except Exception:  # pragma: no cover
    FigureCanvasTkAgg = None
    Figure = None

# Amacım öğrendiklerimi pekiştirmek
# Bu kod bir sunucuya bağlıyor ve ondan veri çekiyor
# Çeşitli güvelik önlemleri var
# JWT kullanıyor
# Mesajlaşma sistemide eklemek istiyorum ve borsa ama önce sistem konrolü amacım
# Bazı kodları açıkladım
# Öncelikli olarak mesaj kutularını artırcam ve admin özelliklerini bitircem
# README zayıf bunu çözcem
# Baya def lerden karmaşaık bir kod oldu class yapıcağım

url = "http://127.0.0.1:8000" #Sunucunun ip si
APP_LOG_DIR = Path("logs")
APP_LOG_DIR.mkdir(exist_ok=True)
APP_LOG_FILE = APP_LOG_DIR / "app.log"

print("ekran açıldı") #Program başladımı diye
def app(): #Anasayfa fonksiyonu tüm kod burda sadece kod çağrılınca açalışsın diye 
    print("Anasyfa") #Fonksiyon çalıştığını anlamak için
    with open("token.json","r",encoding="utf-8") as tkn: #token json dosyasını açıyor
        sn_tk = json.load(tkn)  

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

    def istek_gonder(yol, veri):
        try:
            cevap = requests.post(url + yol, json=veri, timeout=5)
            veri_json = cevap.json()
            uygulama_logla("info", "http_request", f"{yol} -> {cevap.status_code}")
            return cevap.status_code, veri_json
        except requests.exceptions.RequestException as e:
            print("istek hatası", e)
            uygulama_logla("error", "http_error", f"{yol} -> {e}")
            return None, None
        except ValueError:
            print("geçersiz json")
            uygulama_logla("error", "bad_json", yol)
            return None, None

    def piyasa_verilerini_al():
        durum_kodu, cevap = istek_gonder("/market/list", {"token": sn_tk["Token"]})
        if durum_kodu == 200 and cevap and cevap.get("status") == "success":
            return cevap.get("assets", [])
        return []

    def metni_temizle(yazi_alani):
        yazi_alani.config(state="normal")
        yazi_alani.delete("1.0", tk.END)

    def metin_ekle(yazi_alani, metin):
        yazi_alani.insert(tk.END, metin + "\n")
        yazi_alani.config(state="disabled")

    def banka_islem_formu(parent, baslik, islem, alanlar, yenile_fonksiyonu, destek=False):
        pencere = tk.Toplevel(parent)
        pencere.title(baslik)
        pencere.geometry("420x420")
        pencere.resizable(False, False)

        girisler = {}

        tk.Label(pencere, text=baslik, font=("Arial", 16, "bold")).pack(pady=10)

        for alan in alanlar:
            tk.Label(pencere, text=alan["etiket"]).pack(anchor="w", padx=15)
            if alan.get("tip") == "text":
                widget = tk.Text(pencere, height=6)
                widget.pack(fill="both", expand=True, padx=15, pady=4)
            elif alan.get("tip") == "combo":
                widget = ttk.Combobox(pencere, values=alan.get("secenekler", []), state="readonly")
                if alan.get("secenekler"):
                    widget.set(alan["secenekler"][0])
                widget.pack(fill="x", padx=15, pady=4)
            else:
                widget = tk.Entry(pencere)
                if alan.get("gizli"):
                    widget.config(show="*")
                widget.pack(fill="x", padx=15, pady=4)
            girisler[alan["anahtar"]] = widget

        def gonder():
            veri = {"token": sn_tk["Token"]}
            if destek:
                veri["subject"] = girisler["subject"].get().strip()
                veri["message"] = girisler["message"].get("1.0", tk.END).strip()
                if not veri["subject"] or not veri["message"]:
                    messagebox.showerror("Hata", "Konu ve mesaj gerekli")
                    return
                durum_kodu, cevap = istek_gonder("/bank/support", veri)
            else:
                veri["action"] = islem
                if "amount" in girisler:
                    try:
                        veri["amount"] = float(girisler["amount"].get().strip())
                    except ValueError:
                        messagebox.showerror("Hata", "Geçerli bir tutar gir")
                        return
                if "quantity" in girisler:
                    try:
                        veri["quantity"] = float(girisler["quantity"].get().strip())
                    except ValueError:
                        messagebox.showerror("Hata", "Geçerli bir adet gir")
                        return
                if "asset_name" in girisler:
                    veri["asset_name"] = girisler["asset_name"].get().strip()
                if "asset_class" in girisler:
                    veri["asset_class"] = girisler["asset_class"].get().strip()
                if "term_months" in girisler:
                    try:
                        veri["term_months"] = int(girisler["term_months"].get().strip())
                    except ValueError:
                        messagebox.showerror("Hata", "Geçerli vade gir")
                        return
                if "recipient_number" in girisler:
                    veri["recipient_number"] = girisler["recipient_number"].get().strip()
                if "note" in girisler:
                    veri["note"] = girisler["note"].get().strip()
                if "notice_id" in girisler:
                    try:
                        veri["notice_id"] = int(girisler["notice_id"].get().strip())
                    except ValueError:
                        messagebox.showerror("Hata", "Geçerli bildirim ID gir")
                        return
                if "loan_id" in girisler:
                    try:
                        veri["loan_id"] = int(girisler["loan_id"].get().strip())
                    except ValueError:
                        messagebox.showerror("Hata", "Geçerli kredi ID gir")
                        return
                if "mode" in girisler:
                    veri["mode"] = girisler["mode"].get().strip()
                if islem == "transfer":
                    hedef_yol = "/bank/transfer"
                elif islem == "notice_pay":
                    hedef_yol = "/bank/notice/pay"
                elif islem == "loan_pay":
                    hedef_yol = "/bank/loan/pay"
                else:
                    hedef_yol = "/bank/action"
                durum_kodu, cevap = istek_gonder(hedef_yol, veri)

            if durum_kodu == 200 and cevap and cevap.get("status") == "success":
                messagebox.showinfo("Başarılı", "İşlem tamamlandı")
                pencere.destroy()
                yenile_fonksiyonu()
                return

            hata = "İşlem başarısız"
            if cevap and cevap.get("message"):
                hata = cevap["message"]
            messagebox.showerror("Hata", hata)

        tk.Button(pencere, text="Gönder", command=gonder).pack(pady=15)
        tk.Button(pencere, text="Kapat", command=pencere.destroy).pack()

    def banka_panel():
        pencere = tk.Toplevel()
        pencere.title("Banka Paneli")
        pencere.geometry("1180x980")
        pencere.resizable(False, False)

        market_assets = []
        market_history = []
        notices = []
        support_tickets = []

        baslik = tk.Label(pencere, text="Banka Paneli", font=("Arial", 18, "bold"))
        hesap_no_yazi = tk.Label(pencere, text="Hesap No: -", font=("Arial", 12, "bold"))
        bakiye_yazi = tk.Label(pencere, text="Bakiye: -", font=("Arial", 14, "bold"))
        durum_yazi = tk.Label(pencere, text="", fg="gray")

        ozet = tk.Text(pencere, height=16, width=120)
        piyasa = tk.Text(pencere, height=10, width=120)
        bildirim = tk.Text(pencere, height=8, width=120)
        destek = tk.Text(pencere, height=8, width=120)
        ozet.config(state="disabled")
        piyasa.config(state="disabled")
        bildirim.config(state="disabled")
        destek.config(state="disabled")

        def yenile():
            nonlocal market_assets, market_history, notices, support_tickets
            durum_kodu, cevap = istek_gonder("/bank/summary", {"token": sn_tk["Token"]})
            if durum_kodu != 200 or not cevap or cevap.get("status") != "success":
                messagebox.showerror("Hata", "Banka özeti alınamadı")
                return

            market_kodu, market_cevap = istek_gonder("/market/list", {"token": sn_tk["Token"]})
            history_kodu, history_cevap = istek_gonder("/market/history", {"token": sn_tk["Token"]})
            notice_kodu, notice_cevap = istek_gonder("/bank/notices", {"token": sn_tk["Token"]})
            destek_kodu, destek_cevap = istek_gonder("/bank/support/my", {"token": sn_tk["Token"]})
            market_assets = market_cevap.get("assets", []) if market_kodu == 200 and market_cevap and market_cevap.get("status") == "success" else []
            market_history = history_cevap.get("history", []) if history_kodu == 200 and history_cevap and history_cevap.get("status") == "success" else []
            notices = notice_cevap.get("notices", []) if notice_kodu == 200 and notice_cevap and notice_cevap.get("status") == "success" else []
            support_tickets = destek_cevap.get("tickets", []) if destek_kodu == 200 and destek_cevap and destek_cevap.get("status") == "success" else []

            bakiye = cevap.get("balance", 0)
            hesap_no = cevap.get("user_number") or sn_tk.get("Numara") or "-"
            hesap_no_yazi.config(text=f"Hesap No: {hesap_no}")
            bakiye_yazi.config(text=f"Bakiye: {bakiye} TL")
            durum_yazi.config(
                text=(
                    f"{len(cevap.get('transactions', []))} işlem, "
                    f"{len(cevap.get('loans', []))} kredi, "
                    f"{len(cevap.get('transfers', []))} transfer, "
                    f"{len(notices)} bildirim, "
                    f"{len(support_tickets)} destek"
                )
            )

            ozet.config(state="normal")
            ozet.delete("1.0", tk.END)
            ozet.insert(tk.END, "Son İşlemler\n")
            ozet.insert(tk.END, "-" * 95 + "\n")
            for islem in cevap.get("transactions", []):
                ozet.insert(
                    tk.END,
                    f"{islem['created_at']} | {islem['action_type']} | {islem['amount']} TL | {islem.get('asset_name') or '-'} | {islem.get('note') or '-'}\n",
                )
            ozet.insert(tk.END, "\nSon Transferler\n")
            ozet.insert(tk.END, "-" * 95 + "\n")
            for transfer in cevap.get("transfers", []):
                ozet.insert(
                    tk.END,
                    f"{transfer['created_at']} | {transfer['sender_number']} -> {transfer['receiver_number']} | {transfer['amount']} TL | {transfer.get('note') or '-'}\n",
                )
            ozet.insert(tk.END, "\nKrediler\n")
            ozet.insert(tk.END, "-" * 95 + "\n")
            for kredi in cevap.get("loans", []):
                ozet.insert(
                    tk.END,
                    f"{kredi['created_at']} | {kredi['amount']} TL | {kredi['term_months']} ay | Aylık: {kredi['monthly_payment']} TL | Kalan: {kredi.get('remaining_principal', 0)} | {kredi['status']}\n",
                )
            ozet.config(state="disabled")

            piyasa.config(state="normal")
            piyasa.delete("1.0", tk.END)
            piyasa.insert(tk.END, "Aktif Piyasa Varlıkları\n")
            piyasa.insert(tk.END, "-" * 95 + "\n")
            for varlik in market_assets:
                piyasa.insert(
                    tk.END,
                    f"{varlik['asset_class']} | {varlik['name']} | Kod: {varlik.get('symbol') or '-'} | Fiyat: {varlik['current_price']} TL\n",
                )
            piyasa.insert(tk.END, "\nFiyat Hareketleri\n")
            piyasa.insert(tk.END, "-" * 95 + "\n")
            for hareket in market_history[:20]:
                piyasa.insert(
                    tk.END,
                    f"{hareket['created_at']} | {hareket['asset_class']} | {hareket['asset_name']} | {hareket['direction']} | {hareket['old_price']} -> {hareket['new_price']} ({hareket['change_percent']}%)\n",
                )
            piyasa.config(state="disabled")

            bildirim.config(state="normal")
            bildirim.delete("1.0", tk.END)
            bildirim.insert(tk.END, "Vergi / Fatura Bildirimleri\n")
            bildirim.insert(tk.END, "-" * 95 + "\n")
            for notice in notices:
                bildirim.insert(
                    tk.END,
                    f"#{notice['id']} | {notice['notice_type']} | {notice['amount']} TL | {notice['status']} | {notice.get('due_at') or '-'} | {notice.get('description') or '-'}\n",
                )
            bildirim.config(state="disabled")

            destek.config(state="normal")
            destek.delete("1.0", tk.END)
            destek.insert(tk.END, "Destek Talepleri ve Cevaplar\n")
            destek.insert(tk.END, "-" * 95 + "\n")
            for talep in support_tickets:
                destek.insert(
                    tk.END,
                    f"#{talep['id']} | {talep['subject']} | {talep['status']} | Yanıt: {talep.get('admin_reply') or '-'}\nMesaj: {talep['message']}\n\n",
                )
            destek.config(state="disabled")

        def varliklari_goster_ve_sat():
            """Varlıkları görüp satmak için panel"""
            varlik_pencere = tk.Toplevel(pencere)
            varlik_pencere.title("Varlıklarım - Satış Paneli")
            varlik_pencere.geometry("800x500")
            varlik_pencere.resizable(True, True)

            tk.Label(varlik_pencere, text="Sahip Olduğunuz Varlıklar", font=("Arial", 14, "bold")).pack(pady=10)

            # Treeview ile tablo oluştur
            columns = ("Tür", "Varlık Adı", "Sembol", "Miktar", "Ort. Fiyat", "Toplam Değer")
            tree = ttk.Treeview(varlik_pencere, columns=columns, height=15)
            
            tree.column("#0", width=0, stretch=tk.NO)
            tree.column("Tür", anchor=tk.W, width=80)
            tree.column("Varlık Adı", anchor=tk.W, width=150)
            tree.column("Sembol", anchor=tk.W, width=80)
            tree.column("Miktar", anchor=tk.CENTER, width=80)
            tree.column("Ort. Fiyat", anchor=tk.CENTER, width=90)
            tree.column("Toplam Değer", anchor=tk.CENTER, width=100)

            tree.heading("#0", text="", anchor=tk.W)
            tree.heading("Tür", text="Tür", anchor=tk.W)
            tree.heading("Varlık Adı", text="Varlık Adı", anchor=tk.W)
            tree.heading("Sembol", text="Sembol", anchor=tk.W)
            tree.heading("Miktar", text="Miktar", anchor=tk.CENTER)
            tree.heading("Ort. Fiyat", text="Ort. Fiyat", anchor=tk.CENTER)
            tree.heading("Toplam Değer", text="Toplam Değer", anchor=tk.CENTER)

            # Kullanıcının varlıklarını al
            durum, varlik_cevap = istek_gonder("/bank/summary", {"token": sn_tk["Token"]})
            varliklar = []
            if durum == 200 and varlik_cevap:
                varliklar = varlik_cevap.get("assets", [])

            # Varlıkları treeview'a ekle
            for idx, varlik in enumerate(varliklar):
                toplam_deger = float(varlik.get("quantity", 0)) * float(varlik.get("average_price", 0))
                tree.insert(
                    parent="",
                    index="end",
                    iid=idx,
                    text="",
                    values=(
                        varlik.get("asset_class", "-"),
                        varlik.get("asset_name", "-"),
                        varlik.get("symbol", "-"),
                        f"{varlik.get('quantity', 0)}",
                        f"{varlik.get('average_price', 0)} TL",
                        f"{toplam_deger:.2f} TL"
                    )
                )

            tree.pack(fill="both", expand=True, padx=10, pady=10)

            # Alt bölüm - satış kontrolü
            kontrol_frame = tk.Frame(varlik_pencere)
            kontrol_frame.pack(fill="x", padx=10, pady=10)

            tk.Label(kontrol_frame, text="Satış Miktarı:").pack(side="left", padx=5)
            miktar_entry = tk.Entry(kontrol_frame, width=10)
            miktar_entry.pack(side="left", padx=5)

            def varligi_sat():
                secili = tree.selection()
                if not secili:
                    messagebox.showwarning("Uyarı", "Lütfen bir varlık seçin")
                    return
                
                try:
                    miktar = float(miktar_entry.get())
                    if miktar <= 0:
                        messagebox.showerror("Hata", "Miktar 0'dan büyük olmalı")
                        return
                except ValueError:
                    messagebox.showerror("Hata", "Geçerli bir miktar girin")
                    return

                secili_idx = secili[0]
                secili_varlik = varliklar[int(secili_idx)]
                
                if float(secili_varlik.get("quantity", 0)) < miktar:
                    messagebox.showerror("Hata", f"Yeterli varlık yok. Sahibiniz: {secili_varlik.get('quantity', 0)}")
                    return

                veri = {
                    "token": sn_tk["Token"],
                    "action": "stock_sell" if secili_varlik.get("asset_class") == "stock" else "gold_sell",
                    "asset_class": secili_varlik.get("asset_class"),
                    "asset_name": secili_varlik.get("asset_name"),
                    "quantity": miktar
                }

                durum, cevap = istek_gonder("/bank/action", veri)
                if durum == 200 and cevap and cevap.get("status") == "success":
                    tutar = cevap.get("total_revenue", 0)
                    messagebox.showinfo("Başarılı", f"{miktar} adet {secili_varlik.get('asset_name')} satıldı!\n\nAlınan Tutar: {tutar} TL")
                    yenile()
                    varlik_pencere.destroy()
                else:
                    hata = cevap.get("message", "İşlem başarısız") if cevap else "Sunucuya bağlanılamadı"
                    messagebox.showerror("Hata", hata)

            tk.Button(kontrol_frame, text="💰 Sat", command=varligi_sat, bg="#FF6B6B", fg="white", padx=15).pack(side="left", padx=5)
            tk.Button(kontrol_frame, text="❌ Kapat", command=varlik_pencere.destroy, padx=15).pack(side="left", padx=5)

        def destek_talebi():
            banka_islem_formu(
                pencere,
                "Destek Talebi",
                "support",
                [
                    {"anahtar": "subject", "etiket": "Konu"},
                    {"anahtar": "message", "etiket": "Mesaj", "tip": "text"},
                ],
                yenile,
                destek=True,
            )

        def para_gonder():
            banka_islem_formu(
                pencere,
                "Para Gönder",
                "transfer",
                [
                    {"anahtar": "recipient_number", "etiket": "Alıcı Hesap No"},
                    {"anahtar": "amount", "etiket": "Tutar"},
                    {"anahtar": "note", "etiket": "Açıklama"},
                ],
                yenile,
            )

        def bildirim_odeme():
            banka_islem_formu(
                pencere,
                "Vergi/Fatura Öde",
                "notice_pay",
                [{"anahtar": "notice_id", "etiket": "Bildirim ID"}],
                yenile,
            )

        def kredi_odeme():
            banka_islem_formu(
                pencere,
                "Kredi Öde",
                "loan_pay",
                [
                    {"anahtar": "loan_id", "etiket": "Kredi ID"},
                    {"anahtar": "mode", "etiket": "Ödeme Türü", "tip": "combo", "secenekler": ["monthly", "early"]},
                ],
                yenile,
            )

        def grafik_ac():
            if FigureCanvasTkAgg is None or Figure is None:
                messagebox.showerror("Hata", "Grafik için matplotlib gerekli")
                return

            pencere_grafik = tk.Toplevel(pencere)
            pencere_grafik.title("Artış / Azalış Grafiği")
            pencere_grafik.geometry("900x600")
            pencere_grafik.resizable(False, False)

            secenekler = [f"{varlik['asset_class']} | {varlik['name']}" for varlik in market_assets]
            secili = tk.StringVar(value=secenekler[0] if secenekler else "")
            secim = ttk.Combobox(pencere_grafik, values=secenekler, textvariable=secili, state="readonly")
            secim.pack(fill="x", padx=15, pady=10)

            fig = Figure(figsize=(8, 4.5), dpi=100)
            eksen = fig.add_subplot(111)
            canvas = FigureCanvasTkAgg(fig, master=pencere_grafik)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)

            def ciz():
                eksen.clear()
                secim_degeri = secili.get()
                if not secim_degeri:
                    canvas.draw()
                    return
                parcalar = secim_degeri.split(" | ", 1)
                if len(parcalar) != 2:
                    canvas.draw()
                    return
                varlik_turu, varlik_adi = parcalar
                filtrelenmis = [hareket for hareket in market_history if hareket["asset_class"] == varlik_turu and hareket["asset_name"] == varlik_adi]
                filtrelenmis = list(reversed(filtrelenmis))
                if not filtrelenmis:
                    eksen.set_title("Grafik verisi yok")
                    canvas.draw()
                    return
                y_degerleri = [hareket["new_price"] for hareket in filtrelenmis]
                x_degerleri = list(range(1, len(y_degerleri) + 1))
                renk = "green" if y_degerleri[-1] >= y_degerleri[0] else "red"
                eksen.plot(x_degerleri, y_degerleri, color=renk, marker="o")
                eksen.set_title(f"{varlik_turu} / {varlik_adi} fiyat değişimi")
                eksen.set_xlabel("Hareket")
                eksen.set_ylabel("Fiyat")
                eksen.grid(True, alpha=0.3)
                canvas.draw()

            secim.bind("<<ComboboxSelected>>", lambda _event: ciz())
            tk.Button(pencere_grafik, text="Çiz", command=ciz).pack(pady=5)
            ciz()

        def islemler():
            sekme = tk.Toplevel(pencere)
            sekme.title("Banka İşlemleri")
            sekme.geometry("420x620")
            sekme.resizable(False, False)

            stoklar = [varlik["name"] for varlik in market_assets if varlik["asset_class"] == "stock"]
            altinlar = [varlik["name"] for varlik in market_assets if varlik["asset_class"] == "gold"]

            tk.Label(sekme, text="Hızlı İşlemler", font=("Arial", 16, "bold")).pack(pady=10)
            tk.Button(
                sekme,
                text="Para Gönder",
                command=para_gonder,
            ).pack(fill="x", padx=20, pady=4)

            tk.Button(
                sekme,
                text="Vergi / Fatura Bildirimi Öde",
                command=bildirim_odeme,
            ).pack(fill="x", padx=20, pady=4)
            tk.Button(
                sekme,
                text="Hisse Al",
                command=lambda: banka_islem_formu(
                    sekme,
                    "Hisse Al",
                    "stock_buy",
                    [
                        {"anahtar": "asset_class", "etiket": "Tür", "tip": "combo", "secenekler": ["stock"]},
                        {"anahtar": "asset_name", "etiket": "Hisse Türü", "tip": "combo", "secenekler": stoklar or ["Yok"]},
                        {"anahtar": "quantity", "etiket": "Adet"},
                    ],
                    yenile,
                ),
            ).pack(fill="x", padx=20, pady=4)
            tk.Button(
                sekme,
                text="Altın Al",
                command=lambda: banka_islem_formu(
                    sekme,
                    "Altın Al",
                    "gold_buy",
                    [
                        {"anahtar": "asset_class", "etiket": "Tür", "tip": "combo", "secenekler": ["gold"]},
                        {"anahtar": "asset_name", "etiket": "Altın Türü", "tip": "combo", "secenekler": altinlar or ["Yok"]},
                        {"anahtar": "quantity", "etiket": "Adet"},
                    ],
                    yenile,
                ),
            ).pack(fill="x", padx=20, pady=4)
            tk.Button(
                sekme,
                text="Kredi Çek",
                command=lambda: banka_islem_formu(
                    sekme,
                    "Kredi Çek",
                    "loan",
                    [
                        {"anahtar": "amount", "etiket": "Kredi Tutarı"},
                        {"anahtar": "term_months", "etiket": "Vade (ay)"},
                    ],
                    yenile,
                ),
            ).pack(fill="x", padx=20, pady=4)
            tk.Button(
                sekme,
                text="Kredi Öde",
                command=kredi_odeme,
            ).pack(fill="x", padx=20, pady=4)
            tk.Button(
                sekme,
                text="Varlıkları Sat",
                command=varliklari_goster_ve_sat,
                bg="#FF6B6B",
                fg="white"
            ).pack(fill="x", padx=20, pady=4)
            tk.Button(
                sekme,
                text="Grafik",
                command=grafik_ac,
            ).pack(fill="x", padx=20, pady=4)
            tk.Button(sekme, text="Destek Talebi", command=destek_talebi).pack(fill="x", padx=20, pady=10)

        baslik.pack(pady=10)
        hesap_no_yazi.pack()
        bakiye_yazi.pack()
        durum_yazi.pack()
        tk.Button(pencere, text="Yenile", command=yenile).pack(pady=5)
        tk.Button(pencere, text="İşlemler", command=islemler).pack(pady=5)
        tk.Button(pencere, text="Para Gönder", command=para_gonder).pack(pady=5)
        tk.Button(pencere, text="Fatura Öde", command=bildirim_odeme).pack(pady=5)
        tk.Button(pencere, text="Kredi Öde", command=kredi_odeme).pack(pady=5)
        tk.Button(pencere, text="Varlık Sat", command=varliklari_goster_ve_sat, bg="#FF6B6B", fg="white").pack(pady=5)
        tk.Button(pencere, text="Grafik", command=grafik_ac).pack(pady=5)
        tk.Button(pencere, text="Destek", command=destek_talebi).pack(pady=5)
        tk.Label(pencere, text="Banka Hareketleri").pack()
        ozet.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Label(pencere, text="Piyasa ve Fiyat Hareketleri").pack()
        piyasa.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Label(pencere, text="Vergi / Fatura Bildirimleri").pack()
        bildirim.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Label(pencere, text="Destek Cevapları").pack()
        destek.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Button(pencere, text="Kapat", command=pencere.destroy).pack(pady=8)
        yenile()

    def admin_banka_panel():
        pencere = tk.Toplevel()
        pencere.title("Banka Yönetimi")
        pencere.geometry("1200x820")
        pencere.resizable(False, False)

        market_assets = []
        market_history = []

        baslik = tk.Label(pencere, text="Banka Yönetim Paneli", font=("Arial", 18, "bold"))
        ozet = tk.Text(pencere, height=34, width=130)
        ozet.config(state="disabled")

        def yenile():
            nonlocal market_assets, market_history
            hesaplar_kod, hesaplar = istek_gonder("/bank/admin/accounts", {"token": sn_tk["Token"]})
            islemler_kod, islemler = istek_gonder("/bank/admin/transactions", {"token": sn_tk["Token"]})
            krediler_kod, krediler = istek_gonder("/bank/admin/loans", {"token": sn_tk["Token"]})
            destek_kod, destek = istek_gonder("/bank/admin/support", {"token": sn_tk["Token"]})
            market_kod, market_cevap = istek_gonder("/market/list", {"token": sn_tk["Token"]})
            history_kod, history_cevap = istek_gonder("/market/history", {"token": sn_tk["Token"]})

            if any(kod != 200 for kod in (hesaplar_kod, islemler_kod, krediler_kod, destek_kod, market_kod, history_kod)):
                messagebox.showerror("Hata", "Banka yönetim verisi alınamadı")
                return

            if not all(resp and resp.get("status") == "success" for resp in (hesaplar, islemler, krediler, destek, market_cevap, history_cevap)):
                messagebox.showerror("Hata", "Banka yönetim verisi alınamadı")
                return

            market_assets = market_cevap.get("assets", [])
            market_history = history_cevap.get("history", [])

            ozet.config(state="normal")
            ozet.delete("1.0", tk.END)
            ozet.insert(tk.END, "Hesaplar\n")
            ozet.insert(tk.END, "-" * 110 + "\n")
            for hesap in hesaplar.get("accounts", []):
                ozet.insert(tk.END, f"{hesap['Nickname']} | Bakiye: {hesap['Balance']} TL | {hesap['updated_at']}\n")

            ozet.insert(tk.END, "\nSon İşlemler\n")
            ozet.insert(tk.END, "-" * 110 + "\n")
            for islem in islemler.get("transactions", [])[:20]:
                ozet.insert(
                    tk.END,
                    f"#{islem['id']} | {islem['Nickname']} | {islem['action_type']} | {islem['amount']} TL | {islem.get('asset_name') or '-'} | {islem.get('note') or '-'}\n",
                )

            ozet.insert(tk.END, "\nKrediler\n")
            ozet.insert(tk.END, "-" * 110 + "\n")
            for kredi in krediler.get("loans", []):
                ozet.insert(
                    tk.END,
                    f"#{kredi['id']} | {kredi['Nickname']} | {kredi['amount']} TL | {kredi['term_months']} ay | Aylık: {kredi['monthly_payment']} TL | {kredi['status']}\n",
                )

            ozet.insert(tk.END, "\nDestek Talepleri\n")
            ozet.insert(tk.END, "-" * 110 + "\n")
            for talep in destek.get("tickets", []):
                ozet.insert(
                    tk.END,
                    f"#{talep['id']} | {talep['Nickname']} | {talep['subject']} | {talep['status']} | {talep.get('admin_reply') or '-'}\n",
                )

            ozet.insert(tk.END, "\nPiyasa Varlıkları\n")
            ozet.insert(tk.END, "-" * 110 + "\n")
            for varlik in market_assets:
                ozet.insert(
                    tk.END,
                    f"{varlik['asset_class']} | {varlik['name']} | Kod: {varlik.get('symbol') or '-'} | Fiyat: {varlik['current_price']} TL | Aktif: {varlik['active']}\n",
                )

            ozet.insert(tk.END, "\nFiyat Hareketleri\n")
            ozet.insert(tk.END, "-" * 110 + "\n")
            for hareket in market_history[:20]:
                ozet.insert(
                    tk.END,
                    f"{hareket['created_at']} | {hareket['asset_class']} | {hareket['asset_name']} | {hareket['direction']} | {hareket['old_price']} -> {hareket['new_price']} ({hareket['change_percent']}%)\n",
                )

            ozet.config(state="disabled")

        def bakiye_duzenle():
            form = tk.Toplevel(pencere)
            form.title("Bakiye Düzenle")
            form.geometry("360x260")
            form.resizable(False, False)

            alanlar = {}
            for etik, anahtar in [
                ("Kullanıcı Adı", "target_user"),
                ("Tutar", "amount"),
                ("İşlem (credit/debit)", "action"),
                ("Not", "note"),
            ]:
                tk.Label(form, text=etik).pack(anchor="w", padx=15)
                giris = tk.Entry(form)
                giris.pack(fill="x", padx=15, pady=4)
                alanlar[anahtar] = giris

            def gonder():
                try:
                    amount = float(alanlar["amount"].get().strip())
                except ValueError:
                    messagebox.showerror("Hata", "Geçerli bir tutar gir")
                    return

                veri = {
                    "token": sn_tk["Token"],
                    "target_user": alanlar["target_user"].get().strip(),
                    "amount": amount,
                    "action": alanlar["action"].get().strip(),
                    "note": alanlar["note"].get().strip(),
                }
                durum_kodu, cevap = istek_gonder("/bank/admin/adjust", veri)
                if durum_kodu == 200 and cevap and cevap.get("status") == "success":
                    messagebox.showinfo("Başarılı", "Bakiye güncellendi")
                    form.destroy()
                    yenile()
                    return
                messagebox.showerror("Hata", (cevap or {}).get("message", "Bakiye güncellenemedi"))

            tk.Button(form, text="Güncelle", command=gonder).pack(pady=12)

        def destek_yaniti():
            form = tk.Toplevel(pencere)
            form.title("Destek Yanıtla")
            form.geometry("420x340")
            form.resizable(False, False)

            alanlar = {}
            for etik, anahtar in [
                ("Talep ID", "ticket_id"),
                ("Yanıt", "reply"),
                ("Durum", "status"),
            ]:
                tk.Label(form, text=etik).pack(anchor="w", padx=15)
                if anahtar == "reply":
                    giris = tk.Text(form, height=8)
                    giris.pack(fill="both", expand=True, padx=15, pady=4)
                else:
                    giris = tk.Entry(form)
                    giris.pack(fill="x", padx=15, pady=4)
                alanlar[anahtar] = giris

            def gonder():
                try:
                    ticket_id = int(alanlar["ticket_id"].get().strip())
                except ValueError:
                    messagebox.showerror("Hata", "Geçerli bir talep ID gir")
                    return
                reply = alanlar["reply"].get("1.0", tk.END).strip()
                if not reply:
                    messagebox.showerror("Hata", "Yanıt boş olamaz")
                    return
                veri = {
                    "token": sn_tk["Token"],
                    "ticket_id": ticket_id,
                    "reply": reply,
                    "status": alanlar["status"].get().strip() or "closed",
                }
                durum_kodu, cevap = istek_gonder("/bank/admin/support/reply", veri)
                if durum_kodu == 200 and cevap and cevap.get("status") == "success":
                    messagebox.showinfo("Başarılı", "Destek talebi güncellendi")
                    form.destroy()
                    yenile()
                    return
                messagebox.showerror("Hata", "Destek talebi güncellenemedi")

            tk.Button(form, text="Yanıtla", command=gonder).pack(pady=12)

        def bildirim_yaz():
            form = tk.Toplevel(pencere)
            form.title("Vergi / Fatura Yaz")
            form.geometry("420x420")
            form.resizable(False, False)

            alanlar = {}
            for alan in [
                {"anahtar": "target_user", "etiket": "Kullanıcı"},
                {"anahtar": "notice_type", "etiket": "Tür", "tip": "combo", "secenekler": ["tax", "bill"]},
                {"anahtar": "amount", "etiket": "Tutar"},
                {"anahtar": "due_days", "etiket": "Vade Günü"},
                {"anahtar": "description", "etiket": "Açıklama", "tip": "text"},
            ]:
                tk.Label(form, text=alan["etiket"]).pack(anchor="w", padx=15)
                if alan.get("tip") == "combo":
                    giris = ttk.Combobox(form, values=alan.get("secenekler", []), state="readonly")
                    giris.set(alan["secenekler"][0])
                    giris.pack(fill="x", padx=15, pady=4)
                elif alan.get("tip") == "text":
                    giris = tk.Text(form, height=5)
                    giris.pack(fill="both", expand=True, padx=15, pady=4)
                else:
                    giris = tk.Entry(form)
                    giris.pack(fill="x", padx=15, pady=4)
                alanlar[alan["anahtar"]] = giris

            def gonder():
                try:
                    amount = float(alanlar["amount"].get().strip())
                    due_days = int(alanlar["due_days"].get().strip())
                except ValueError:
                    messagebox.showerror("Hata", "Geçerli tutar ve gün gir")
                    return
                veri = {
                    "token": sn_tk["Token"],
                    "target_user": alanlar["target_user"].get().strip(),
                    "notice_type": alanlar["notice_type"].get().strip(),
                    "amount": amount,
                    "due_days": due_days,
                    "description": alanlar["description"].get("1.0", tk.END).strip(),
                }
                durum_kodu, cevap = istek_gonder("/bank/admin/notice", veri)
                if durum_kodu == 200 and cevap and cevap.get("status") == "success":
                    messagebox.showinfo("Başarılı", "Bildirim yazıldı")
                    form.destroy()
                    yenile()
                    return
                messagebox.showerror("Hata", "Bildirim yazılamadı")

            tk.Button(form, text="Yaz", command=gonder).pack(pady=12)

        def varlik_ekle():
            form = tk.Toplevel(pencere)
            form.title("Varlık Ekle")
            form.geometry("360x320")
            form.resizable(False, False)

            alanlar = {}
            for alan in [
                {"anahtar": "asset_class", "etiket": "Tür", "tip": "combo", "secenekler": ["stock", "gold"]},
                {"anahtar": "name", "etiket": "Ad"},
                {"anahtar": "symbol", "etiket": "Kod"},
                {"anahtar": "base_price", "etiket": "Başlangıç Fiyatı"},
            ]:
                tk.Label(form, text=alan["etiket"]).pack(anchor="w", padx=15)
                if alan.get("tip") == "combo":
                    giris = ttk.Combobox(form, values=alan.get("secenekler", []), state="readonly")
                    giris.set(alan["secenekler"][0])
                else:
                    giris = tk.Entry(form)
                giris.pack(fill="x", padx=15, pady=4)
                alanlar[alan["anahtar"]] = giris

            def gonder():
                try:
                    base_price = float(alanlar["base_price"].get().strip())
                except ValueError:
                    messagebox.showerror("Hata", "Geçerli bir fiyat gir")
                    return
                veri = {
                    "token": sn_tk["Token"],
                    "asset_class": alanlar["asset_class"].get().strip(),
                    "name": alanlar["name"].get().strip(),
                    "symbol": alanlar["symbol"].get().strip() or None,
                    "base_price": base_price,
                }
                durum_kodu, cevap = istek_gonder("/market/admin/add", veri)
                if durum_kodu == 200 and cevap and cevap.get("status") == "success":
                    messagebox.showinfo("Başarılı", "Varlık eklendi")
                    form.destroy()
                    yenile()
                    return
                messagebox.showerror("Hata", "Varlık eklenemedi")

            tk.Button(form, text="Ekle", command=gonder).pack(pady=12)

        baslik.pack(pady=10)
        tk.Button(pencere, text="Yenile", command=yenile).pack(pady=4)
        tk.Button(pencere, text="Bakiye Düzenle", command=bakiye_duzenle).pack(pady=4)
        tk.Button(pencere, text="Vergi/Fatura Yaz", command=bildirim_yaz).pack(pady=4)
        tk.Button(pencere, text="Destek Yanıtla", command=destek_yaniti).pack(pady=4)
        tk.Button(pencere, text="Varlık Ekle", command=varlik_ekle).pack(pady=4)
        ozet.pack(padx=10, pady=10, fill="both", expand=True)
        tk.Button(pencere, text="Kapat", command=pencere.destroy).pack(pady=8)
        yenile()

    def admin_panel(): #Admin özel panel
        
        if sn_tk["Rol"] == "admin": #Bir yetki ön doğrulaması

            def geridonad(): #Geri dönme fonksiyonu
                print("Geri dönüldü") #Bilgi için
                adm.destroy() #Eski pencereyi öldürüyor
                anasyfa.deiconify() #Anasayfayı geri açıyor

            def veri_panel(): # Admin panelden erişilen lot dan gelen verilerin paneli
                def veri_al(): # Veri almak için sunucu burda doğrulama  yapıyor eğer geçemezse app kapanır
                    print("veri_çekilecek") # Fonksiyon başladımı diye
                    try:
                        veriler = requests.post(url+"/veri", json={"token": sn_tk["Token"]}, timeout=5) # Sunucuya post gönderiyor
                        data = veriler.json() # Verileri jsondan python için çeviriyor
                    except requests.exceptions.RequestException as e:
                        print("veri alınamadı", e)
                        messagebox.showerror("Hata", "Sunucuya bağlanılamadı")
                        return
                    except ValueError:
                        print("geçersiz json")
                        messagebox.showerror("Hata", "Sunucudan geçersiz yanıt geldi")
                        return

                    if data["status"] == "success": # Data yazdıran kısım
                        print("tamamlandı doğrulama")
                        sicaklik = data.get("temperature")
                        nem = data.get("humidity")
                        guncelleme = data.get("updated_at") or "-"
                        if sicaklik is None or nem is None:
                            label_5.config(text="Henüz sensör verisi yok.")
                        else:
                            label_5.config(
                                text=(
                                    f"Sıcaklık: {sicaklik} °C\n"
                                    f"Nem: {nem} %\n"
                                    f"Güncelleme: {guncelleme}"
                                )
                            )
                        
                    else: # Doğrulamayı geçemezse ekranı kapatıyor
                        print("doğrulama hatası")
                        messagebox.showerror("Hata", "Doğrulama hatası")
                        return

                def geri_don(): # Admin panele geri dönme
                    print("geri dönüldü admin panel")
                    panel.destroy()
                    adm.deiconify()

                adm.withdraw() # Admin paneli gizliyor   
                print("veri panel açıldı") # Bilgi
                panel = tk.Toplevel() # Paneli oluşturuyor
                panel.title("Veri-Lot-Panel") # Panel ismi
                panel.geometry("700x450") # Normal pencere boyutu
                panel.resizable(False, False)
                panel.bind("<Escape>", lambda e: geri_don()) # ESC ile geridönme foksiyonu çalışıyor

                label_4 = tk.Label(panel, text= "veri panel") # label lar
                label_5 = tk.Label(panel, text="")
                buton_4 = tk.Button(panel, text="Güncelle", command=veri_al)

                label_4.pack() # Labellar görülsün diye
                label_5.pack()
                buton_4.pack()

            print("admin panel açıldı")
            label_3.config(text="")
            anasyfa.withdraw()
            adm = tk.Toplevel()
            adm.title("Admin Panel")
            adm.geometry("500x350")
            adm.resizable(False, False)
            adm.bind("<Escape>", lambda e: geridonad())

            label_2 = tk.Label(adm,text="Hogeldiniz")
            buton_3 = tk.Button(adm, text="Veri Panel", command=veri_panel)
            buton_4 = tk.Button(adm, text="Banka Yönetimi", command=admin_banka_panel)

            label_2.pack()
            buton_3.pack()
            buton_4.pack()

        else:
            print("Yetkiniz yok") #ön yetki kontrol
            label_3.config(text="Yetkiniz yok!")
            
    def bildirim_panosu():
        """Bildirim ve haberleri görmek için panel"""
        pencere = tk.Toplevel()
        pencere.title("Bildirim Panosu")
        pencere.geometry("900x600")
        pencere.resizable(True, True)

        # Üst bölüm - başlık
        baslik = tk.Label(pencere, text="📬 Bildirim Panosu", font=("Arial", 16, "bold"))
        baslik.pack(pady=10)

        # Sekme oluşturma
        notebook = ttk.Notebook(pencere)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Fatura/Vergi Bildirimleri Sekmesi
        bildirim_frame = tk.Frame(notebook)
        notebook.add(bildirim_frame, text="💳 Vergi/Fatura Bildirimleri")
        
        bildirim_text = tk.Text(bildirim_frame, height=20, width=100, state="disabled")
        bildirim_scroll = tk.Scrollbar(bildirim_frame, command=bildirim_text.yview)
        bildirim_text.config(yscrollcommand=bildirim_scroll.set)
        bildirim_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        bildirim_scroll.pack(side="right", fill="y")

        # Destek Talepleri Sekmesi
        destek_frame = tk.Frame(notebook)
        notebook.add(destek_frame, text="🎫 Destek Talepleri")
        
        destek_text = tk.Text(destek_frame, height=20, width=100, state="disabled")
        destek_scroll = tk.Scrollbar(destek_frame, command=destek_text.yview)
        destek_text.config(yscrollcommand=destek_scroll.set)
        destek_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        destek_scroll.pack(side="right", fill="y")

        # İşlem Özeti Sekmesi
        ozet_frame = tk.Frame(notebook)
        notebook.add(ozet_frame, text="📊 İşlem Özeti")
        
        ozet_text = tk.Text(ozet_frame, height=20, width=100, state="disabled")
        ozet_scroll = tk.Scrollbar(ozet_frame, command=ozet_text.yview)
        ozet_text.config(yscrollcommand=ozet_scroll.set)
        ozet_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        ozet_scroll.pack(side="right", fill="y")

        def yenile_bildirimler():
            """Tüm bildirimleri sunucudan al ve göster"""
            # Bildirimler
            bildirim_text.config(state="normal")
            bildirim_text.delete("1.0", tk.END)
            
            durum, cevap = istek_gonder("/bank/notices", {"token": sn_tk["Token"]})
            if durum == 200 and cevap and cevap.get("status") == "success":
                bildirimler = cevap.get("notices", [])
                if bildirimler:
                    bildirim_text.insert(tk.END, "VERGI VE FATURA BİLDİRİMLERİ\n")
                    bildirim_text.insert(tk.END, "=" * 90 + "\n\n")
                    for bildirim in bildirimler:
                        durum_renk = "✅ ÖDENDI" if bildirim.get("status") == "paid" else "⏳ ÖDENMEMIŞ"
                        bildirim_text.insert(tk.END, 
                            f"📌 {bildirim.get('notice_type', 'Bilinmiyor')}\n"
                            f"   Tutar: {bildirim.get('amount', 0)} TL\n"
                            f"   Durum: {durum_renk}\n"
                            f"   Tarih: {bildirim.get('created_at', '-')}\n"
                            f"   Açıklama: {bildirim.get('description', '-')}\n"
                            f"\n"
                        )
                else:
                    bildirim_text.insert(tk.END, "✨ Hiçbir bildirim yok!\n")
            else:
                bildirim_text.insert(tk.END, "❌ Bildirimler yüklenemedi.\n")
            
            bildirim_text.config(state="disabled")

            # Destek Talepleri
            destek_text.config(state="normal")
            destek_text.delete("1.0", tk.END)
            
            durum, cevap = istek_gonder("/bank/support/my", {"token": sn_tk["Token"]})
            if durum == 200 and cevap and cevap.get("status") == "success":
                destek_talepleri = cevap.get("tickets", [])
                if destek_talepleri:
                    destek_text.insert(tk.END, "DESTEK TALEPLERİ\n")
                    destek_text.insert(tk.END, "=" * 90 + "\n\n")
                    for destek in destek_talepleri:
                        durum_badge = "🟢 AÇIK" if destek.get("status") == "open" else "🟠 CEVAPLI"
                        destek_text.insert(tk.END,
                            f"🎫 {destek.get('subject', 'Başlık yok')}\n"
                            f"   Durum: {durum_badge}\n"
                            f"   Mesaj: {destek.get('message', '')}\n"
                            f"   Oluşturulma: {destek.get('created_at', '-')}\n"
                        )
                        if destek.get('admin_reply'):
                            destek_text.insert(tk.END, f"   💬 Cevap: {destek.get('admin_reply')}\n")
                        destek_text.insert(tk.END, "\n")
                else:
                    destek_text.insert(tk.END, "✨ Hiçbir destek talebiniz yok!\n")
            else:
                destek_text.insert(tk.END, "❌ Destek talepleri yüklenemedi.\n")
            
            destek_text.config(state="disabled")

            # İşlem Özeti
            ozet_text.config(state="normal")
            ozet_text.delete("1.0", tk.END)
            
            durum, cevap = istek_gonder("/bank/summary", {"token": sn_tk["Token"]})
            if durum == 200 and cevap and cevap.get("status") == "success":
                ozet_text.insert(tk.END, "HESAP ÖZETİ\n")
                ozet_text.insert(tk.END, "=" * 90 + "\n\n")
                ozet_text.insert(tk.END, f"💰 Bakiye: {cevap.get('balance', 0)} TL\n\n")
                
                ozet_text.insert(tk.END, "Son İşlemler:\n")
                ozet_text.insert(tk.END, "-" * 90 + "\n")
                islemler = cevap.get('transactions', [])
                if islemler:
                    for islem in islemler[:10]:
                        ozet_text.insert(tk.END,
                            f"  • {islem.get('action_type', 'İşlem')} - {islem.get('amount', 0)} TL"
                            f" ({islem.get('created_at', '-')})\n"
                        )
                else:
                    ozet_text.insert(tk.END, "  İşlem yok\n")
                
                ozet_text.insert(tk.END, "\n\nTransferler:\n")
                ozet_text.insert(tk.END, "-" * 90 + "\n")
                transferler = cevap.get('transfers', [])
                if transferler:
                    for transfer in transferler[:10]:
                        ozet_text.insert(tk.END,
                            f"  • {transfer.get('receiver_nickname', 'Bilinmiyor')} - {transfer.get('amount', 0)} TL"
                            f" ({transfer.get('created_at', '-')})\n"
                        )
                else:
                    ozet_text.insert(tk.END, "  Transfer yok\n")
            else:
                ozet_text.insert(tk.END, "❌ Özet yüklenemedi.\n")
            
            ozet_text.config(state="disabled")

        # Alt bölüm - butonlar
        button_frame = tk.Frame(pencere)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="🔄 Yenile", command=yenile_bildirimler, bg="#4CAF50", fg="white", padx=10).pack(side="left", padx=5)
        tk.Button(button_frame, text="❌ Kapat", command=pencere.destroy, bg="#f44336", fg="white", padx=10).pack(side="left", padx=5)

        # İlk yükleme
        yenile_bildirimler()

    def cıkıs():
        cevap = messagebox.askyesno("Çıkış", "Programdan çıkmak istiyor musunuz?")
        if cevap:              
              print("Çıkıldı")
              anasyfa.destroy()

    anasyfa = tk.Tk()
    anasyfa.title("Anasyfa")
    anasyfa.geometry("800x600")
    anasyfa.resizable(False, False)
    anasyfa.bind("<Escape>", lambda e: cıkıs())

    label_1 = tk.Label(anasyfa, text="Hoşgeldin" + " " + sn_tk["Kim"] + " | Hesap No: " + str(sn_tk.get("Numara", "-")))

    label_3 = tk.Label(anasyfa, text="")

    buton = tk.Button(anasyfa,text="Admin panel",command=admin_panel)

    buton_1 = tk.Button(anasyfa,text="Banka panel", command=banka_panel)

    buton_2 = tk.Button(anasyfa,text="Bildirim Panosu", command=bildirim_panosu)

    label_1.pack()
    buton.pack()
    buton_1.pack()
    buton_2.pack() 
    label_3.pack()  

    anasyfa.mainloop()
