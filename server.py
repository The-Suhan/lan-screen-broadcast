"""
lan-screen-broadcast - sunucu

Bu betik, aynı Wi-Fi / yerel agda bulunan bilgisayarlara kisa mesajlar
yayinlamak icin basit bir HTTP sunucusudur. Internete veya herhangi bir
ucuncu taraf servise (ntfy.sh vb.) ihtiyac duymaz; sadece yerel agda calisir.

Calistirma:
    python server.py

Sunucu calisirken, ayni agdaki herhangi bir cihaz tarayicisinda:
    http://<BU_BILGISAYARIN_IP_ADRESI>:5000
adresini acarsa, mesajlari canli olarak gorur.

Mesaj gondermek icin (ayni bilgisayarda veya ayni agdaki baska bir
bilgisayardan) sender.py kullanilir.
"""

from flask import Flask, jsonify, request
import threading
import time

app = Flask(__name__)

# (mesaj_id, metin) ciftlerini tutan basit bir liste. Gercek bir veritabani
# degil, kucuk olcekli/demo kullanim icin yeterli.
olaylar = []
kilit = threading.Lock()

# IP -> {"user_agent": str, "son_gorulme": float} seklinde, /poll atan
# istemcileri tutan basit bir sozluk. Bir cihaz uzerinden kimlik dogrulama
# degil, sadece "su an kim yokluyor" bilgisi.
istemciler = {}
ISTEMCI_ZAMAN_ASIMI = 15  # saniye - bu sureden uzun yoklamayan "cevrimdisi" sayilir


def istemci_kaydet(ip: str, user_agent: str) -> None:
    with kilit:
        istemciler[ip] = {"user_agent": user_agent, "son_gorulme": time.time()}


def aktif_istemcileri_al() -> list:
    simdi = time.time()
    with kilit:
        return [
            {"ip": ip, "user_agent": v["user_agent"], "son_gorulme_once": round(simdi - v["son_gorulme"], 1)}
            for ip, v in istemciler.items()
            if simdi - v["son_gorulme"] <= ISTEMCI_ZAMAN_ASIMI
        ]

# Tarayicida acilacak, otomatik yenilenen siyah ekran sayfasi.
SAYFA = """
<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>lan-screen-broadcast</title>
<style>
  html,body{margin:0;height:100%;background:#000;overflow:hidden;
    font-family:ui-monospace,Consolas,monospace;color:#0f0}
  #box{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;
    font-size:6vw;text-align:center;padding:5vw;opacity:0;transition:opacity .4s}
  #box.show{opacity:1}
  #dot{position:fixed;bottom:10px;right:14px;width:10px;height:10px;border-radius:50%;
    background:#063;transition:background .3s}
  #dot.live{background:#0f0}
</style>
<body>
<div id=box></div>
<div id=dot title="baglanti durumu"></div>
<script>
let son = 0;
async function g(){
  try{
    const r = await fetch('/poll?since=' + son);
    const j = await r.json();
    document.getElementById('dot').classList.add('live');
    for (const o of j){
      son = o.id;
      const b = document.getElementById('box');
      b.textContent = o.text;
      b.classList.add('show');
      setTimeout(() => b.classList.remove('show'), 6000);
    }
  }catch(e){
    document.getElementById('dot').classList.remove('live');
  }
}
g(); setInterval(g, 1000);
</script>
"""


@app.get("/")
def index():
    return SAYFA


@app.post("/send")
def send():
    """Yeni bir mesaj ekler. Govde duz metin olarak gonderilir."""
    metin = request.get_data(as_text=True)
    if not metin:
        return "bos mesaj", 400
    with kilit:
        olaylar.append((len(olaylar) + 1, metin))
    return "ok"


@app.get("/poll")
def poll():
    """since parametresinden sonraki tum mesajlari dondurur."""
    # Bu istegi atan cihazi "su an bagli" olarak kaydet.
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "bilinmiyor"
    istemci_kaydet(ip, request.headers.get("User-Agent", ""))

    son = int(request.args.get("since", 0))
    with kilit:
        yeni = [{"id": i, "text": t} for i, t in olaylar if i > son]
    return jsonify(yeni)


@app.get("/clients")
def clients():
    """Son ISTEMCI_ZAMAN_ASIMI saniye icinde yoklayan cihazlarin listesi."""
    return jsonify(aktif_istemcileri_al())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)