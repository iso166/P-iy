import tkinter as tk
import mysql.connector
import bcrypt
import anasayfa
import os
from dotenv import load_dotenv

load_dotenv()  

db_user = os.getenv("DB_USER")      
db_password = os.getenv("DB_PASSWORD")  

print("hello")


class LoginApp:

    def __init__(self):
        self.x = 0
        self.db_config = {
            'host': 'localhost',
            'user': db_user,
            'password': db_password,
            'database': 'testdb'
        }

        self.conn = mysql.connector.connect(**self.db_config)

        self.cursor = self.conn.cursor()

        print("bağlantı tamam")

        self.sorgu_SQL = "SELECT Password FROM Kullanıcılar WHERE Nickname = %s"

        self.pencere = tk.Tk()

        self.pencere.title("Giriş")

        self.pencere.geometry("400x250")

        self.pencere.resizable(False, False)

        self.label_0 = tk.Label(
            text="Giriş",
            font=("Arial", 16, "bold")
        )

        self.label_1 = tk.Label(
            text="Kullanıcı Adı"
        )

        self.label_2 = tk.Label(
            text="Şifre"
        )

        self.entry_0 = tk.Entry()

        self.entry_1 = tk.Entry(show="*")

        self.button_0 = tk.Button(
            text="giriş",
            command=lambda: self.sorgu(
                self.entry_0.get(),
                self.entry_1.get()
            )
        )

        self.button_1 = tk.Button(
            text="Kayıt ol",
            command=self.kayıt_panel
        )

        self.label_0.pack()

        self.label_1.pack()

        self.entry_0.pack()

        self.label_2.pack()

        self.entry_1.pack()

        self.button_0.pack()

        self.button_1.pack()

        self.pencere.mainloop()

    def sorgu(self, girilen_kullanici, girilen_sifre):

        print("sorgu başladı")

        if not girilen_kullanici or not girilen_sifre:
            print("boş")
            return

        self.cursor.execute(self.sorgu_SQL, (girilen_kullanici,))

        sonuc = self.cursor.fetchone()

        if sonuc:

            db_sifre_hash = sonuc[0]

            if isinstance(db_sifre_hash, str):
                db_sifre_hash = db_sifre_hash.encode('utf-8')

            girilen_sifre_bytes = girilen_sifre.encode('utf-8')

            if bcrypt.checkpw(girilen_sifre_bytes, db_sifre_hash):

                print(f"[BAŞARILI] Giriş yapıldı! Hoş geldiniz: {girilen_kullanici}")
                self.x = 0
                self.cursor.close()
                self.conn.close()
                self.pencere.destroy()
                anasayfa.app()
            else:

                print("[HATA] Hatalı şifre yada kullanıcı adı!")
                self.hata_kontrol()
        else:       

            print("[HATA] Hatalı şifre yada kullanıcı adı!")
            self.hata_kontrol()

    def kaydet_veritabani(self, yeni_kullanici, yeni_sifre, alt_pencere):

        print("Kayıt işlemi başladı...")

        KAYIT_SQL = """
INSERT INTO Kullanıcılar (Nickname, Password)
VALUES (%s, %s)
"""

        if not yeni_kullanici or not yeni_sifre:

            print("[HATA] Kayıt için kullanıcı adı veya şifre boş bırakılamaz!")

            return

        try:

            sifre_bytes = yeni_sifre.encode('utf-8')

            tuz = bcrypt.gensalt()

            hashlenmis_sifre = bcrypt.hashpw(sifre_bytes, tuz)

            self.cursor.execute(
                KAYIT_SQL,
                (yeni_kullanici, hashlenmis_sifre.decode('utf-8'))
            )

            self.conn.commit()

            print(f"[BAŞARILI] {yeni_kullanici} başarıyla kayıt edildi!")

            alt_pencere.destroy()

            self.pencere.deiconify()

        except mysql.connector.Error as err:
            if err.errno == 1062:
                print("[HATA] Bu kullanıcı adı zaten kullanılıyor!")
            else:
                print(f"[HATA] Veritabanı hatası: {err}")

    def hata_kontrol(self):
        self.x += 1

        if self.x >= 5:
            print("[HATA] Çok fazla yanlış giriş!")
            self.pencere.withdraw()
            self.pencere.after(10000, self.pencere.deiconify)
            self.x = 0

    def kayıt_panel(self):
        
        print("Kayıt yapılıyor")

        self.pencere.withdraw()

        alt_pencere = tk.Toplevel()

        alt_pencere.title("Kayıt ol")

        alt_pencere.geometry("400x250")

        alt_pencere.resizable(False, False)

        def geridon():

            print("geri dönüldü")

            alt_pencere.destroy()

            self.pencere.deiconify()

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

        entry_2 = tk.Entry(alt_pencere)

        entry_3 = tk.Entry(
            alt_pencere,
            show="*"
        )

        button_2 = tk.Button(
            alt_pencere,
            text="Kayıt ol",
            command=lambda: self.kaydet_veritabani(
                entry_2.get(),
                entry_3.get(),
                alt_pencere
            )
        )

        label_3.pack()

        label_4.pack()

        entry_2.pack()

        label_5.pack()

        entry_3.pack()

        button_2.pack()

        alt_pencere.protocol("WM_DELETE_WINDOW", geridon)


LoginApp()