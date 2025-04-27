import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import sqlite3
from datetime import datetime
import os

class KafeAdisyonProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title("Kafe Adisyon Programı")
        self.root.geometry("1200x800")
        
        self.baglanti_olustur()
        self.arayuz_olustur()
        self.notebook.select(self.masalar_cercevesi)
    
    def baglanti_olustur(self):
        self.conn = sqlite3.connect('kafe_veritabani.db')
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS masalar (
                masa_no INTEGER PRIMARY KEY,
                durum TEXT,
                acilis_zamani TEXT,
                kapanis_zamani TEXT,
                toplam_tutar REAL DEFAULT 0,
                indirim REAL DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS siparisler (
                siparis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no INTEGER,
                urun_adi TEXT,
                adet INTEGER,
                birim_fiyat REAL,
                toplam_fiyat REAL,
                eklenme_zamani TEXT,
                FOREIGN KEY (masa_no) REFERENCES masalar (masa_no)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kategoriler (
                kategori_id INTEGER PRIMARY KEY AUTOINCREMENT,
                kategori_adi TEXT UNIQUE,
                sira INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS urunler (
                urun_id INTEGER PRIMARY KEY AUTOINCREMENT,
                kategori_id INTEGER,
                urun_adi TEXT,
                fiyat REAL,
                sira INTEGER DEFAULT 0,
                FOREIGN KEY (kategori_id) REFERENCES kategoriler (kategori_id)
            )
        ''')
        
        self.baslangic_verilerini_ekle()
        self.conn.commit()
    
    def baslangic_verilerini_ekle(self):
        kategoriler = [('İçecekler', 1), ('Yiyecekler', 2), ('Tatlılar', 3)]
        for kategori, sira in kategoriler:
            try:
                self.cursor.execute("INSERT INTO kategoriler (kategori_adi, sira) VALUES (?, ?)", 
                                  (kategori, sira))
            except sqlite3.IntegrityError:
                pass
        
        urunler = [
            (1, 'Çay', 5.0, 1),
            (1, 'Kahve', 10.0, 2),
            (1, 'Su', 2.0, 3),
            (2, 'Tost', 15.0, 1),
            (2, 'Sandviç', 20.0, 2),
            (3, 'Baklava', 25.0, 1),
            (3, 'Sütlaç', 15.0, 2)
        ]
        
        for urun in urunler:
            self.cursor.execute('''
                INSERT OR IGNORE INTO urunler (kategori_id, urun_adi, fiyat, sira)
                VALUES (?, ?, ?, ?)
            ''', urun)
        
        for masa_no in range(1, 21):
            self.cursor.execute('''
                INSERT OR IGNORE INTO masalar (masa_no, durum)
                VALUES (?, 'Boş')
            ''', (masa_no,))
    
    def arayuz_olustur(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Masalar sekmesi
        self.masalar_cercevesi = tk.Frame(self.notebook)
        self.notebook.add(self.masalar_cercevesi, text="Masalar")
        self.masalar_arayuz_olustur()
        
        # Siparişler sekmesi
        self.siparisler_cercevesi = tk.Frame(self.notebook)
        self.notebook.add(self.siparisler_cercevesi, text="Siparişler")
        self.siparisler_arayuz_olustur()
        
        # Raporlar sekmesi
        self.raporlar_cercevesi = tk.Frame(self.notebook)
        self.notebook.add(self.raporlar_cercevesi, text="Raporlar")
        self.raporlar_arayuz_olustur()
    
    def masalar_arayuz_olustur(self):
        # Başlık
        baslik_cercevesi = tk.Frame(self.masalar_cercevesi)
        baslik_cercevesi.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(baslik_cercevesi, text="MASALAR", font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Masa ekle/sil butonları
        tk.Button(baslik_cercevesi, text="Masa Ekle", command=self.masa_ekle,
                 bg='#4CAF50', fg='white').pack(side=tk.RIGHT, padx=5)
        tk.Button(baslik_cercevesi, text="Masa Sil", command=self.masa_sil,
                 bg='#F44336', fg='white').pack(side=tk.RIGHT, padx=5)
        
        # Masalar için canvas ve scrollbar
        self.masalar_canvas = tk.Canvas(self.masalar_cercevesi)
        scrollbar = ttk.Scrollbar(self.masalar_cercevesi, orient="vertical", command=self.masalar_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.masalar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.masalar_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.masalar_icerik_cercevesi = tk.Frame(self.masalar_canvas)
        self.masalar_canvas.create_window((0,0), window=self.masalar_icerik_cercevesi, anchor="nw")
        
        self.masalari_yukle()
        
        self.masalar_icerik_cercevesi.bind("<Configure>", 
            lambda e: self.masalar_canvas.configure(scrollregion=self.masalar_canvas.bbox("all")))
    
    def masalari_yukle(self):
        for widget in self.masalar_icerik_cercevesi.winfo_children():
            widget.destroy()
        
        self.cursor.execute("SELECT masa_no, durum, toplam_tutar FROM masalar ORDER BY masa_no")
        masalar = self.cursor.fetchall()
        
        for i, (masa_no, durum, toplam_tutar) in enumerate(masalar):
            row = i // 5
            col = i % 5
            
            masa_rengi = '#FFA500' if durum == 'Dolu' else '#8BC34A'
            
            masa_cercevesi = tk.Frame(self.masalar_icerik_cercevesi, bg=masa_rengi, 
                                     bd=2, relief=tk.RAISED, width=200, height=150)
            masa_cercevesi.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            masa_cercevesi.pack_propagate(False)
            
            # Masa numarası
            tk.Label(masa_cercevesi, text=f"Masa {masa_no}", 
                    font=('Arial', 14, 'bold'), bg=masa_rengi).pack(pady=5)
            
            # Durum ve bakiye bilgisi (Dolu masalarda bakiye göster)
            durum_text = f"Dolu ({toplam_tutar:.2f} TL)" if durum == 'Dolu' else 'Boş'
            tk.Label(masa_cercevesi, text=durum_text, font=('Arial', 10), bg=masa_rengi).pack()
            
            # Butonlar
            buton_cercevesi = tk.Frame(masa_cercevesi, bg=masa_rengi)
            buton_cercevesi.pack(pady=10)
            
            if durum == 'Boş':
                tk.Button(buton_cercevesi, text="AÇ", 
                         command=lambda mn=masa_no: self.masa_ac(mn),
                         bg='#4CAF50', fg='white', width=8).pack(pady=2)
            else:
                tk.Button(buton_cercevesi, text="KAPAT", 
                         command=lambda mn=masa_no: self.masa_kapat(mn),
                         bg='#F44336', fg='white', width=8).pack(pady=2)
                tk.Button(buton_cercevesi, text="SİPARİŞ EKLE", 
                         command=lambda mn=masa_no: self.siparis_ekle_icin_gecis(mn),
                         bg='#2196F3', fg='white', width=8).pack(pady=2)
            
            # DETAY butonu (TÜM MASALARDA - ÖZELLİKLE AÇIK MASALAR İÇİN KRİTİK)
            tk.Button(buton_cercevesi, text="DETAY", 
                     command=lambda mn=masa_no: self.masa_detay_goster(mn),
                     bg='#607D8B', fg='white', width=8).pack(pady=2)
    
    def masa_ekle(self):
        # Mevcut en büyük masa numarasını bul
        self.cursor.execute("SELECT MAX(masa_no) FROM masalar")
        max_masa = self.cursor.fetchone()[0] or 0
        yeni_masa_no = max_masa + 1
        
        self.cursor.execute("INSERT INTO masalar (masa_no, durum) VALUES (?, 'Boş')", (yeni_masa_no,))
        self.conn.commit()
        self.masalari_yukle()
        messagebox.showinfo("Başarılı", f"{yeni_masa_no} numaralı masa eklendi")
    
    def masa_sil(self):
        masa_no = simpledialog.askinteger("Masa Sil", "Silinecek masa numarasını girin:", 
                                        parent=self.root, minvalue=1)
        if masa_no:
            # Masa dolu mu kontrol et
            self.cursor.execute("SELECT durum FROM masalar WHERE masa_no=?", (masa_no,))
            durum = self.cursor.fetchone()
            
            if not durum:
                messagebox.showerror("Hata", "Bu numarada masa yok!")
                return
            
            if durum[0] == 'Dolu':
                messagebox.showerror("Hata", "Dolu masalar silinemez! Önce kapatın.")
                return
            
            if messagebox.askyesno("Onay", f"{masa_no} numaralı masayı silmek istediğinize emin misiniz?"):
                # Siparişleri sil
                self.cursor.execute("DELETE FROM siparisler WHERE masa_no=?", (masa_no,))
                # Masayı sil
                self.cursor.execute("DELETE FROM masalar WHERE masa_no=?", (masa_no,))
                self.conn.commit()
                self.masalari_yukle()
                messagebox.showinfo("Başarılı", "Masa silindi")
    
    def masa_ac(self, masa_no):
        self.cursor.execute("UPDATE masalar SET durum='Dolu', acilis_zamani=? WHERE masa_no=?", 
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), masa_no))
        self.conn.commit()
        self.masalari_yukle()
    
    def masa_kapat(self, masa_no):
        if messagebox.askyesno("Onay", "Masayı kapatmak istediğinize emin misiniz?"):
            # Toplam tutarı hesapla
            self.cursor.execute("SELECT SUM(toplam_fiyat) FROM siparisler WHERE masa_no=?", (masa_no,))
            toplam_tutar = self.cursor.fetchone()[0] or 0
            
            # İndirim varsa uygula
            self.cursor.execute("SELECT indirim FROM masalar WHERE masa_no=?", (masa_no,))
            indirim = self.cursor.fetchone()[0] or 0
            indirimli_tutar = toplam_tutar * (100 - indirim) / 100
            
            # Fiş oluştur
            fis_icerik = self.fis_olustur(masa_no, toplam_tutar, indirim, indirimli_tutar)
            
            # Fişi dosyaya yaz
            fis_dosya_adi = f"fis_masa_{masa_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(fis_dosya_adi, 'w', encoding='utf-8') as f:
                f.write(fis_icerik)
            
            # Temizle
            self.cursor.execute("DELETE FROM siparisler WHERE masa_no=?", (masa_no,))
            self.cursor.execute("UPDATE masalar SET durum='Boş', acilis_zamani=NULL, kapanis_zamani=?, toplam_tutar=0, indirim=0 WHERE masa_no=?", 
                              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), masa_no))
            self.conn.commit()
            
            self.masalari_yukle()
            messagebox.showinfo("Başarılı", f"Masa kapatıldı.\n\nFiş dosyası oluşturuldu: {fis_dosya_adi}")
    
    def fis_olustur(self, masa_no, toplam_tutar, indirim, indirimli_tutar):
        fis_icerik = f"""
        {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
        Masa No: {masa_no}
        ----------------------------
        """
        
        self.cursor.execute("""
            SELECT urun_adi, adet, birim_fiyat, toplam_fiyat 
            FROM siparisler 
            WHERE masa_no=?
            ORDER BY eklenme_zamani
        """, (masa_no,))
        siparisler = self.cursor.fetchall()
        
        for urun_adi, adet, birim_fiyat, toplam_fiyat in siparisler:
            fis_icerik += f"{urun_adi} x{adet} {birim_fiyat:.2f} TL = {toplam_fiyat:.2f} TL\n"
        
        fis_icerik += f"""
        ----------------------------
        Ara Toplam: {toplam_tutar:.2f} TL
        İndirim: %{indirim}
        Toplam: {indirimli_tutar:.2f} TL
        ----------------------------
        Teşekkür Ederiz!
        """
        return fis_icerik
    
    def siparis_ekle_icin_gecis(self, masa_no):
        self.secili_masa = masa_no
        self.notebook.select(self.siparisler_cercevesi)
        self.siparisler_arayuz_guncelle()
    
    def masa_detay_goster(self, masa_no):
        detay_penceresi = tk.Toplevel(self.root)
        detay_penceresi.title(f"Masa {masa_no} Detayları")
        detay_penceresi.geometry("800x600")
        
        # Masa bilgilerini al
        self.cursor.execute("SELECT durum, acilis_zamani, toplam_tutar, indirim FROM masalar WHERE masa_no=?", (masa_no,))
        masa_bilgisi = self.cursor.fetchone()
        
        if not masa_bilgisi:
            messagebox.showerror("Hata", "Masa bulunamadı!")
            detay_penceresi.destroy()
            return
        
        durum, acilis_zamani, toplam_tutar, indirim = masa_bilgisi
        
        # Masa bilgilerini göster
        tk.Label(detay_penceresi, text=f"Masa {masa_no} - {durum}", 
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        if durum == 'Dolu':
            tk.Label(detay_penceresi, text=f"Açılış Zamanı: {acilis_zamani}").pack(anchor='w', padx=20)
        
        # Siparişler başlığı
        tk.Label(detay_penceresi, text="Siparişler:", font=('Arial', 12)).pack(anchor='w', padx=20, pady=(20,5))
        
        # Siparişler çerçevesi
        siparisler_cercevesi = tk.Frame(detay_penceresi)
        siparisler_cercevesi.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Sipariş başlıkları
        baslik_cercevesi = tk.Frame(siparisler_cercevesi)
        baslik_cercevesi.pack(fill=tk.X)
        
        tk.Label(baslik_cercevesi, text="Ürün", width=25, anchor='w').pack(side=tk.LEFT)
        tk.Label(baslik_cercevesi, text="Adet", width=10).pack(side=tk.LEFT)
        tk.Label(baslik_cercevesi, text="Birim Fiyat", width=15).pack(side=tk.LEFT)
        tk.Label(baslik_cercevesi, text="Toplam", width=15).pack(side=tk.LEFT)
        tk.Label(baslik_cercevesi, text="Zaman", width=15).pack(side=tk.LEFT)
        
        # Siparişleri getir
        self.cursor.execute("""
            SELECT urun_adi, adet, birim_fiyat, toplam_fiyat, eklenme_zamani 
            FROM siparisler 
            WHERE masa_no=?
            ORDER BY eklenme_zamani DESC
        """, (masa_no,))
        siparisler = self.cursor.fetchall()
        
        if not siparisler:
            tk.Label(siparisler_cercevesi, text="Henüz sipariş yok", fg='gray').pack(pady=20)
        else:
            for urun_adi, adet, birim_fiyat, toplam_fiyat, eklenme_zamani in siparisler:
                siparis_cercevesi = tk.Frame(siparisler_cercevesi)
                siparis_cercevesi.pack(fill=tk.X, pady=2)
                
                tk.Label(siparis_cercevesi, text=urun_adi, width=25, anchor='w').pack(side=tk.LEFT)
                tk.Label(siparis_cercevesi, text=str(adet), width=10).pack(side=tk.LEFT)
                tk.Label(siparis_cercevesi, text=f"{birim_fiyat:.2f} TL", width=15).pack(side=tk.LEFT)
                tk.Label(siparis_cercevesi, text=f"{toplam_fiyat:.2f} TL", width=15).pack(side=tk.LEFT)
                tk.Label(siparis_cercevesi, text=eklenme_zamani, width=15).pack(side=tk.LEFT)
                
                # Sipariş silme butonu (sadece dolu masalar için)
                if durum == 'Dolu':
                    tk.Button(siparis_cercevesi, text="Sil", 
                             command=lambda u=urun_adi, m=masa_no: self.siparisi_sil(u, m, detay_penceresi),
                             bg='#F44336', fg='white', width=5).pack(side=tk.RIGHT, padx=5)
        
        # Toplam bilgisi
        toplam_cercevesi = tk.Frame(detay_penceresi)
        toplam_cercevesi.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(toplam_cercevesi, text=f"Ara Toplam: {toplam_tutar:.2f} TL", 
                font=('Arial', 12)).pack(side=tk.LEFT)
        
        if indirim > 0:
            indirimli_tutar = toplam_tutar * (100 - indirim) / 100
            tk.Label(toplam_cercevesi, text=f"İndirim: %{indirim}", 
                    font=('Arial', 12)).pack(side=tk.LEFT, padx=20)
            tk.Label(toplam_cercevesi, text=f"Toplam: {indirimli_tutar:.2f} TL", 
                    font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        else:
            tk.Label(toplam_cercevesi, text=f"Toplam: {toplam_tutar:.2f} TL", 
                    font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # İşlem butonları (sadece dolu masalar için)
        islem_cercevesi = tk.Frame(detay_penceresi)
        islem_cercevesi.pack(fill=tk.X, padx=20, pady=10)
        
        if durum == 'Dolu':
            tk.Button(islem_cercevesi, text="İndirim Yap", 
                     command=lambda: self.masaya_indirim_yap(masa_no, detay_penceresi),
                     bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=5)
            tk.Button(islem_cercevesi, text="Hesap Kapat", 
                     command=lambda: self.masa_kapat_ve_kapat(masa_no, detay_penceresi),
                     bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)
        
        tk.Button(islem_cercevesi, text="Kapat", 
                 command=detay_penceresi.destroy,
                 bg='#607D8B', fg='white').pack(side=tk.RIGHT, padx=5)
    
    def masaya_indirim_yap(self, masa_no, pencere):
        indirim = simpledialog.askinteger("İndirim Yap", "İndirim yüzdesini giriniz (0-100):", 
                                        parent=pencere, minvalue=0, maxvalue=100)
        
        if indirim is not None:
            self.cursor.execute("UPDATE masalar SET indirim=? WHERE masa_no=?", (indirim, masa_no))
            self.conn.commit()
            
            # Toplam tutarı yeniden hesapla
            self.cursor.execute("SELECT SUM(toplam_fiyat) FROM siparisler WHERE masa_no=?", (masa_no,))
            toplam_tutar = self.cursor.fetchone()[0] or 0
            self.cursor.execute("UPDATE masalar SET toplam_tutar=? WHERE masa_no=?", (toplam_tutar, masa_no))
            self.conn.commit()
            
            messagebox.showinfo("Başarılı", f"%{indirim} indirim uygulandı.")
            pencere.destroy()
            self.masa_detay_goster(masa_no)
            self.masalari_yukle()
    
    def masa_kapat_ve_kapat(self, masa_no, pencere):
        self.masa_kapat(masa_no)
        pencere.destroy()
    
    def siparisi_sil(self, urun_adi, masa_no, pencere):
        if messagebox.askyesno("Onay", f"{urun_adi} siparişini silmek istediğinize emin misiniz?"):
            self.cursor.execute("DELETE FROM siparisler WHERE masa_no=? AND urun_adi=?", (masa_no, urun_adi))
            
            # Masanın toplam tutarını güncelle
            self.cursor.execute('''
                UPDATE masalar 
                SET toplam_tutar = (SELECT SUM(toplam_fiyat) FROM siparisler WHERE masa_no=?)
                WHERE masa_no=?
            ''', (masa_no, masa_no))
            
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Sipariş silindi.")
            pencere.destroy()
            self.masa_detay_goster(masa_no)
            self.masalari_yukle()
    
    def siparisler_arayuz_olustur(self):
        # Üst bilgi çerçevesi
        ust_bilgi_cercevesi = tk.Frame(self.siparisler_cercevesi)
        ust_bilgi_cercevesi.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(ust_bilgi_cercevesi, text="Masa No:", font=('Arial', 12)).pack(side=tk.LEFT)
        self.masa_no_label = tk.Label(ust_bilgi_cercevesi, text="-", font=('Arial', 12, 'bold'))
        self.masa_no_label.pack(side=tk.LEFT, padx=10)
        
        tk.Label(ust_bilgi_cercevesi, text="Toplam:", font=('Arial', 12)).pack(side=tk.LEFT, padx=20)
        self.toplam_label = tk.Label(ust_bilgi_cercevesi, text="0.00 TL", font=('Arial', 12, 'bold'))
        self.toplam_label.pack(side=tk.LEFT)
        
        # Kategori seçimi
        self.kategori_combobox = ttk.Combobox(ust_bilgi_cercevesi, state="readonly")
        self.kategori_combobox.pack(side=tk.LEFT, padx=20)
        self.kategori_combobox.bind('<<ComboboxSelected>>', self.kategori_secildi)
        
        # Kategorileri yükle
        self.cursor.execute("SELECT kategori_adi FROM kategoriler ORDER BY sira")
        kategoriler = [row[0] for row in self.cursor.fetchall()]
        self.kategori_combobox['values'] = kategoriler
        if kategoriler:
            self.kategori_combobox.current(0)
        
        # Ürünler çerçevesi (scrollbar ile)
        self.urunler_canvas = tk.Canvas(self.siparisler_cercevesi)
        self.urunler_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.siparisler_cercevesi, orient="vertical", command=self.urunler_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        self.urunler_canvas.configure(yscrollcommand=scrollbar.set)
        self.urunler_canvas.bind('<Configure>', lambda e: self.urunler_canvas.configure(scrollregion=self.urunler_canvas.bbox("all")))
        
        self.urunler_icerik_cercevesi = tk.Frame(self.urunler_canvas)
        self.urunler_canvas.create_window((0, 0), window=self.urunler_icerik_cercevesi, anchor="nw")
        
        # İşlem butonları
        islem_cercevesi = tk.Frame(self.siparisler_cercevesi)
        islem_cercevesi.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(islem_cercevesi, text="İndirim Yap", command=self.indirim_yap, bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(islem_cercevesi, text="Hesap Kapat", command=self.hesap_kapat, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(islem_cercevesi, text="Ürün Yönetimi", command=self.urun_yonetimi, bg='#607D8B', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(islem_cercevesi, text="Masaya Dön", command=lambda: self.notebook.select(self.masalar_cercevesi), 
                bg='#2196F3', fg='white').pack(side=tk.RIGHT, padx=5)
    
    def kategori_secildi(self, event=None):
        # Önceki ürünleri temizle
        for widget in self.urunler_icerik_cercevesi.winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'secili_masa'):
            return
            
        kategori = self.kategori_combobox.get()
        if not kategori:
            return
            
        # Kategoriye ait ürünleri al
        self.cursor.execute('''
            SELECT u.urun_adi, u.fiyat 
            FROM urunler u
            JOIN kategoriler k ON u.kategori_id = k.kategori_id
            WHERE k.kategori_adi=?
            ORDER BY u.sira
        ''', (kategori,))
        
        urunler = self.cursor.fetchall()
        
        # Ürün butonlarını oluştur
        for urun_adi, fiyat in urunler:
            urun_butonu = tk.Button(
                self.urunler_icerik_cercevesi, 
                text=f"{urun_adi}\n{fiyat:.2f} TL", 
                command=lambda u=urun_adi, p=fiyat: self.urun_ekle(u, p),
                width=15, height=5, bg='#E1F5FE', relief=tk.RAISED
            )
            urun_butonu.pack(side=tk.LEFT, padx=10, pady=10)
            
            # Çift tıklama ile 2 adet ekle
            urun_butonu.bind('<Double-Button-1>', lambda e, u=urun_adi, p=fiyat: self.urun_ekle(u, p, 2))
    
    def urun_ekle(self, urun_adi, birim_fiyat, adet=1):
        if not hasattr(self, 'secili_masa'):
            messagebox.showerror("Hata", "Önce bir masa seçmelisiniz!")
            return
            
        toplam_fiyat = birim_fiyat * adet
        
        # Siparişi veritabanına ekle
        self.cursor.execute('''
            INSERT INTO siparisler (masa_no, urun_adi, adet, birim_fiyat, toplam_fiyat, eklenme_zamani)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.secili_masa, urun_adi, adet, birim_fiyat, toplam_fiyat, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Masanın toplam tutarını güncelle
        self.cursor.execute('''
            UPDATE masalar 
            SET toplam_tutar = (SELECT SUM(toplam_fiyat) FROM siparisler WHERE masa_no=?)
            WHERE masa_no=?
        ''', (self.secili_masa, self.secili_masa))
        
        self.conn.commit()
        
        # Arayüzü güncelle
        self.siparisler_arayuz_guncelle()
        messagebox.showinfo("Başarılı", f"{adet} adet {urun_adi} masaya eklendi!")
    
    def siparisler_arayuz_guncelle(self):
        if hasattr(self, 'secili_masa'):
            self.masa_no_label.config(text=str(self.secili_masa))
            
            # Toplam tutarı güncelle
            self.cursor.execute("SELECT SUM(toplam_fiyat) FROM siparisler WHERE masa_no=?", (self.secili_masa,))
            toplam_tutar = self.cursor.fetchone()[0] or 0
            self.toplam_label.config(text=f"{toplam_tutar:.2f} TL")
            
            # Ürünleri yükle
            self.kategori_secildi()
    
    def indirim_yap(self):
        if not hasattr(self, 'secili_masa'):
            messagebox.showerror("Hata", "Önce bir masa seçmelisiniz!")
            return
            
        indirim = simpledialog.askinteger("İndirim Yap", "İndirim yüzdesini giriniz (0-100):", 
                                        parent=self.root, minvalue=0, maxvalue=100)
        
        if indirim is not None:
            self.cursor.execute("UPDATE masalar SET indirim=? WHERE masa_no=?", (indirim, self.secili_masa))
            self.conn.commit()
            self.siparisler_arayuz_guncelle()
            messagebox.showinfo("Başarılı", f"%{indirim} indirim uygulandı.")
    
    def hesap_kapat(self):
        if not hasattr(self, 'secili_masa'):
            messagebox.showerror("Hata", "Önce bir masa seçmelisiniz!")
            return
            
        self.masa_kapat(self.secili_masa)
        self.notebook.select(self.masalar_cercevesi)
    
    def urun_yonetimi(self):
        yonetim_penceresi = tk.Toplevel(self.root)
        yonetim_penceresi.title("Ürün Yönetimi")
        yonetim_penceresi.geometry("800x600")
        
        # Notebook (sekmeler)
        notebook = ttk.Notebook(yonetim_penceresi)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Kategoriler sekmesi
        kategoriler_cercevesi = tk.Frame(notebook)
        notebook.add(kategoriler_cercevesi, text="Kategoriler")
        
        # Kategori listesi
        self.kategori_listesi = ttk.Treeview(kategoriler_cercevesi, columns=('kategori_id', 'kategori_adi', 'sira'), show='headings')
        self.kategori_listesi.heading('kategori_id', text='ID')
        self.kategori_listesi.heading('kategori_adi', text='Kategori Adı')
        self.kategori_listesi.heading('sira', text='Sıra')
        self.kategori_listesi.column('kategori_id', width=50)
        self.kategori_listesi.column('sira', width=50)
        self.kategori_listesi.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Kategori işlem butonları
        kategori_buton_cercevesi = tk.Frame(kategoriler_cercevesi)
        kategori_buton_cercevesi.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(kategori_buton_cercevesi, text="Yeni Kategori", command=self.yeni_kategori_ekle, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(kategori_buton_cercevesi, text="Kategori Sil", command=self.kategori_sil, bg='#F44336', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(kategori_buton_cercevesi, text="Sıra Güncelle", command=self.kategori_sira_guncelle, bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=5)
        
        # Kategorileri yükle
        self.kategorileri_yukle()
        
        # Ürünler sekmesi
        urunler_cercevesi = tk.Frame(notebook)
        notebook.add(urunler_cercevesi, text="Ürünler")
        
        # Ürün listesi
        self.urun_listesi = ttk.Treeview(urunler_cercevesi, columns=('urun_id', 'kategori', 'urun_adi', 'fiyat', 'sira'), show='headings')
        self.urun_listesi.heading('urun_id', text='ID')
        self.urun_listesi.heading('kategori', text='Kategori')
        self.urun_listesi.heading('urun_adi', text='Ürün Adı')
        self.urun_listesi.heading('fiyat', text='Fiyat')
        self.urun_listesi.heading('sira', text='Sıra')
        self.urun_listesi.column('urun_id', width=50)
        self.urun_listesi.column('sira', width=50)
        self.urun_listesi.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ürün işlem butonları
        urun_buton_cercevesi = tk.Frame(urunler_cercevesi)
        urun_buton_cercevesi.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(urun_buton_cercevesi, text="Yeni Ürün", command=self.yeni_urun_ekle, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(urun_buton_cercevesi, text="Ürün Sil", command=self.urun_sil, bg='#F44336', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(urun_buton_cercevesi, text="Fiyat Güncelle", command=self.urun_fiyat_guncelle, bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(urun_buton_cercevesi, text="Sıra Güncelle", command=self.urun_sira_guncelle, bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=5)
        
        # Ürünleri yükle
        self.urunleri_listele()
    
    def kategorileri_yukle(self):
        # Önceki listeyi temizle
        for item in self.kategori_listesi.get_children():
            self.kategori_listesi.delete(item)
        
        # Kategorileri veritabanından al
        self.cursor.execute("SELECT kategori_id, kategori_adi, sira FROM kategoriler ORDER BY sira")
        kategoriler = self.cursor.fetchall()
        
        # Listeye ekle
        for kategori in kategoriler:
            self.kategori_listesi.insert('', tk.END, values=kategori)
    
    def yeni_kategori_ekle(self):
        kategori_adi = simpledialog.askstring("Yeni Kategori", "Kategori adını giriniz:", parent=self.root)
        
        if kategori_adi:
            try:
                # Sıra numarasını belirle (en büyük sıra + 1)
                self.cursor.execute("SELECT MAX(sira) FROM kategoriler")
                max_sira = self.cursor.fetchone()[0] or 0
                
                self.cursor.execute("INSERT INTO kategoriler (kategori_adi, sira) VALUES (?, ?)", 
                                  (kategori_adi, max_sira + 1))
                self.conn.commit()
                self.kategorileri_yukle()
                messagebox.showinfo("Başarılı", "Kategori eklendi.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu kategori zaten var!")
    
    def kategori_sil(self):
        secili = self.kategori_listesi.selection()
        if not secili:
            messagebox.showerror("Hata", "Lütfen bir kategori seçiniz!")
            return
            
        kategori_id = self.kategori_listesi.item(secili[0])['values'][0]
        kategori_adi = self.kategori_listesi.item(secili[0])['values'][1]
        
        # Kategoride ürün var mı kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM urunler WHERE kategori_id=?", (kategori_id,))
        urun_sayisi = self.cursor.fetchone()[0]
        
        if urun_sayisi > 0:
            messagebox.showerror("Hata", "Bu kategoride ürünler var! Önce ürünleri silmelisiniz.")
            return
            
        if messagebox.askyesno("Onay", f"{kategori_adi} kategorisini silmek istediğinize emin misiniz?"):
            self.cursor.execute("DELETE FROM kategoriler WHERE kategori_id=?", (kategori_id,))
            self.conn.commit()
            self.kategorileri_yukle()
            messagebox.showinfo("Başarılı", "Kategori silindi.")
    
    def kategori_sira_guncelle(self):
        secili = self.kategori_listesi.selection()
        if not secili:
            messagebox.showerror("Hata", "Lütfen bir kategori seçiniz!")
            return
            
        kategori_id = self.kategori_listesi.item(secili[0])['values'][0]
        mevcut_sira = self.kategori_listesi.item(secili[0])['values'][2]
        
        yeni_sira = simpledialog.askinteger("Sıra Güncelle", 
                                          "Yeni sıra numarasını giriniz:",
                                          parent=self.root,
                                          minvalue=1,
                                          initialvalue=mevcut_sira)
        
        if yeni_sira:
            self.cursor.execute("UPDATE kategoriler SET sira=? WHERE kategori_id=?", 
                              (yeni_sira, kategori_id))
            self.conn.commit()
            self.kategorileri_yukle()
            messagebox.showinfo("Başarılı", "Sıra numarası güncellendi.")
    
    def urunleri_listele(self):
        # Önceki listeyi temizle
        for item in self.urun_listesi.get_children():
            self.urun_listesi.delete(item)
        
        # Ürünleri veritabanından al
        self.cursor.execute('''
            SELECT u.urun_id, k.kategori_adi, u.urun_adi, u.fiyat, u.sira 
            FROM urunler u
            JOIN kategoriler k ON u.kategori_id = k.kategori_id
            ORDER BY k.sira, u.sira
        ''')
        urunler = self.cursor.fetchall()
        
        # Listeye ekle
        for urun in urunler:
            self.urun_listesi.insert('', tk.END, values=urun)
    
    def yeni_urun_ekle(self):
        ekle_penceresi = tk.Toplevel(self.root)
        ekle_penceresi.title("Yeni Ürün Ekle")
        ekle_penceresi.geometry("400x300")
        
        # Kategori seçimi
        tk.Label(ekle_penceresi, text="Kategori:").pack(pady=5)
        kategori_combobox = ttk.Combobox(ekle_penceresi, state="readonly")
        kategori_combobox.pack(pady=5, padx=10, fill=tk.X)
        
        # Kategorileri yükle
        self.cursor.execute("SELECT kategori_adi FROM kategoriler")
        kategoriler = [row[0] for row in self.cursor.fetchall()]
        kategori_combobox['values'] = kategoriler
        if kategoriler:
            kategori_combobox.current(0)
        
        # Ürün adı
        tk.Label(ekle_penceresi, text="Ürün Adı:").pack(pady=5)
        urun_adi_entry = tk.Entry(ekle_penceresi)
        urun_adi_entry.pack(pady=5, padx=10, fill=tk.X)
        
        # Fiyat
        tk.Label(ekle_penceresi, text="Fiyat:").pack(pady=5)
        fiyat_entry = tk.Entry(ekle_penceresi)
        fiyat_entry.pack(pady=5, padx=10, fill=tk.X)
        
        # Sıra
        tk.Label(ekle_penceresi, text="Sıra:").pack(pady=5)
        sira_entry = tk.Entry(ekle_penceresi)
        sira_entry.pack(pady=5, padx=10, fill=tk.X)
        
        # Ekle butonu
        tk.Button(ekle_penceresi, text="Ekle", 
                 command=lambda: self.urun_ekle_db(
                     kategori_combobox.get(),
                     urun_adi_entry.get(),
                     fiyat_entry.get(),
                     sira_entry.get(),
                     ekle_penceresi),
                 bg='#4CAF50', fg='white').pack(pady=20)
    
    def urun_ekle_db(self, kategori_adi, urun_adi, fiyat, sira, pencere):
        if not kategori_adi or not urun_adi or not fiyat or not sira:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurunuz!")
            return
            
        try:
            fiyat = float(fiyat)
            if fiyat <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir fiyat giriniz!")
            return
            
        try:
            sira = int(sira)
            if sira <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir sıra numarası giriniz!")
            return
            
        # Kategori ID'sini al
        self.cursor.execute("SELECT kategori_id FROM kategoriler WHERE kategori_adi=?", (kategori_adi,))
        kategori_id = self.cursor.fetchone()
        
        if not kategori_id:
            messagebox.showerror("Hata", "Geçersiz kategori!")
            return
            
        kategori_id = kategori_id[0]
        
        # Ürünü ekle
        try:
            self.cursor.execute('''
                INSERT INTO urunler (kategori_id, urun_adi, fiyat, sira)
                VALUES (?, ?, ?, ?)
            ''', (kategori_id, urun_adi, fiyat, sira))
            self.conn.commit()
            
            self.urunleri_listele()
            pencere.destroy()
            messagebox.showinfo("Başarılı", "Ürün eklendi.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu ürün zaten var!")
    
    def urun_sil(self):
        secili = self.urun_listesi.selection()
        if not secili:
            messagebox.showerror("Hata", "Lütfen bir ürün seçiniz!")
            return
            
        urun_id = self.urun_listesi.item(secili[0])['values'][0]
        urun_adi = self.urun_listesi.item(secili[0])['values'][2]
        
        # Ürün siparişlerde var mı kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM siparisler WHERE urun_adi=?", (urun_adi,))
        siparis_sayisi = self.cursor.fetchone()[0]
        
        if siparis_sayisi > 0:
            messagebox.showerror("Hata", "Bu ürün siparişlerde kullanılmış! Silinemez.")
            return
            
        if messagebox.askyesno("Onay", f"{urun_adi} ürününü silmek istediğinize emin misiniz?"):
            self.cursor.execute("DELETE FROM urunler WHERE urun_id=?", (urun_id,))
            self.conn.commit()
            self.urunleri_listele()
            messagebox.showinfo("Başarılı", "Ürün silindi.")
    
    def urun_fiyat_guncelle(self):
        secili = self.urun_listesi.selection()
        if not secili:
            messagebox.showerror("Hata", "Lütfen bir ürün seçiniz!")
            return
            
        urun_id = self.urun_listesi.item(secili[0])['values'][0]
        urun_adi = self.urun_listesi.item(secili[0])['values'][2]
        mevcut_fiyat = self.urun_listesi.item(secili[0])['values'][3]
        
        yeni_fiyat = simpledialog.askfloat("Fiyat Güncelle", 
                                          f"{urun_adi} için yeni fiyat giriniz:",
                                          parent=self.root,
                                          minvalue=0.01,
                                          initialvalue=mevcut_fiyat)
        
        if yeni_fiyat:
            self.cursor.execute("UPDATE urunler SET fiyat=? WHERE urun_id=?", (yeni_fiyat, urun_id))
            self.conn.commit()
            self.urunleri_listele()
            messagebox.showinfo("Başarılı", "Fiyat güncellendi.")
    
    def urun_sira_guncelle(self):
        secili = self.urun_listesi.selection()
        if not secili:
            messagebox.showerror("Hata", "Lütfen bir ürün seçiniz!")
            return
            
        urun_id = self.urun_listesi.item(secili[0])['values'][0]
        mevcut_sira = self.urun_listesi.item(secili[0])['values'][4]
        
        yeni_sira = simpledialog.askinteger("Sıra Güncelle", 
                                          "Yeni sıra numarasını giriniz:",
                                          parent=self.root,
                                          minvalue=1,
                                          initialvalue=mevcut_sira)
        
        if yeni_sira:
            self.cursor.execute("UPDATE urunler SET sira=? WHERE urun_id=?", (yeni_sira, urun_id))
            self.conn.commit()
            self.urunleri_listele()
            messagebox.showinfo("Başarılı", "Sıra numarası güncellendi.")
    
    def raporlar_arayuz_olustur(self):
        # Rapor tipi seçimi
        rapor_tipi_cercevesi = tk.Frame(self.raporlar_cercevesi)
        rapor_tipi_cercevesi.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(rapor_tipi_cercevesi, text="Rapor Tipi:").pack(side=tk.LEFT)
        self.rapor_tipi_combobox = ttk.Combobox(rapor_tipi_cercevesi, 
                                               values=["Günlük", "Tarih Aralığı"], 
                                               state="readonly")
        self.rapor_tipi_combobox.pack(side=tk.LEFT, padx=10)
        self.rapor_tipi_combobox.current(0)
        self.rapor_tipi_combobox.bind('<<ComboboxSelected>>', self.rapor_tipi_degisti)
        
        # Tarih seçimi
        self.tarih_cercevesi = tk.Frame(self.raporlar_cercevesi)
        self.tarih_cercevesi.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.tarih_cercevesi, text="Tarih:").pack(side=tk.LEFT)
        self.tarih_entry = tk.Entry(self.tarih_cercevesi)
        self.tarih_entry.pack(side=tk.LEFT, padx=5)
        self.tarih_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Tarih aralığı çerçevesi (başlangıçta gizli)
        self.tarih_araligi_cercevesi = tk.Frame(self.raporlar_cercevesi)
        
        tk.Label(self.tarih_araligi_cercevesi, text="Başlangıç:").pack(side=tk.LEFT)
        self.baslangic_tarih_entry = tk.Entry(self.tarih_araligi_cercevesi)
        self.baslangic_tarih_entry.pack(side=tk.LEFT, padx=5)
        self.baslangic_tarih_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Label(self.tarih_araligi_cercevesi, text="Bitiş:").pack(side=tk.LEFT, padx=(10,0))
        self.bitis_tarih_entry = tk.Entry(self.tarih_araligi_cercevesi)
        self.bitis_tarih_entry.pack(side=tk.LEFT, padx=5)
        self.bitis_tarih_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Rapor butonu
        rapor_buton_cercevesi = tk.Frame(self.raporlar_cercevesi)
        rapor_buton_cercevesi.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(rapor_buton_cercevesi, text="Rapor Oluştur", 
                 command=self.rapor_olustur, bg='#4CAF50', fg='white').pack(side=tk.LEFT)
        tk.Button(rapor_buton_cercevesi, text="Dosyaya Kaydet", 
                 command=self.rapor_kaydet, bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=10)
        
        # Rapor içeriği
        self.rapor_icerik = scrolledtext.ScrolledText(self.raporlar_cercevesi, width=100, height=20)
        self.rapor_icerik.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlangıçta günlük raporu göster
        self.rapor_tipi_degisti()
    
    def rapor_tipi_degisti(self, event=None):
        rapor_tipi = self.rapor_tipi_combobox.get()
        
        if rapor_tipi == "Günlük":
            self.tarih_cercevesi.pack(fill=tk.X, padx=10, pady=5)
            self.tarih_araligi_cercevesi.pack_forget()
        else:
            self.tarih_cercevesi.pack_forget()
            self.tarih_araligi_cercevesi.pack(fill=tk.X, padx=10, pady=5)
    
    def rapor_olustur(self):
        rapor_tipi = self.rapor_tipi_combobox.get()
        
        if rapor_tipi == "Günlük":
            tarih = self.tarih_entry.get()
            try:
                datetime.strptime(tarih, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz tarih formatı! (YYYY-AA-GG)")
                return
                
            baslangic_tarih = tarih + " 00:00:00"
            bitis_tarih = tarih + " 23:59:59"
        else:
            baslangic_tarih = self.baslangic_tarih_entry.get() + " 00:00:00"
            bitis_tarih = self.bitis_tarih_entry.get() + " 23:59:59"
            
            try:
                datetime.strptime(baslangic_tarih, "%Y-%m-%d %H:%M:%S")
                datetime.strptime(bitis_tarih, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz tarih formatı! (YYYY-AA-GG)")
                return
        
        # Masa bazlı rapor
        self.cursor.execute('''
            SELECT m.masa_no, COUNT(s.siparis_id), SUM(s.toplam_fiyat)
            FROM masalar m
            LEFT JOIN siparisler s ON m.masa_no = s.masa_no AND 
                                    (s.eklenme_zamani BETWEEN ? AND ?)
            WHERE m.durum = 'Dolu' OR 
                 (m.durum = 'Boş' AND m.kapanis_zamani BETWEEN ? AND ?)
            GROUP BY m.masa_no
            ORDER BY m.masa_no
        ''', (baslangic_tarih, bitis_tarih, baslangic_tarih, bitis_tarih))
        
        masa_raporu = self.cursor.fetchall()
        
        # Ürün bazlı rapor
        self.cursor.execute('''
            SELECT s.urun_adi, SUM(s.adet), SUM(s.toplam_fiyat)
            FROM siparisler s
            WHERE s.eklenme_zamani BETWEEN ? AND ?
            GROUP BY s.urun_adi
            ORDER BY SUM(s.toplam_fiyat) DESC
        ''', (baslangic_tarih, bitis_tarih))
        
        urun_raporu = self.cursor.fetchall()
        
        # Toplam ciro
        self.cursor.execute('''
            SELECT SUM(s.toplam_fiyat)
            FROM siparisler s
            WHERE s.eklenme_zamani BETWEEN ? AND ?
        ''', (baslangic_tarih, bitis_tarih))
        
        toplam_ciro = self.cursor.fetchone()[0] or 0
        
        # Rapor içeriğini oluştur
        rapor_metni = f"""
        {'='*50}
        KAFE ADİSYON RAPORU
        {'='*50}
        Rapor Tipi: {rapor_tipi}
        Tarih: {baslangic_tarih.split()[0]} - {bitis_tarih.split()[0]}
        Oluşturulma Zamanı: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        {'='*50}

        MASA BAZLI RAPOR:
        {'-'*50}
        Masa No | Sipariş Sayısı | Toplam Tutar
        {'-'*50}
        """
        
        for masa_no, siparis_sayisi, toplam_tutar in masa_raporu:
            rapor_metni += f"{masa_no:7} | {siparis_sayisi:14} | {toplam_tutar or 0:.2f} TL\n"
        
        rapor_metni += f"""
        {'-'*50}

        ÜRÜN BAZLI RAPOR:
        {'-'*50}
        Ürün Adı | Satış Adedi | Toplam Tutar
        {'-'*50}
        """
        
        for urun_adi, adet, toplam_tutar in urun_raporu:
            rapor_metni += f"{urun_adi:8} | {adet:11} | {toplam_tutar:.2f} TL\n"
        
        rapor_metni += f"""
        {'-'*50}
        TOPLAM CİRO: {toplam_ciro:.2f} TL
        {'='*50}
        """
        
        # Raporu göster
        self.rapor_icerik.delete(1.0, tk.END)
        self.rapor_icerik.insert(tk.END, rapor_metni)
        
        messagebox.showinfo("Başarılı", "Rapor oluşturuldu!")
    
    def rapor_kaydet(self):
        rapor_icerik = self.rapor_icerik.get(1.0, tk.END)
        if not rapor_icerik.strip():
            messagebox.showerror("Hata", "Önce rapor oluşturmalısınız!")
            return
            
        dosya_adi = f"kafe_rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(dosya_adi, 'w', encoding='utf-8') as f:
            f.write(rapor_icerik)
        
        messagebox.showinfo("Başarılı", f"Rapor dosyaya kaydedildi:\n{dosya_adi}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KafeAdisyonProgrami(root)
    root.mainloop()
