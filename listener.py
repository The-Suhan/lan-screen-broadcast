"""
lan-screen-broadcast - masaustu dinleyici (Windows / macOS / Linux)

Bu betik, server.py'nin calistigi bilgisayara yerel agdan baglanir ve
gelen her mesaji ekranin sol ust kosesinde kisa sureli, siyah-yesil
bir kutu olarak gosterir. Hicbir internet servisine (ntfy.sh vb.)
ihtiyac duymaz.

Kullanim:
    1. Asagidaki SUNUCU degiskenini, server.py'yi calistiran
       bilgisayarin yerel IP adresine gore ayarla.
    2. python listener.py

Gereksinimler:
    pip install requests
    (tkinter genelde Python ile birlikte gelir; Linux'ta eksikse:
     Arch/CachyOS:  sudo pacman -S tk
     Debian/Ubuntu: sudo apt install python3-tk)
"""

import sys
import time
import threading
import tkinter as tk

import requests

# server.py'yi calistiran bilgisayarin yerel Wi-Fi IP adresi.
# `ip a` (Linux/macOS) veya `ipconfig` (Windows) ile kontrol et.
SUNUCU = "http://10.192.5.26:5000"


def goster(metin: str) -> None:
    pen = tk.Toplevel(root)
    if sys.platform in ("win32", "darwin"):
        # Linux/Wayland'da overrideredirect pencereyi gizleyebildigi icin
        # sadece Windows ve macOS'ta kullaniliyor.
        pen.overrideredirect(True)
    pen.attributes("-topmost", True)
    pen.configure(bg="black", highlightbackground="#0f0", highlightthickness=2)
    tk.Label(
        pen, text=metin, fg="#0f0", bg="black",
        font=("Courier", 16, "bold"), padx=24, pady=16,
    ).pack()
    pen.geometry("+40+40")
    pen.update_idletasks()
    pen.lift()
    pen.after(5000, pen.destroy)


def dinle() -> None:
    oturum = requests.Session()
    oturum.trust_env = False  # sistem proxy ayarlarini yok say

    son = 0
    try:
        eski = oturum.get(f"{SUNUCU}/poll", timeout=5).json()
        if eski:
            son = eski[-1]["id"]
    except Exception as e:
        print("baslangic hatasi:", e)

    while True:
        try:
            yeni = oturum.get(f"{SUNUCU}/poll", params={"since": son}, timeout=5).json()
            for olay in yeni:
                son = olay["id"]
                print("geldi:", olay["text"])
                root.after(0, goster, olay["text"])
        except Exception as e:
            print("hata:", e)
        time.sleep(1)


root = tk.Tk()
root.withdraw()
threading.Thread(target=dinle, daemon=True).start()
root.mainloop()
