import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import sqlite3
import os
from tkinter import filedialog

class KafeAdisyonProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title("Kafe Adisyon Programı")
        self.root.geometry("1200x800")
        
        # Renk tanımlamaları
        self.BOS_MASA_RENGI = "#e0e0e0"  # Gri
        self.DOLU_MASA_RENGI = "#ffa500"  # Turuncu
        self.UZUN_BEKLEYEN_MASA_RENGI = "#ff4500"  # Kırmızımsı turuncu
        self.ODEMESI_GECIKMIS_MASA_RENGI = "#ff0000"  # Kırmızı
        
        # Veritabanı bağlantısı
        self.db_connect()
        self.db_tablari_olustur()
        
        # Verileri yükle
        self.verileri_yukle()
        
        # Arayüz
        self.arayuz_olustur()
        
        # Masa durumlarını kontrol etmek için periyodik kontrol başlat
        self.masa_durum_kontrol()
    
    def db_connect(self):
        self.conn = sqlite3.connect('kafe_veritabani.db')
        self.cursor = self.conn.cursor()
    
    def db_tablari_olustur(self):
        # Masalar tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS masalar (
                masa_no TEXT PRIMARY KEY,
                adi TEXT,
                bakiye REAL,
                acilis_zamani TEXT,
                durum TEXT,
                kapanis_zamani TEXT
            )
        ''')
        
        # Siparisler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS siparisler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                urun_id INTEGER,
                urun_adi TEXT,
                adet INTEGER,
                fiyat REAL,
                zaman TEXT,
                FOREIGN KEY (masa_no) REFERENCES masalar (masa_no),
                FOREIGN KEY (urun_id) REFERENCES menu (id)
            )
        ''')
        
        # Menu tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kategori TEXT,
                urun_adi TEXT,
                fiyat REAL,
                siparis_sayisi INTEGER DEFAULT 0,
                sira_no INTEGER
            )
        ''')
        
        # Odemeler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS odemeler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                tutar REAL,
                alinan REAL,
                para_ustu REAL,
                yontem TEXT,
                zaman TEXT,
                FOREIGN KEY (masa_no) REFERENCES masalar (masa_no)
            )
        ''')
        
        self.conn.commit()
    
    def verileri_yukle(self):
        # Varsayılan menü öğelerini ekle (eğer tablo boşsa)
        self.cursor.execute("SELECT COUNT(*) FROM menu")
        if self.cursor.fetchone()[0] == 0:
            varsayilan_menu = [
                ("SICAK İÇECEKLER", "Çay", 10, 0, 1),
                ("SICAK İÇECEKLER", "Kahve", 15, 0, 2),
                ("SICAK İÇECEKLER", "Sıcak Çikolata", 20, 0, 3),
                ("SOĞUK İÇECEKLER", "Kola", 12, 0, 1),
                ("SOĞUK İÇECEKLER", "Meyve Suyu", 10, 0, 2),
                ("SOĞUK İÇECEKLER", "Su", 5, 0, 3),
                ("TATLILAR", "Baklava", 25, 0, 1),
                ("TATLILAR", "Künefe", 30, 0, 2),
                ("TATLILAR", "Profiterol", 20, 0, 3)
            ]
            self.cursor.executemany(
                "INSERT INTO menu (kategori, urun_adi, fiyat, siparis_sayisi, sira_no) VALUES (?, ?, ?, ?, ?)",
                varsayilan_menu
            )
            self.conn.commit()
    
    def arayuz_olustur(self):
        # Notebook (sekmeler)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Masa Yönetimi Sekmesi
        self.masa_sekmesi = ttk.Frame(self.notebook)
        self.notebook.add(self.masa_sekmesi, text="Masa Yönetimi")
        self.masa_arayuzu()
        
        # Menü Yönetimi Sekmesi
        self.menu_sekmesi = ttk.Frame(self.notebook)
        self.notebook.add(self.menu_sekmesi, text="Menü Yönetimi")
        self.menu_arayuzu()
        
        # Sipariş Yönetimi Sekmesi
        self.siparis_sekmesi = ttk.Frame(self.notebook)
        self.notebook.add(self.siparis_sekmesi, text="Sipariş Yönetimi")
        self.siparis_arayuzu()
        
        # Raporlama Sekmesi
        self.rapor_sekmesi = ttk.Frame(self.notebook)
        self.notebook.add(self.rapor_sekmesi, text="Raporlama")
        self.rapor_arayuzu()
    
    def masa_durum_kontrol(self):
        simdi = datetime.now()
        
        self.cursor.execute("SELECT masa_no FROM masalar")
        masalar = self.cursor.fetchall()
        
        for masa_no in masalar:
            masa_no = masa_no[0]
            self.cursor.execute(
                "SELECT zaman FROM siparisler WHERE masa_no=? ORDER BY zaman DESC LIMIT 1",
                (masa_no,)
            )
            son_siparis = self.cursor.fetchone()
            
            if son_siparis:
                son_siparis_zamani = datetime.strptime(son_siparis[0], "%Y-%m-%d %H:%M:%S")
                fark = simdi - son_siparis_zamani
                
                if fark > timedelta(minutes=30):
                    # 30 dakikadan uzun süredir yeni sipariş eklenmemiş
                    self.cursor.execute(
                        "UPDATE masalar SET durum=? WHERE masa_no=?",
                        ("UZUN_BEKLEYEN", masa_no)
                    )
                else:
                    # Normal dolu masa
                    self.cursor.execute(
                        "UPDATE masalar SET durum=? WHERE masa_no=?",
                        ("DOLU", masa_no)
                    )
            else:
                # Boş masa
                self.cursor.execute(
                    "UPDATE masalar SET durum=? WHERE masa_no=?",
                    ("BOS", masa_no)
                )
        
        self.conn.commit()
        self.masalar_goster()
        self.root.after(60000, self.masa_durum_kontrol)  # Her 1 dakikada bir kontrol et
    
    def masa_arayuzu(self):
        # Masa Ekleme Bölümü
        masa_ekle_frame = ttk.LabelFrame(self.masa_sekmesi, text="Masa Ekle/Düzenle")
        masa_ekle_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(masa_ekle_frame, text="Masa No:").grid(row=0, column=0, padx=5, pady=5)
        self.masa_no_entry = ttk.Entry(masa_ekle_frame)
        self.masa_no_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(masa_ekle_frame, text="Masa Adı:").grid(row=0, column=2, padx=5, pady=5)
        self.masa_adi_entry = ttk.Entry(masa_ekle_frame)
        self.masa_adi_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(masa_ekle_frame, text="Masa Ekle", command=self.masa_ekle).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(masa_ekle_frame, text="Masa Düzenle", command=self.masa_duzenle).grid(row=0, column=5, padx=5, pady=5)
        ttk.Button(masa_ekle_frame, text="Masa Sil", command=self.masa_sil).grid(row=0, column=6, padx=5, pady=5)
        
        # Masaları Görüntüleme Bölümü
        self.masalar_frame = ttk.LabelFrame(self.masa_sekmesi, text="Masalar")
        self.masalar_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.masalar_canvas = tk.Canvas(self.masalar_frame)
        self.masalar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.masalar_frame, orient="vertical", command=self.masalar_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.masalar_canvas_frame = ttk.Frame(self.masalar_canvas)
        self.masalar_canvas.create_window((0, 0), window=self.masalar_canvas_frame, anchor="nw")
        
        self.masalar_canvas.configure(yscrollcommand=scrollbar.set)
        self.masalar_canvas_frame.bind("<Configure>", lambda e: self.masalar_canvas.configure(scrollregion=self.masalar_canvas.bbox("all")))
        
        self.masalar_goster()
    
    def masalar_goster(self):
        # Önceki masaları temizle
        for widget in self.masalar_canvas_frame.winfo_children():
            widget.destroy()
        
        # Masaları veritabanından al
        self.cursor.execute("SELECT masa_no, adi, bakiye, durum FROM masalar ORDER BY CAST(masa_no AS INTEGER)")
        masalar = self.cursor.fetchall()
        
        # Her 5 masadan sonra yeni bir sütun başlat
        max_rows = 5
        current_row = 0
        current_col = 0
        
        for masa in masalar:
            masa_no, masa_adi, bakiye, durum = masa
            
            masa_frame = ttk.Frame(self.masalar_canvas_frame, borderwidth=2, relief="groove", padding=5)
            
            # Masa durumuna göre renk belirle
            if durum == "DOLU":
                arkaplan_rengi = self.DOLU_MASA_RENGI
            elif durum == "UZUN_BEKLEYEN":
                arkaplan_rengi = self.UZUN_BEKLEYEN_MASA_RENGI
            elif durum == "ODEMESI_GECIKMIS":
                arkaplan_rengi = self.ODEMESI_GECIKMIS_MASA_RENGI
            else:
                arkaplan_rengi = self.BOS_MASA_RENGI
            
            masa_frame.configure(style='Masa.TFrame')
            masa_frame.grid(row=current_row, column=current_col, padx=5, pady=5, sticky="nsew")
            
            # Masa bilgilerini göster
            ttk.Label(masa_frame, text=f"{masa_no} - {masa_adi}", 
                     font=('Arial', 10, 'bold'), background=arkaplan_rengi).pack(fill=tk.X)
            ttk.Label(masa_frame, text=f"Bakiye: {bakiye:.2f} TL", 
                     background=arkaplan_rengi).pack(fill=tk.X)
            
            # Durum bilgisi
            durum_metni = ""
            if durum == "DOLU":
                durum_metni = "Dolu"
            elif durum == "UZUN_BEKLEYEN":
                durum_metni = "Uzun Bekleyen"
            elif durum == "ODEMESI_GECIKMIS":
                durum_metni = "Ödemesi Gecikmiş"
            else:
                durum_metni = "Boş"
            
            ttk.Label(masa_frame, text=f"Durum: {durum_metni}", 
                     background=arkaplan_rengi).pack(fill=tk.X)
            
            # Butonlar
            btn_frame = ttk.Frame(masa_frame)
            btn_frame.pack(fill=tk.X)
            
            ttk.Button(btn_frame, text="Detay", 
                      command=lambda mn=masa_no: self.masa_detay_goster(mn)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(btn_frame, text="Sipariş Ekle", 
                      command=lambda mn=masa_no: self.siparis_ekle(mn)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(btn_frame, text="Ödeme Al", 
                      command=lambda mn=masa_no: self.odeme_al(mn)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            current_row += 1
            if current_row >= max_rows:
                current_row = 0
                current_col += 1
        
        # Grid yapılandırması
        for i in range(max_rows):
            self.masalar_canvas_frame.grid_rowconfigure(i, weight=1)
        for j in range(current_col + 1):
            self.masalar_canvas_frame.grid_columnconfigure(j, weight=1)
    
    def masa_ekle(self):
        masa_no = self.masa_no_entry.get()
        masa_adi = self.masa_adi_entry.get()
        
        if not masa_no:
            messagebox.showerror("Hata", "Masa numarası boş olamaz!")
            return
        
        # Masa numarasının zaten var olup olmadığını kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM masalar WHERE masa_no=?", (masa_no,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror("Hata", "Bu masa numarası zaten var!")
            return
        
        # Yeni masayı veritabanına ekle
        self.cursor.execute(
            "INSERT INTO masalar (masa_no, adi, bakiye, acilis_zamani, durum) VALUES (?, ?, ?, ?, ?)",
            (masa_no, masa_adi if masa_adi else f"Masa {masa_no}", 0, 
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "BOS")
        )
        self.conn.commit()
        
        self.masalar_goster()
        self.masa_no_entry.delete(0, tk.END)
        self.masa_adi_entry.delete(0, tk.END)
        messagebox.showinfo("Başarılı", "Masa başarıyla eklendi!")
    
    def masa_duzenle(self):
        masa_no = self.masa_no_entry.get()
        yeni_adi = self.masa_adi_entry.get()
        
        if not masa_no:
            messagebox.showerror("Hata", "Masa numarası boş olamaz!")
            return
        
        # Masa numarasının var olup olmadığını kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM masalar WHERE masa_no=?", (masa_no,))
        if self.cursor.fetchone()[0] == 0:
            messagebox.showerror("Hata", "Bu masa numarası bulunamadı!")
            return
        
        # Masayı güncelle
        self.cursor.execute(
            "UPDATE masalar SET adi=? WHERE masa_no=?",
            (yeni_adi if yeni_adi else f"Masa {masa_no}", masa_no)
        )
        self.conn.commit()
        
        self.masalar_goster()
        self.masa_no_entry.delete(0, tk.END)
        self.masa_adi_entry.delete(0, tk.END)
        messagebox.showinfo("Başarılı", "Masa başarıyla güncellendi!")
    
    def masa_sil(self):
        masa_no = simpledialog.askstring("Masa Sil", "Silinecek masa numarasını girin:")
        
        if not masa_no:
            return
        
        # Masa numarasının var olup olmadığını kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM masalar WHERE masa_no=?", (masa_no,))
        if self.cursor.fetchone()[0] == 0:
            messagebox.showerror("Hata", "Bu masa numarası bulunamadı!")
            return
        
        if messagebox.askyesno("Onay", f"{masa_no} numaralı masayı silmek istediğinize emin misiniz?"):
            # İlişkili siparişleri sil
            self.cursor.execute("DELETE FROM siparisler WHERE masa_no=?", (masa_no,))
            # Masayı sil
            self.cursor.execute("DELETE FROM masalar WHERE masa_no=?", (masa_no,))
            self.conn.commit()
            
            self.masalar_goster()
            messagebox.showinfo("Başarılı", "Masa başarıyla silindi!")
    
    def masa_detay_goster(self, masa_no):
        detay_penceresi = tk.Toplevel(self.root)
        detay_penceresi.title(f"{masa_no} Nolu Masa Detayları")
        detay_penceresi.geometry("600x400")
        
        # Masa bilgilerini veritabanından al
        self.cursor.execute(
            "SELECT adi, bakiye, acilis_zamani FROM masalar WHERE masa_no=?",
            (masa_no,)
        )
        masa_adi, bakiye, acilis_zamani = self.cursor.fetchone()
        
        ttk.Label(detay_penceresi, text=f"{masa_no} - {masa_adi}", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Masa bilgileri
        bilgi_frame = ttk.Frame(detay_penceresi)
        bilgi_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(bilgi_frame, text="Açılış Zamanı:").grid(row=0, column=0, sticky="w")
        ttk.Label(bilgi_frame, text=acilis_zamani).grid(row=0, column=1, sticky="w")
        
        ttk.Label(bilgi_frame, text="Bakiye:").grid(row=1, column=0, sticky="w")
        ttk.Label(bilgi_frame, text=f"{bakiye:.2f} TL").grid(row=1, column=1, sticky="w")
        
        # Siparişler
        siparisler_frame = ttk.LabelFrame(detay_penceresi, text="Siparişler")
        siparisler_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("#", "Ürün", "Adet", "Fiyat", "Toplam", "Zaman")
        tree = ttk.Treeview(siparisler_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor="center")
        
        tree.column("#", width=40)
        tree.column("Zaman", width=120)
        
        # Siparişleri veritabanından al
        self.cursor.execute(
            "SELECT urun_adi, adet, fiyat, zaman FROM siparisler WHERE masa_no=? ORDER BY zaman",
            (masa_no,)
        )
        for i, (urun, adet, fiyat, zaman) in enumerate(self.cursor.fetchall(), 1):
            tree.insert("", "end", values=(i, urun, adet, f"{fiyat:.2f}", f"{adet * fiyat:.2f}", zaman))
        
        scrollbar = ttk.Scrollbar(siparisler_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # İndirim butonu
        indirim_frame = ttk.Frame(detay_penceresi)
        indirim_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(indirim_frame, text="İndirim (%):").pack(side=tk.LEFT)
        indirim_entry = ttk.Entry(indirim_frame, width=5)
        indirim_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(indirim_frame, text="Uygula", 
                  command=lambda: self.indirim_uygula(masa_no, indirim_entry.get())).pack(side=tk.LEFT)
    
    def indirim_uygula(self, masa_no, indirim_orani):
        try:
            indirim = float(indirim_orani)
            if indirim < 0 or indirim > 100:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz indirim oranı! 0-100 arasında bir değer girin.")
            return
        
        # Toplam bakiyeyi al
        self.cursor.execute(
            "SELECT bakiye FROM masalar WHERE masa_no=?",
            (masa_no,)
        )
        toplam = self.cursor.fetchone()[0]
        
        indirim_miktari = toplam * indirim / 100
        yeni_bakiye = toplam - indirim_miktari
        
        # Bakiyeyi güncelle
        self.cursor.execute(
            "UPDATE masalar SET bakiye=? WHERE masa_no=?",
            (yeni_bakiye, masa_no)
        )
        
        # İndirimi sipariş olarak ekle
        self.cursor.execute(
            "INSERT INTO siparisler (masa_no, urun_adi, adet, fiyat, zaman) VALUES (?, ?, ?, ?, ?)",
            (masa_no, f"İndirim (%{indirim})", 1, -indirim_miktari, 
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        
        self.conn.commit()
        self.masalar_goster()
        messagebox.showinfo("Başarılı", f"%{indirim} indirim uygulandı. Yeni bakiye: {yeni_bakiye:.2f} TL")
    
    def menu_arayuzu(self):
        # Menü Ekleme/Düzenleme Bölümü
        menu_ekle_frame = ttk.LabelFrame(self.menu_sekmesi, text="Menü Ekle/Düzenle")
        menu_ekle_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # Kategori seçimi
        ttk.Label(menu_ekle_frame, text="Kategori:").grid(row=0, column=0, padx=5, pady=5)
        self.kategori_combobox = ttk.Combobox(menu_ekle_frame, state="readonly")
        self.kategori_combobox.grid(row=0, column=1, padx=5, pady=5)
        
        # Kategorileri yükle
        self.kategori_combobox['values'] = self.kategorileri_getir()
        if self.kategori_combobox['values']:
            self.kategori_combobox.current(0)
        
        ttk.Button(menu_ekle_frame, text="Yeni Kategori Ekle", 
                  command=self.yeni_kategori_ekle).grid(row=0, column=2, padx=5, pady=5)
        
        # Ürün bilgileri
        ttk.Label(menu_ekle_frame, text="Ürün Adı:").grid(row=1, column=0, padx=5, pady=5)
        self.urun_adi_entry = ttk.Entry(menu_ekle_frame)
        self.urun_adi_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(menu_ekle_frame, text="Fiyat:").grid(row=1, column=2, padx=5, pady=5)
        self.urun_fiyat_entry = ttk.Entry(menu_ekle_frame)
        self.urun_fiyat_entry.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(menu_ekle_frame, text="Sıra No:").grid(row=1, column=4, padx=5, pady=5)
        self.urun_sira_entry = ttk.Entry(menu_ekle_frame)
        self.urun_sira_entry.grid(row=1, column=5, padx=5, pady=5)
        
        # Butonlar
        ttk.Button(menu_ekle_frame, text="Ürün Ekle", 
                  command=self.urun_ekle).grid(row=1, column=6, padx=5, pady=5)
        ttk.Button(menu_ekle_frame, text="Ürün Sil", 
                  command=self.urun_sil).grid(row=1, column=7, padx=5, pady=5)
        ttk.Button(menu_ekle_frame, text="Ürün Güncelle", 
                  command=self.urun_guncelle).grid(row=1, column=8, padx=5, pady=5)
        
        # Menü Görüntüleme Bölümü
        self.menu_frame = ttk.LabelFrame(self.menu_sekmesi, text="Menü")
        self.menu_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.menu_tree = ttk.Treeview(self.menu_frame, columns=("ID", "Kategori", "Ürün", "Fiyat", "Sipariş Sayısı", "Sıra No"), show="headings")
        
        self.menu_tree.heading("ID", text="ID")
        self.menu_tree.heading("Kategori", text="Kategori")
        self.menu_tree.heading("Ürün", text="Ürün")
        self.menu_tree.heading("Fiyat", text="Fiyat (TL)")
        self.menu_tree.heading("Sipariş Sayısı", text="Sipariş Sayısı")
        self.menu_tree.heading("Sıra No", text="Sıra No")
        
        self.menu_tree.column("ID", width=50)
        self.menu_tree.column("Kategori", width=150)
        self.menu_tree.column("Ürün", width=150)
        self.menu_tree.column("Fiyat", width=80, anchor="e")
        self.menu_tree.column("Sipariş Sayısı", width=100, anchor="e")
        self.menu_tree.column("Sıra No", width=80, anchor="e")
        
        scrollbar = ttk.Scrollbar(self.menu_frame, orient="vertical", command=self.menu_tree.yview)
        self.menu_tree.configure(yscrollcommand=scrollbar.set)
        
        self.menu_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview'da seçim yapıldığında bilgileri forma yükle
        self.menu_tree.bind("<<TreeviewSelect>>", self.menu_secildi)
        
        self.menu_goster()
    
    def kategorileri_getir(self):
        self.cursor.execute("SELECT DISTINCT kategori FROM menu ORDER BY kategori")
        return [kategori[0] for kategori in self.cursor.fetchall()]
    
    def menu_secildi(self, event):
        selected = self.menu_tree.selection()
        if not selected:
            return
        
        item = self.menu_tree.item(selected[0])
        values = item['values']
        
        self.urun_id = values[0]  # Seçilen ürünün ID'sini sakla
        self.kategori_combobox.set(values[1])
        self.urun_adi_entry.delete(0, tk.END)
        self.urun_adi_entry.insert(0, values[2])
        self.urun_fiyat_entry.delete(0, tk.END)
        self.urun_fiyat_entry.insert(0, values[3])
        self.urun_sira_entry.delete(0, tk.END)
        self.urun_sira_entry.insert(0, values[5])
    
    def yeni_kategori_ekle(self):
        yeni_kategori = simpledialog.askstring("Yeni Kategori", "Yeni kategori adı girin:")
        
        if yeni_kategori and yeni_kategori.strip():
            # Kategorinin zaten var olup olmadığını kontrol et
            self.cursor.execute("SELECT COUNT(*) FROM menu WHERE kategori=?", (yeni_kategori,))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showerror("Hata", "Bu kategori zaten var!")
            else:
                # Kategorileri yenile
                self.kategori_combobox['values'] = self.kategorileri_getir()
                self.kategori_combobox.set(yeni_kategori)
                messagebox.showinfo("Başarılı", "Yeni kategori eklendi!")
    
    def urun_ekle(self):
        kategori = self.kategori_combobox.get()
        urun_adi = self.urun_adi_entry.get()
        urun_fiyat = self.urun_fiyat_entry.get()
        sira_no = self.urun_sira_entry.get()
        
        if not all([kategori, urun_adi, urun_fiyat, sira_no]):
            messagebox.showerror("Hata", "Tüm alanları doldurun!")
            return
        
        try:
            fiyat = float(urun_fiyat)
            if fiyat <= 0:
                raise ValueError
            sira = int(sira_no)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz fiyat veya sıra numarası! Pozitif sayı girin.")
            return
        
        # Ürünün zaten var olup olmadığını kontrol et
        self.cursor.execute(
            "SELECT COUNT(*) FROM menu WHERE kategori=? AND urun_adi=?",
            (kategori, urun_adi)
        )
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror("Hata", "Bu ürün zaten bu kategoride var!")
            return
        
        # Yeni ürünü ekle
        self.cursor.execute(
            "INSERT INTO menu (kategori, urun_adi, fiyat, sira_no) VALUES (?, ?, ?, ?)",
            (kategori, urun_adi, fiyat, sira)
        )
        self.conn.commit()
        
        self.urun_adi_entry.delete(0, tk.END)
        self.urun_fiyat_entry.delete(0, tk.END)
        self.urun_sira_entry.delete(0, tk.END)
        self.menu_goster()
        messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi!")
    
    def urun_guncelle(self):
        if not hasattr(self, 'urun_id'):
            messagebox.showerror("Hata", "Lütfen güncellenecek bir ürün seçin!")
            return
        
        kategori = self.kategori_combobox.get()
        urun_adi = self.urun_adi_entry.get()
        urun_fiyat = self.urun_fiyat_entry.get()
        sira_no = self.urun_sira_entry.get()
        
        if not all([kategori, urun_adi, urun_fiyat, sira_no]):
            messagebox.showerror("Hata", "Tüm alanları doldurun!")
            return
        
        try:
            fiyat = float(urun_fiyat)
            if fiyat <= 0:
                raise ValueError
            sira = int(sira_no)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz fiyat veya sıra numarası! Pozitif sayı girin.")
            return
        
        # Ürünü güncelle
        self.cursor.execute(
            "UPDATE menu SET kategori=?, urun_adi=?, fiyat=?, sira_no=? WHERE id=?",
            (kategori, urun_adi, fiyat, sira, self.urun_id)
        )
        self.conn.commit()
        
        self.menu_goster()
        messagebox.showinfo("Başarılı", "Ürün başarıyla güncellendi!")
    
    def urun_sil(self):
        if not hasattr(self, 'urun_id'):
            messagebox.showerror("Hata", "Lütfen silinecek bir ürün seçin!")
            return
        
        if messagebox.askyesno("Onay", "Bu ürünü silmek istediğinize emin misiniz?"):
            self.cursor.execute("DELETE FROM menu WHERE id=?", (self.urun_id,))
            self.conn.commit()
            
            self.urun_adi_entry.delete(0, tk.END)
            self.urun_fiyat_entry.delete(0, tk.END)
            self.urun_sira_entry.delete(0, tk.END)
            self.menu_goster()
            messagebox.showinfo("Başarılı", "Ürün başarıyla silindi!")
    
    def menu_goster(self):
        self.menu_tree.delete(*self.menu_tree.get_children())
        
        # Menü öğelerini veritabanından al (sıra numarasına göre sırala)
        self.cursor.execute(
            "SELECT id, kategori, urun_adi, fiyat, siparis_sayisi, sira_no FROM menu ORDER BY kategori, sira_no"
        )
        
        for id, kategori, urun, fiyat, siparis_sayisi, sira_no in self.cursor.fetchall():
            self.menu_tree.insert("", "end", values=(id, kategori, urun, f"{fiyat:.2f}", siparis_sayisi, sira_no))
    
    def siparis_arayuzu(self):
        # Sipariş Düzeltme Bölümü
        siparis_duzenle_frame = ttk.LabelFrame(self.siparis_sekmesi, text="Sipariş Düzeltme")
        siparis_duzenle_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(siparis_duzenle_frame, text="Masa No:").grid(row=0, column=0, padx=5, pady=5)
        self.duzenle_masa_no_entry = ttk.Entry(siparis_duzenle_frame)
        self.duzenle_masa_no_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(siparis_duzenle_frame, text="Sipariş No:").grid(row=0, column=2, padx=5, pady=5)
        self.duzenle_siparis_no_entry = ttk.Entry(siparis_duzenle_frame)
        self.duzenle_siparis_no_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(siparis_duzenle_frame, text="Siparişi Sil", 
                  command=self.siparis_sil).grid(row=0, column=4, padx=5, pady=5)
        
        # Sipariş Aktarma Bölümü
        siparis_aktarma_frame = ttk.LabelFrame(self.siparis_sekmesi, text="Sipariş Aktarma")
        siparis_aktarma_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(siparis_aktarma_frame, text="Kaynak Masa No:").grid(row=0, column=0, padx=5, pady=5)
        self.kaynak_masa_entry = ttk.Entry(siparis_aktarma_frame)
        self.kaynak_masa_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(siparis_aktarma_frame, text="Hedef Masa No:").grid(row=0, column=2, padx=5, pady=5)
        self.hedef_masa_entry = ttk.Entry(siparis_aktarma_frame)
        self.hedef_masa_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(siparis_aktarma_frame, text="Siparişleri Aktar", 
                  command=self.siparis_aktar).grid(row=0, column=4, padx=5, pady=5)
    
    def siparis_ekle(self, masa_no):
        siparis_penceresi = tk.Toplevel(self.root)
        siparis_penceresi.title(f"{masa_no} Nolu Masa - Sipariş Ekle")
        siparis_penceresi.geometry("600x400")
        
        # Masa bilgilerini veritabanından al
        self.cursor.execute(
            "SELECT adi FROM masalar WHERE masa_no=?",
            (masa_no,)
        )
        masa_adi = self.cursor.fetchone()[0]
        
        ttk.Label(siparis_penceresi, text=f"{masa_no} - {masa_adi}", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Kategori seçimi
        kategori_frame = ttk.Frame(siparis_penceresi)
        kategori_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(kategori_frame, text="Kategori:").pack(side=tk.LEFT)
        kategori_combobox = ttk.Combobox(kategori_frame, values=self.kategorileri_getir(), state="readonly")
        kategori_combobox.pack(side=tk.LEFT, padx=5)
        if self.kategorileri_getir():
            kategori_combobox.current(0)
        
        # Ürün seçimi
        urun_frame = ttk.Frame(siparis_penceresi)
        urun_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(urun_frame, text="Ürün:").pack(side=tk.LEFT)
        urun_combobox = ttk.Combobox(urun_frame, state="readonly")
        urun_combobox.pack(side=tk.LEFT, padx=5)
        
        # Kategori değiştiğinde ürünleri güncelle
        def kategori_degisti(event):
            secili_kategori = kategori_combobox.get()
            self.cursor.execute(
                "SELECT urun_adi FROM menu WHERE kategori=? ORDER BY sira_no",
                (secili_kategori,)
            )
            urunler = [urun[0] for urun in self.cursor.fetchall()]
            urun_combobox['values'] = urunler
            if urunler:
                urun_combobox.current(0)
                urun_degisti(None)  # Fiyatı güncelle
        
        kategori_combobox.bind("<<ComboboxSelected>>", kategori_degisti)
        if self.kategorileri_getir():
            kategori_degisti(None)  # Başlangıç durumu için
        
        # Adet
        adet_frame = ttk.Frame(siparis_penceresi)
        adet_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(adet_frame, text="Adet:").pack(side=tk.LEFT)
        adet_spinbox = ttk.Spinbox(adet_frame, from_=1, to=20, width=5)
        adet_spinbox.pack(side=tk.LEFT, padx=5)
        adet_spinbox.set(1)
        
        # Fiyat bilgisi
        fiyat_frame = ttk.Frame(siparis_penceresi)
        fiyat_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(fiyat_frame, text="Fiyat:").pack(side=tk.LEFT)
        fiyat_label = ttk.Label(fiyat_frame, text="0.00 TL")
        fiyat_label.pack(side=tk.LEFT, padx=5)
        
        # Ürün değiştiğinde fiyatı güncelle
        def urun_degisti(event):
            secili_kategori = kategori_combobox.get()
            secili_urun = urun_combobox.get()
            if secili_kategori and secili_urun:
                self.cursor.execute(
                    "SELECT fiyat FROM menu WHERE kategori=? AND urun_adi=?",
                    (secili_kategori, secili_urun)
                )
                fiyat = self.cursor.fetchone()[0]
                fiyat_label.config(text=f"{fiyat:.2f} TL")
        
        urun_combobox.bind("<<ComboboxSelected>>", urun_degisti)
        if self.kategorileri_getir():
            urun_degisti(None)  # Başlangıç durumu için
        
        # Ekle butonu
        def siparis_ekle():
            secili_kategori = kategori_combobox.get()
            secili_urun = urun_combobox.get()
            adet = int(adet_spinbox.get())
            
            if not all([secili_kategori, secili_urun, adet > 0]):
                messagebox.showerror("Hata", "Geçersiz sipariş bilgisi!")
                return
            
            # Ürün ID ve fiyatını al
            self.cursor.execute(
                "SELECT id, fiyat FROM menu WHERE kategori=? AND urun_adi=?",
                (secili_kategori, secili_urun)
            )
            urun_id, fiyat = self.cursor.fetchone()
            toplam = adet * fiyat
            
            # Siparişi veritabanına ekle
            self.cursor.execute(
                "INSERT INTO siparisler (masa_no, urun_id, urun_adi, adet, fiyat, zaman) VALUES (?, ?, ?, ?, ?, ?)",
                (masa_no, urun_id, secili_urun, adet, fiyat, 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            
            # Bakiyeyi güncelle
            self.cursor.execute(
                "UPDATE masalar SET bakiye=bakiye+?, durum=? WHERE masa_no=?",
                (toplam, "DOLU", masa_no)
            )
            
            # Ürünün sipariş sayısını artır
            self.cursor.execute(
                "UPDATE menu SET siparis_sayisi=siparis_sayisi+1 WHERE id=?",
                (urun_id,)
            )
            
            self.conn.commit()
            self.masalar_goster()
            messagebox.showinfo("Başarılı", f"{adet} x {secili_urun} siparişi eklendi. Toplam: {toplam:.2f} TL")
            siparis_penceresi.destroy()
        
        ttk.Button(siparis_penceresi, text="Sipariş Ekle", command=siparis_ekle).pack(pady=10)
    
    def siparis_sil(self):
        masa_no = self.duzenle_masa_no_entry.get()
        siparis_no = self.duzenle_siparis_no_entry.get()
        
        if not all([masa_no, siparis_no]):
            messagebox.showerror("Hata", "Masa numarası ve sipariş numarası girin!")
            return
        
        # Masa numarasının var olup olmadığını kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM masalar WHERE masa_no=?", (masa_no,))
        if self.cursor.fetchone()[0] == 0:
            messagebox.showerror("Hata", "Bu masa numarası bulunamadı!")
            return
        
        try:
            siparis_no = int(siparis_no)
            if siparis_no < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz sipariş numarası!")
            return
        
        # Sipariş bilgilerini al
        self.cursor.execute(
            "SELECT id, urun_id, urun_adi, adet, fiyat FROM siparisler WHERE masa_no=? ORDER BY id LIMIT 1 OFFSET ?",
            (masa_no, siparis_no-1)
        )
        siparis = self.cursor.fetchone()
        
        if not siparis:
            messagebox.showerror("Hata", "Bu sipariş numarası bulunamadı!")
            return
        
        siparis_id, urun_id, urun_adi, adet, fiyat = siparis
        toplam = adet * fiyat
        
        if messagebox.askyesno("Onay", f"{siparis_no}. siparişi silmek istediğinize emin misiniz?\n{adet} x {urun_adi} = {toplam:.2f} TL"):
            # Siparişi sil
            self.cursor.execute("DELETE FROM siparisler WHERE id=?", (siparis_id,))
            
            # Bakiyeyi güncelle
            self.cursor.execute(
                "UPDATE masalar SET bakiye=bakiye-? WHERE masa_no=?",
                (toplam, masa_no)
            )
            
            # Ürünün sipariş sayısını azalt
            self.cursor.execute(
                "UPDATE menu SET siparis_sayisi=siparis_sayisi-1 WHERE id=?",
                (urun_id,)
            )
            
            # Eğer sipariş kalmadıysa masayı boş olarak işaretle
            self.cursor.execute(
                "SELECT COUNT(*) FROM siparisler WHERE masa_no=?",
                (masa_no,)
            )
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute(
                    "UPDATE masalar SET durum=? WHERE masa_no=?",
                    ("BOS", masa_no)
                )
            
            self.conn.commit()
            self.masalar_goster()
            messagebox.showinfo("Başarılı", "Sipariş başarıyla silindi!")
    
    def siparis_aktar(self):
        kaynak_masa = self.kaynak_masa_entry.get()
        hedef_masa = self.hedef_masa_entry.get()
        
        if not all([kaynak_masa, hedef_masa]):
            messagebox.showerror("Hata", "Kaynak ve hedef masa numaralarını girin!")
            return
        
        # Masaların var olup olmadığını kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM masalar WHERE masa_no=?", (kaynak_masa,))
        if self.cursor.fetchone()[0] == 0:
            messagebox.showerror("Hata", "Kaynak masa numarası bulunamadı!")
            return
        
        self.cursor.execute("SELECT COUNT(*) FROM masalar WHERE masa_no=?", (hedef_masa,))
        if self.cursor.fetchone()[0] == 0:
            messagebox.showerror("Hata", "Hedef masa numarası bulunamadı!")
            return
        
        if kaynak_masa == hedef_masa:
            messagebox.showerror("Hata", "Kaynak ve hedef masa aynı olamaz!")
            return
        
        # Kaynak masada sipariş olup olmadığını kontrol et
        self.cursor.execute(
            "SELECT COUNT(*) FROM siparisler WHERE masa_no=?",
            (kaynak_masa,)
        )
        if self.cursor.fetchone()[0] == 0:
            messagebox.showerror("Hata", "Kaynak masada aktarılacak sipariş yok!")
            return
        
        if messagebox.askyesno("Onay", f"{kaynak_masa} numaralı masadaki tüm siparişleri {hedef_masa} numaralı masaya aktarmak istediğinize emin misiniz?"):
            # Siparişleri aktar
            self.cursor.execute(
                "UPDATE siparisler SET masa_no=? WHERE masa_no=?",
                (hedef_masa, kaynak_masa)
            )
            
            # Toplam bakiyeyi hesapla ve aktar
            self.cursor.execute(
                "SELECT SUM(adet*fiyat) FROM siparisler WHERE masa_no=?",
                (kaynak_masa,)
            )
            toplam_bakiye = self.cursor.fetchone()[0] or 0
            
            # Bakiyeleri güncelle
            self.cursor.execute(
                "UPDATE masalar SET bakiye=bakiye-? WHERE masa_no=?",
                (toplam_bakiye, kaynak_masa)
            )
            self.cursor.execute(
                "UPDATE masalar SET bakiye=bakiye+?, durum=? WHERE masa_no=?",
                (toplam_bakiye, "DOLU", hedef_masa)
            )
            
            # Kaynak masayı boş olarak işaretle
            self.cursor.execute(
                "UPDATE masalar SET durum=? WHERE masa_no=?",
                ("BOS", kaynak_masa)
            )
            
            self.conn.commit()
            self.masalar_goster()
            messagebox.showinfo("Başarılı", "Siparişler başarıyla aktarıldı!")
    
    def odeme_al(self, masa_no):
        # Masa bilgilerini veritabanından al
        self.cursor.execute(
            "SELECT adi, bakiye FROM masalar WHERE masa_no=?",
            (masa_no,)
        )
        masa_adi, bakiye = self.cursor.fetchone()
        
        if bakiye <= 0:
            messagebox.showinfo("Bilgi", "Bu masada ödenecek bir tutar yok!")
            return
        
        odeme_penceresi = tk.Toplevel(self.root)
        odeme_penceresi.title(f"{masa_no} Nolu Masa - Ödeme Al")
        odeme_penceresi.geometry("400x300")
        
        ttk.Label(odeme_penceresi, text=f"{masa_no} - {masa_adi}", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Label(odeme_penceresi, text=f"Toplam Tutar: {bakiye:.2f} TL", 
                 font=('Arial', 10)).pack(pady=5)
        
        # Ödeme yöntemi
        odeme_yontemi_frame = ttk.Frame(odeme_penceresi)
        odeme_yontemi_frame.pack(pady=10)
        
        ttk.Label(odeme_yontemi_frame, text="Ödeme Yöntemi:").pack(side=tk.LEFT)
        self.odeme_yontemi = tk.StringVar(value="Nakit")
        ttk.Radiobutton(odeme_yontemi_frame, text="Nakit", 
                       variable=self.odeme_yontemi, value="Nakit").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(odeme_yontemi_frame, text="Kredi Kartı", 
                       variable=self.odeme_yontemi, value="Kredi Kartı").pack(side=tk.LEFT, padx=5)
        
        # Alınan tutar
        alinan_frame = ttk.Frame(odeme_penceresi)
        alinan_frame.pack(pady=10)
        
        ttk.Label(alinan_frame, text="Alınan Tutar:").pack(side=tk.LEFT)
        alinan_entry = ttk.Entry(alinan_frame)
        alinan_entry.pack(side=tk.LEFT, padx=5)
        alinan_entry.insert(0, f"{bakiye:.2f}")
        
        def odeme_yap():
            try:
                alinan = float(alinan_entry.get())
                if alinan < bakiye:
                    messagebox.showerror("Hata", "Alınan tutar toplam tutardan az olamaz!")
                    return
                
                para_ustu = alinan - bakiye
                
                # Ödeme bilgilerini veritabanına kaydet
                self.cursor.execute(
                    "INSERT INTO odemeler (masa_no, tutar, alinan, para_ustu, yontem, zaman) VALUES (?, ?, ?, ?, ?, ?)",
                    (masa_no, bakiye, alinan, para_ustu, self.odeme_yontemi.get(), 
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                
                # Masayı kapat
                self.cursor.execute(
                    "UPDATE masalar SET kapanis_zamani=?, durum=? WHERE masa_no=?",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "KAPALI", masa_no)
                )
                
                # Siparişleri geçmişe taşı (bu örnekte siliniyor, gerçek uygulamada başka bir tabloya taşınabilir)
                self.cursor.execute(
                    "DELETE FROM siparisler WHERE masa_no=?",
                    (masa_no,)
                )
                
                self.conn.commit()
                self.masalar_goster()
                
                messagebox.showinfo("Başarılı", f"Ödeme alındı!\nPara Üstü: {para_ustu:.2f} TL")
                odeme_penceresi.destroy()
                
                # Fiş yazdırma seçeneği
                if messagebox.askyesno("Fiş Yazdır", "Fiş yazdırmak ister misiniz?"):
                    self.fis_yazdir(masa_no, masa_adi, bakiye, alinan, para_ustu)
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz tutar!")
        
        ttk.Button(odeme_penceresi, text="Ödemeyi Tamamla", command=odeme_yap).pack(pady=20)
    
    def fis_yazdir(self, masa_no, masa_adi, toplam, alinan, para_ustu):
        fis_penceresi = tk.Toplevel(self.root)
        fis_penceresi.title("Fiş Yazdır")
        fis_penceresi.geometry("400x600")
        
        fis_text = tk.Text(fis_penceresi, font=('Courier New', 10))
        fis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Fiş başlığı
        fis_text.insert(tk.END, " KAFE ADISYON PROGRAMI\n".center(40))
        fis_text.insert(tk.END, "="*40 + "\n")
        fis_text.insert(tk.END, f"Masa No: {masa_no}\n")
        fis_text.insert(tk.END, f"Masa Adı: {masa_adi}\n")
        fis_text.insert(tk.END, f"Tarih: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        fis_text.insert(tk.END, "-"*40 + "\n")
        
        # Siparişler
        fis_text.insert(tk.END, " Siparişler\n".center(40))
        fis_text.insert(tk.END, "-"*40 + "\n")
        
        # Siparişleri veritabanından al
        self.cursor.execute(
            "SELECT urun_adi, adet, fiyat FROM siparisler WHERE masa_no=?",
            (masa_no,)
        )
        for urun, adet, fiyat in self.cursor.fetchall():
            line = f"{adet}x {urun[:20]:<20} {adet * fiyat:>7.2f} TL\n"
            fis_text.insert(tk.END, line)
        
        fis_text.insert(tk.END, "-"*40 + "\n")
        fis_text.insert(tk.END, f"Toplam: {toplam:>30.2f} TL\n")
        fis_text.insert(tk.END, f"Alınan: {alinan:>30.2f} TL\n")
        fis_text.insert(tk.END, f"Para Üstü: {para_ustu:>27.2f} TL\n")
        fis_text.insert(tk.END, f"Ödeme Yöntemi: {self.odeme_yontemi.get():>23}\n")
        fis_text.insert(tk.END, "="*40 + "\n")
        fis_text.insert(tk.END, " Teşekkür Ederiz!\n".center(40))
        fis_text.insert(tk.END, "="*40 + "\n")
        
        fis_text.config(state=tk.DISABLED)
        
        ttk.Button(fis_penceresi, text="Yazdır", 
                  command=lambda: self.gercek_fis_yazdir(fis_text.get("1.0", tk.END))).pack(pady=10)
        ttk.Button(fis_penceresi, text="Kaydet", 
                  command=lambda: self.fis_kaydet(masa_no, fis_text.get("1.0", tk.END))).pack(pady=5)
    
    def gercek_fis_yazdir(self, fis_metni):
        # Bu fonksiyon gerçek bir yazıcıya bağlantı için genişletilebilir
        messagebox.showinfo("Yazdır", "Fiş yazdırma işlemi simüle edildi.\n\n" + fis_metni)
    
    def fis_kaydet(self, masa_no, fis_metni):
        dosya_adi = f"fis_{masa_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        dosya_yolu = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=dosya_adi)
        
        if dosya_yolu:
            with open(dosya_yolu, 'w', encoding='utf-8') as f:
                f.write(fis_metni)
            messagebox.showinfo("Başarılı", f"Fiş başarıyla kaydedildi:\n{dosya_yolu}")
    
    def rapor_arayuzu(self):
        # Rapor Türü Seçimi
        rapor_turu_frame = ttk.LabelFrame(self.rapor_sekmesi, text="Rapor Türü")
        rapor_turu_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.rapor_turu = tk.StringVar(value="gunluk")
        ttk.Radiobutton(rapor_turu_frame, text="Günlük", 
                       variable=self.rapor_turu, value="gunluk").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(rapor_turu_frame, text="Aylık", 
                       variable=self.rapor_turu, value="aylik").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(rapor_turu_frame, text="Özel Tarih Aralığı", 
                       variable=self.rapor_turu, value="ozel").pack(side=tk.LEFT, padx=5)
        
        # Tarih Seçimi
        tarih_frame = ttk.Frame(self.rapor_sekmesi)
        tarih_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(tarih_frame, text="Başlangıç Tarihi:").pack(side=tk.LEFT, padx=5)
        self.baslangic_tarihi_entry = ttk.Entry(tarih_frame)
        self.baslangic_tarihi_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(tarih_frame, text="Bitiş Tarihi:").pack(side=tk.LEFT, padx=5)
        self.bitis_tarihi_entry = ttk.Entry(tarih_frame)
        self.bitis_tarihi_entry.pack(side=tk.LEFT, padx=5)
        
        # Rapor Butonu
        ttk.Button(self.rapor_sekmesi, text="Rapor Oluştur", 
                  command=self.rapor_olustur).pack(pady=10)
        
        # Rapor Görüntüleme Bölümü
        self.rapor_frame = ttk.LabelFrame(self.rapor_sekmesi, text="Rapor")
        self.rapor_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.rapor_tree = ttk.Treeview(self.rapor_frame, 
                                      columns=("Tarih", "Masa No", "Masa Adı", "Toplam Tutar", "Ödeme Yöntemi"), 
                                      show="headings")
        
        self.rapor_tree.heading("Tarih", text="Tarih")
        self.rapor_tree.heading("Masa No", text="Masa No")
        self.rapor_tree.heading("Masa Adı", text="Masa Adı")
        self.rapor_tree.heading("Toplam Tutar", text="Toplam Tutar")
        self.rapor_tree.heading("Ödeme Yöntemi", text="Ödeme Yöntemi")
        
        self.rapor_tree.column("Tarih", width=120)
        self.rapor_tree.column("Masa No", width=80)
        self.rapor_tree.column("Masa Adı", width=150)
        self.rapor_tree.column("Toplam Tutar", width=100, anchor="e")
        self.rapor_tree.column("Ödeme Yöntemi", width=100)
        
        scrollbar = ttk.Scrollbar(self.rapor_frame, orient="vertical", command=self.rapor_tree.yview)
        self.rapor_tree.configure(yscrollcommand=scrollbar.set)
        
        self.rapor_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Toplam Bilgisi
        self.toplam_label = ttk.Label(self.rapor_sekmesi, text="Toplam: 0.00 TL", 
                                     font=('Arial', 10, 'bold'))
        self.toplam_label.pack(pady=5)
        
        # Dışa Aktarma Butonları
        export_frame = ttk.Frame(self.rapor_sekmesi)
        export_frame.pack(pady=10)
        
        ttk.Button(export_frame, text="Excel'e Aktar", 
                  command=self.excele_aktar).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="TXT'ye Aktar", 
                  command=self.txte_aktar).pack(side=tk.LEFT, padx=5)
    
    def rapor_olustur(self):
        rapor_turu = self.rapor_turu.get()
        baslangic_tarihi = self.baslangic_tarihi_entry.get()
        bitis_tarihi = self.bitis_tarihi_entry.get()
        
        try:
            if rapor_turu == "gunluk":
                bugun = datetime.now().strftime("%Y-%m-%d")
                self.cursor.execute(
                    '''SELECT o.zaman, m.masa_no, m.adi, o.tutar, o.yontem 
                    FROM odemeler o
                    JOIN masalar m ON o.masa_no = m.masa_no
                    WHERE o.zaman LIKE ? || '%'
                    ORDER BY o.zaman''',
                    (bugun,)
                )
            elif rapor_turu == "aylik":
                bu_ay = datetime.now().strftime("%Y-%m")
                self.cursor.execute(
                    '''SELECT o.zaman, m.masa_no, m.adi, o.tutar, o.yontem 
                    FROM odemeler o
                    JOIN masalar m ON o.masa_no = m.masa_no
                    WHERE o.zaman LIKE ? || '%'
                    ORDER BY o.zaman''',
                    (bu_ay,)
                )
            elif rapor_turu == "ozel":
                if not baslangic_tarihi or not bitis_tarihi:
                    messagebox.showerror("Hata", "Tarih aralığı belirtin!")
                    return
                
                try:
                    baslangic = datetime.strptime(baslangic_tarihi, "%Y-%m-%d")
                    bitis = datetime.strptime(bitis_tarihi, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Hata", "Tarih formatı yanlış! YYYY-AA-GG şeklinde girin.")
                    return
                
                self.cursor.execute(
                    '''SELECT o.zaman, m.masa_no, m.adi, o.tutar, o.yontem 
                    FROM odemeler o
                    JOIN masalar m ON o.masa_no = m.masa_no
                    WHERE date(o.zaman) BETWEEN date(?) AND date(?)
                    ORDER BY o.zaman''',
                    (baslangic_tarihi, bitis_tarihi)
                )
            else:
                messagebox.showerror("Hata", "Geçersiz rapor türü!")
                return
            
            rapor_verileri = self.cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulurken hata: {str(e)}")
            return
        
        self.rapor_tree.delete(*self.rapor_tree.get_children())
        toplam = 0
        
        for tarih, masa_no, masa_adi, tutar, yontem in rapor_verileri:
            self.rapor_tree.insert("", "end", values=(tarih, masa_no, masa_adi, f"{tutar:.2f}", yontem))
            toplam += tutar
        
        self.toplam_label.config(text=f"Toplam: {toplam:.2f} TL")
    
    def excele_aktar(self):
        try:
            import pandas as pd
        except ImportError:
            messagebox.showerror("Hata", "Excel aktarımı için pandas kütüphanesi gerekli!")
            return
        
        items = []
        for item in self.rapor_tree.get_children():
            items.append(self.rapor_tree.item(item)['values'])
        
        if not items:
            messagebox.showerror("Hata", "Aktarılacak veri yok!")
            return
        
        df = pd.DataFrame(items, columns=["Tarih", "Masa No", "Masa Adı", "Toplam Tutar", "Ödeme Yöntemi"])
        
        dosya_yolu = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if dosya_yolu:
            try:
                df.to_excel(dosya_yolu, index=False)
                messagebox.showinfo("Başarılı", f"Veri başarıyla Excel'e aktarıldı:\n{dosya_yolu}")
            except Exception as e:
                messagebox.showerror("Hata", f"Excel'e aktarım sırasında hata: {str(e)}")
    
    def txte_aktar(self):
        items = []
        for item in self.rapor_tree.get_children():
            items.append(self.rapor_tree.item(item)['values'])
        
        if not items:
            messagebox.showerror("Hata", "Aktarılacak veri yok!")
            return
        
        rapor_metni = "Tarih\tMasa No\tMasa Adı\tToplam Tutar\tÖdeme Yöntemi\n"
        rapor_metni += "-"*80 + "\n"
        
        for item in items:
            rapor_metni += f"{item[0]}\t{item[1]}\t{item[2]}\t{item[3]}\t{item[4]}\n"
        
        toplam = self.toplam_label.cget("text")
        rapor_metni += "-"*80 + "\n"
        rapor_metni += f"{toplam}\n"
        
        dosya_yolu = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if dosya_yolu:
            try:
                with open(dosya_yolu, 'w', encoding='utf-8') as f:
                    f.write(rapor_metni)
                messagebox.showinfo("Başarılı", f"Veri başarıyla TXT'ye aktarıldı:\n{dosya_yolu}")
            except Exception as e:
                messagebox.showerror("Hata", f"TXT'ye aktarım sırasında hata: {str(e)}")
    
    def __del__(self):
        # Program kapatılırken veritabanı bağlantısını kapat
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    
    # Masa renkleri için özel stil
    style = ttk.Style()
    style.configure('Masa.TFrame', background='#e0e0e0')  # Varsayılan renk
    
    app = KafeAdisyonProgrami(root)
    root.mainloop()