import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
import webbrowser
import json
import os
import uuid
import math
import subprocess
import random
import signal
import atexit
import time
from datetime import datetime
from pathlib import Path


class ButonUygulamasi:
    def __init__(self, ana_pencere):
        self.pencere = ana_pencere
        self.pencere.title("Spiral Buton Sistemi")
        self.pencere.geometry("1100x900")
        
        # Temel Değişkenler
        self.ana_dosya = "ana_kutu.json"
        self.dosya_yolu_listesi = [self.ana_dosya]
        self.isim_yolu_listesi = ["Ana Kutu"]
        self.veriler = self.ayarlari_yukle(self.ana_dosya)
        self.pixel_sanal = tk.PhotoImage(width=1, height=1)
        
        self.suruklenen_index = None
        self.fare_hareket_etti_mi = False
        self.secili_buton_index = None
        self.ses_hover = "/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"
        self.ses_click = "/usr/share/sounds/freedesktop/stereo/button-pressed.oga"
        # Renk ve Görsel Ayarlar
        self.RENK_BG = "#000000"
        self.RENK_MATRIX = "#1a1a1a"
        self.matrix_karakterler = "0123456789ABCDEFHIJKLMNOPQRSTUVWXYZ$+-*/=%#&@"
        self.char_boyutu = 20
        self.matrix_sutunlar = [] 
        self.matrix_hizi = 50 
        self.dalga_baslangic = time.time()
        
        # 1. ADIM: Tek bir ana Canvas oluştur (En alta)
        self.canvas = tk.Canvas(self.pencere, bg=self.RENK_BG, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # 2. ADIM: Butonların dizileceği Frame'i oluştur
        self.buton_alani = tk.Frame(self.canvas, bg=self.RENK_BG) 
        
        # 3. ADIM: Bu Frame'i Canvas'a "Pencere" olarak ekle (Merkezleme için)
        self.canvas_frame_id = self.canvas.create_window(
            (550, 450), 
            window=self.buton_alani, 
            anchor="center"
        )

        # Grid yapılandırması
        for i in range(200):
            self.buton_alani.grid_columnconfigure(i, weight=1)
            self.buton_alani.grid_rowconfigure(i, weight=1)

        # Alt Panel ve Etiketler (Canvas'ın üzerinde kalmaları için en son)
        self.bilgi_etiketi = tk.Label(self.pencere, text="", font=("Arial", 9, "italic"), fg="gray", bg=self.RENK_BG)
        self.bilgi_etiketi.pack(pady=5)

        self.alt_panel = tk.Frame(self.pencere, bg="#111111")
        self.alt_panel.pack(side="bottom", fill="x", pady=10)
        
        tk.Button(self.alt_panel, text="➕ Yeni Buton Ekle", command=self.yeni_buton_ekle, bg="#d4edda").pack(side="left", padx=10)
        self.geri_butonu = tk.Button(self.alt_panel, text="↑ Geri Çık", command=self.disari_cik, bg="#e1e1e1")

        
        
        
        # MÜZİK KONTROL BUTONU
        self.btn_muzik_dur = tk.Button(self.alt_panel, text="⏸ DURDUR", command=self.durdur_devam_et, bg="#000000", fg="#ffffff")
        self.btn_muzik_dur.pack(side="left", padx=10)
        
        tk.Button(self.alt_panel, text="⏭ SONRAKİ", command=self.sonraki_muzik, bg="#222222", fg="white").pack(side="left", padx=5)

        self.geri_butonu = tk.Button(self.alt_panel, text="↑ Geri Çık", command=self.disari_cik, bg="#e1e1e1")
        # Geri butonu ekrani_guncelle içinde otomatik paketlenecek.

        # PENCERE BOYUTU DEĞİŞİNCE MERKEZLEMEK İÇİN BIND
        self.pencere.bind("<Configure>", self.merkezle)

        # Sağ tık menüsü
        self.menu = tk.Menu(self.pencere, tearoff=0)
        self.menu.add_command(label="📥 İçine Gir", command=self.iceri_gir)
        self.menu.add_command(label="📝 Notlar", command=self.not_penceresi_ac)
        self.menu.add_command(label="⚙️ Düzenle", command=self.duzenle_penceresi_ac)
        self.menu.add_separator()
        self.menu.add_command(label="❌ Sil", command=self.buton_sil)

        # Müzik ve Zaman Birimleri
        self.muzik_aktif = True
        self.muzik_process = None
        self.su_anki_index = -1
        self.muzik_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), "muzikler")
        self.yerel_playlist = []
        self.playlist_tazele()

        self.birimler = [
            "YIL/AY/GÜN", "SAAT:DK:SN", "MİLİ (10⁻³)", "MİKRO (10⁻⁶)", "NANO (10⁻⁹)", "PLANCK (10⁻⁴⁴)"
        ]
        self.zaman_etiketleri = [] # Kuantum zaman etiketlerini buraya ekleyebilirsin
        self.gecmis = []


       # --- SAĞ ÜST KUANTUM SAAT PANELİ ---
        self.saat_over_frame = tk.Frame(self.alt_panel, bg="#111111", bd=0)
        
        # relx=0.5 (Yatayda orta), rely=0.5 (Alt panelin kendi dikey ortası)
        self.saat_over_frame.place(relx=0.5, rely=0.5, anchor="center")
        # 24 hane için Courier fontu (harf genişlikleri sabittir, kayma yapmaz)
        self.zaman_etiketi = tk.Label(self.saat_over_frame, text="", font=("Courier", 12, "bold"), 
                                     fg="#00FF41", bg="#000000", justify="right")
        self.zaman_etiketi.pack(anchor="e")

        # Başlatıcılar
        self.sidebar_sistemini_kur()

        self.firefox_temasini_yukle()
        self.sonraki_muzik() 
        self.muzik_kontrol_dongusu()
        self.kuantum_zaman_dongusu()
        self.matrix_animasyonu()
        self.ekrani_guncelle()

        self.pencere.protocol("WM_DELETE_WINDOW", self.programi_kapat)
        atexit.register(self.muzik_durdur_tamamen) # Program beklenmedik şekilde çökerse de durdurur
    # --- SIDEBAR METOTLARI ---
    # __init__ içinde self.sidebar_sistemini_kur() çağrısını unutmayın.


    def programi_kapat(self):
        """Program kapatılırken tüm yan süreçleri temizler."""
        self.muzik_durdur_tamamen()
        # Eğer başka subprocess süreçlerin varsa burada durdurabilirsin
        self.pencere.destroy()
        os._exit(0) # Tüm alt süreçlerle birlikte zorunlu çıkış

    def muzik_durdur_tamamen(self):
        if self.muzik_process:
            try:
                # Süreç grubunu komple öldür (ffplay ve bağlı olduğu shell)
                os.killpg(os.getpgid(self.muzik_process.pid), signal.SIGKILL)
            except Exception:
                try:
                    self.muzik_process.kill() # Alternatif yöntem
                except:
                    pass
            self.muzik_process = None
    
    def sidebar_sistemini_kur(self):
        self.paneller = {} 
        self.panel_genislik = 200
        self.ust_panel_yukseklik = 100
        # Alt panelin yaklaşık yüksekliği (pady ve içindeki butonlarla birlikte)
        self.alt_alan_payi = 45 
        self.aktif_panel = None
        self.kilitli_paneller = {"sol": False, "sag": False, "ust": False}

        # --- SOL SIDEBAR ---
        # highlightthickness=0 yaparak yeşil çizgiyi kaldırdık
        self.paneller["sol"] = tk.Frame(self.pencere, bg="#050505", highlightthickness=0)
        self.paneller["sol"].place(x=-self.panel_genislik, y=0, height=-self.alt_alan_payi, relheight=1, width=self.panel_genislik)
        # Beyaz Tutamaç (Sağ kenara dikey çubuk)
        tk.Frame(self.paneller["sol"], bg="white", width=3).pack(side="right", fill="y")
        self.sidebar_icerik_doldur(self.paneller["sol"], "SOL PANEL", "sol")

        # --- SAĞ SIDEBAR ---
        self.paneller["sag"] = tk.Frame(self.pencere, bg="#050505", highlightthickness=0)
        self.paneller["sag"].place(relx=1.0, y=0, height=-self.alt_alan_payi, relheight=1, width=self.panel_genislik)
        # Beyaz Tutamaç (Sol kenara dikey çubuk)
        tk.Frame(self.paneller["sag"], bg="white", width=3).pack(side="left", fill="y")
        self.sidebar_icerik_doldur(self.paneller["sag"], "SAĞ PANEL", "sag")

        # --- ÜST SIDEBAR ---
        self.paneller["ust"] = tk.Frame(self.pencere, bg="#050505", highlightthickness=0)
        self.paneller["ust"].place(x=0, y=-self.ust_panel_yukseklik, relwidth=1, height=self.ust_panel_yukseklik)
        # Beyaz Tutamaç (Alt kenara yatay çubuk)
        tk.Frame(self.paneller["ust"], bg="white", height=3).pack(side="bottom", fill="x")
        self.sidebar_icerik_doldur(self.paneller["ust"], "ÜST KONTROL", "ust", yatay=True)

        self.pencere.bind("<Motion>", self.fare_hareket_kontrol)

   

    def panel_kilitle(self, yon):
        # Durumu değiştir
        durum = not self.kilitli_paneller.get(yon, False)
        self.kilitli_paneller[yon] = durum
        self.efekt_cal(self.ses_click)

        # ARTIK ÇİZGİ YOK: Görsel geri bildirimi tutamacın rengini değiştirerek yapalım
        # Panelin içindeki ilk widget (tutamaç frame'i) rengini değiştirir
        for widget in self.paneller[yon].winfo_children():
            if isinstance(widget, tk.Frame) and widget.cget("bg") in ["white", "#FF0000"]:
                widget.config(bg="#FF0000" if durum else "white")
                break

    def ust_paneli_guncelle(self):
        w = self.pencere.winfo_width()
        x_baslangic = 0
        yeni_genislik = w

        # Yan panellerin koordinatlarına göre genişliği hesapla
        sol_acik = (self.paneller["sol"].winfo_x() >= 0)
        sag_limit = w - self.panel_genislik
        sag_acik = (self.paneller["sag"].winfo_x() <= sag_limit)

        if sol_acik:
            x_baslangic = self.panel_genislik
            yeni_genislik -= self.panel_genislik
        if sag_acik:
            yeni_genislik -= self.panel_genislik

        # KRİTİK KONTROL: Panel şu an görünür mü?
        su_anki_y = self.paneller["ust"].winfo_y()
        
        if su_anki_y >= 0:
            # Panel açıksa hem konumunu (y=0) hem genişliğini koru
            self.paneller["ust"].place(x=x_baslangic, y=0, width=yeni_genislik, relwidth=0)
        else:
            # Panel kapalıysa ekranın yukarısında tut, sadece genişliğini hazırla
            self.paneller["ust"].place(x=x_baslangic, y=-self.ust_panel_yukseklik, width=yeni_genislik, relwidth=0)

    def sidebar_icerik_doldur(self, parent, baslik, yon, yatay=False):
        # Kilit Butonu
        kilit_btn = tk.Button(parent, text="🔓", command=lambda y=yon: self.panel_kilitle(y), 
                              bg="#222222", fg="white", font=("Arial", 8, "bold"), width=5)
        kilit_btn.pack(side="top" if not yatay else "left", padx=5, pady=5)
        
        tk.Label(parent, text=baslik, fg="#00FF41", bg="#050505", font=("Arial", 9, "bold")).pack(side="top" if not yatay else "left", padx=10)
        
        # Örnek içerik
        if not yatay:
            tk.Button(parent, text="Seçenek A", bg="#111111", fg="white", relief="flat").pack(fill="x", pady=2, padx=5)
            tk.Button(parent, text="Seçenek B", bg="#111111", fg="white", relief="flat").pack(fill="x", pady=2, padx=5)
        else:
            tk.Button(parent, text="Hızlı Ayar 1", bg="#111111", fg="white", relief="flat").pack(side="left", padx=5)
            tk.Button(parent, text="Hızlı Ayar 2", bg="#111111", fg="white", relief="flat").pack(side="left", padx=5)

    

    

    def fare_hareket_kontrol(self, event):
        # Gerçek global koordinatları alıyoruz
        x_root = self.pencere.winfo_pointerx() - self.pencere.winfo_rootx()
        y_root = self.pencere.winfo_pointery() - self.pencere.winfo_rooty()
        
        w = self.pencere.winfo_width()
        h = self.pencere.winfo_height()
        
        kenar = 10 # Açılma sınırı
        pay = 40   # Kapanma payı (Dead-zone)

        # --- SOL PANEL KONTROL ---
        if x_root < kenar:
            self.panel_goster("sol")
        elif x_root > (self.panel_genislik + pay):
            self.panel_gizle("sol")

        # --- SAĞ PANEL KONTROL ---
        if x_root > (w - kenar):
            self.panel_goster("sag")
        elif x_root < (w - self.panel_genislik - pay):
            self.panel_gizle("sag")

        # --- ÜST PANEL KONTROL ---
        # Yanlışlıkla açılmaması için sadece merkez bölgede y < 10 ise açılır
        if y_root < kenar and 100 < x_root < (w - 100):
            self.panel_goster("ust")
        elif y_root > (self.ust_panel_yukseklik + pay):
            self.panel_gizle("ust")

    def panel_goster(self, yon):
        self.paneller[yon].tkraise()
        
        if yon == "sol":
            self.paneller["sol"].place(x=0, y=0, relheight=1)
        elif yon == "sag":
            self.paneller["sag"].place(relx=1.0, x=-self.panel_genislik, y=0, relheight=1)
        elif yon == "ust":
            # Üst panel açılırken genişliği tekrar hesapla
            self.ust_paneli_guncelle()
            return # ust_paneli_guncelle zaten place işlemini yapıyor

        # Yan panellerden biri açıldıysa üst paneli daralt/genişlet
        self.ust_paneli_guncelle()

    def panel_gizle(self, yon):
        if self.kilitli_paneller.get(yon, False):
            return

        if yon == "sol":
            self.paneller["sol"].place(x=-self.panel_genislik)
        elif yon == "sag":
            self.paneller["sag"].place(relx=1.0, x=0)
        elif yon == "ust":
            self.paneller["ust"].place(y=-self.ust_panel_yukseklik)
        
        # Yan panellerden biri kapandıysa üst paneli genişlet
        self.ust_paneli_guncelle()

    def panel_kilitle(self, yon):
        # Durumu değiştir
        durum = not self.kilitli_paneller.get(yon, False)
        self.kilitli_paneller[yon] = durum
        self.efekt_cal(self.ses_click)

        # Kilitli olduğunu görsel olarak belli et (Kenarlık rengi değişir)
        yeni_renk = "#FF0000" if durum else "#00FF41" # Kilitliyse Kırmızı, değilse Matrix Yeşili
        self.paneller[yon].config(highlightbackground=yeni_renk)

    def panel_goster(self, yon):
        # Eğer açılmak istenen panel zaten aktifse veya kilitliyse işlem yapma (Titremeyi önler)
        if self.aktif_panel == yon:
            return

        # DİĞER PANELLERİ KONTROL ET:
        # Sadece kilitli OLMAYAN ve şu an açık olan panelleri gizle
        for p_yon in ["sol", "sag", "ust"]:
            if p_yon != yon: # Açmaya çalıştığımız panel dışındakiler
                if not self.kilitli_paneller.get(p_yon, False):
                    # Kilitli değilse, bu paneli dışarı it (Kapat)
                    self.pasif_konuma_it(p_yon)

        # Seçilen paneli EN ÜSTE getir (Butonların fareyi çalmasını engeller)
        self.paneller[yon].tkraise() 
        
        # Paneli içeri sür (Görünür yap)
        if yon == "sol":
            self.paneller["sol"].place(x=0, y=0, relheight=1)
        elif yon == "sag":
            self.paneller["sag"].place(relx=1.0, x=-self.panel_genislik, y=0, relheight=1)
        elif yon == "ust":
            self.paneller["ust"].place(x=0, y=0, relwidth=1)
        
        self.aktif_panel = yon

    def pasif_konuma_it(self, yon):
        """Paneli animasyonsuz/sessizce ekran dışına iter (Kilitli değilse)"""
        if yon == "sol":
            self.paneller["sol"].place(x=-self.panel_genislik)
        elif yon == "sag":
            self.paneller["sag"].place(relx=1.0, x=0)
        elif yon == "ust":
            self.paneller["ust"].place(y=-self.ust_panel_yukseklik)

    

    def merkezle(self, event=None):
        """Pencere boyutu ne olursa olsun spiral alanını merkeze çeker."""
        w = self.pencere.winfo_width()
        h = self.pencere.winfo_height()
        # Canvas üzerindeki pencere nesnesinin koordinatlarını güncelle
        self.canvas.coords(self.canvas_frame_id, w // 2, h // 2)


    def efekt_cal(self, dosya_yolu):
        if os.path.exists(dosya_yolu):
            try:
                subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", dosya_yolu],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except: pass

    def playlist_tazele(self):
        desteklenenler = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
        if os.path.exists(self.muzik_klasoru):
            self.yerel_playlist = [os.path.join(self.muzik_klasoru, f) for f in os.listdir(self.muzik_klasoru) if f.lower().endswith(desteklenenler)]
            random.shuffle(self.yerel_playlist)
        else: os.makedirs(self.muzik_klasoru, exist_ok=True)

    def firefox_temasini_yukle(self):
        try:
            ff_path = Path.home() / ".mozilla/firefox"
            if not ff_path.exists(): return
            profiles = [p for p in ff_path.glob("*.default-release")] or [p for p in ff_path.glob("*.default")]
            for profile in profiles:
                chrome_path = profile / "chrome"
                chrome_path.mkdir(exist_ok=True)
                css_content = ":pencere { --toolbar-bgcolor: #000000 !important; --toolbar-color: #00FF41 !important; }"
                with open(chrome_path / "userChrome.css", "w") as f: f.write(css_content)
        except: pass
    
    def kuantum_zaman_dongusu(self):
        try:
            # Zamanı al
            t_ns = time.time_ns()
            simdi = datetime.fromtimestamp(t_ns / 1e9)
            derinlik = len(self.dosya_yolu_listesi)

            if derinlik == 1:
                # 1. KATMAN: YIL.AY.GÜN
                gosterilecek_metin = simdi.strftime("%Y.%m.%d")
            
            elif derinlik == 2:
                # 2. KATMAN: SAAT:DAKİKA:SANİYE
                gosterilecek_metin = simdi.strftime("%H:%M:%S")
            
            elif derinlik == 3:
                # 3. KATMAN: MİLİ | MİKRO | NANO
                # Sola yaslı 8 hane akış
                mili = f"{(t_ns // 1000000) % 100000000:0<8}"
                mikro = f"{(t_ns // 1000) % 100000000:0<8}"
                nano = f"{t_ns % 100000000:0<8}"
                gosterilecek_metin = f"ML:{mili} | MK:{mikro} | NN:{nano}"
            
            else:
                # 4. KATMAN VE ÖTESİ: PİKO | FEMTO | ATTO
                piko = f"{(t_ns * 1000) % 100000000:0<8}"
                femto = f"{(t_ns * 1000000) % 100000000:0<8}"
                atto = f"{(t_ns * 1000000000) % 100000000:0<8}"
                gosterilecek_metin = f"PK:{piko} | FM:{femto} | AT:{atto}"

            # Arayüzü güncelle
            if hasattr(self, 'zaman_etiketi'):
                self.zaman_etiketi.config(text=gosterilecek_metin)

        except Exception as e:
            # Hata varsa terminale bas ama döngüyü bozma
            print(f"Zamanlama Hatası: {e}")

        # KRİTİK: Bu satır try-except dışında olmalı ki hata olsa bile döngü sürsün
        self.pencere.after(10, self.kuantum_zaman_dongusu)
        
    def muzik_cal(self):
        self.muzik_durdur_tamamen()
        if self.muzik_aktif and self.yerel_playlist:
            try: self.muzik_process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", self.yerel_playlist[self.su_anki_index]], preexec_fn=os.setsid)
            except: pass

    def muzik_durdur_tamamen(self):
        if self.muzik_process:
            try: os.killpg(os.getpgid(self.muzik_process.pid), signal.SIGKILL)
            except: pass
            self.muzik_process = None

    def sonraki_muzik(self):
        if not self.yerel_playlist: self.playlist_tazele()
        if self.yerel_playlist: self.su_anki_index = (self.su_anki_index + 1) % len(self.yerel_playlist); self.muzik_cal()

    def muzik_kontrol_dongusu(self):
        if self.muzik_aktif:
            if self.muzik_process is None or self.muzik_process.poll() is not None: 
                self.sonraki_muzik()
        self.pencere.after(1000, self.muzik_kontrol_dongusu)

    def durdur_devam_et(self):
        # Tıklama sesini çal
        self.efekt_cal(self.ses_click)
        
        if self.muzik_aktif: 
            self.muzik_durdur_tamamen()
            if hasattr(self, 'btn_muzik_dur'):
                self.btn_muzik_dur.config(text="▶ OYNAT", bg="#ffffff", fg="#000000")
            self.muzik_aktif = False
        else: 
            self.muzik_aktif = True
            self.muzik_cal()
            if hasattr(self, 'btn_muzik_dur'):
                self.btn_muzik_dur.config(text="⏸ DURDUR", bg="#000000", fg="#ffffff")

    def matrix_animasyonu(self):
        self.canvas.delete("matrix_char")
        w, h = self.pencere.winfo_width(), self.pencere.winfo_height()
        sutun_sayisi = max(1, w // self.char_boyutu)
        while len(self.matrix_sutunlar) < sutun_sayisi: self.matrix_sutunlar.append(random.randint(0, 50))

        # DALGA EFEKTİ MANTIĞI (30 Saniyelik Periyot)
        if self.muzik_aktif:
            gecen_sure = time.time() - self.dalga_baslangic
            # Sinüs dalgası: 0 ile 1 arası değer üretir, bunu 10ms ile 50ms arasına yayarız
            dalga = (math.sin(2 * math.pi * gecen_sure / 30) + 1) / 2
            self.matrix_hizi = int(50 - (dalga * 40)) # 50'den 10'a iner ve çıkar
        else:
            self.matrix_hizi = 50

        for i in range(min(len(self.matrix_sutunlar), sutun_sayisi)):
            char = random.choice(self.matrix_karakterler)
            x, y = i * self.char_boyutu + 10, self.matrix_sutunlar[i] * self.char_boyutu
            self.canvas.create_text(x, y, text=char, fill=self.RENK_MATRIX, font=("Courier", 14, "bold"), tags="matrix_char")
            if y > h or random.random() > 0.98: self.matrix_sutunlar[i] = 0
            else: self.matrix_sutunlar[i] += 1
        self.canvas.tag_lower("matrix_char")
        self.pencere.after(self.matrix_hizi, self.matrix_animasyonu)

    def ayarlari_yukle(self, dosya_adi):
        if os.path.exists(dosya_adi):
            try:
                with open(dosya_adi, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"butonlar": []}

    def ayarlari_kaydet(self):
        with open(self.dosya_yolu_listesi[-1], "w", encoding="utf-8") as f:
            json.dump(self.veriler, f, ensure_ascii=False, indent=4)

    def ekrani_guncelle(self):
        # Ekranı temizle
        for widget in self.buton_alani.winfo_children():
            widget.destroy()

        

        konum_metni = " > ".join(self.isim_yolu_listesi)
        self.bilgi_etiketi.config(text=f"Konum: {konum_metni}")

        # --- SPIRAL ALGORİTMASI ---
        x, y = 100, 100 # Merkez koordinat (grid üzerinde)
        dx, dy = 0, 1   # Başlangıç yönü (Aşağı)
        adim_uzunlugu = 1
        adim_sayaci = 0
        donus_sayaci = 0
        
        buton_listesi = self.veriler.get("butonlar", [])
        
        for idx, b in enumerate(buton_listesi):
            # Butonu oluştur
            btn = tk.Button(
                self.buton_alani, text=b["ad"], image=self.pixel_sanal,
                compound="center", width=80, height=50,
                bg=b.get("bg", "#f0f0f0"), fg=b.get("fg", "black"),
                font=("Arial", 8, "bold"), relief="raised", wraplength=70
            )
            # Grid'e yerleştir
            btn.grid(row=y, column=x, padx=5, pady=5)
            
            

            # Spiral bir sonraki koordinatı hesapla
            x += dx
            y += dy
            adim_sayaci += 1
            
            if adim_sayaci == adim_uzunlugu:
                adim_sayaci = 0
                # Yön değiştir (Saat yönünde: Aşağı -> Sol -> Yukarı -> Sağ)
                dx, dy = -dy, dx 
                donus_sayaci += 1
                if donus_sayaci == 2:
                    donus_sayaci = 0
                    adim_uzunlugu += 1

            # --- SES EFEKTLERİ BAĞLANTISI ---
            # Fare üzerine gelince (Hover)
            btn.bind("<Enter>", lambda e: self.efekt_cal(self.ses_hover))
            
            # Tıklayınca (Click) - Mevcut surukle_baslat içine de ekleyebilirsin ama garanti olsun:
            btn.bind("<Button-1>", lambda e, i=idx: [self.efekt_cal(self.ses_click), self.surukle_baslat(e, i)], add="+")

            #-- TEKERLEK BAĞLANTILARI (WINDOWS + LINUX) ---
            btn.bind("<MouseWheel>", lambda e, i=idx: self.tekerlek_sirala(e, i)) # Windows & MacOS
            btn.bind("<Button-4>", lambda e, i=idx: self.tekerlek_sirala(e, i))   # Linux Yukarı
            btn.bind("<Button-5>", lambda e, i=idx: self.tekerlek_sirala(e, i))   # Linux Aşağı
            
            # --- SAĞ TIK ---
            btn.bind("<Button-3>", lambda e, i=idx: self.menu_goster(e, i))
            
            # --- SÜRÜKLEME VE TIKLAMA ---
            btn.bind("<Button-1>", lambda e, i=idx: self.surukle_baslat(e, i))
            btn.bind("<B1-Motion>", self.surukle_devam)
            btn.bind("<ButtonRelease-1>", lambda e, v=b: self.surukle_bitir(e, v))
        if len(self.dosya_yolu_listesi) > 1:
            self.geri_butonu.pack(side="right", padx=10)
        else:
            self.geri_butonu.pack_forget()
        
    def not_penceresi_ac(self):
        if self.secili_buton_index is None: return
        veri = self.veriler["butonlar"][self.secili_buton_index]
        
        pencere = tk.Toplevel(self.pencere)
        pencere.title(f"{veri['ad']} - Not Defteri")
        pencere.geometry("300x350")

        tk.Label(pencere, text="Buton Notu:", font=("Arial", 10, "bold")).pack(pady=5)
        
        # Not alanı (Metin kutusu)
        metin_alani = tk.Text(pencere, wrap="word", font=("Arial", 10))
        metin_alani.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Varsa eski notu yükle
        eski_not = veri.get("not", "")
        metin_alani.insert("1.0", eski_not)

        def not_kaydet():
            veri["not"] = metin_alani.get("1.0", "end-1c") # Metni al
            self.ayarlari_kaydet()
            pencere.destroy()
            messagebox.showinfo("Başarılı", "Not kaydedildi!")

        tk.Button(pencere, text="💾 Notu Kaydet", command=not_kaydet, bg="#d4edda").pack(pady=10)
   
    def tekerlek_sirala(self, event, index):
        liste = self.veriler["butonlar"]
        yeni_index = index

        # Yön tespiti
        if event.num == 4 or event.delta > 0: # Yukarı (Linux 4 veya Windows Pozitif Delta)
            yeni_index = max(0, index - 1)
        elif event.num == 5 or event.delta < 0: # Aşağı (Linux 5 veya Windows Negatif Delta)
            yeni_index = min(len(liste) - 1, index + 1)

        if yeni_index != index:
            liste[index], liste[yeni_index] = liste[yeni_index], liste[index]
            self.ayarlari_kaydet()
            self.ekrani_guncelle()

    # --- SÜRÜKLEME MANTIĞI ---
    # --- AKICI VE KEYİFLİ SÜRÜKLEME ---
    def surukle_baslat(self, event, index):
        self.suruklenen_index = index
        self.fare_hareket_etti_mi = False
        # Başlangıçta butonu en üste getir ve küçült
        event.widget.lift()
        event.widget.config(relief="flat", bg="#d1d1d1")

    def surukle_devam(self, event):
        self.fare_hareket_etti_mi = True
        
        # Farenin koordinatlarını al
        x_fare = event.x_root - self.buton_alani.winfo_rootx()
        y_fare = event.y_root - self.buton_alani.winfo_rooty()
        
        # --- KADEMELİ BÜYÜME (DALGA EFEKTİ) ---
        children = self.buton_alani.winfo_children()
        for idx, child in enumerate(children):
            if idx == self.suruklenen_index:
                # Sürüklenen buton hep küçük kalsın
                child.config(width=60, height=40)
                continue
            
            # Butonun merkezini bul
            bx = child.winfo_x() + (child.winfo_width() / 2)
            by = child.winfo_y() + (child.winfo_height() / 2)
            
            # Fareye olan mesafeyi hesapla
            mesafe = math.sqrt((x_fare - bx)**2 + (y_fare - by)**2)
            
            # KADEMELİ HESAP: Mesafe arttıkça büyüme etkisi azalır
            # 150px içindeyse etkilenir
            if mesafe < 150:
                # Mesafe 0 ise en büyük (120px), 150 ise normal (80px)
                oran = 1 - (mesafe / 150)
                yeni_w = int(80 + (40 * oran)) # 80'den 120'ye kadar
                yeni_h = int(50 + (25 * oran)) # 50'den 75'e kadar
                child.config(width=yeni_w, height=yeni_h, bg="#ffffff")
            else:
                # Uzaktakiler normal boyut
                child.config(width=80, height=50, bg="#f0f0f0")

        # Hedef indexi sürekli güncelle ama ekrani_guncelle() çağırma!
        self.gecici_hedef_index = self.en_yakin_index_bul(x_fare, y_fare)

    def surukle_bitir(self, event, veri):
        if not self.fare_hareket_etti_mi:
            self.sol_tik_islevi(veri)
        else:
            if hasattr(self, 'gecici_hedef_index') and self.gecici_hedef_index is not None:
                if self.gecici_hedef_index != self.suruklenen_index:
                    liste = self.veriler["butonlar"]
                    item = liste.pop(self.suruklenen_index)
                    liste.insert(self.gecici_hedef_index, item)
                    self.ayarlari_kaydet()
        
        self.suruklenen_index = None
        self.ekrani_guncelle() # Bırakınca her şeyi temizle ve spiral yapısına oturt
    def en_yakin_index_bul(self, x, y):
        """Spiral yapıda farenin en yakın olduğu butonun indexini döner."""
        en_yakin_mesafe = float('inf')
        hedef_index = None
        
        children = self.buton_alani.winfo_children()
        for idx, child in enumerate(children):
            # Butonun merkez koordinatlarını hesapla
            bx = child.winfo_x() + (child.winfo_width() / 2)
            by = child.winfo_y() + (child.winfo_height() / 2)
            
            # Öklid mesafesi hesapla: d = sqrt((x2-x1)^2 + (y2-y1)^2)
            mesafe = math.sqrt((x - bx)**2 + (y - by)**2)
            
            if mesafe < en_yakin_mesafe:
                en_yakin_mesafe = mesafe
                hedef_index = idx
                
        return hedef_index
    #########################
    def sol_tik_islevi(self, veri):
        if veri.get("link"):
            try:
                webbrowser.open(veri["link"])
            except: pass
        else:
            messagebox.showinfo("Bilgi", "Link atanmamış. Sağ tıkla düzenle.")

    def yeni_buton_ekle(self):
        yeni_id = f"katman_{uuid.uuid4().hex[:8]}.json"
        yeni_b = {"ad": f"B {len(self.veriler['butonlar'])+1}", "link": "", "bg": "#ffffff", "fg": "black", "hedef_dosya": yeni_id, "not":""}
        self.veriler["butonlar"].append(yeni_b)
        self.ayarlari_kaydet()
        self.ekrani_guncelle()

        
    

    def menu_goster(self, event, index):
        self.secili_buton_index = index
        self.menu.tk_popup(event.x_root, event.y_root)

    def iceri_gir(self):
        if self.secili_buton_index is not None:
            secili = self.veriler["butonlar"][self.secili_buton_index]
            self.dosya_yolu_listesi.append(secili["hedef_dosya"])
            self.isim_yolu_listesi.append(secili["ad"])
            self.veriler = self.ayarlari_yukle(self.dosya_yolu_listesi[-1])
            self.ekrani_guncelle()

    def disari_cik(self):
        if len(self.dosya_yolu_listesi) > 1:
            self.dosya_yolu_listesi.pop()
            self.isim_yolu_listesi.pop()
            self.veriler = self.ayarlari_yukle(self.dosya_yolu_listesi[-1])
            self.ekrani_guncelle()
    def duzenle_penceresi_ac(self):
        if self.secili_buton_index is None: return
        veri = self.veriler["butonlar"][self.secili_buton_index]
        pencere = tk.Toplevel(self.pencere)
        pencere.title(f"Düzenle: {veri['ad']}")
        pencere.geometry("350x550")

        # --- TEMEL BİLGİLER ---
        tk.Label(pencere, text="Buton Metni:", font=("Arial", 9, "bold")).pack(pady=2)
        e_ad = tk.Entry(pencere); e_ad.insert(0, veri["ad"]); e_ad.pack(fill="x", padx=20)
        
        tk.Label(pencere, text="Bağlantı (Link/Yol):", font=("Arial", 9, "bold")).pack(pady=2)
        e_link = tk.Entry(pencere); e_link.insert(0, veri.get("link", "")); e_link.pack(fill="x", padx=20)

        ttk.Separator(pencere, orient='horizontal').pack(fill='x', pady=10, padx=10)
        tk.Label(pencere, text="🎨 TASARIM AYARLARI", font=("Arial", 10, "bold"), fg="blue").pack()

        # --- YARDIMCI FONKSİYONLAR (GİRİNTİYE DİKKAT) ---
        def renk_sec(tip):
            renk = colorchooser.askcolor(title="Renk Seç")[1]
            if renk:
                veri[tip] = renk

        def ikon_sec():
            dosya = filedialog.askopenfilename(filetypes=[("Görsel Dosyaları", "*.png *.gif")])
            if dosya:
                veri["icon_path"] = dosya

        def son_kaydet():
            veri["ad"] = e_ad.get()
            veri["link"] = e_link.get()
            veri["font_family"] = font_var.get()
            self.ayarlari_kaydet()
            self.ekrani_guncelle()
            pencere.destroy()

        # --- RENK SEÇİMİ ---
        renk_frame = tk.Frame(pencere)
        renk_frame.pack(pady=5)
        tk.Button(renk_frame, text="Arkaplan Rengi", command=lambda: renk_sec("bg")).pack(side="left", padx=5)
        tk.Button(renk_frame, text="Yazı Rengi", command=lambda: renk_sec("fg")).pack(side="left", padx=5)

        # --- FONT STİLİ ---
        tk.Label(pencere, text="Yazı Tipi / Font:").pack()
        fontlar = ["Arial", "Courier", "Verdana", "Times New Roman", "Impact"]
        font_var = tk.StringVar(value=veri.get("font_family", "Arial"))
        font_menu = tk.OptionMenu(pencere, font_var, *fontlar)
        font_menu.pack(pady=5)       

        # --- İKON SEÇİMİ ---
        tk.Button(pencere, text="🖼️ İkon Seç (.png/.gif)", command=ikon_sec, bg="#e1e1e1").pack(pady=5)

        # --- KAYDET BUTONU ---
        tk.Button(pencere, text="💾 DEĞİŞİKLİKLERİ KAYDET", command=son_kaydet, bg="#d4edda", font=("Arial", 10, "bold")).pack(pady=20)

    def kaydet():
        veri["ad"] = e_ad.get(); veri["link"] = e_link.get()
        self.ayarlari_kaydet(); self.ekrani_guncelle(); pencere.destroy()
        
        tk.Button(pencere, text="Kaydet", command=kaydet).pack(pady=10)

    def buton_sil(self):
        if self.secili_buton_index is not None:
            self.veriler["butonlar"].pop(self.secili_buton_index)
            self.ayarlari_kaydet()
            self.ekrani_guncelle()

if __name__ == "__main__":
    root = tk.Tk()
    app = ButonUygulamasi(root)
    root.mainloop()