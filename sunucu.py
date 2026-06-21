from fastapi import FastAPI, Form, Cookie, Header, Response
from pydantic import BaseModel, EmailStr, Field
import mysql.connector
import bcrypt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import jwt

load_dotenv()  

db_user = os.getenv("DB_USER")      
db_password = os.getenv("DB_PASSWORD")
SECRET_KEY = os.getenv("KEY")
db_config ={
'host': 'localhost',
'user': db_user,
'password': db_password,
'database': 'testdb'
}

app = FastAPI()


sorgu_SQL = "SELECT Password , ROL FROM Kullanıcılar WHERE Nickname = %s"

def sorgu(girilen_kullanici, girilen_sifre):
        print("sorgu başladı")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("Başarılı bağlantı")
        if not girilen_kullanici or not girilen_sifre:
            print("boş")
            return False

        print("Sorgu başladı")
        cursor.execute(sorgu_SQL, (girilen_kullanici,))
        print("Sorgu bitii")

        sonuc = cursor.fetchone()

        if sonuc:

            db_sifre_hash = sonuc[0]
            db_rol = sonuc[1]
            if isinstance(db_sifre_hash, str):
                db_sifre_hash = db_sifre_hash.encode('utf-8')
                print("hash lendi")     
            girilen_sifre_bytes = girilen_sifre.encode('utf-8')
               
            if bcrypt.checkpw(girilen_sifre_bytes, db_sifre_hash):

                print(f"[BAŞARILI] Giriş yapıldı! Hoş geldiniz: {girilen_kullanici}")
                cursor.close()
                conn.close()
                payload = {
                    "sub": girilen_kullanici,
                    "rol": db_rol,
                    "exp": datetime.utcnow() + timedelta(minutes=120)
                }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                return token, db_rol, girilen_kullanici 
                
                
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
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    print("Bağlantı kuruldu")
    KAYIT_SQL = """
INSERT INTO Kullanıcılar (Nickname, Password, EMail, Rol)
VALUES (%s, %s, %s, %s)
"""

    if not yeni_kullanici or not yeni_sifre:

        print("[HATA] Kayıt için kullanıcı adı veya şifre boş bırakılamaz!")
        cursor.close()
        conn.close()
        return False

    if yeni_sifre != yeni_sifre2:
        print("şifreyi düzgün tekrarla")
        cursor.close()
        conn.close()
        return False

    try:

        sifre_bytes = yeni_sifre.encode('utf-8')

        tuz = bcrypt.gensalt()

        hashlenmis_sifre = bcrypt.hashpw(sifre_bytes, tuz)
        print("Hashlendi")
        cursor.execute(
            KAYIT_SQL,
            (yeni_kullanici, hashlenmis_sifre.decode('utf-8'),email,"normal")
        )
        print("Kayıt işemi yapılıyor")
        conn.commit()

        print(f"[BAŞARILI] {yeni_kullanici} başarıyla kayıt edildi!")
        
        return True

    except mysql.connector.Error as err:
        if err.errno == 1062:
                      
            print("[HATA] Bu kullanıcı adı zaten kullanılıyor!")
            return False
        else:
            
            print(f"[HATA] Veritabanı hatası: {err}")
            return False            
    finally:
        print("Bağlantıdan çıkıldı")
        cursor.close()
        conn.close()
class LoginData(BaseModel):
    username: str
    password: str
class SingupData(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8)
    password2: str
    mail: EmailStr    

@app.post("/login")
def login(data: LoginData):
    token, db_rol, girilenkullancı = sorgu(data.username, data.password)
    if token:
        print("Başarılı")
        return {"status": "success", "Token": token, "Rol": db_rol,"Kim": girilenkullancı}
    else:
        print("Giriş başarısız")            
    return {"status": "fail"}
@app.post("/singup")
def singup(data: SingupData):
    if kaydet_veritabani(data.username, data.password, data.password2, data.mail):
        print("Kayıt yapıldı")
        return {"status": "success"}
    print("Kayıt yapılamadı")
    return {"status": "fail"}