# lan-screen-broadcast

Ayni yerel ag (ev Wi-Fi'si, bir hotspot, bir ofis agi) uzerindeki
bilgisayarlarin ekranina kisa mesajlar yayinlayan kucuk bir arac.
Tek bir bilgisayar (**sunucu**) mesajlari tutar; diger bilgisayarlar
(**istemciler**) bu mesajlari bir masaustu uygulamasiyla ya da bir
tarayici sekmesiyle goruntuler.

Internete veya ucuncu taraf bir servise ihtiyac duymaz, sadece yerel
agda calisir.

> **Onemli - dogru beklenti:** Bu arac, bir bilgisayarin baska bir
> bilgisayara/telefona *izinsiz, kurulumsuz* bir sekilde bir seyler
> gostermesini saglamaz; boyle bir sey hicbir isletim sisteminde
> mumkun degildir (kasitli bir guvenlik siniridir). Her istemci,
> mesajlari almak icin ya `listener.py`'yi bir kez calistirmis ya da
> sunucunun sayfasini bir kez tarayicida acmis olmalidir. Sadece
> **kendi** cihazlarinda veya izin verilen cihazlarda kullan.

## Nasil calisir

```
[server.py]  <-- POST /send --  [sender.py]
     |
     |  GET /poll (her saniye)
     v
[listener.py]  veya  [tarayicida http://<ip>:5000]
```

1. `server.py` bir bilgisayarda calisir, kucuk bir HTTP sunucusu acar
   ve gelen mesajlari hafizada tutar.
2. Diger bilgisayarlarda `listener.py` calisir; sunucuyu saniyede bir
   yoklar (`/poll`), yeni mesaj gelince ekranin kosesinde kisa sureli
   bir kutu gosterir. Tarayicida sunucunun adresini acmak da ayni isi
   gorur.
3. Sunucunun calistigi bilgisayardan `sender.py` ile mesaj gonderilir,
   tum baglı istemcilere birkac saniye icinde dagilir.

## Kurulum

### Sunucu bilgisayarinda (mesaji gonderecek olan)

```bash
pip install flask requests
python server.py
```

Baslarken terminalde su satiri gorursun:

```
 * Running on http://10.x.x.x:5000
```

Buradaki IP, **yerel agdaki IP adresin**. Bunu asagidaki "Yerel IP
adresini bulma" bolumune gore de teyit edebilirsin.

### Istemci bilgisayarlarda

```bash
pip install requests
```

`listener.py` icindeki `SUNUCU` degiskenini, sunucu bilgisayarin IP
adresine gore duzenle:

```python
SUNUCU = "http://10.192.5.26:5000"
```

Sonra calistir:

```bash
python listener.py
```

Python ve pip kurulu olmayan ya da hicbir sey kuramadigin cihazlarda
(ornegin baskasina ait bir telefon/bilgisayar), tarayicida sunucunun
adresini (`http://10.192.5.26:5000`) acip sekmeyi acik birakman
yeterlidir.

### tkinter eksikse (Linux)

```bash
# Arch / CachyOS
sudo pacman -S tk

# Debian / Ubuntu
sudo apt install python3-tk
```

## Kullanim

Sunucu ve en az bir istemci calisirken, sunucu bilgisayarindan:

```bash
python sender.py "merhaba, proje calisiyor"
```

Mesaj, baglı tum istemcilerin ekraninda birkac saniye icinde belirir.

### Su an bagli cihazlari gorme

`server.py`, kendisine `/poll` atan her cihazi (IP + tarayici/isletim
sistemi bilgisi + son yoklama zamani) hafizada tutar ve bunu `/clients`
ucundan gercek zamanli JSON olarak verir:

```bash
curl http://<SUNUCU_IP>:5000/clients
```

`sender.py`, mesaj gondermeden once bu ucu otomatik olarak sorar ve
animasyondaki "cihaz bulundu" satirinda **gercek** sayiyi ve her
cihazin IP'sini/kaba platform tahminini gosterir (ornegin
`iPhone (Safari/tarayici)`, `Android (tarayici)`,
`masaustu (listener.py)`). Hic cihaz bagli degilse bunu da acikca
soyler, sahte bir sayi uretmez.

**Sinirlamalar:**
- Ayni yerel IP'den (ayni NAT, ayni cihaz, ya da ayni makinede birden
  fazla sekme) gelen istekler tek bir kayit olarak gorunur; cihaz
  sayisi degil, **farkli IP** sayisi sayilir.
- Tarayicilar gizlilik nedeniyle gercek telefon modelini (`iPhone 15
  Pro` gibi) vermez; sadece genel isletim sistemi/tarayici turu
  cikarilabilir.
- Bir cihaz son 15 saniye icinde yoklamadiysa listede gorunmez
  (`ISTEMCI_ZAMAN_ASIMI`, `server.py` icinde degistirilebilir).

### Terminal animasyonu ve diller

`sender.py`, mesaj gonderilmeden once terminalde gosteri amacli bir
animasyon oynatir (sahte baglanti adimlari, ilerleme cubuklari, sahte
kod satirlari, basit bir ASCII simge). **Gercek bir ag taramasi veya
saldiri yapmaz**; tamamen gorsel bir efekttir.

Animasyon 4 dilde calisir. Dil kodu ilk argüman olarak verilir:

| Kod  | Dil        |
|------|------------|
| `tr` | Turkce (varsayilan) |
| `tk` | Turkmence  |
| `ru` | Rusca      |
| `en` | Ingilizce  |

```bash
python sender.py                        # varsayilan dil (tr), varsayilan mesaj
python sender.py "özel mesajım"         # varsayilan dil (tr), ozel mesaj
python sender.py tk                     # turkmence, turkmence varsayilan mesaj
python sender.py tk "ulanyjy"           # turkmence, ozel mesaj
python sender.py ru "привет"            # rusca, ozel mesaj
python sender.py en "it works"          # ingilizce, ozel mesaj
```

Her dilin kendi varsayilan "sonuc" mesaji vardir (ornegin Turkce icin
"ERİŞİM SAĞLANDI"); bir mesaj argumanı verildiginde o mesaj kullanilir,
sadece ekrandaki adim etiketleri (baglaniliyor, taraniyor, vb.) secilen
dile gore degisir.

## Yerel IP adresini bulma

**Linux / macOS**

```bash
ip a | grep "inet "
```

veya

```bash
hostname -I
```

Wi-Fi arayuzu genelde `wlan0` (Linux) ya da `en0` (macOS) olarak
gecer; `10.x.x.x` veya `192.168.x.x` ile baslayan adresi kullan.

**Windows**

```powershell
ipconfig
```

"Wireless LAN adapter Wi-Fi" altindaki "IPv4 Address" satirina bak.

**Not:** Bu adres genelde DHCP ile atanir ve zaman zaman degisebilir.
Degisirse `listener.py` icindeki `SUNUCU` satirini guncellemen gerekir.

## Bir Wi-Fi hotspot ile demo yapmak

Eger kendi agin yoksa veya bir grup insana ayni anda gostermek
istiyorsan, laptopunda bir hotspot acip herkesin ona baglanmasini
isteyebilirsin:

```bash
# NetworkManager ile (çoğu Linux masaustu dagitiminda hazir gelir)
nmcli device wifi hotspot ifname wlan0 ssid "Demo-Agi" password "demo1234"
```

Hotspot'un kendisine atadigi IP'yi `ip a` ile ogren, `server.py`'yi
calistir, baglanan herkese `listener.py`'yi calistirmasini veya
`http://<hotspot-ip>:5000` adresini tarayicida acmasini soyle.

Bu modda, hotspot'a baglanan cihazlarin gercek internete cikisi
genelde olmaz; bu beklenen bir durumdur, demo bittikten sonra herkes
kendi normal Wi-Fi'sine geri donebilir.

## Guvenlik notu

`server.py` herhangi bir kimlik dogrulama yapmaz. Ayni agdaki herkes
`/send` ucuna istek atarak mesaj gonderebilir. Bu yuzden:

- Sadece guvendigin, kucuk/kapali bir agda kullan.
- Genel/halka acik bir Wi-Fi'de calistirma.
- Uzun vadeli/gercek bir urun icin kullanmayacaksan (demo/egitim
  amacli), bu sinirlamalar yeterlidir.

## Dosyalar

| Dosya          | Nerede calisir            | Gorevi                                  |
|----------------|----------------------------|------------------------------------------|
| `server.py`    | Mesaji gonderen bilgisayar | Mesajlari tutan HTTP sunucusu            |
| `listener.py`  | Mesaji gorecek bilgisayarlar | Sunucuyu yoklar, ekranda kutu gosterir |
| `sender.py`    | Mesaji gonderen bilgisayar | Sunucuya yeni mesaj gonderir (4 dilli gosteri animasyonuyla) |

## Lisans

Bu kucuk proje, istediginiz gibi kullanabileceginiz, degistirebileceginiz
ve paylasabileceginiz basit bir ornektir (MIT benzeri, serbest kullanim).