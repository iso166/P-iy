import tkinter as tk
import anasayfa
import requests

print("hello")

url = "http://127.0.0.1:8000/"



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
        print(cevap.json())

        if cevap.status_code == 200:
            sonuc = cevap.json()
            print(sonuc)

            if sonuc.get("status") == "success":
                print("Giriş başarılı")
            else:
                print("Giriş başarısız")
        else:
            print("Server hatası")

    except requests.exceptions.RequestException as e:
        print("Bağlantı hatası:", e)

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
        print(durum.json())
        if durum.status_code == 200:
            sonuc = durum.json()
            print(sonuc)

            if sonuc.get("status") == "success":
                print("Giriş başarılı")
            else:
                print("Giriş başarısız")
        else:
            print("Server hatası")

    except requests.exceptions.RequestException as e:
        print("Bağlantı hatası:", e)

def kayıt_panel():
    
    print("Kayıt yapılıyor")

    pencere.withdraw()

    alt_pencere = tk.Toplevel()

    alt_pencere.title("Kayıt ol")

    alt_pencere.geometry("400x250")

    alt_pencere.resizable(False, False)

    def geridon():

        print("geri dönüldü")

        alt_pencere.destroy()

        pencere.deiconify()

    label_3 = tk.Label(
        alt_pencere,
        text="Kayıt ol",
        font=("Arial", 16, "bold")
    )

    label_4 = tk.Label(
        alt_pencere,
        text="Kullanıcı adı"
    )

    label_5 = tk.Label(
        alt_pencere,
        text="Şifre"
    )

    label_6 = tk.Label(
        alt_pencere,
        text="Şifreyi tekrarla"
    )    
    label_7 = tk.Label(
        alt_pencere,
        text="Mail"
    )
    entry_2 = tk.Entry(alt_pencere)

    entry_3 = tk.Entry(
        alt_pencere,
        show="*"
    )
    entry_4 = tk.Entry(
        alt_pencere,
        show="*"
    )
    entry_5 = tk.Entry(alt_pencere)

    button_2 = tk.Button(
        alt_pencere,
        text="Kayıt ol",
        command=lambda: kaydet_post(
            entry_2.get(),
            entry_3.get(),
            entry_4.get(),
            entry_5.get(),
        )
    )

    label_3.pack()
    label_4.pack()
    entry_2.pack()
    label_5.pack()
    entry_3.pack()
    label_6.pack()
    entry_4.pack()
    label_7.pack()
    entry_5.pack()
    button_2.pack()

    alt_pencere.protocol("WM_DELETE_WINDOW", geridon)


pencere = tk.Tk()

pencere.title("Giriş")

pencere.geometry("400x250")

pencere.resizable(False, False)

label_0 = tk.Label(
    text="Giriş",
    font=("Arial", 16, "bold")
)

label_1 = tk.Label(
    text="Kullanıcı Adı"
)

label_2 = tk.Label(
    text="Şifre"
)

entry_0 = tk.Entry()

entry_1 = tk.Entry(show="*")

button_0 = tk.Button(
    text="giriş",
    command=lambda: sorgu(
        entry_0.get(),
        entry_1.get()
    )
)

button_1 = tk.Button(
    text="Kayıt ol",
    command=kayıt_panel
)

label_0.pack()
label_1.pack()
entry_0.pack()
label_2.pack()
entry_1.pack()
button_0.pack()
button_1.pack()

x = 0

pencere.mainloop()