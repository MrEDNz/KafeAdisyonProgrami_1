import sqlite3
import os
import tkinter as tk
from tkinter import ttk, messagebox
from contextlib import contextmanager
from datetime import datetime

# --- VERİTABANI KISMI ---
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kafe.db')

def init_db():
    """Veritabanı tablolarını oluşturur (yeniden başlatmadan korur)"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Tabloların varlığını kontrol et
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='masalar'")
        if not cursor.fetchone():
            # Tablo yoksa oluştur
            cursor.execute("""
                CREATE TABLE masalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_no TEXT UNIQUE NOT NULL,
                    durum TEXT DEFAULT 'bos'
                )
            """)
            cursor.execute("INSERT INTO masalar (masa_no) VALUES ('Masa 1')")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='menu'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE menu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    urun_adi TEXT NOT NULL,
                    fiyat REAL NOT NULL,
                    kategori TEXT NOT NULL
                )
            """)
            cursor.execute("INSERT INTO menu (urun_adi, fiyat, kategori) VALUES ('Çay', 5.0, 'İçecek')")
    sql_commands = [
        """CREATE TABLE IF NOT EXISTS masalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            masa_no TEXT UNIQUE NOT NULL,
            durum TEXT DEFAULT 'bos'
        )""",
        """CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT NOT NULL,
            fiyat REAL NOT NULL,
            kategori TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS siparisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            masa_id INTEGER NOT NULL,
            urun_id INTEGER NOT NULL,
            adet INTEGER NOT NULL,
            tarih TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (masa_id) REFERENCES masalar (id),
            FOREIGN KEY (urun_id) REFERENCES menu (id)
        )""",
        """CREATE TABLE IF NOT EXISTS adisyon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            masa_id INTEGER NOT NULL,
            toplam_tutar REAL NOT NULL DEFAULT 0,
            odeme_durumu TEXT DEFAULT 'acik',
            tarih TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (masa_id) REFERENCES masalar (id)
        )""",
        """CREATE TABLE IF NOT EXISTS adisyon_siparis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adisyon_id INTEGER NOT NULL,
            siparis_id INTEGER NOT NULL,
            FOREIGN KEY (adisyon_id) REFERENCES adisyon (id),
            FOREIGN KEY (siparis_id) REFERENCES siparisler (id)
        )"""
    ]
    
@contextmanager
def get_db():
    """Veritabanı bağlantısı sağlar (otomatik kapatma)"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    except sqlite3.Error as e:
        print(f"Veritabanı hatası: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(query, params=(), fetchone=False, fetchall=False):
    """Daha güvenli sorgu çalıştırma"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            conn.commit()
            return cursor.lastrowid
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                # Tablo yoksa oluştur
                init_db()
                # Sorguyu tekrar dene
                cursor.execute(query, params)
                if fetchone:
                    return cursor.fetchone()
                if fetchall:
                    return cursor.fetchall()
                conn.commit()
                return cursor.lastrowid
            else:
                raise
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Sorgu hatası: {e}\nSorgu: {query}\nParametreler: {params}")
            raise

@contextmanager
def get_db():
    """Veritabanı bağlantısı sağlar"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=(), fetchone=False, fetchall=False):
    """SQL sorgusu çalıştırır"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        
        conn.commit()
        return cursor.lastrowid

def test_verileri_ekle():
    """Test verilerini ekler (sadece tablolar boşsa)"""
    with get_db() as conn:
        cursor = conn.cursor()
        # ... (test verisi ekleme kodları) ...
        conn.commit()

# --- MODÜLLER ---
class MasaYonetimi:
    def __init__(self, parent, app=None):  # app opsiyonel
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        
        # Masaları tutacak canvas
        self.canvas = tk.Canvas(self.frame, bg='white')
        self.scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Masa ekleme bölümü
        ekle_frame = tk.Frame(self.frame)
        ekle_frame.pack(fill='x', pady=5)
        
        tk.Label(ekle_frame, text="Yeni Masa No:").pack(side='left')
        self.yeni_masa_no = tk.Entry(ekle_frame)
        self.yeni_masa_no.pack(side='left', padx=5)
        tk.Button(ekle_frame, text="Ekle", command=self.masa_ekle).pack(side='left')
        
        # Masaları yükle
        self.masaları_guncelle()

    def masa_bosalt(self, masa_id):
        """Masayı boşaltma işlemi - Artık daha güvenli"""
        if self.app and hasattr(self.app, 'notebook') and hasattr(self.app, 'adisyon_modulu'):
            try:
                # Adisyon modülüne geçiş yap
                self.app.notebook.select(3)
                
                # Adisyon modülündeki ilgili masayı seç
                self.app.adisyon_modulu.masa_sec(masa_id)
                
                messagebox.showinfo("Bilgi", f"Masa {masa_id} adisyon işlemleri için yönlendirildi.")
            except Exception as e:
                print(f"Yönlendirme hatası: {e}")
                # Yedek yöntem
                execute_query('UPDATE masalar SET durum = "bos" WHERE id = ?', (masa_id,))
                self.masaları_guncelle()
        else:
            # Yedek yöntem
            execute_query('UPDATE masalar SET durum = "bos" WHERE id = ?', (masa_id,))
            self.masaları_guncelle()
            messagebox.showinfo("Başarılı", "Masa boşaltıldı!")

        if self.app and hasattr(self.app, 'otomatik_yenile'):
            self.app.otomatik_yenile('masa')
            self.app.otomatik_yenile('adisyon')
    
    def masaları_guncelle(self):
        """Masaları grafik olarak gösterir"""
        # Önce mevcut masaları temizle
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Masaları veritabanından al
        masalar = execute_query('SELECT id, masa_no, durum FROM masalar', fetchall=True)
        
        for masa in masalar:
            self.masa_kutusu_olustur(masa['id'], masa['masa_no'], masa['durum'])
    
    def masa_kutusu_olustur(self, masa_id, masa_no, durum):
        """Tek bir masa için grafik kutu oluşturur"""
        # Masa çerçevesi
        masa_frame = tk.Frame(self.scrollable_frame, 
                            bd=2, 
                            relief='ridge', 
                            padx=10, 
                            pady=10,
                            bg='lightgreen' if durum == 'dolu' else 'lightgray')
        masa_frame.pack(fill='x', pady=5)
        
        # Masa bilgileri
        tk.Label(masa_frame, 
                text=f"Masa {masa_no}",
                font=('Arial', 12, 'bold'),
                bg=masa_frame['bg']).pack(anchor='w')
        
        tk.Label(masa_frame, 
                text="Dolu" if durum == 'dolu' else "Boş",
                bg=masa_frame['bg']).pack(anchor='w')
        
        # Masa siparişleri
        siparisler = execute_query('''
            SELECT u.urun_adi, s.adet, u.fiyat 
            FROM siparisler s
            JOIN menu u ON s.urun_id = u.id
            WHERE s.masa_id = ?
            ORDER BY s.tarih DESC
        ''', (masa_id,), fetchall=True)
        
        if siparisler:
            toplam = 0.0
            for siparis in siparisler:
                tutar = siparis['adet'] * siparis['fiyat']
                toplam += tutar
                tk.Label(masa_frame, 
                        text=f"{siparis['urun_adi']} x{siparis['adet']} = {tutar:.2f}₺",
                        bg=masa_frame['bg']).pack(anchor='w')
            
            tk.Label(masa_frame, 
                    text=f"Toplam: {toplam:.2f}₺",
                    font=('Arial', 10, 'bold'),
                    bg=masa_frame['bg']).pack(anchor='w')
        
        # Boşalt butonu (sadece dolu masalar için)
        if durum == 'dolu':
            tk.Button(masa_frame, 
                    text="Masa Boşalt",
                    command=lambda id=masa_id: self.masa_bosalt(id)).pack(pady=5)
    
    def masa_bosalt(self, masa_id):
        """Masayı boşaltma işlemi - Artık direkt boşaltmak yerine adisyon modülüne yönlendiriyor"""
        # Adisyon modülüne geçiş yap
        self.notebook.select(3)  # 4. sekme (0'dan başlar, adisyon modülü)
        
        # Adisyon modülündeki ilgili masayı seç
        app.adisyon_modulu.masa_sec(masa_id)
        
        # Kullanıcıya bilgi ver
        messagebox.showinfo("Bilgi", f"Masa {masa_id} adisyon işlemleri için adisyon modülüne yönlendirildi.")
    
    def masa_ekle(self):
        """Yeni masa ekler"""
        masa_no = self.yeni_masa_no.get()
        if not masa_no:
            messagebox.showwarning("Uyarı", "Lütfen masa numarası girin!")
            return
        
        try:
            execute_query('INSERT INTO masalar (masa_no) VALUES (?)', (masa_no,))
            self.yeni_masa_no.delete(0, tk.END)
            self.masaları_guncelle()
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu masa numarası zaten var!")

        # Masa eklendikten sonra otomatik yenile
        if self.app and hasattr(self.app, 'otomatik_yenile'):
            self.app.otomatik_yenile('masa')

class MenuYonetimi:
    def __init__(self, parent, app=None):  # app opsiyonel
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        
        # Ürün ekleme
        self.urun_ekle_frame = tk.LabelFrame(self.frame, text="Ürün Ekle")
        self.urun_ekle_frame.pack(pady=10, fill='x', padx=10)
        
        tk.Label(self.urun_ekle_frame, text="Ürün Adı:").grid(row=0, column=0)
        self.urun_adi_entry = tk.Entry(self.urun_ekle_frame)
        self.urun_adi_entry.grid(row=0, column=1)
        
        tk.Label(self.urun_ekle_frame, text="Fiyat:").grid(row=0, column=2)
        self.fiyat_entry = tk.Entry(self.urun_ekle_frame)
        self.fiyat_entry.grid(row=0, column=3)
        
        tk.Label(self.urun_ekle_frame, text="Kategori:").grid(row=0, column=4)
        self.kategori_entry = tk.Entry(self.urun_ekle_frame)
        self.kategori_entry.grid(row=0, column=5)
        
        tk.Button(self.urun_ekle_frame, text="Ekle", command=self.urun_ekle).grid(row=0, column=6)
        
        # Ürün listesi
        self.urun_liste_frame = tk.LabelFrame(self.frame, text="Ürün Listesi")
        self.urun_liste_frame.pack(pady=10, fill='both', expand=True, padx=10)
        
        self.tree = ttk.Treeview(self.urun_liste_frame, columns=('ad', 'fiyat', 'kategori'), show='headings')
        self.tree.heading('ad', text='Ürün Adı')
        self.tree.heading('fiyat', text='Fiyat')
        self.tree.heading('kategori', text='Kategori')
        self.tree.pack(fill='both', expand=True)
        
        self.menu_guncelle()
    
    def menu_guncelle(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        urunler = execute_query("SELECT * FROM menu", fetchall=True)
        for urun in urunler:
            self.tree.insert('', 'end', values=(urun['urun_adi'], urun['fiyat'], urun['kategori']))
    
    def urun_ekle(self):
        urun_adi = self.urun_adi_entry.get()
        fiyat = self.fiyat_entry.get()
        kategori = self.kategori_entry.get()
        
        if not all([urun_adi, fiyat, kategori]):
            messagebox.showerror("Hata", "Tüm alanları doldurun!")
            return
        
        try:
            execute_query(
                "INSERT INTO menu (urun_adi, fiyat, kategori) VALUES (?, ?, ?)",
                (urun_adi, float(fiyat), kategori)
            )
            self.menu_guncelle()
            self.urun_adi_entry.delete(0, tk.END)
            self.fiyat_entry.delete(0, tk.END)
            self.kategori_entry.delete(0, tk.END)
            messagebox.showinfo("Başarılı", "Ürün eklendi")
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz fiyat!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu ürün zaten var!")

class SiparisYonetimi:
    def __init__(self, parent, app=None):  # app opsiyonel
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        
        # Masa seçimi
        tk.Label(self.frame, text="Masa Seç:").grid(row=0, column=0, sticky='w')
        self.masa_var = tk.StringVar()
        self.masa_combobox = ttk.Combobox(self.frame, textvariable=self.masa_var)
        self.masa_combobox.grid(row=0, column=1, sticky='w')
        self.masa_combobox.bind('<<ComboboxSelected>>', self.masa_secildi)
        
        # Ürün seçimi
        tk.Label(self.frame, text="Ürün Seç:").grid(row=1, column=0, sticky='w')
        self.urun_var = tk.StringVar()
        self.urun_combobox = ttk.Combobox(self.frame, textvariable=self.urun_var)
        self.urun_combobox.grid(row=1, column=1, sticky='w')
        
        # Adet
        tk.Label(self.frame, text="Adet:").grid(row=2, column=0, sticky='w')
        self.adet_var = tk.IntVar(value=1)
        tk.Spinbox(self.frame, from_=1, to=10, textvariable=self.adet_var).grid(row=2, column=1, sticky='w')  #GENŞLİĞİ AYARLANACAK !!!!
        
        # Ekle butonu
        tk.Button(self.frame, text="Sipariş Ekle", command=self.siparis_ekle).grid(row=3, column=0, columnspan=2)
        
        # Seçili masaya ait siparişler
        tk.Label(self.frame, text="Mevcut Siparişler:").grid(row=4, column=0, columnspan=2, sticky='w')
        self.siparis_listbox = tk.Listbox(self.frame, height=8)
        self.siparis_listbox.grid(row=5, column=0, columnspan=2, sticky='nsew')
        
        # Toplam tutar
        self.toplam_label = tk.Label(self.frame, text="Toplam: 0.00₺", font=('Arial', 10, 'bold'))
        self.toplam_label.grid(row=6, column=0, columnspan=2, sticky='e')
        
        # Grid yapılandırması
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(5, weight=1)
        
        # Verileri yükle
        self.masaları_guncelle()
        self.menu_urunlerini_guncelle()
    
    def masaları_guncelle(self):
        """Masa combobox'ını günceller"""
        masalar = execute_query('SELECT id, masa_no FROM masalar', fetchall=True)
        self.masa_combobox['values'] = [f"{m['masa_no']} (ID:{m['id']})" for m in masalar]
    
    def menu_urunlerini_guncelle(self):
        """Ürün combobox'ını günceller"""
        urunler = execute_query('SELECT id, urun_adi, fiyat FROM menu', fetchall=True)
        self.urun_combobox['values'] = [f"{u['urun_adi']} - {u['fiyat']}₺ (ID:{u['id']})" for u in urunler]
    
    def masa_secildi(self, event=None):
        """Masa seçildiğinde o masaya ait siparişleri gösterir"""
        masa_secim = self.masa_var.get()
        if not masa_secim:
            return
        
        masa_id = int(masa_secim.split('ID:')[1].rstrip(')'))
        
        # Listbox'ı temizle
        self.siparis_listbox.delete(0, tk.END)
        
        # Seçili masaya ait siparişleri getir
        siparisler = execute_query('''
            SELECT u.urun_adi, s.adet, u.fiyat, s.tarih 
            FROM siparisler s
            JOIN menu u ON s.urun_id = u.id
            WHERE s.masa_id = ?
            ORDER BY s.tarih DESC
        ''', (masa_id,), fetchall=True)
        
        toplam = 0.0
        for siparis in siparisler:
            tutar = siparis['adet'] * siparis['fiyat']
            toplam += tutar
            list_item = f"{siparis['urun_adi']} x{siparis['adet']} = {tutar:.2f}₺ ({siparis['tarih'][11:16]})"
            self.siparis_listbox.insert(tk.END, list_item)
        
        self.toplam_label.config(text=f"Toplam: {toplam:.2f}₺")
    
    def siparis_ekle(self):
        """Yeni sipariş ekler ve direkt adisyona yansıtır"""
        masa_secim = self.masa_var.get()
        urun_secim = self.urun_var.get()
        adet = self.adet_var.get()
        
        if not masa_secim or not urun_secim:
            messagebox.showwarning("Uyarı", "Lütfen masa ve ürün seçin!")
            return
        
        try:
            masa_id = int(masa_secim.split('ID:')[1].rstrip(')'))
            urun_id = int(urun_secim.split('ID:')[1].rstrip(')'))
        except:
            messagebox.showerror("Hata", "Geçersiz seçim!")
            return
        
        # Ürün fiyatını al
        urun_fiyat = execute_query('SELECT fiyat FROM menu WHERE id = ?', (urun_id,), fetchone=True)['fiyat']
        toplam_tutar = urun_fiyat * adet
        
        # Siparişi ekle
        execute_query('''
            INSERT INTO siparisler (masa_id, urun_id, adet) 
            VALUES (?, ?, ?)
        ''', (masa_id, urun_id, adet))
        
        # Masayı dolu olarak işaretle
        execute_query('UPDATE masalar SET durum = "dolu" WHERE id = ?', (masa_id,))
        
        # Adisyon kontrolü (yoksa oluştur)
        acik_adisyon = execute_query('''
            SELECT id FROM adisyon 
            WHERE masa_id = ? AND odeme_durumu = 'acik'
        ''', (masa_id,), fetchone=True)
        
        if not acik_adisyon:
            execute_query('INSERT INTO adisyon (masa_id, toplam_tutar) VALUES (?, ?)', (masa_id, toplam_tutar))
            adisyon_id = execute_query('SELECT last_insert_rowid()', fetchone=True)[0]
        else:
            adisyon_id = acik_adisyon['id']
            # Adisyon toplamını güncelle
            execute_query('UPDATE adisyon SET toplam_tutar = toplam_tutar + ? WHERE id = ?', 
                         (toplam_tutar, adisyon_id))
        
        # Siparişi adisyona bağla
        siparis_id = execute_query('SELECT last_insert_rowid()', fetchone=True)[0]
        execute_query('INSERT INTO adisyon_siparis (adisyon_id, siparis_id) VALUES (?, ?)', 
                     (adisyon_id, siparis_id))
        
        # Listeleri yenile
        self.masa_secildi()
        messagebox.showinfo("Başarılı", "Sipariş eklendi ve adisyona yansıtıldı!")

        # Sipariş eklendikten sonra otomatik yenile
        if self.app and hasattr(self.app, 'otomatik_yenile'):
            self.app.otomatik_yenile('siparis')
            self.app.otomatik_yenile('masa')
            self.app.otomatik_yenile('adisyon')

        # Otomatik yenileme
        if self.app and hasattr(self.app, 'otomatik_yenile'):
            self.app.otomatik_yenile('siparis')
            self.app.otomatik_yenile('masa')
            self.app.otomatik_yenile('adisyon')

class AdisyonYonetimi:
    def __init__(self, parent, app=None):   # app opsiyonel
        self.parent = parent
        self.app = app                      # Ana uygulama referansı
        self.frame = tk.Frame(parent)
        
        # Masa seçimi
        tk.Label(self.frame, text="Masa Seç:").pack(pady=5)
        self.masa_combobox = ttk.Combobox(self.frame, state="readonly")
        self.masa_combobox.pack()
        self.masa_combobox.bind('<<ComboboxSelected>>', self.masa_secildi)
        
        # Adisyon bilgileri
        self.bilgi_frame = tk.LabelFrame(self.frame, text="Adisyon Bilgileri", padx=10, pady=10)
        self.bilgi_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sipariş listesi
        self.siparis_tree = ttk.Treeview(self.bilgi_frame, columns=('urun', 'adet', 'tutar'), show='headings', height=5)
        self.siparis_tree.heading('urun', text='Ürün Adı')
        self.siparis_tree.heading('adet', text='Adet')
        self.siparis_tree.heading('tutar', text='Tutar')
        self.siparis_tree.pack(fill='both', expand=True)
        
        # Toplam tutar
        self.toplam_label = tk.Label(self.bilgi_frame, text="Toplam: 0.00₺", font=('Arial', 12, 'bold'))
        self.toplam_label.pack(pady=5)
        
        # Ödeme butonları
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Nakit Ödeme", command=lambda: self.odeme_al('nakit')).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Kredi Kartı", command=lambda: self.odeme_al('kredi')).pack(side='left', padx=5)
        tk.Button(btn_frame, text="İptal", command=self.iptal).pack(side='left', padx=5)
        
        # Verileri yükle
        self.masaları_guncelle()
    
    def masaları_guncelle(self):
        """Sadece dolu ve ödemesi bekleyen masaları listeler"""
        masalar = execute_query('''
            SELECT m.id, m.masa_no 
            FROM masalar m
            JOIN adisyon a ON m.id = a.masa_id
            WHERE m.durum = 'dolu' AND a.odeme_durumu = 'acik'
            ORDER BY m.masa_no
        ''', fetchall=True)
        
        self.masa_combobox['values'] = [f"{m['masa_no']} (ID:{m['id']})" for m in masalar]
        if masalar:
            self.masa_combobox.current(0)
            self.masa_secildi()
    
    def masa_sec(self, masa_id):
        """Dışarıdan masa seçimi için"""
        for i, masa in enumerate(self.masa_combobox['values']):
            if f"ID:{masa_id})" in masa:
                self.masa_combobox.current(i)
                self.masa_secildi()
                break
    
    def masa_secildi(self, event=None):
        """Seçili masanın adisyon bilgilerini gösterir"""
        masa_secim = self.masa_combobox.get()
        if not masa_secim:
            return
        
        masa_id = int(masa_secim.split('ID:')[1].rstrip(')'))
        
        # Sipariş listesini temizle
        for item in self.siparis_tree.get_children():
            self.siparis_tree.delete(item)
        
        # Siparişleri getir
        siparisler = execute_query('''
            SELECT u.urun_adi, s.adet, u.fiyat 
            FROM siparisler s
            JOIN menu u ON s.urun_id = u.id
            JOIN adisyon_siparis a_s ON s.id = a_s.siparis_id
            JOIN adisyon a ON a_s.adisyon_id = a.id
            WHERE a.masa_id = ? AND a.odeme_durumu = 'acik'
        ''', (masa_id,), fetchall=True)
        
        toplam = 0.0
        for siparis in siparisler:
            tutar = siparis['adet'] * siparis['fiyat']
            toplam += tutar
            self.siparis_tree.insert('', 'end', 
                                   values=(siparis['urun_adi'], 
                                          siparis['adet'], 
                                          f"{tutar:.2f}₺"))
        
        self.toplam_label.config(text=f"Toplam: {toplam:.2f}₺")
    
    def odeme_al(self, odeme_tipi):
        """Ödeme işlemini gerçekleştirir"""
        masa_secim = self.masa_combobox.get()
        if not masa_secim:
            messagebox.showwarning("Uyarı", "Lütfen bir masa seçin!")
            return
        
        masa_id = int(masa_secim.split('ID:')[1].rstrip(')'))
        toplam_tutar = float(self.toplam_label.cget("text").split(":")[1].strip().replace("₺", ""))
        
        # Ödeme işlemi
        if messagebox.askyesno("Onay", f"{odeme_tipi.title()} ile {toplam_tutar:.2f}₺ ödeme alınsın mı?"):
            # Adisyonu kapat
            execute_query('''
                UPDATE adisyon 
                SET odeme_durumu = 'kapali', 
                    odeme_tipi = ? 
                WHERE masa_id = ? AND odeme_durumu = 'acik'
            ''', (odeme_tipi, masa_id))
            
            # Masayı boşalt
            execute_query('UPDATE masalar SET durum = "bos" WHERE id = ?', (masa_id,))
            
            # Siparişleri temizle (isteğe bağlı)
            # execute_query('DELETE FROM siparisler WHERE masa_id = ?', (masa_id,))
            
            messagebox.showinfo("Başarılı", f"Ödeme alındı: {toplam_tutar:.2f}₺ ({odeme_tipi})")
            
            # Listeleri güncelle
            self.masaları_guncelle()
            app.masa_modulu.masaları_guncelle()  # Masa görünümünü güncelle
        
        # Ödeme alındıktan sonra otomatik yenile
        if self.app and hasattr(self.app, 'otomatik_yenile'):
            self.app.otomatik_yenile('masa')
            self.app.otomatik_yenile('adisyon')
    
    def iptal(self):
        """Seçimi iptal eder"""
        self.masa_combobox.set('')
        for item in self.siparis_tree.get_children():
            self.siparis_tree.delete(item)
        self.toplam_label.config(text="Toplam: 0.00₺")

# --- ANA UYGULAMA ---
class KafeAdisyonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kafe Adisyon Yönetimi")
        
        # Notebook oluştur
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)
        
        # Modülleri oluştur
        self.masa_modulu = MasaYonetimi(self.notebook, self)
        self.menu_modulu = MenuYonetimi(self.notebook)  # MenuYonetimi app parametresi almıyor
        self.siparis_modulu = SiparisYonetimi(self.notebook, self)
        self.adisyon_modulu = AdisyonYonetimi(self.notebook, self)
        
        # Sekmeleri ekle
        self.notebook.add(self.masa_modulu.frame, text="Masa Yönetimi")
        self.notebook.add(self.menu_modulu.frame, text="Menü Yönetimi")
        self.notebook.add(self.siparis_modulu.frame, text="Sipariş Yönetimi")
        self.notebook.add(self.adisyon_modulu.frame, text="Adisyon Yönetimi")
        
        # Tümünü Yenile butonu
        tk.Button(root, text="Tümünü Yenile", command=self.tumunu_yenile).pack(pady=5)
        
        # Modüller arası referanslar
        self.masa_modulu.app = self
        self.adisyon_modulu.app = self
        
        # Pencere kapatma davranışı (EKLEMENİZ GEREKEN KISIM)
        def on_closing():
            # Burada herhangi bir temizlik yapmanız gerekmiyorsa boş bırakabilirsiniz
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
    
    def otomatik_yenile(self, modul_adi=None):
        """İlgili modülleri otomatik olarak yeniler"""
        try:
            if modul_adi is None or modul_adi == 'masa':
                if hasattr(self.masa_modulu, 'masaları_guncelle'):
                    self.masa_modulu.masaları_guncelle()
            
            if modul_adi is None or modul_adi == 'menu':
                if hasattr(self.menu_modulu, 'menu_guncelle'):
                    self.menu_modulu.menu_guncelle()
            
            if modul_adi is None or modul_adi == 'siparis':
                if hasattr(self.siparis_modulu, 'masaları_guncelle'):
                    self.siparis_modulu.masaları_guncelle()
                if hasattr(self.siparis_modulu, 'menu_urunlerini_guncelle'):
                    self.siparis_modulu.menu_urunlerini_guncelle()
                if hasattr(self.siparis_modulu, 'siparis_listesini_guncelle'):
                    self.siparis_modulu.siparis_listesini_guncelle()
            
            if modul_adi is None or modul_adi == 'adisyon':
                if hasattr(self.adisyon_modulu, 'masaları_guncelle'):
                    self.adisyon_modulu.masaları_guncelle()
        except Exception as e:
            print(f"Otomatik yenileme hatası: {e}")

    # Tümünü Yenile butonu için alternatif (isteğe bağlı)
    def tumunu_yenile(self):
        """Tüm modülleri yenilemek için buton fonksiyonu"""
        self.otomatik_yenile()  # Parametresiz çağırıyoruz
    
    def test_verileri_ekle(self):
        """Örnek veriler ekler"""
        # Masalar
        execute_query("INSERT OR IGNORE INTO masalar (masa_no) VALUES ('Masa 1')")
        execute_query("INSERT OR IGNORE INTO masalar (masa_no) VALUES ('Masa 2')")
        
        # Menü
        execute_query("INSERT OR IGNORE INTO menu (urun_adi, fiyat, kategori) VALUES ('Kahve', 15.0, 'İçecek')")
        execute_query("INSERT OR IGNORE INTO menu (urun_adi, fiyat, kategori) VALUES ('Çay', 10.0, 'İçecek')")

# --- UYGULAMAYI BAŞLAT ---
if __name__ == "__main__":
    # Veritabanı başlat
    init_db()

    # Test verilerini ekle (isteğe bağlı)
    try:
        test_verileri_ekle()
    except Exception as e:
        print(f"Test verileri eklenirken hata: {e}")


       
    root = tk.Tk()
    app = KafeAdisyonApp(root)
    
    def on_closing():
        if hasattr(app, 'db_conn'):
            app.db_conn.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()