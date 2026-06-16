from fastapi import FastAPI, Form, Cookie, Header, Response
from pydantic import BaseModel
import mysql.connector
import bcrypt

import os
from dotenv import load_dotenv

load_dotenv()  

db_user = os.getenv("DB_USER")      
db_password = os.getenv("DB_PASSWORD")

db_config ={
'host': 'localhost',
'user': db_user,
'password': db_password,
'database': 'testdb'
}

app = FastAPI()

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

sorgu_SQL = "SELECT Password FROM Kullanıcılar WHERE Nickname = %s"

def sorgu(girilen_kullanici, girilen_sifre):
        print("sorgu başladı")

        if not girilen_kullanici or not girilen_sifre:
            print("boş")
            return False

        cursor.execute(sorgu_SQL, (girilen_kullanici,))

        sonuc = cursor.fetchone()

        if sonuc:

            db_sifre_hash = sonuc[0]

            if isinstance(db_sifre_hash, str):
                db_sifre_hash = db_sifre_hash.encode('utf-8')

            girilen_sifre_bytes = girilen_sifre.encode('utf-8')

            if bcrypt.checkpw(girilen_sifre_bytes, db_sifre_hash):

                print(f"[BAŞARILI] Giriş yapıldı! Hoş geldiniz: {girilen_kullanici}")
                cursor.close()
                conn.close()
                return True
                
                
            else:

                print("[HATA] Hatalı şifre yada kullanıcı adı!")
                cursor.close()
                conn.close()
                return False
                
                
        else:       

            print("[HATA] Hatalı şifre yada kullanıcı adı!")
            cursor.close()
            conn.close()
            return False
        
def kaydet_veritabani(yeni_kullanici, yeni_sifre, yeni_sifre2, email):

    print("Kayıt işlemi başladı...")

    KAYIT_SQL = """
INSERT INTO Kullanıcılar (Nickname, Password, EMail)
VALUES (%s, %s, %s)
"""

    if not yeni_kullanici or not yeni_sifre:

        print("[HATA] Kayıt için kullanıcı adı veya şifre boş bırakılamaz!")
        return False

    if yeni_sifre != yeni_sifre2:
        print("şifreyi düzgün tekrarla")
        return False

    try:

        sifre_bytes = yeni_sifre.encode('utf-8')

        tuz = bcrypt.gensalt()

        hashlenmis_sifre = bcrypt.hashpw(sifre_bytes, tuz)

        cursor.execute(
            KAYIT_SQL,
            (yeni_kullanici, hashlenmis_sifre.decode('utf-8'),email)
        )

        conn.commit()

        print(f"[BAŞARILI] {yeni_kullanici} başarıyla kayıt edildi!")
        return True

    except mysql.connector.Error as err:
        if err.errno == 1062:
            print("[HATA] Bu kullanıcı adı zaten kullanılıyor!")
        else:
            print(f"[HATA] Veritabanı hatası: {err}")            

class LoginData(BaseModel):
    username: str
    password: str
class SingupData(BaseModel):
    username: str
    password: str
    password2: str
    mail: str    

@app.post("/login")
def login(data: LoginData):
    if sorgu(data.username, data.password):
        return {"status": "success"}
    return {"status": "fail"}
@app.post("/singup")
def login(data: SingupData):
    if kaydet_veritabani(data.username, data.password, data.password2, data.mail):
        return {"status": "success"}
    return {"status": "fail"}