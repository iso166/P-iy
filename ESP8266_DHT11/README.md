# ESP8266_DHT11

Bu klasor, ESP8266 ile DHT11 sensöründen okunan sicaklik ve nem bilgisini sunucuya gondermek icin hazirlandi.

## Gerekli Kutuphanler

- ESP8266WiFi
- ESP8266HTTPClient
- DHT sensor library
- Adafruit Unified Sensor

## Baglanti

- DHT11 veri pini: `D4`
- VCC: `3.3V`
- GND: `GND`

## Ayarlanacak Degerler

`ESP8266_DHT11.ino` dosyasinda su alanlari degistirin:

- `WIFI_SSID`
- `WIFI_PASSWORD`
- `SERVER_URL`
- `DEVICE_KEY`

ESP8266 kodu veriyi 5 dakikada bir gonderir. Bu ayar `SEND_INTERVAL_MS` sabitinden kontrol edilir.

## Sunucu Notu

ESP8266 icin `SERVER_URL` adresi `127.0.0.1` olmamalidir.
Sunucunun calistigi bilgisayarin yerel IP adresini kullanin.

Ornek:

```text
http://192.168.1.10:8000/sensor/update
```

## Veri Akisi

1. ESP8266 DHT11 verisini okur.
2. `/sensor/update` endpointine JSON olarak yollar.
3. Sunucu bu veriyi `SensorOlcumleri` tablosuna kaydeder.
4. `Anasayfa` icindeki Veri Paneli `/veri` uzerinden son kayitli degeri okur.

## `ESP_DEVICE_KEY` Nedir?

Bu deger basit bir paylasilan gizli anahtardir.

- ESP8266 istek atarken bu anahtari JSON icinde yollar.
- Sunucu `.env` icindeki `ESP_DEVICE_KEY` ile gelen degeri karsilastirir.
- Degerler ayni degilse veri kabul edilmez.

Bu, cihazi tamamen profesyonel sekilde kimlik dogrulamaz ama rastgele bir cihazin sizin endpointinize veri yazmasini engeller.
