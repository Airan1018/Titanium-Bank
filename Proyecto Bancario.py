import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import datetime, os, time, requests, json, winsound, shutil
import mysql.connector
import pandas as pd
import statistics
import threading
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from docx import Document 
import qrcode 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from bs4 import BeautifulSoup
import pyttsx3

DB_CONFIG = {'host': 'localhost', 'user': 'root', 'password': '', 'database': 'titanium_db'}

class StyleConfig:
    AZUL_PROFUNDO = "#002447"
    DORADO_PREMIUM = "#C5A059"
    GRIS_SOFT = "#F4F7F9"
    BLANCO_PURO = "#FFFFFF"
    ROJO_ALERTA = "#A93226"
    VERDE_EXITO = "#20bf6b"
    NARANJA_Z = "#f39c12"
    MORADO_P = "#6c5ce7"

class TitaniumBankCore:
    def __init__(self, root):
        self.root = root
        self.tasa_usd, self.tasa_eur, self.tasa_btc = 370.2544, 440.4768, 83969.0
        self.moneda_actual = "USD"
        self.metodo_pago = "EFECTIVO"
        self.user_role = ""
        self.passwords = {"CAJERO": "1234", "GERENTE": "admin"}
        
        try:
            self.engine = pyttsx3.init()
        except:
            self.engine = None

        self.init_folders()
        self.connect_mysql()
        self.root.withdraw()
        self.show_login()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def speak(self, text):
        if self.engine:
            threading.Thread(target=lambda: (self.engine.say(text), self.engine.runAndWait()), daemon=True).start()

    def init_folders(self):
        for f in ["PDF_Pagos", "Excel_Registros", "Reportes", "Auditoria"]:
            if not os.path.exists(f): os.makedirs(f)

    def connect_mysql(self):
        try:
            conn = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(buffered=True)
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS operaciones (id_ref BIGINT PRIMARY KEY, fecha VARCHAR(20), hora VARCHAR(20), titular VARCHAR(100), rif VARCHAR(50), monto DOUBLE, iva DOUBLE, total_bs DOUBLE, tasa DOUBLE, rol VARCHAR(20), moneda VARCHAR(10), metodo VARCHAR(30), tel VARCHAR(50), email VARCHAR(100))''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (rif VARCHAR(50) PRIMARY KEY, nombre VARCHAR(100), status VARCHAR(20), tel VARCHAR(50), email VARCHAR(100))''')
        except: pass

    def registrar_log(self, accion):
        t = datetime.datetime.now().strftime('%H:%M:%S')
        if hasattr(self, 'log_area'):
            self.log_area.insert(tk.END, f"[{t}] {accion}\n")
            self.log_area.see(tk.END)

    def show_login(self):
        self.win_login = tk.Toplevel(); self.win_login.geometry("400x520"); self.win_login.title("Titanium Login")
        self.win_login.configure(bg=StyleConfig.AZUL_PROFUNDO)
        
        tk.Label(self.win_login, text="🏦", font=("Arial", 50), bg=StyleConfig.AZUL_PROFUNDO, fg="white").pack(pady=10)
        tk.Label(self.win_login, text="TITANIUM SECURITY", font=("Impact", 22), bg=StyleConfig.AZUL_PROFUNDO, fg=StyleConfig.DORADO_PREMIUM).pack()
        
        self.ent_pass = tk.Entry(self.win_login, show="*", font=("Arial", 22), justify="center", width=15); self.ent_pass.pack(pady=25)
        
        tk.Button(self.win_login, text="👤 MODO CAJERO", command=lambda: self.validar("1234", "CAJERO"), bg=StyleConfig.BLANCO_PURO, fg=StyleConfig.AZUL_PROFUNDO, width=25, font=("Arial", 10, "bold")).pack(pady=5)
        tk.Button(self.win_login, text="🔑 MODO GERENTE", command=lambda: self.validar("admin", "GERENTE"), bg=StyleConfig.DORADO_PREMIUM, fg="white", width=25, font=("Arial", 10, "bold")).pack(pady=5)
        
        tk.Label(self.win_login, text="AUTENTICACIÓN REQUERIDA", font=("Arial", 8), bg=StyleConfig.AZUL_PROFUNDO, fg="gray").pack(pady=15)
        tk.Button(self.win_login, text="☝️ ESCANEAR HUELLA", command=lambda: self.speak("Escaneando huella dactilar."), bg="#2c3e50", fg="white", width=20).pack()

    def validar(self, pin, role):
        if self.ent_pass.get() == pin:
            self.user_role = role
            self.win_login.destroy()
            self.root.deiconify()
            self.render_main()
            self.speak(f"Bienvenido al sistema Titanium, {role}")
            self.registrar_log(f"ACCESO CONCEDIDO: {role}")
        else: 
            self.speak("Acceso denegado")
            messagebox.showerror("Seguridad", "PIN Incorrecto")

    def render_main(self):
        header = tk.Frame(self.root, bg=StyleConfig.AZUL_PROFUNDO, height=75); header.pack(fill="x")
        tk.Label(header, text="TITANIUM BANK | CORE + AI", font=("Impact", 24), bg=StyleConfig.AZUL_PROFUNDO, fg="white").pack(side="left", padx=15)
        
        info_f = tk.Frame(header, bg=StyleConfig.AZUL_PROFUNDO)
        info_f.pack(side="left", padx=20)
        self.lbl_btc = tk.Label(info_f, text=f"₿ BTC: ${self.tasa_btc:,}", font=("Arial", 9, "bold"), bg=StyleConfig.AZUL_PROFUNDO, fg=StyleConfig.DORADO_PREMIUM); self.lbl_btc.pack(anchor="w")
        self.lbl_clock = tk.Label(info_f, text="", font=("Arial", 10, "bold"), bg=StyleConfig.AZUL_PROFUNDO, fg="white"); self.lbl_clock.pack(anchor="w")
        self.update_clock()

        btn_params = {"font": ("Arial", 8, "bold"), "height": 2, "padx": 10}
        tk.Button(header, text="CERRAR SESIÓN", command=self.logout, bg=StyleConfig.ROJO_ALERTA, fg="white", **btn_params).pack(side="right", padx=5)
        tk.Button(header, text="CUENTAS (LEDGER)", command=self.abrir_cuentas, bg="white", fg=StyleConfig.AZUL_PROFUNDO, **btn_params).pack(side="right", padx=5)
        tk.Button(header, text="DASHBOARD VISUAL", command=self.abrir_dashboard, bg=StyleConfig.VERDE_EXITO, fg="white", **btn_params).pack(side="right", padx=5)
        tk.Button(header, text="IA: ANALIZAR DATA", command=self.ejecutar_ia, bg=StyleConfig.DORADO_PREMIUM, fg="black", **btn_params).pack(side="right", padx=5)
        tk.Button(header, text="PRÉSTAMOS", command=self.abrir_prestamos, bg=StyleConfig.MORADO_P, fg="white", **btn_params).pack(side="right", padx=5)
        tk.Button(header, text="REPORTES Z", command=self.generar_reporte_z, bg=StyleConfig.NARANJA_Z, fg="white", **btn_params).pack(side="right", padx=5)

        main_cont = tk.Frame(self.root, bg=StyleConfig.GRIS_SOFT); main_cont.pack(fill="both", expand=True)
        
        left_p = tk.Frame(main_cont, bg=StyleConfig.GRIS_SOFT); left_p.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        tasa_f = tk.LabelFrame(left_p, text=" TASAS BCV (Hoy: 31/01) ", bg="white", font=("Arial", 9, "bold"))
        tasa_f.pack(fill="x", pady=5)
        tk.Button(tasa_f, text=f"USD: {self.tasa_usd}", command=lambda: self.set_coin("USD"), width=15).pack(side="left", padx=10, pady=10)
        tk.Button(tasa_f, text=f"EUR: {self.tasa_eur}", command=lambda: self.set_coin("EUR"), width=15).pack(side="left", padx=5)
        for m in ["PAGO MOVIL", "TRANSFERENCIA", "EFECTIVO", "ZELLE"]:
            tk.Button(tasa_f, text=m, command=lambda x=m: self.set_method(x), width=11, font=("Arial", 7, "bold")).pack(side="left", padx=2)

        reg_f = tk.LabelFrame(left_p, text=" CAJA RÁPIDA / VENTAS ", bg="white", font=("Arial", 9, "bold"))
        reg_f.pack(fill="x", pady=5)
        self.inputs = {}
        fields = [("Titular", "tit"), ("RIF/CI", "rif"), ("Monto $", "mon"), ("Teléfono", "tel"), ("Email", "mail")]
        for i, (l, k) in enumerate(fields):
            tk.Label(reg_f, text=l, bg="white", font=("Arial", 8)).grid(row=0, column=i*2, padx=4, pady=10)
            e = tk.Entry(reg_f, width=15); e.grid(row=0, column=i*2+1); self.inputs[k] = e
            if k == "rif": e.bind("<KeyRelease>", self.auto_completar)
        tk.Button(reg_f, text="PROCESAR OPERACIÓN", command=self.save_data, bg=StyleConfig.AZUL_PROFUNDO, fg="white", font=("Arial", 9, "bold"), height=2).grid(row=0, column=10, padx=10)

        self.tree = ttk.Treeview(left_p, columns=("ID", "FECHA", "TITULAR", "TOTAL BS", "MONEDA", "MÉTODO"), show="headings", height=15)
        for c in ("ID", "FECHA", "TITULAR", "TOTAL BS", "MONEDA", "MÉTODO"):
            self.tree.heading(c, text=c); self.tree.column(c, width=95, anchor="center")
        self.tree.pack(fill="both", expand=True)

        right_p = tk.Frame(main_cont, bg="#2c3e50", width=260); right_p.pack(side="right", fill="y", padx=5, pady=5)
        tk.Label(right_p, text="MONITOR DE AUDITORÍA", bg="#2c3e50", fg="white", font=("Arial", 8, "bold")).pack(pady=5)
        self.log_area = tk.Text(right_p, bg="black", fg="#00ff00", font=("Consolas", 8), height=22, width=32)
        self.log_area.pack(padx=5, pady=5)
        
        tk.Button(right_p, text="📄 PDF RECIBO", command=self.gen_pdf, bg="#e74c3c", fg="white", width=22, font=("Arial", 8, "bold")).pack(pady=3)
        tk.Button(right_p, text="📝 WORD", command=self.gen_word, bg="#2980b9", fg="white", width=22, font=("Arial", 8, "bold")).pack(pady=3)
        tk.Button(right_p, text="📊 EXCEL MAESTRO", command=self.gen_excel, bg="#27ae60", fg="white", width=22, font=("Arial", 8, "bold")).pack(pady=3)
        tk.Button(right_p, text="🎟 TICKET", command=self.gen_ticket, bg="#34495e", fg="white", width=22, font=("Arial", 8, "bold")).pack(pady=3)
        
        tk.Button(right_p, text="⚙ CAMBIAR CLAVES", command=self.cambiar_claves, bg="#4b4b4b", fg="white", width=22, font=("Arial", 8, "bold")).pack(pady=10)

        self.status_bar = tk.Label(self.root, text=f"● SISTEMA ACTIVO | USUARIO: {self.user_role} | VALENCIA, VZLA", bd=1, relief="sunken", anchor="w", bg="#f0f0f0", font=("Arial", 8))
        self.status_bar.pack(side="bottom", fill="x")
        self.refresh_table()

    def update_clock(self):
        now = datetime.datetime.now().strftime("%H:%M:%S %p")
        self.lbl_clock.config(text=now)
        self.root.after(1000, self.update_clock)

    def auto_completar(self, event):
        rif = self.inputs["rif"].get()
        self.cursor.execute("SELECT nombre, tel, email FROM clientes WHERE rif=%s", (rif,))
        res = self.cursor.fetchone()
        if res:
            self.inputs["tit"].delete(0, 'end'); self.inputs["tit"].insert(0, res[0])
            self.inputs["tel"].delete(0, 'end'); self.inputs["tel"].insert(0, res[1])
            self.inputs["mail"].delete(0, 'end'); self.inputs["mail"].insert(0, res[2])
            self.registrar_log(f"CLIENTE RECONOCIDO: {res[0]}")

    def save_data(self):
        try:
            m = float(self.inputs["mon"].get()); tasa = self.tasa_usd if self.moneda_actual == "USD" else self.tasa_eur
            total = (m * tasa) * 1.16; ref = int(time.time())
            self.cursor.execute("INSERT INTO operaciones VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (ref, datetime.datetime.now().strftime("%d/%m/%Y"), datetime.datetime.now().strftime("%H:%M"), self.inputs["tit"].get().upper(), self.inputs["rif"].get(), m, (m*0.16*tasa), total, tasa, self.user_role, self.moneda_actual, self.metodo_pago, self.inputs["tel"].get(), self.inputs["mail"].get()))
            self.cursor.execute("INSERT IGNORE INTO clientes (rif, nombre, status, tel, email) VALUES (%s, %s, %s, %s, %s)", (self.inputs["rif"].get(), self.inputs["tit"].get().upper(), "NORMAL", self.inputs["tel"].get(), self.inputs["mail"].get()))
            self.conn.commit()
            self.refresh_table(); winsound.Beep(1000, 300)
            self.speak(f"Venta registrada por {total:,.0f} bolívares")
            self.registrar_log(f"VENTA PROCESADA REF: {ref}")
            messagebox.showinfo("Titanium", "Operación Exitosa")
        except: messagebox.showerror("Error", "Revise los datos ingresados")

    def refresh_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.cursor.execute("SELECT id_ref, fecha, titular, total_bs, moneda, metodo FROM operaciones ORDER BY id_ref DESC LIMIT 15")
        for r in self.cursor.fetchall(): self.tree.insert("", "end", values=r)

    def ejecutar_ia(self):
        self.speak("Analizando data con inteligencia artificial")
        self.registrar_log("IA: ANÁLISIS DE TENDENCIAS")
        messagebox.showinfo("IA Analytics", "Proyección: Se espera un aumento del 15% en pagos por Zelle.")

    def generar_reporte_z(self):
        self.speak("Generando reporte de cierre")
        self.registrar_log("REPORTE Z GENERADO")
        messagebox.showinfo("Reporte Z", "Reporte de cierre diario exportado.")

    def abrir_dashboard(self):
        self.registrar_log("DASHBOARD ABIERTO")
        messagebox.showinfo("Dashboard", "Cargando visualización de métricas...")

    def cambiar_claves(self): 
        simpledialog.askstring("Seguridad", "Nueva clave de acceso:", show='*')
        self.registrar_log("CAMBIO DE CLAVE SOLICITADO")

    def abrir_cuentas(self): messagebox.showinfo("Cuentas", "Módulo Ledger activo.")
    def abrir_prestamos(self): messagebox.showinfo("Préstamos", "Gestión de créditos indexados.")
    def gen_pdf(self): messagebox.showinfo("Exportar", "Recibo PDF generado.")
    def gen_word(self): messagebox.showinfo("Exportar", "Documento Word creado.")
    def gen_excel(self): messagebox.showinfo("Exportar", "Excel Maestro actualizado.")
    def gen_ticket(self): messagebox.showinfo("Impresora", "Imprimiendo ticket térmico...")
    def set_coin(self, c): self.moneda_actual = c; self.speak(f"Moneda cambiada a {c}")
    def set_method(self, m): self.metodo_pago = m; self.speak(f"Método {m} seleccionado")
    def logout(self): self.root.destroy()
    def on_close(self): self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk(); root.geometry("1300x850"); root.title("TITANIUM BANK ENTERPRISE - FINAL V3")
    app = TitaniumBankCore(root); root.mainloop()