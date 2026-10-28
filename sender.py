"""
lan-screen-broadcast - gonderici (4 dilli)

server.py ile ayni bilgisayarda calistirilir ve /send ucuna bir mesaj
POST eder. Yerel agdaki tum listener.py istemcilerine ve acik
tarayici sekmelerine dagitilir.

Kullanim:
    python sender.py                          -> varsayilan dil (tr)
    python sender.py "mesajin"                -> varsayilan dil (tr)
    python sender.py <dil> "mesajin"          -> secilen dilde animasyon
    python sender.py <dil>                    -> o dilin varsayilan mesaji

Dil kodlari:
    tr -> Turkce
    tk -> Turkmence
    ru -> Rusca
    en -> Ingilizce

Ornekler:
    python sender.py tr "proje calisiyor"
    python sender.py tk
    python sender.py ru "привет"
    python sender.py en "it works"

Not: Asagidaki terminal animasyonu tamamen gosteri amaclidir, gercek
bir ag taramasi veya saldiri yapmaz; sadece mesaj gonderilmeden once
ekrana "hacker vibe" bir giris yazar. Koddaki ornek satirlar (IP,
sifreleme vb.) da sahte, calismayan ornek metinlerdir.
"""

import sys
import time
import random
import requests

SUNUCU = "http://127.0.0.1:5000"

HEX_KARAKTERLER = "0123456789abcdef"
SPIN_KARELERI = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


# ---------------------------------------------------------------------------
# Diller
# ---------------------------------------------------------------------------

LANG = {
    "tr": {
        "connecting": "suhan-net'e bağlanılıyor...",
        "step_session": "oturum başlatılıyor",
        "step_handshake": "bağlantı doğrulandı",
        "route": "rota: TR -> NL -> ?? -> yerel ağ",
        "scan": "ağ taranıyor",
        "step_devices": "{n} cihaz bulundu",
        "no_devices": "[!] şu an bağlı hiçbir cihaz görünmüyor (sunucu mu kapalı, yoksa kimse dinlemiyor mu?)",
        "pack": "payload paketleniyor",
        "step_encrypt": "şifreleme katmanı hazır",
        "wipe": "iz siliniyor",
        "sending": "yayınlanıyor",
        "step_delivered": "teslim edildi",
        "default_message": "BAĞLANTI KURULDU",
    },
    "tk": {
        "connecting": "suhan-net bilen baglanyşyk edilýär...",
        "step_session": "sessiýa başladylýar",
        "step_handshake": "baglanyşyk tassyklandy",
        "route": "ugur: TR -> NL -> ?? -> ýerli ulgam",
        "scan": "ulgam skanirlenýär",
        "step_devices": "{n} enjam tapyldy",
        "no_devices": "[!] häzir baglanan enjam ýok görünýär (serwer öçük bolup biler)",
        "pack": "ýük paketlenýär",
        "step_encrypt": "şifrleme gatlagy taýýar",
        "wipe": "yzlar pozulýar",
        "sending": "iberilýär",
        "step_delivered": "gowşuryldy",
        "default_message": "BAGLANYŞYK GURULDY",
    },
    "ru": {
        "connecting": "подключение к suhan-net...",
        "step_session": "инициализация сессии",
        "step_handshake": "соединение подтверждено",
        "route": "маршрут: TR -> NL -> ?? -> локальная сеть",
        "scan": "сканирование сети",
        "step_devices": "найдено {n} устройств",
        "no_devices": "[!] сейчас нет подключённых устройств (возможно, сервер выключен)",
        "pack": "упаковка payload",
        "step_encrypt": "слой шифрования готов",
        "wipe": "удаление следов",
        "sending": "отправка",
        "step_delivered": "доставлено",
        "default_message": "СОЕДИНЕНИЕ УСТАНОВЛЕНО",
    },
    "en": {
        "connecting": "connecting to suhan-net...",
        "step_session": "initializing session",
        "step_handshake": "connection verified",
        "route": "route: TR -> NL -> ?? -> local network",
        "scan": "scanning network",
        "step_devices": "{n} device(s) found",
        "no_devices": "[!] no devices currently connected (server down, or no one listening?)",
        "pack": "packaging payload",
        "step_encrypt": "encryption layer ready",
        "wipe": "wiping traces",
        "sending": "broadcasting",
        "step_delivered": "delivered",
        "default_message": "CONNECTION ESTABLISHED",
    },
}

# Sahte "kod" satirlari; her dilde ayni kaliyor (kod zaten evrensel gorunur).
SAHTE_KOD_1 = [
    "import socket, random, time",
    'target = "10.192.5." + str(random.randint(2, 254))',
    "sock.connect((target, 31337))",
    "handshake: SYN -> SYN/ACK -> ACK",
]
SAHTE_KOD_2 = [
    "10.192.5.14  windows-pc    [açık]",
    "10.192.5.22  macbook-pro   [açık]",
    "10.192.5.31  ubuntu-dev    [açık]",
]
SAHTE_KOD_3 = [
    "key = sha256(random_bytes(32))",
    "payload = encrypt(mesaj, key)",
    "mode: AES-256 // sadece gösteri",
]

def _cihaz_etiketi(user_agent: str) -> str:
    """User-Agent basliginden kaba bir isletim sistemi/tarayici tahmini.

    Not: Tarayicilar gizlilik nedeniyle tam telefon modelini (ornegin
    "iPhone 15 Pro") vermez; sadece genel platform/tarayici bilgisi
    cikarilabilir. Bu yuzden kesin bir cihaz adi degil, kaba bir tahmindir.
    """
    ua = (user_agent or "").lower()

    if "listener.py" in ua or "python-requests" in ua:
        isletim = "masaustu (listener.py)"
    elif "iphone" in ua:
        isletim = "iPhone (Safari/tarayici)"
    elif "ipad" in ua:
        isletim = "iPad (Safari/tarayici)"
    elif "android" in ua:
        isletim = "Android (tarayici)"
    elif "windows" in ua:
        isletim = "Windows (tarayici)"
    elif "macintosh" in ua or "mac os" in ua:
        isletim = "macOS (tarayici)"
    elif "linux" in ua:
        isletim = "Linux (tarayici)"
    else:
        isletim = "bilinmiyor"

    return isletim


def _bagli_cihazlari_al(sunucu: str) -> list:
    """server.py'den /clients ile su an bagli (son 15 sn icinde yoklayan)
    gercek cihaz listesini alir. Sunucuya ulasilamazsa bos liste doner."""
    try:
        oturum = requests.Session()
        oturum.trust_env = False
        r = oturum.get(f"{sunucu}/clients", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


# Orijinal, sade bir ASCII sekil; herhangi bir logo/markanin kopyasi degildir.
IKON = r"""
      .--'  '--.
     /  o    o  \
     \     ~     /
      '--------'
     [##########]
"""


# ---------------------------------------------------------------------------
# Yardimci fonksiyonlar (gorsel efektler)
# ---------------------------------------------------------------------------

def _hex_satir(uzunluk: int = 48) -> str:
    return "".join(random.choice(HEX_KARAKTERLER) for _ in range(uzunluk))


def _yaz(metin: str, gecikme: float = 0.012) -> None:
    for harf in metin:
        sys.stdout.write(harf)
        sys.stdout.flush()
        time.sleep(gecikme)
    print()


def _adim(etiket: str, sure: float = 0.9) -> None:
    """Donen bir spinner gosterir, sonunda yesil bir onay isaretine doner."""
    baslangic = time.time()
    i = 0
    dolgu = " " * max(0, 60 - len(etiket))
    while time.time() - baslangic < sure:
        kare = SPIN_KARELERI[i % len(SPIN_KARELERI)]
        sys.stdout.write(f"\r{kare} {etiket}{dolgu}")
        sys.stdout.flush()
        time.sleep(0.07)
        i += 1
    sys.stdout.write(f"\r✓ {etiket}{dolgu}\n")
    sys.stdout.flush()


def _ilerleme(etiket: str, sure: float = 2.0, genislik: int = 28) -> None:
    adim_sayisi = 40
    for i in range(1, adim_sayisi + 1):
        yuzde = int(i / adim_sayisi * 100)
        dolu = int(genislik * i / adim_sayisi)
        bar = "#" * dolu + "-" * (genislik - dolu)
        sys.stdout.write(f"\r{etiket} [{bar}] {yuzde:3d}%")
        sys.stdout.flush()
        time.sleep(sure / adim_sayisi)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _kod_blok(satirlar: list, ara_gecikme: float = 0.18) -> None:
    for satir in satirlar:
        _yaz("  " + satir, 0.01)
        time.sleep(ara_gecikme)


def intro(dil: str, sunucu: str) -> None:
    """Gorsel efekt + gercek cihaz sayisi icin tek bir /clients istegi.

    Animasyonun kendisi (spinner, ilerleme cubuklari, sahte IP/kod
    satirlari) hala tamamen gosteri amaclidir ve ag taramasi yapmaz.
    Ama "X cihaz bulundu" artik sahte degil: server.py'nin /clients
    ucundan, su an gercekten yoklayan (/poll atan) cihazlarin gercek
    sayisini ve kaba platform tahminini okur.
    """
    metin = LANG[dil]
    cihazlar = _bagli_cihazlari_al(sunucu)

    print("\n" + "=" * 54)
    for _ in range(6):
        print(_hex_satir())
        time.sleep(0.06)
    print("=" * 54)

    _yaz(metin["connecting"])
    _adim(metin["step_session"], 0.9)
    _adim(metin["step_handshake"], 0.75)

    _kod_blok(SAHTE_KOD_1)

    _yaz(metin["route"])
    _ilerleme(metin["scan"], 2.2)

    if cihazlar:
        # Gercek cihaz listesi: IP + kaba platform tahmini + kac saniye once yoklandi.
        gercek_satirlar = [
            f'{c["ip"]:<15} {_cihaz_etiketi(c["user_agent"]):<24} [{c["son_gorulme_once"]}s önce]'
            for c in cihazlar
        ]
        _kod_blok(gercek_satirlar)
        _adim(metin["step_devices"].format(n=len(cihazlar)), 0.6)
    else:
        # Sunucuya ulasilamadi ya da su an hic cihaz yoklamiyor; sahte sayi uretmek yerine durumu bildir.
        _yaz(metin["no_devices"])

    _ilerleme(metin["pack"], 2.0)

    _kod_blok(SAHTE_KOD_3)

    _adim(metin["step_encrypt"], 0.75)
    _ilerleme(metin["wipe"], 1.8)

    print(IKON)
    time.sleep(1.2)

    print("-" * 54)


# ---------------------------------------------------------------------------
# Gercek gonderim
# ---------------------------------------------------------------------------

def gonder(metin: str, dil: str) -> None:
    oturum = requests.Session()
    oturum.trust_env = False  # sistem proxy ayarlarini yok say

    cursor_satir = f'» {LANG[dil]["sending"]}: "{metin}"'
    _yaz(cursor_satir, 0.01)
    time.sleep(0.5)

    r = oturum.post(f"{SUNUCU}/send", data=metin.encode("utf-8"))

    if r.status_code == 200:
        _adim(f'{LANG[dil]["step_delivered"]} — 200 OK', 0.55)
    else:
        _adim(f"[!] hata ({r.status_code})", 0.4)

    print(metin)


# ---------------------------------------------------------------------------
# Giris noktasi
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    if args and args[0].lower() in LANG:
        dil = args[0].lower()
        mesaj = " ".join(args[1:]) or LANG[dil]["default_message"]
    else:
        dil = "tr"
        mesaj = " ".join(args) or LANG[dil]["default_message"]

    intro(dil, SUNUCU)
    gonder(mesaj, dil)