# P-iy

Python ogrenmek ve pekistirmek icin yapilmis kucuk bir giris sistemi projesi.

## Ne Yapar?

- `main.py` ile kullanici girisi yapar
- `anasayfa.py` ile giris sonrasi ana ekranı acar
- `sunucu.py` ile FastAPI uzerinden login, kayit ve yetki kontrolu saglar
- JWT token olusturur ve `token.json` dosyasina kaydeder
- Server ve istemci icin `logs/` altinda basit log dosyalari tutar
- ESP8266_DHT11 klasoru ile DHT11 sensor verisini sunucuya yollar
- Banka paneli ile para transferi, fatura/vergi bildirimleri, hisse, altin, kredi ve destek islemlerini yonetir
- Kullanici bazinda 8 haneli hesap numarasi üretir ve para transferi yapar
- Admin paneli hisse ve altin türlerini ekler, vergi/fatura bildirimleri olusturur ve destek yaniti verir
- Piyasa fiyatlari otomatik olarak güncellenir, artiş/azalış gecmisi tutulur ve grafik halinde gosterilir
- Krediler aylik olarak tahsil edilir, %5 faiz uygulanir ve erken kapatma destegi vardir
- Tahsil edilemeyen kredi durumunda kullanici bakiyesi ve varliklari `root` hesabina aktarilir

## Gereksinimler

- Python 3.10+
- MySQL
- Aşağıdaki Python paketleri:
  - `tkinter`
  - `requests`
  - `fastapi`
  - `uvicorn`
  - `mysql-connector-python`
  - `bcrypt`
  - `python-dotenv`
  - `PyJWT`
  - `pydantic`
  - `matplotlib`

## Kurulum

1. Sanal ortam olusturun ve aktif edin.
2. Paketleri kurun:

```bash
pip install -r requirements.txt
```

3. `.env.example` dosyasini `.env` olarak kopyalayin ve degerleri doldurun:

```env
DB_USER=kullanici_adi
DB_PASSWORD=sifre
KEY=jwt_gizli_anahtari
ESP_DEVICE_KEY=esp_icin_anahtar
```

4. MySQL'de `testdb` veritabanini ve `Kullanıcılar` tablosunu hazirlayin.
5. `Db/SensorOlcumleri.sql`, `Db/BankaTablolari.sql` ve `Db/KullaniciNumara.sql` dosyalarini calistirarak ilgili tabloları olusturun. Sunucu baslayinca bunlar yoksa kendisi de olusturmaya calisir.

## Calistirma

1. Sunucuyu baslatin:

```bash
uvicorn sunucu:app --reload
```

2. Ayrı bir terminalde istemciyi calistirin:

```bash
python main.py
```

## ESP8266 Sensor

- ESP8266 kodu `ESP8266_DHT11/ESP8266_DHT11.ino` icindedir.
- `SERVER_URL` alanina kendi bilgisayarinizin yerel IP adresini yazin.
- ESP cihazı `/sensor/update` endpointine veri yollar.
- ESP her 5 dakikada bir yeni veri gonderir ve sunucu bunu `SensorOlcumleri` tablosuna yazar.
- Admin panelindeki Veri Panel butonu `/veri` uzerinden son sicaklik ve nem bilgisini gosterir.
- `ESP_DEVICE_KEY`, ESP cihazindan gelen istegin basit bir paylasilan anahtarla dogrulanmasi icindir. Bu degeri `.env` ve ESP kodunda ayni tutarsaniz, sunucu yalnizca o cihazin gonderdigi sensor verisini kabul eder. Anahtar yoksa dogrulama devre disi kalir.

## Banka Paneli

- `Banka panel` butonu ile kullanici bakiye gorebilir ve islem yapabilir.
- Para gonderme, vergi, fatura, hisse alma, altin alma, kredi cekme ve destek talebi acma islemleri bulunur.
- Kullanici transferlerinde 8 haneli hesap numarasi kullanilir.
- Admin panelindeki `Banka Yönetimi` alt paneli tum hesaplari, islemleri, kredileri, destek taleplerini, piyasa varliklarini ve fiyat hareketlerini gosterir.
- Admin, kullanicilara vergi veya fatura bildirimi yazabilir; kullanici bunlari panelden odeme listesinde gorur.
- Destek talepleri icin admin yanitlari kullanici tarafinda ayni panelde gorunur.
- Admin, hesap bakiyesi duzenleyebilir, destek taleplerine yanit verebilir ve yeni hisse/altin türleri ekleyebilir.
- Piyasa fiyatlari otomatik olarak güncellenir ve degisim gecmisi tabloda tutulur.

## Notlar

- Uygulama varsayilan olarak `http://127.0.0.1:8000` adresine baglanir.
- `/singup` endpoint adi kodda bu sekilde yazilmis durumda.
- `token.json` giris sonrasi olusur; bu dosya yerel oturum bilgisi gibi kullanilir.

## Proje Yapisi

- `main.py`: giris ve kayit ekranı
- `anasayfa.py`: ana sayfa ve admin paneli
- `sunucu.py`: FastAPI sunucu ve veritabani islemleri
- `Db/`: veritabani dosyasi
