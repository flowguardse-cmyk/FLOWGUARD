import json
import os
import re
import subprocess
import webbrowser
import requests
import telnetlib
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from flask import Flask, jsonify, render_template, request
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import messagebox

_servidor_web_estado = None

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


def _w(ctk_image_light_dark_or_pil, size=None):
    """Envuelve en CTkImage para HighDPI y quitar warning de CustomTkinter v6."""
    if ctk_image_light_dark_or_pil is None:
        return None
    if isinstance(ctk_image_light_dark_or_pil, ctk.CTkImage):
        return ctk_image_light_dark_or_pil
    if isinstance(ctk_image_light_dark_or_pil, Image.Image):
        img_pil = ctk_image_light_dark_or_pil
        sz = size or (img_pil.width, img_pil.height)
        return ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=sz)
    if isinstance(ctk_image_light_dark_or_pil, ImageTk.PhotoImage):
        img_pil = getattr(ctk_image_light_dark_or_pil, "_PhotoImage__photo", None)
        if img_pil is None:
            return ctk_image_light_dark_or_pil
        return ctk_image_light_dark_or_pil
    return ctk_image_light_dark_or_pil

# --- VENTANA DE LOGIN ---
class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("850x500")
        self.title("FLOWGUARD · Autenticación NOC")
        self.resizable(False, False)

        # Tokens de Telegram para alertas de seguridad en el Login
        self.TELEGRAM_TOKEN = "8843336136:AAHCvX-p4gqDMB3Y8F0kzd2PrhEOdXRHJdY"
        self.TELEGRAM_CHAT_ID = "6343384187"

        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        x = (ancho_pantalla // 2) - (850 // 2)
        y = (alto_pantalla // 2) - (500 // 2)
        self.geometry(f"850x500+{x}+{y}")

        self.frame_izq = ctk.CTkFrame(self, fg_color="#0B1224", corner_radius=0, width=425, height=500)
        self.frame_izq.pack(side="left", fill="both")

        self.lbl_gif = ctk.CTkLabel(self.frame_izq, text="")
        self.lbl_gif.pack(expand=True, padx=20, pady=20)

        self.frames = []
        self.frame_index = 0
        self.animacion_activa = True
        self._login_procesando = False

        gif_path = "intro.gif"
        if os.path.exists(gif_path):
            try:
                self.gif_imagen = Image.open(gif_path)
                self._gif_frames_pil = []
                for frame in range(self.gif_imagen.n_frames):
                    self.gif_imagen.seek(frame)
                    img_resized = self.gif_imagen.copy().resize((380, 420))
                    self._gif_frames_pil.append(img_resized)
                    self.frames.append(ImageTk.PhotoImage(img_resized))
                self.reproducir_gif()
            except Exception:
                self._render_login_fallback_noc()
        else:
            self._render_login_fallback_noc()

        self.frame_der = ctk.CTkFrame(self, fg_color="#060A14", corner_radius=0, width=425, height=500)
        self.frame_der.pack(side="right", fill="both", expand=True)

        self.card_login = ctk.CTkFrame(self.frame_der, fg_color="#0B1224", corner_radius=16, border_width=1, border_color="#1E2E55")
        self.card_login.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88, relheight=0.90)

        ctk.CTkLabel(self.card_login, text="Iniciar sesión", font=("Arial", 22, "bold"), text_color="#E6EEFB").pack(anchor="w", padx=25, pady=(25, 5))
        ctk.CTkLabel(self.card_login, text="Network Operations Center · Telemetría SDN en tiempo real.", font=("Arial", 11, "normal"), text_color="#7A8BB5", justify="left").pack(anchor="w", padx=25, pady=(0, 18))

        ctk.CTkLabel(self.card_login, text="USUARIO", font=("Arial", 10, "bold"), text_color="#50628C").pack(anchor="w", padx=25, pady=(5, 2))
        self.entry_usuario = ctk.CTkEntry(self.card_login, placeholder_text="admin", width=290, height=42,
                                          fg_color="#162241", border_color="#1E2E55",
                                          text_color="#E6EEFB",
                                          border_width=1, corner_radius=9,
                                          placeholder_text_color="#50628C")
        self.entry_usuario.pack(padx=25, pady=(0, 2))
        self.entry_usuario.bind("<Return>", lambda event: self.entry_pass.focus())
        self.entry_usuario.bind("<FocusIn>", lambda e: self._focus_entry(self.entry_usuario))
        self.entry_usuario.bind("<FocusOut>", lambda e: self._blur_entry(self.entry_usuario))

        ctk.CTkLabel(self.card_login, text="CONTRASEÑA", font=("Arial", 10, "bold"), text_color="#50628C").pack(anchor="w", padx=25, pady=(10, 2))
        self.entry_pass = ctk.CTkEntry(self.card_login, placeholder_text="••••••••", show="•", width=290, height=42,
                                       fg_color="#162241", border_color="#1E2E55",
                                       text_color="#E6EEFB",
                                       border_width=1, corner_radius=9,
                                       placeholder_text_color="#50628C")
        self.entry_pass.pack(padx=25, pady=(0, 16))
        self.entry_pass.bind("<Return>", lambda event: self.verificar_login())
        self.entry_pass.bind("<FocusIn>", lambda e: self._focus_entry(self.entry_pass))
        self.entry_pass.bind("<FocusOut>", lambda e: self._blur_entry(self.entry_pass))

        self.btn_login = ctk.CTkButton(self.card_login, text="⚡ Acceder al Sistema", command=self.verificar_login,
                                       fg_color="#F97316", hover_color="#EA580C",
                                       font=("Arial", 13, "bold"), text_color="#FFFFFF",
                                       width=290, height=44, corner_radius=9)
        self.btn_login.pack(padx=25, pady=(0, 14))

        self._login_footer = ctk.CTkFrame(self.card_login, fg_color="transparent")
        self._login_footer.pack(fill="x", padx=25)
        ctk.CTkLabel(self._login_footer,
                     text="● 24h Monitoreo Activo",
                     text_color="#10B981",
                     font=("Arial", 10, "bold")).pack(side="left")
        ctk.CTkLabel(self._login_footer,
                     text="v2 · NOC R1",
                     text_color="#50628C",
                     font=("Arial", 10)).pack(side="right")

    def _focus_entry(self, entry):
        entry.configure(fg_color="#131E3D", border_color="#22D3EE")
    def _blur_entry(self, entry):
        entry.configure(fg_color="#162241", border_color="#1E2E55")

    def _render_login_fallback_noc(self):
        from PIL import ImageDraw, ImageFilter
        w, h = 380, 420
        bg = Image.new("RGBA", (w, h), (11, 18, 36, 255))
        draw = ImageDraw.Draw(bg)

        for y in range(h):
            t = y / h
            r = int(11 + t * (16 - 11))
            g = int(18 + t * (34 - 18))
            b = int(36 + t * (65 - 36))
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        draw.ellipse([-120, -140, 220, 200], fill=(34, 211, 238, 32))
        draw.ellipse([w - 200, h - 200, w + 80, h + 80], fill=(99, 102, 241, 30))

        import random
        rng = random.Random(1234)
        nodos = []
        for _ in range(18):
            nx = rng.randint(25, w - 25)
            ny = rng.randint(25, h - 25)
            nodos.append((nx, ny))
        for i, a in enumerate(nodos):
            for b in nodos[i + 1:]:
                d = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
                if d < 120:
                    alpha = int(180 - d)
                    draw.line([a, b], fill=(34, 211, 238, max(40, alpha - 90)), width=1)
        for (nx, ny) in nodos:
            draw.ellipse([nx - 3, ny - 3, nx + 3, ny + 3], fill=(34, 211, 238, 200))

        draw.rounded_rectangle([26, 26, w - 26, 104], radius=14,
                               fill=(22, 34, 65, 120), outline=(34, 211, 238, 60), width=1)

        def draw_centered_text(y, text, font_size, color, bold=True):
            try:
                from PIL import ImageFont
                fn = ("Arial Bold.ttf",) if bold else ("Arial.ttf",)
                try:
                    f = ImageFont.truetype(fn[0], font_size)
                except Exception:
                    f = ImageFont.load_default()
            except Exception:
                f = ImageFont.load_default()
            try:
                bb = draw.textbbox((0, 0), text, font=f)
                tw = bb[2] - bb[0]
            except Exception:
                tw = len(text) * (font_size // 2)
            draw.text(((w - tw) / 2, y), text, fill=color, font=f)

        draw_centered_text(40, "FLOWGUARD", 42, (230, 238, 251, 255), True)
        draw_centered_text(86, "NETWORK OPERATIONS CENTER", 12, (122, 139, 181, 255), True)

        draw.rounded_rectangle([30, h - 140, w - 30, h - 34], radius=12,
                               fill=(6, 10, 20, 200), outline=(42, 65, 120, 140), width=1)
        rows = [
            ("●", "GNS3 API", "ONLINE", (16, 185, 129, 255)),
            ("●", "Telegram Bot", "OK", (16, 185, 129, 255)),
            ("●", "Monitor ICMP", "ARMADO", (34, 211, 238, 255)),
            ("●", "Dashboard Web", "PORT 5000", (124, 58, 237, 255)),
        ]
        y0 = h - 126
        for (bullet, lbl, val, col) in rows:
            draw.text((46, y0), bullet, fill=col)
            draw.text((64, y0), lbl, fill=(122, 139, 181, 255))
            try:
                from PIL import ImageFont
                try: f = ImageFont.truetype("Arial Bold.ttf", 11)
                except Exception: f = ImageFont.load_default()
            except Exception:
                f = ImageFont.load_default()
            draw.text((w - 48 - 60, y0), val, fill=col, font=f)
            y0 += 24

        blurred = bg.filter(ImageFilter.SMOOTH)
        self._login_bg_pil = blurred
        self._login_bg_ctk = ctk.CTkImage(light_image=blurred, dark_image=blurred, size=(blurred.width, blurred.height))
        self.lbl_gif.configure(image=self._login_bg_ctk, text="")

    def reproducir_gif(self):
        if self.frames and self.animacion_activa:
            idx = self.frame_index
            pil_img = None
            if hasattr(self, "_gif_frames_pil") and self._gif_frames_pil:
                try:
                    pil_img = self._gif_frames_pil[idx]
                except Exception:
                    pil_img = None
            if pil_img is not None:
                if not hasattr(self, "_gif_ctk_cache"):
                    self._gif_ctk_cache = {}
                ctk_img = self._gif_ctk_cache.get(idx)
                if ctk_img is None:
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(pil_img.width, pil_img.height))
                    self._gif_ctk_cache[idx] = ctk_img
                self.lbl_gif.configure(image=ctk_img, text="")
            else:
                self.lbl_gif.configure(image=self.frames[idx], text="")
            self.frame_index = (idx + 1) % len(self.frames)
            self.after(100, self.reproducir_gif)

    def enviar_alerta_telegram_login(self, mensaje):
        if not self.TELEGRAM_TOKEN:
            return
        url = f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": self.TELEGRAM_CHAT_ID, "text": mensaje}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass

    def verificar_login(self):
        if self._login_procesando:
            return
        self._login_procesando = True
        txt_original = self.btn_login.cget("text")
        self.btn_login.configure(state="disabled", text="⏳ Validando credenciales…", fg_color="#7C3AED")
        self.update_idletasks()

        usuario = self.entry_usuario.get()
        password = self.entry_pass.get()
        ok = (usuario == "admin" and password == "sdn2026")

        def _finalizar():
            if ok:
                msg_exito = f"🟢 ACCESO EXITOSO AL DASHBOARD 🟢\n\nEl operador [{usuario}] ha iniciado sesión en el sistema de gestión de redes inteligentes."
                threading.Thread(target=self.enviar_alerta_telegram_login, args=(msg_exito,), daemon=True).start()
                self.animacion_activa = False
                self.destroy()
                PanelPrincipalApp().mainloop()
            else:
                msg_fallo = f"🚨 ALERTA DE SEGURIDAD 🚨\n\nIntento de inicio de sesión no autorizado.\nUsuario intentado: [{usuario}]"
                threading.Thread(target=self.enviar_alerta_telegram_login, args=(msg_fallo,), daemon=True).start()
                self.btn_login.configure(state="normal", text=txt_original, fg_color="#F97316")
                self._login_procesando = False
                messagebox.showerror("Error de Autenticación", "Credenciales incorrectas o acceso denegado")

        self.after(450, _finalizar)


# --- PANEL PRINCIPAL RACK ---
class PanelPrincipalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1080x860")
        self.title("FLOWGUARD · Network Operations Center")
        self.minsize(960, 720)

        global _servidor_web_estado

        self.TELEGRAM_TOKEN = "8727879839:AAETXFCQinl4N1GC-vYHdvJpBSchzBRb_N4"
        self.TELEGRAM_CHAT_ID = "6025764214"
        self.GNS3_URL = "http://localhost:3080/v2"
        self.estado_anterior_equipos = {}
        self.estado_anterior_puertos = {}
        self.estado_anterior_interfaces = {}
        self._estado_anterior_ping = {}
        self._contadores_ping_offline = {}
        self._cache_eq_version = {}
        self._cache_eq_cpu = {}
        self.imagenes_cache = {}
        self._ping_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="fg-ping")
        self._ultimo_ciclo_ping = 0
        self._gns3_status_ok = False
        self._grafana_status_ok = False

        self.estado_global = {
            "resumen_kpi": {
                "equipos_totales": 0,
                "up_gns3": 0,
                "down_gns3": 0,
                "ping_promedio_ms": None,
                "alertas_activas": 0,
                "total_intf": 0,
                "up_intf": 0,
                "down_intf": 0,
                "ultima_actualizacion": None,
            },
            "equipos": {},
            "alertas_historial": deque(maxlen=100),
            "dashboard_http": "http://127.0.0.1:5000"
        }

        _servidor_web_estado = self
        self._iniciar_servidor_web()

        self.main_container = ctk.CTkFrame(self, fg_color="#060A14", corner_radius=0)
        self.main_container.pack(fill="both", expand=True, padx=12, pady=8)

        # ========================
        #  TOPBAR (NOC HEADER)
        # ========================
        topbar = ctk.CTkFrame(self.main_container, fg_color="#0B1224", corner_radius=10,
                              border_width=1, border_color="#1E2E55")
        topbar.pack(fill="x", pady=(0, 8), ipady=4)

        title_col = ctk.CTkFrame(topbar, fg_color="transparent")
        title_col.pack(side="left", padx=14, pady=6, fill="y")
        ctk.CTkLabel(title_col,
                     text="⚡ FLOWGUARD  ·  Network Operations Center",
                     font=("Arial", 16, "bold"),
                     text_color="#E6EEFB").pack(anchor="w")
        ctk.CTkLabel(title_col,
                     text="Supervisión GNS3 + CLI Cisco + Ping ICMP + Alertas Telegram en tiempo real",
                     font=("Arial", 10, "italic"),
                     text_color="#7A8BB5").pack(anchor="w")

        status_col = ctk.CTkFrame(topbar, fg_color="transparent")
        status_col.pack(side="left", padx=8, pady=6, fill="y")
        self._badge_gns3 = ctk.CTkLabel(status_col, text="●  GNS3 API: …",
                                        text_color="#F59E0B",
                                        corner_radius=22,
                                        fg_color=("#2B2010", "#2B2010"),
                                        border_width=1,
                                        border_color=("#7C5A1E", "#7C5A1E"),
                                        width=0, padx=12, pady=3,
                                        font=("Arial", 10, "bold"))
        self._badge_gns3.pack(side="left", padx=4, pady=8)
        self._badge_mon = ctk.CTkLabel(status_col, text="●  MONITOR LIVE (5s)",
                                       text_color="#67E8F9",
                                       corner_radius=22,
                                       fg_color=("#0D2A35", "#0D2A35"),
                                       border_width=1,
                                       border_color=("#1F5F78", "#1F5F78"),
                                       width=0, padx=12, pady=3,
                                       font=("Arial", 10, "bold"))
        self._badge_mon.pack(side="left", padx=4, pady=8)
        self._badge_user = ctk.CTkLabel(status_col, text="👤 admin",
                                        text_color="#C4B5FD",
                                        corner_radius=22,
                                        fg_color=("#24183B", "#24183B"),
                                        border_width=1,
                                        border_color=("#533A8F", "#533A8F"),
                                        width=0, padx=12, pady=3,
                                        font=("Arial", 10, "bold"))
        self._badge_user.pack(side="left", padx=4, pady=8)
        self._badge_updated = ctk.CTkLabel(status_col, text="🕒 —",
                                           text_color="#7A8BB5",
                                           width=0, padx=10, pady=3,
                                           font=("Consolas", 10))
        self._badge_updated.pack(side="left", padx=6, pady=8)

        topbar_right = ctk.CTkFrame(topbar, fg_color="transparent")
        topbar_right.pack(side="right", padx=10, pady=6, fill="y")
        def _logout():
            if messagebox.askyesno("Cerrar sesión", "¿Cerrar sesión y volver al login?"):
                self.destroy()
                LoginApp().mainloop()
        ctk.CTkButton(topbar_right, text="✕ Cerrar Sesión", command=_logout,
                      fg_color="transparent", hover_color="#162241",
                      text_color="#FCA5A5", border_width=1, border_color="#5A1E1E",
                      corner_radius=8, height=34, width=118,
                      font=("Arial", 10, "bold")).pack(side="right", pady=8)

        # ========================
        #  KPI STRIP (compacto)
        # ========================
        kpi_strip = ctk.CTkFrame(self.main_container, fg_color="transparent")
        kpi_strip.pack(fill="x", pady=(0, 6))

        kpi_specs = [
            ("Equipos", "#67E8F9", "rgba(34,211,238,.10)", "rgba(34,211,238,.25)", "equipos_totales"),
            ("UP", "#6EE7B7", "rgba(16,185,129,.10)", "rgba(16,185,129,.25)", "up_gns3"),
            ("DOWN", "#FCA5A5", "rgba(239,68,68,.10)", "rgba(239,68,68,.25)", "down_gns3"),
            ("Ping Prom.", "#FDBA74", "rgba(249,115,22,.10)", "rgba(249,115,22,.25)", "ping_promedio_ms"),
            ("Alertas", "#FCA5A5", "rgba(239,68,68,.10)", "rgba(239,68,68,.25)", "alertas_activas"),
            ("Int UP/DOWN", "#C4B5FD", "rgba(124,58,237,.10)", "rgba(124,58,237,.25)", "up_intf"),
        ]
        self._kpi_widgets = {}
        for (titulo, color, fg, border, k) in kpi_specs:
            k_fr = ctk.CTkFrame(kpi_strip, fg_color="#0B1224", corner_radius=10,
                                border_width=1, border_color="#1E2E55")
            k_fr.pack(side="left", padx=4, fill="x", expand=True, ipady=3)
            ctk.CTkLabel(k_fr, text=titulo.upper(),
                         text_color="#50628C",
                         font=("Arial", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 0))
            lbl_val = ctk.CTkLabel(k_fr, text="0",
                                   text_color=color,
                                   font=("Arial", 18, "bold"))
            lbl_val.pack(anchor="w", padx=10, pady=(1, 4))
            self._kpi_widgets[k] = lbl_val

        # ========================
        #  CONTENEDOR RACK
        # ========================
        self.scroll_rack = ctk.CTkScrollableFrame(self.main_container,
                                                   fg_color="#162241",
                                                   corner_radius=12,
                                                   border_width=2,
                                                   border_color="#1E2E55",
                                                   label_text="[ RACK 19\"  ·  TOPOLOGÍA DE RED VIRTUALIZADA ]",
                                                   label_fg_color="#67E8F9",
                                                   label_font=("Consolas", 10, "bold"))
        self.scroll_rack.pack(fill="both", expand=True, padx=0, pady=(4, 8))

        # ========================
        #  PANEL INFERIOR FIJO
        # ========================
        bottom_panel = ctk.CTkFrame(self.main_container, fg_color="#0B1224", corner_radius=10,
                                    border_width=1, border_color="#1E2E55")
        bottom_panel.pack(fill="x", pady=(0, 2))

        left_foot = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        left_foot.pack(side="left", fill="x", expand=True, padx=12, pady=6)

        servicios_info = "● Telegram Bot Activo    ● Polling GNS3 + CLI + Ping: Cada 5s    ● Grafana Telemetría en :3000"
        ctk.CTkLabel(left_foot, text=servicios_info,
                     font=("Consolas", 10), text_color="#7A8BB5").pack(anchor="w", pady=2)
        self._lbl_foot_extra = ctk.CTkLabel(left_foot,
                                            text="● Dashboard Web en http://127.0.0.1:5000",
                                            font=("Consolas", 10), text_color="#67E8F9")
        self._lbl_foot_extra.pack(anchor="w", pady=(0, 2))

        def abrir_grafana():
            webbrowser.open("http://localhost:3000")

        def abrir_web_dashboard():
            webbrowser.open(self.estado_global["dashboard_http"])

        btn_web = ctk.CTkButton(bottom_panel, text="🌐 Dashboard Web", command=abrir_web_dashboard,
                                fg_color="#7C3AED", hover_color="#6D28D9",
                                font=("Arial", 11, "bold"), height=36, width=170, corner_radius=9)
        btn_web.pack(side="right", padx=10, pady=10)

        btn_grafana = ctk.CTkButton(bottom_panel, text="📊 Dashboard Grafana", command=abrir_grafana,
                                    fg_color="#2563EB", hover_color="#1D4ED8",
                                    font=("Arial", 11, "bold"), height=36, width=170, corner_radius=9)
        btn_grafana.pack(side="right", padx=(0, 2), pady=10)

        self.after(1500, self._refresh_header_statuses)
        self.actualizar_dispositivos()
        self.iniciar_hilo_monitoreo_integral()

    def _refresh_header_statuses(self):
        def _trabajo():
            try:
                if not getattr(self, "winfo_exists", lambda: True)():
                    return
            except Exception:
                return
            g_ok = False
            try:
                r = requests.get(f"{self.GNS3_URL}/projects", timeout=3)
                g_ok = (r.status_code == 200)
            except Exception:
                g_ok = False
            gr_ok = False
            try:
                r = requests.get("http://localhost:3000", timeout=3)
                gr_ok = (r.status_code == 200)
            except Exception:
                gr_ok = False
            self._gns3_status_ok = g_ok
            self._grafana_status_ok = gr_ok
            try:
                self.after(0, lambda: self._actualizar_badges_header(g_ok, gr_ok))
            except Exception:
                return
            try:
                self.after(15000, self._refresh_header_statuses)
            except Exception:
                return
        threading.Thread(target=_trabajo, daemon=True).start()

    def _actualizar_badges_header(self, g_ok, gr_ok):
        if g_ok:
            self._badge_gns3.configure(text="●  GNS3 API: OK",
                                       text_color="#6EE7B7",
                                       fg_color=("#0E2C20", "#0E2C20"),
                                       border_color=("#1F7A50", "#1F7A50"))
        else:
            self._badge_gns3.configure(text="●  GNS3 API: OFFLINE",
                                       text_color="#FCA5A5",
                                       fg_color=("#351717", "#351717"),
                                       border_color=("#873636", "#873636"))

    def _actualizar_kpi_desktop(self, kpi):
        try:
            mapa = {
                "equipos_totales": ("{v}", False),
                "up_gns3":        ("{v}", False),
                "down_gns3":      ("{v}", False),
                "ping_promedio_ms": (("{v} ms" if isinstance(v, int) else "N/D") if (v := kpi.get("ping_promedio_ms")) is not None else "N/D", True),
                "alertas_activas": ("{v}", False),
                "up_intf":        (f"{kpi.get('up_intf',0)} / {kpi.get('down_intf',0)}", False),
            }
            for key, lbl in self._kpi_widgets.items():
                raw = kpi.get(key)
                if key == "ping_promedio_ms":
                    txt = f"{raw} ms" if isinstance(raw, int) else ("N/D" if raw is None else str(raw))
                    lbl.configure(text=txt)
                elif key == "up_intf":
                    lbl.configure(text=f"{kpi.get('up_intf',0)} / {kpi.get('down_intf',0)}")
                else:
                    lbl.configure(text=str(raw if raw is not None else 0))
            ts = kpi.get("ultima_actualizacion")
            if ts and self._badge_updated:
                self._badge_updated.configure(text=f"🕒 {ts}")
        except Exception:
            pass

    def obtener_proyecto_activo(self):
        try:
            resp_proj = requests.get(f"{self.GNS3_URL}/projects", timeout=2)
            if resp_proj.status_code == 200:
                projects = resp_proj.json()
                proyectos_abiertos = [p for p in projects if p.get("status") == "opened"]
                if proyectos_abiertos:
                    return proyectos_abiertos[0]["project_id"]
                if projects:
                    return projects[0]["project_id"]
        except Exception:
            pass
        return None
    def consultar_estado_interfaz_cisco(self, host, puerto, interfaz):
        """
        Consulta el estado de una interfaz Cisco mediante Telnet.

        Devuelve:
            "Up"   -> interfaz operativa
            "Down" -> interfaz apagada o caída
            None   -> no fue posible consultar
        """

        import telnetlib
        import time

        try:
            tn = telnetlib.Telnet(host, int(puerto), timeout=3)

            # Esperamos el prompt del equipo.
            time.sleep(1)

            tn.write(b"\r\n")
            time.sleep(0.5)

            # Desactivamos el paginado.
            tn.write(b"terminal length 0\r\n")
            time.sleep(0.5)

            # Consultamos específicamente la interfaz.
            comando = f"show interfaces {interfaz}\r\n"
            tn.write(comando.encode("ascii"))

            time.sleep(1)

            salida = tn.read_very_eager().decode(
                "utf-8",
                errors="ignore"
            )

            tn.close()

            salida_lower = salida.lower()

            # Cisco normalmente muestra:
            # GigabitEthernet0/1 is up, line protocol is up
            #
            # o:
            # GigabitEthernet0/1 is administratively down,
            # line protocol is down

            if "administratively down" in salida_lower:
                return "Down"

            if " is up, line protocol is up" in salida_lower:
                return "Up"

            if " is down, line protocol is down" in salida_lower:
                return "Down"

            if " is down" in salida_lower:
                return "Down"

            return None

        except Exception as e:
            print(f"[CLI] Error consultando {host}:{puerto} {interfaz}: {e}")
            return None
    def consultar_puertos_switch(self, host, puerto_consola):
        """
        Consulta todos los puertos de un switch Cisco
        mediante Telnet y devuelve sus estados.
        """

        import telnetlib
        import time
        import re

        estados = {}

        try:
            print(f"[FLOWGUARD] Consultando switch {host}:{puerto_consola}")

            tn = telnetlib.Telnet(
                host,
                int(puerto_consola),
                timeout=5
            )

            time.sleep(1)

            # Enviamos ENTER para despertar el CLI
            tn.write(b"\r\n")
            time.sleep(0.5)

            # Desactivar paginación
            tn.write(b"terminal length 0\r\n")
            time.sleep(0.5)

            # Comando que estamos utilizando manualmente
            tn.write(b"show interfaces status\r\n")

            time.sleep(1.5)

            salida = tn.read_very_eager().decode(
                "utf-8",
                errors="ignore"
            )

            tn.close()

            print(f"[FLOWGUARD] Salida recibida de {host}:")
            print(salida)

            # Analizamos línea por línea
            for linea in salida.splitlines():

                linea = linea.strip()

                if not linea:
                    continue

                # Ignoramos encabezados
                if linea.startswith("Port "):
                    continue

                if linea.startswith("Name "):
                    continue

                # Buscamos estados típicos de Cisco
                estados_validos = [
                    "connected",
                    "disabled",
                    "notconnect",
                    "err-disabled",
                    "suspended",
                    "inactive",
                    "monitoring"
                ]

                encontrado = None

                for estado in estados_validos:
                    if re.search(
                        rf"\b{re.escape(estado)}\b",
                        linea,
                        re.IGNORECASE
                    ):
                        encontrado = estado
                        break

                if encontrado:

                    partes = linea.split()

                    if len(partes) >= 2:

                        puerto = partes[0]

                        estados[puerto] = encontrado

            print(
                f"[FLOWGUARD] Puertos detectados en "
                f"{host}: {estados}"
            )

            return estados

        except Exception as e:

            print(
                f"[FLOWGUARD] Error consultando "
                f"{host}:{puerto_consola}: {e}"
            )

            return {}
    def monitorear_interfaces_switch(
        self,
        nombre_equipo,
        host,
        puerto_consola
    ):
        """
        Consulta todos los puertos del switch
        y detecta cambios UP/DOWN.
        """

        estados_actuales = self.consultar_puertos_switch(
            host,
            puerto_consola
        )

        if not estados_actuales:
            return

        # Si es la primera lectura,
        # solamente guardamos los estados.
        if nombre_equipo not in self.estado_anterior_interfaces:

            self.estado_anterior_interfaces[nombre_equipo] = (
                estados_actuales.copy()
            )

            print(
                f"[FLOWGUARD] Estado inicial cargado: "
                f"{nombre_equipo}"
            )

            return

        estados_anteriores = (
            self.estado_anterior_interfaces[nombre_equipo]
        )

        # Revisamos todos los puertos actuales
        for puerto, estado_actual in estados_actuales.items():

            estado_anterior = estados_anteriores.get(puerto)

            # Primera vez que vemos este puerto
            if estado_anterior is None:

                estados_anteriores[puerto] = estado_actual

                continue

            # No hubo cambio
            if estado_anterior == estado_actual:
                continue

            print(
                f"[FLOWGUARD] CAMBIO DETECTADO | "
                f"{nombre_equipo} | "
                f"{puerto} | "
                f"{estado_anterior} -> "
                f"{estado_actual}"
            )

            # Detectamos DOWN
            estados_down = [
                "disabled",
                "notconnect",
                "err-disabled",
                "suspended",
                "inactive"
            ]

            # Detectamos UP
            estados_up = [
                "connected"
            ]

            if estado_actual in estados_down:

                mensaje = (
                    "🔴 FLOWGUARD - INTERFAZ DOWN 🔴\n\n"
                    f"Equipo: {nombre_equipo}\n"
                    f"Puerto: {puerto}\n"
                    f"Estado anterior: {estado_anterior}\n"
                    f"Estado actual: {estado_actual}\n\n"
                    "Se detectó una caída o desactivación "
                    "de la interfaz."
                )

                self.enviar_alerta_telegram(mensaje)

            elif estado_actual in estados_up:

                mensaje = (
                    "🟢 FLOWGUARD - INTERFAZ UP 🟢\n\n"
                    f"Equipo: {nombre_equipo}\n"
                    f"Puerto: {puerto}\n"
                    f"Estado anterior: {estado_anterior}\n"
                    f"Estado actual: {estado_actual}\n\n"
                    "La interfaz se encuentra nuevamente "
                    "operativa."
                )

                self.enviar_alerta_telegram(mensaje)

            # Guardamos el nuevo estado
            estados_anteriores[puerto] = estado_actual

        # Guardamos todos los estados
        self.estado_anterior_interfaces[nombre_equipo] = (
            estados_actuales.copy()
        )
    def enviar_alerta_telegram(self, mensaje):
        if not self.TELEGRAM_TOKEN:
            return
        try:
            self.estado_global["alertas_historial"].appendleft({
                "fecha": datetime.now().isoformat(timespec="seconds"),
                "mensaje": mensaje[:500]
            })
            self.estado_global["resumen_kpi"]["alertas_activas"] = len(
                [a for a in self.estado_global["alertas_historial"] if any(k in a.get("mensaje","") for k in ["ALERTA","DOWN","OFFLINE","Caída","inactivo"])]
            )
        except Exception:
            pass
        url = f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": self.TELEGRAM_CHAT_ID, "text": mensaje}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass

    def _ejecutar_comando_cisco(self, host, puerto, comando, espera_respuesta=1.5):
        try:
            tn = telnetlib.Telnet(host, int(puerto), timeout=5)
            time.sleep(1)
            tn.write(b"\r\n")
            time.sleep(0.5)
            tn.write(b"terminal length 0\r\n")
            time.sleep(0.5)
            tn.write((comando + "\r\n").encode("ascii"))
            time.sleep(espera_respuesta)
            salida = tn.read_very_eager().decode("utf-8", errors="ignore")
            tn.close()
            return salida
        except Exception as e:
            print(f"[CLI] {host}:{puerto} cmd={comando} error: {e}")
            return ""

    def consultar_ip_interfaces_cisco(self, host, puerto_consola):
        salida = self._ejecutar_comando_cisco(host, puerto_consola, "show ip interface brief", espera_respuesta=2)
        resultado = {}
        if not salida:
            return resultado
        for linea in salida.splitlines():
            linea = linea.strip()
            if not linea or linea.lower().startswith("interface") or linea.lower().startswith("-"):
                continue
            partes = linea.split()
            if len(partes) >= 4 and "." not in partes[0] and ("/" in partes[0] or partes[0].startswith("Vlan")):
                nombre = partes[0]
                ip = partes[1] if partes[1] != "unassigned" else None
                status_ok = partes[2] if len(partes) > 2 else ""
                protocol = partes[3] if len(partes) > 3 else ""
                resultado[nombre] = {
                    "ip": ip,
                    "admin": status_ok,
                    "protocol": protocol,
                    "estado": "Up" if ("up" in status_ok.lower() and "up" in protocol.lower()) else "Down"
                }
        return resultado

    def consultar_descripciones_cisco(self, host, puerto_consola):
        salida = self._ejecutar_comando_cisco(host, puerto_consola, "show interfaces description", espera_respuesta=2)
        resultado = {}
        if not salida:
            return resultado
        for linea in salida.splitlines():
            linea = linea.strip()
            if not linea or linea.lower().startswith("interface") or linea.lower().startswith("-"):
                continue
            partes = linea.split(maxsplit=3)
            if len(partes) >= 3 and ("/" in partes[0] or partes[0].startswith("Vlan")):
                nombre = partes[0]
                admin = partes[1]
                link = partes[2] if len(partes) > 2 else ""
                descripcion = partes[3] if len(partes) > 3 else ""
                resultado[nombre] = {
                    "admin": admin,
                    "link": link,
                    "descripcion": descripcion,
                    "estado": "Up" if ("up" in admin.lower() and "up" in link.lower()) else "Down"
                }
        return resultado

    def consultar_version_cisco(self, host, puerto_consola):
        salida = self._ejecutar_comando_cisco(host, puerto_consola, "show version", espera_respuesta=2.5)
        if not salida:
            return {"version_so": "N/D", "modelo": "N/D", "hostname": "N/D", "uptime": "N/D"}
        version_so = "N/D"
        modelo = "N/D"
        hostname = "N/D"
        uptime = "N/D"
        m_ver = re.search(r"(Cisco IOS|IOS-XE|IOS Software|C2900|C3600|IOSv)\s*[^\n,]*?Version\s+([0-9A-Za-z._() ]+)", salida, re.IGNORECASE)
        if m_ver:
            version_so = m_ver.group(2).strip().strip(",")
        m_model = re.search(r"(?:Model number|Processor board ID|cisco|^)[\s:]*([A-Z][A-Z0-9-]+)", salida, re.MULTILINE)
        if m_model:
            modelo = m_model.group(1).strip()
        m_host = re.search(r"\n([A-Za-z0-9_-]+)\s+uptime\s+is\s+([^\n]+)", salida, re.IGNORECASE)
        if m_host:
            hostname = m_host.group(1).strip()
            uptime = m_host.group(2).strip()
        else:
            m_host2 = re.search(r"\n(.+?)\s+uptime is ", salida, re.IGNORECASE)
            if m_host2:
                hostname = m_host2.group(1).strip()
                m_up2 = re.search(r"uptime is ([^\n]+)", salida, re.IGNORECASE)
                if m_up2:
                    uptime = m_up2.group(1).strip()
        return {"version_so": version_so, "modelo": modelo, "hostname": hostname, "uptime": uptime}

    def consultar_cpu_cisco(self, host, puerto_consola):
        salida = self._ejecutar_comando_cisco(host, puerto_consola, "show processes cpu | include CPU", espera_respuesta=1.5)
        if not salida:
            return {"cpu_5s": None, "cpu_1m": None, "cpu_5m": None, "raw": "N/D"}
        m = re.search(r"CPU utilization for five seconds:\s*([0-9]+)%/[0-9]+%;\s*one minute:\s*([0-9]+)%;\s*five minutes:\s*([0-9]+)%", salida, re.IGNORECASE)
        if m:
            return {"cpu_5s": int(m.group(1)), "cpu_1m": int(m.group(2)), "cpu_5m": int(m.group(3)), "raw": salida.strip()}
        m2 = re.search(r"CPU utilization:\s+([0-9.]+)%\s+\(5s average\)", salida, re.IGNORECASE)
        if m2:
            return {"cpu_5s": float(m2.group(1)), "cpu_1m": None, "cpu_5m": None, "raw": salida.strip()}
        return {"cpu_5s": None, "cpu_1m": None, "cpu_5m": None, "raw": salida.strip()}

    def _ping_windows(self, ip):
        if not ip or ip in ("0.0.0.0", "localhost", "127.0.0.1", ""):
            return False, None
        try:
            proc = subprocess.run(
                ["ping.exe", "-n", "1", "-w", "1500", ip],
                capture_output=True, text=True, timeout=3
            )
            stdout = proc.stdout or ""
            m = re.search(r"tiempo[=<](\d+)\s*ms", stdout, re.IGNORECASE)
            if m:
                ms = int(m.group(1))
                return True, ms
            m2 = re.search(r"time[=<](\d+)\s*ms", stdout, re.IGNORECASE)
            if m2:
                ms = int(m2.group(1))
                return True, ms
            if "TTL=" in stdout or "ttl=" in stdout:
                return True, None
            return False, None
        except Exception as e:
            print(f"[PING] {ip} fallo: {e}")
            return False, None

    def _sincronizar_estado_global_con_gns3_y_cli_y_ping(self):
        try:
            project_id = self.obtener_proyecto_activo()
            resumen = self.estado_global["resumen_kpi"]
            resumen["equipos_totales"] = 0
            resumen["up_gns3"] = 0
            resumen["down_gns3"] = 0
            resumen["total_intf"] = 0
            resumen["up_intf"] = 0
            resumen["down_intf"] = 0
            total_ping_ms = 0
            total_ping_count = 0

            if project_id:
                nodes_resp = requests.get(f"{self.GNS3_URL}/projects/{project_id}/nodes", timeout=2)
                if nodes_resp.status_code == 200:
                    nodes = [n for n in nodes_resp.json() if "cloud" not in n.get("name","").lower()]

                    ips_a_ping = []
                    for node in nodes:
                        nid = node.get("node_id")
                        nombre = node.get("name","")
                        raw_status = str(node.get("status","")).lower()
                        gns3_up = raw_status in ["started","running","on"]

                        console_host = node.get("console_host","127.0.0.1")
                        if not console_host or console_host == "0.0.0.0":
                            console_host = "127.0.0.1"
                        console_port = node.get("console")

                        if gns3_up:
                            resumen["up_gns3"] += 1
                        else:
                            resumen["down_gns3"] += 1

                        estado_anterior = self.estado_global["equipos"].get(nid, {})
                        interfaces_merged = estado_anterior.get("interfaces", {})
                        mgmt_ip = estado_anterior.get("ip_gestion") or console_host
                        ping_ok = estado_anterior.get("ping_ok")
                        ping_ms = estado_anterior.get("ping_ms")

                        nombre_l = nombre.lower()
                        if any(k in nombre_l for k in ["sw","router","core","mikrotik","r1","r2","switch"]) and gns3_up and console_port:
                            try:
                                ip_map = self.consultar_ip_interfaces_cisco(console_host, console_port)
                                desc_map = self.consultar_descripciones_cisco(console_host, console_port)
                                puertos = self.consultar_puertos_switch(console_host, console_port)
                                merged = {}
                                todos_nombres = set(list(ip_map.keys()) + list(desc_map.keys()) + list(puertos.keys()))
                                for iface in todos_nombres:
                                    info_ip = ip_map.get(iface, {})
                                    info_desc = desc_map.get(iface, {})
                                    estado_puerto = puertos.get(iface)
                                    estado_final = info_ip.get("estado") or info_desc.get("estado") or ("Up" if (estado_puerto == "connected" or estado_puerto == "monitoring") else "Down")
                                    if info_ip.get("ip") and (info_ip.get("ip") not in ("127.0.0.1", "0.0.0.0", None)) and mgmt_ip in ("127.0.0.1", None):
                                        mgmt_ip = info_ip.get("ip")
                                    merged[iface] = {
                                        "estado": estado_final,
                                        "estado_raw": estado_puerto,
                                        "ip": info_ip.get("ip"),
                                        "admin": info_desc.get("admin") or info_ip.get("admin"),
                                        "link": info_desc.get("link") or info_ip.get("protocol"),
                                        "descripcion": info_desc.get("descripcion",""),
                                    }
                                interfaces_merged = merged
                            except Exception as e:
                                print(f"[FLOWGUARD] error interfaces {nombre}: {e}")

                            try:
                                if not estado_anterior.get("version_so") or estado_anterior.get("version_so") in ("N/D", None):
                                    eq_version = self.consultar_version_cisco(console_host, console_port)
                                else:
                                    eq_version = {
                                        "version_so": estado_anterior.get("version_so"),
                                        "modelo": estado_anterior.get("modelo"),
                                        "hostname": estado_anterior.get("hostname_so"),
                                        "uptime": estado_anterior.get("uptime"),
                                    }
                                eq_cpu = self.consultar_cpu_cisco(console_host, console_port)
                            except Exception as e:
                                print(f"[FLOWGUARD] error version/cpu {nombre}: {e}")
                                eq_version = {"version_so": "N/D", "modelo": "N/D", "hostname": nombre, "uptime": "N/D"}
                                eq_cpu = {"cpu_5s": None, "cpu_1m": None, "cpu_5m": None}
                        else:
                            eq_version = estado_anterior.get("version_so") and {"version_so": estado_anterior.get("version_so"), "modelo": estado_anterior.get("modelo"), "hostname": estado_anterior.get("hostname_so"), "uptime": estado_anterior.get("uptime")} or {"version_so": "N/D", "modelo": "N/D", "hostname": nombre, "uptime": "N/D"}
                            eq_cpu = estado_anterior.get("cpu_uso") or {"cpu_5s": None, "cpu_1m": None, "cpu_5m": None}
                        self._cache_eq_version[nid] = eq_version
                        self._cache_eq_cpu[nid] = eq_cpu

                        for iface, info in interfaces_merged.items():
                            resumen["total_intf"] += 1
                            if info.get("estado") == "Up":
                                resumen["up_intf"] += 1
                            else:
                                resumen["down_intf"] += 1

                        if mgmt_ip and mgmt_ip not in ("127.0.0.1", "0.0.0.0", ""):
                            ips_a_ping.append((nid, mgmt_ip))

                        self.estado_global["equipos"][nid] = {
                            "node_id": nid,
                            "nombre": nombre,
                            "gns3_status": raw_status,
                            "gns3_encendido": gns3_up,
                            "console_host": console_host,
                            "console_port": console_port,
                            "ip_gestion": mgmt_ip,
                            "ping_ok": ping_ok,
                            "ping_ms": ping_ms,
                            "interfaces": interfaces_merged,
                            "version_so": self._cache_eq_version.get(nid, {}).get("version_so"),
                            "hostname_so": self._cache_eq_version.get(nid, {}).get("hostname"),
                            "modelo": self._cache_eq_version.get(nid, {}).get("modelo"),
                            "uptime": self._cache_eq_version.get(nid, {}).get("uptime"),
                            "cpu_uso": self._cache_eq_cpu.get(nid, {}),
                        }

                    for nid, mgmt_ip in ips_a_ping:
                        fut = self._ping_executor.submit(self._ping_windows, mgmt_ip)
                        try:
                            ok, ms = fut.result(timeout=3.1)
                        except Exception:
                            ok, ms = False, None
                        self.estado_global["equipos"][nid]["ping_ok"] = ok
                        self.estado_global["equipos"][nid]["ping_ms"] = ms
                        if ok and isinstance(ms, int):
                            total_ping_ms += ms
                            total_ping_count += 1

                        previo_ping = self._estado_anterior_ping.get(nid, {"alerta_enviada_offline": False, "alerta_enviada_online": True, "ok_anterior": None})
                        if ok:
                            self._contadores_ping_offline[nid] = 0
                            if previo_ping.get("ok_anterior") is False and not previo_ping.get("alerta_enviada_online", False):
                                nombre = self.estado_global["equipos"][nid]["nombre"]
                                ms_txt = f"{ms} ms" if isinstance(ms, int) else "desconocido"
                                self.enviar_alerta_telegram(
                                    "🟢 EQUIPO PING ONLINE 🟢\n\n"
                                    f"El equipo [{nombre}] ({mgmt_ip}) ha vuelto a responder ping.\n"
                                    f"Latencia: {ms_txt}"
                                )
                                self._estado_anterior_ping[nid] = {
                                    "alerta_enviada_offline": False,
                                    "alerta_enviada_online": True,
                                    "ok_anterior": True
                                }
                            else:
                                self._estado_anterior_ping[nid] = {
                                    "alerta_enviada_offline": previo_ping.get("alerta_enviada_offline", False),
                                    "alerta_enviada_online": True,
                                    "ok_anterior": True
                                }
                        else:
                            self._contadores_ping_offline[nid] = self._contadores_ping_offline.get(nid, 0) + 1
                            if self._contadores_ping_offline[nid] >= 2 and not previo_ping.get("alerta_enviada_offline", False):
                                nombre = self.estado_global["equipos"][nid]["nombre"]
                                self.enviar_alerta_telegram(
                                    "🟠 EQUIPO PING OFFLINE 🟠\n\n"
                                    f"El equipo [{nombre}] ({mgmt_ip}) ha dejado de responder ICMP en los últimos 2 ciclos."
                                )
                                self._estado_anterior_ping[nid] = {
                                    "alerta_enviada_offline": True,
                                    "alerta_enviada_online": False,
                                    "ok_anterior": False
                                }
                            else:
                                self._estado_anterior_ping[nid] = {
                                    "alerta_enviada_offline": previo_ping.get("alerta_enviada_offline", False),
                                    "alerta_enviada_online": False,
                                    "ok_anterior": False
                                }

                    resumen["equipos_totales"] = len(nodes)

            if total_ping_count > 0:
                resumen["ping_promedio_ms"] = round(total_ping_ms / total_ping_count, 1)
            resumen["ultima_actualizacion"] = datetime.now().isoformat(timespec="seconds")
            try:
                copia = dict(resumen)
                self.after(0, lambda: self._actualizar_kpi_desktop(copia))
            except Exception:
                pass
        except Exception as e:
            print(f"[FLOWGUARD] error sincronizando estado global: {e}")

    def _iniciar_servidor_web(self):
        def lanzar():
            try:
                import logging
                log = logging.getLogger("werkzeug")
                log.setLevel(logging.ERROR)

                app = Flask(__name__, template_folder="templates", static_folder="static")

                @app.route("/")
                def vista_dashboard():
                    return render_template("dashboard.html", proyecto="FLOWGUARD")

                @app.route("/api/estado", methods=["GET"])
                def api_estado():
                    try:
                        equipos_list = [v for k, v in sorted(self.estado_global["equipos"].items(), key=lambda kv: kv[1].get("nombre",""))]
                        historial = list(self.estado_global["alertas_historial"])
                        return jsonify({
                            "ok": True,
                            "resumen_kpi": self.estado_global["resumen_kpi"],
                            "equipos": equipos_list,
                            "alertas_historial": historial,
                        })
                    except Exception as e:
                        return jsonify({"ok": False, "error": str(e)}), 500

                @app.route("/api/abrir-cli", methods=["GET"])
                def api_abrir_cli():
                    host = request.args.get("host", "127.0.0.1")
                    port = request.args.get("port", "5003")
                    abrio_local = False
                    error_putty = None
                    try:
                        ruta_putty = r"C:\Program Files\PuTTY\putty.exe"
                        if not os.path.exists(ruta_putty):
                            ruta_putty = r"C:\Program Files (x86)\PuTTY\putty.exe"
                        if os.path.exists(ruta_putty):
                            subprocess.Popen([ruta_putty, "-telnet", str(host), str(port)])
                            abrio_local = True
                        else:
                            error_putty = "PuTTY no encontrado en rutas x64/x86"
                    except Exception as e:
                        error_putty = str(e)
                    telnet_link = f"telnet://{host}:{port}"
                    return jsonify({
                        "ok": abrio_local,
                        "host": host,
                        "port": port,
                        "telnet_link": telnet_link,
                        "mensaje": (
                            "✅ PuTTY abierto en esta PC (misma que corre FLOWGUARD). Si accedés desde OTRO dispositivo, usá el link telnet:// o copiá host:puerto."
                            if abrio_local else
                            f"⚠️ No se abrió PuTTY automáticamente ({error_putty}). Abrí manualmente o usá el enlace telnet:// de abajo."
                        )
                    })

                @app.route("/api/abrir-grafana", methods=["GET"])
                def api_abrir_grafana():
                    try:
                        webbrowser.open("http://localhost:3000")
                        return jsonify({"ok": True})
                    except Exception as e:
                        return jsonify({"ok": False, "error": str(e)}), 500

                @app.route("/detalle/<node_id>")
                def vista_detalle(node_id):
                    return render_template(
                        "detalle_equipo.html",
                        node_id=node_id,
                        dashboard_url=self.estado_global["dashboard_http"]
                    )

                @app.route("/api/equipo/<node_id>")
                def api_equipo_individual(node_id):
                    eq = (self.estado_global.get("equipos") or {}).get(node_id)
                    if not eq:
                        return jsonify({
                            "ok": False,
                            "error": (
                                "Equipo no encontrado en telemetría local. "
                                "Esto suele pasar si abriste DETALLE antes de que el hilo de monitoreo "
                                "sincronice el primer inventario (primer ciclo ~5s). "
                                "Refrescar la página en 5 segundos."
                            )
                        }), 404
                    return jsonify({
                        "ok": True,
                        "equipo": eq,
                        "resumen": self.estado_global.get("resumen_kpi") or {"ultima_actualizacion": None}
                    })

                print(f"[FLOWGUARD] Servidor web iniciado: {self.estado_global['dashboard_http']}")
                app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)
            except Exception as e:
                print(f"[FLOWGUARD] Error servidor web: {e}")

        t = threading.Thread(target=lanzar, daemon=True)
        t.start()

    def iniciar_hilo_monitoreo_integral(self):

        def bucle_monitoreo():

            time.sleep(3)

            # =====================================================
            # PRIMERA CARGA DE ESTADOS
            # =====================================================

            try:
                project_id = self.obtener_proyecto_activo()

                if project_id:

                    resp_nodes = requests.get(
                        f"{self.GNS3_URL}/projects/{project_id}/nodes",
                        timeout=2
                    )

                    resp_links = requests.get(
                        f"{self.GNS3_URL}/projects/{project_id}/links",
                        timeout=2
                    )

                    # =================================================
                    # CARGAR ESTADO INICIAL DE LOS EQUIPOS
                    # =================================================

                    if resp_nodes.status_code == 200:

                        nodes = resp_nodes.json()

                        for node in nodes:

                            nombre = node.get("name", "")

                            if "cloud" in nombre.lower():
                                continue

                            node_id = node.get("node_id")

                            es_encendido = (
                                str(node.get("status", "")).lower()
                                in ["started", "running", "on"]
                            )

                            self.estado_anterior_equipos[node_id] = {
                                "nombre": nombre,
                                "es_encendido": es_encendido,
                                "alerta_enviada": False
                            }

                    # =================================================
                    # CARGAR ESTADO INICIAL DE LOS ENLACES
                    # =================================================

                    if resp_links.status_code == 200:

                        for link in resp_links.json():

                            link_id = link.get("link_id")

                            self.estado_anterior_puertos[link_id] = {
                                "estado": "Up",
                                "detalles": link
                            }

            except Exception as e:

                print(
                    f"[FLOWGUARD] Error en carga inicial: {e}"
                )

            # =====================================================
            # BUCLE PRINCIPAL
            # =====================================================

            while True:

                try:

                    project_id = self.obtener_proyecto_activo()

                    if project_id:

                        resp_nodes = requests.get(
                            f"{self.GNS3_URL}/projects/{project_id}/nodes",
                            timeout=2
                        )

                        resp_links = requests.get(
                            f"{self.GNS3_URL}/projects/{project_id}/links",
                            timeout=2
                        )

                        # =================================================
                        # MONITOREO DE NODOS Y PUERTOS
                        # =================================================

                        if resp_nodes.status_code == 200:

                            nodes = resp_nodes.json()

                            # =================================================
                            # MONITOREO REAL DE PUERTOS DE SWITCHES
                            # =================================================

                            for node in nodes:

                                nombre_switch = node.get(
                                    "name",
                                    ""
                                )

                                # Ignorar Cloud
                                if "cloud" in nombre_switch.lower():
                                    continue

                                # Buscar switches / routers / core / mikrotik por nombre
                                nombre_switch_l = nombre_switch.lower()
                                if not any(k in nombre_switch_l for k in ["sw","switch","router","core","mikrotik","r1","r2"]):
                                    continue

                                host_consola = node.get(
                                    "console_host",
                                    "127.0.0.1"
                                )

                                if (
                                    not host_consola
                                    or host_consola == "0.0.0.0"
                                ):
                                    host_consola = "127.0.0.1"

                                puerto_consola = node.get(
                                    "console",
                                    None
                                )

                                if puerto_consola:

                                    print(
                                        f"[PUERTOS] Consultando "
                                        f"{nombre_switch} "
                                        f"en "
                                        f"{host_consola}:"
                                        f"{puerto_consola}"
                                    )

                                    self.monitorear_interfaces_switch(
                                        nombre_switch,
                                        host_consola,
                                        puerto_consola
                                    )

                            # =================================================
                            # MONITOREO DEL ESTADO DE LOS EQUIPOS
                            # =================================================

                            estado_actual_eq = {}

                            for node in nodes:

                                nombre = node.get(
                                    "name",
                                    ""
                                )

                                if "cloud" in nombre.lower():
                                    continue

                                node_id = node.get(
                                    "node_id"
                                )

                                es_encendido = (
                                    str(
                                        node.get(
                                            "status",
                                            ""
                                        )
                                    ).lower()
                                    in [
                                        "started",
                                        "running",
                                        "on"
                                    ]
                                )

                                alerta_enviada = False

                                if node_id in self.estado_anterior_equipos:

                                    alerta_enviada = (
                                        self.estado_anterior_equipos[
                                            node_id
                                        ].get(
                                            "alerta_enviada",
                                            False
                                        )
                                    )

                                estado_actual_eq[node_id] = {
                                    "nombre": nombre,
                                    "es_encendido": es_encendido,
                                    "alerta_enviada": alerta_enviada
                                }

                                if node_id in self.estado_anterior_equipos:

                                    estaba_encendido = (
                                        self.estado_anterior_equipos[
                                            node_id
                                        ]["es_encendido"]
                                    )

                                    # Equipo se apagó
                                    if (
                                        estaba_encendido
                                        and not es_encendido
                                        and not alerta_enviada
                                    ):

                                        self.enviar_alerta_telegram(
                                            "⚠️ ALERTA INFRAESTRUCTURA SDN ⚠️\n\n"
                                            f"El equipo [{nombre}] "
                                            "se encuentra inactivo "
                                            "(Apagado)."
                                        )

                                        estado_actual_eq[
                                            node_id
                                        ]["alerta_enviada"] = True

                                    # Equipo volvió a encender
                                    elif (
                                        not estaba_encendido
                                        and es_encendido
                                    ):

                                        self.enviar_alerta_telegram(
                                            "🟢 ESTADO OPERATIVO 🟢\n\n"
                                            f"El equipo [{nombre}] "
                                            "se ha iniciado correctamente."
                                        )

                                        estado_actual_eq[
                                            node_id
                                        ]["alerta_enviada"] = False

                            self.estado_anterior_equipos = (
                                estado_actual_eq
                            )

                        # =================================================
                        # MONITOREO DE ENLACES GNS3
                        # =================================================

                        if resp_links.status_code == 200:

                            links = resp_links.json()

                            links_ids_actuales = set()

                            for link in links:

                                link_id = link.get(
                                    "link_id"
                                )

                                links_ids_actuales.add(
                                    link_id
                                )

                                nodos_link = link.get(
                                    "nodes",
                                    []
                                )

                                if len(nodos_link) == 2:

                                    n1_id = nodos_link[0].get(
                                        "node_id"
                                    )

                                    p1_adapter = nodos_link[0].get(
                                        "adapter_number",
                                        0
                                    )

                                    p1_port = nodos_link[0].get(
                                        "port_number",
                                        0
                                    )

                                    n2_id = nodos_link[1].get(
                                        "node_id"
                                    )

                                    p2_adapter = nodos_link[1].get(
                                        "adapter_number",
                                        0
                                    )

                                    p2_port = nodos_link[1].get(
                                        "port_number",
                                        0
                                    )

                                    n1_nombre = (
                                        self.estado_anterior_equipos
                                        .get(
                                            n1_id,
                                            {}
                                        )
                                        .get(
                                            "nombre",
                                            "Disp A"
                                        )
                                    )

                                    n2_nombre = (
                                        self.estado_anterior_equipos
                                        .get(
                                            n2_id,
                                            {}
                                        )
                                        .get(
                                            "nombre",
                                            "Disp B"
                                        )
                                    )

                                    if p1_adapter > 0:
                                        port_name_1 = (
                                            f"Gi0/"
                                            f"{p1_adapter}/"
                                            f"{p1_port}"
                                        )
                                    else:
                                        port_name_1 = (
                                            f"Gi0/{p1_port}"
                                        )

                                    if p2_adapter > 0:
                                        port_name_2 = (
                                            f"Gi0/"
                                            f"{p2_adapter}/"
                                            f"{p2_port}"
                                        )
                                    else:
                                        port_name_2 = (
                                            f"Gi0/{p2_port}"
                                        )

                                    par_puerto = (
                                        f"{n1_nombre} "
                                        f"({port_name_1}) <-> "
                                        f"{n2_nombre} "
                                        f"({port_name_2})"
                                    )

                                    n1_activo = (
                                        self.estado_anterior_equipos
                                        .get(
                                            n1_id,
                                            {}
                                        )
                                        .get(
                                            "es_encendido",
                                            True
                                        )
                                    )

                                    n2_activo = (
                                        self.estado_anterior_equipos
                                        .get(
                                            n2_id,
                                            {}
                                        )
                                        .get(
                                            "es_encendido",
                                            True
                                        )
                                    )

                                    estado_actual_link = (
                                        "Up"
                                        if (
                                            n1_activo
                                            and n2_activo
                                        )
                                        else
                                        "Down"
                                    )

                                    if (
                                        link_id
                                        in self.estado_anterior_puertos
                                    ):

                                        estado_anterior_link = (
                                            self.estado_anterior_puertos[
                                                link_id
                                            ]["estado"]
                                        )

                                        if (
                                            estado_anterior_link
                                            == "Up"
                                            and
                                            estado_actual_link
                                            == "Down"
                                        ):

                                            self.enviar_alerta_telegram(
                                                "🔴 INTERFAZ DOWN 🔴\n\n"
                                                f"El enlace [{par_puerto}] "
                                                "ha cambiado a estado: DOWN."
                                            )

                                        elif (
                                            estado_anterior_link
                                            == "Down"
                                            and
                                            estado_actual_link
                                            == "Up"
                                        ):

                                            self.enviar_alerta_telegram(
                                                "🟢 INTERFAZ UP 🟢\n\n"
                                                f"El enlace [{par_puerto}] "
                                                "se ha restablecido a estado: UP."
                                            )

                                    self.estado_anterior_puertos[
                                        link_id
                                    ] = {
                                        "estado": estado_actual_link,
                                        "par": par_puerto
                                    }

                            # =================================================
                            # DETECTAR ENLACES ELIMINADOS
                            # =================================================

                            links_anteriores = list(
                                self.estado_anterior_puertos.keys()
                            )

                            for lid in links_anteriores:

                                if lid not in links_ids_actuales:

                                    par_info = (
                                        self.estado_anterior_puertos[
                                            lid
                                        ].get(
                                            "par",
                                            "Enlace de Red"
                                        )
                                    )

                                    if (
                                        self.estado_anterior_puertos[
                                            lid
                                        ]["estado"]
                                        == "Up"
                                    ):

                                        self.enviar_alerta_telegram(
                                            "🔴 INTERFAZ DOWN "
                                            "(DESCONECTADO) 🔴\n\n"
                                            f"El enlace físico "
                                            f"[{par_info}] "
                                            "ha sido interrumpido."
                                        )

                                    del self.estado_anterior_puertos[
                                        lid
                                    ]

                except Exception as e:

                    print(
                        f"[FLOWGUARD] Error en ciclo de monitoreo: "
                        f"{e}"
                    )

                # Actualizar el estado global para el Dashboard Web
                try:
                    self._sincronizar_estado_global_con_gns3_y_cli_y_ping()
                except Exception as e2:
                    print(f"[FLOWGUARD] error actualizando dashboard web: {e2}")

                time.sleep(5)

        hilo = threading.Thread(
            target=bucle_monitoreo,
            daemon=True
        )

        hilo.start()

    def sincronizar_con_gns3_local(self):
        try:
            project_id = self.obtener_proyecto_activo()
            lista_dispositivos = []

            if project_id:
                nodes_resp = requests.get(f"{self.GNS3_URL}/projects/{project_id}/nodes", timeout=2)
                links_resp = requests.get(f"{self.GNS3_URL}/projects/{project_id}/links", timeout=2)
                
                puertos_por_nodo = {}
                if links_resp.status_code == 200:
                    for link in links_resp.json():
                        for ln in link.get("nodes", []):
                            nid = ln.get("node_id")
                            adapter = ln.get("adapter_number", 0)
                            port = ln.get("port_number", 0)
                            p_str = f"Gig0/{adapter}/{port}" if adapter > 0 else f"Gi0/{port}"
                            if nid not in puertos_por_nodo:
                                puertos_por_nodo[nid] = []
                            if p_str not in puertos_por_nodo[nid]:
                                puertos_por_nodo[nid].append(p_str)

                if nodes_resp.status_code == 200:
                    nodes = nodes_resp.json()
                    
                    for node in nodes:
                        nombre = node.get("name", "")
                        if "cloud" in nombre.lower():
                            continue

                        raw_status = str(node.get("status", "")).lower()
                        node_id = node.get("node_id")
                        
                        es_encendido = raw_status in ["started", "running", "on"]
                        estado_texto = "Conectado" if es_encendido else "Apagado"
                            
                        nombre_lower = nombre.lower()
                        if (
                            "router" in nombre_lower or "mikrotik" in nombre_lower
                            or "core" in nombre_lower
                            or re.fullmatch(r"r\d+.*", nombre_lower)
                        ):
                            imagen_tipo = "router.png"
                        elif (
                            "switch" in nombre_lower or "asw" in nombre_lower
                            or "dsw" in nombre_lower
                            or re.fullmatch(r"sw\d+.*", nombre_lower)
                            or "switch" in nombre_lower
                        ):
                            imagen_tipo = "switch.png"
                        else:
                            imagen_tipo = "pc.png"

                        console_host = node.get("console_host", "127.0.0.1")
                        if not console_host or console_host == "0.0.0.0":
                            console_host = "127.0.0.1"
                            
                        pto_consola = node.get("console", 5003)
                        puertos_activos = puertos_por_nodo.get(node_id, ["Gi0/1", "Gi0/2"])

                        if "modem" in nombre_lower:
                            orden = 1
                        elif re.fullmatch(r"r\d+.*", nombre_lower) or "router" in nombre_lower or "core" in nombre_lower:
                            orden = 2
                        elif "dsw1" in nombre_lower or "distribucion1" in nombre_lower:
                            orden = 4
                        elif "dsw2" in nombre_lower or "distribucion2" in nombre_lower:
                            orden = 5
                        elif "asw1" in nombre_lower or "acceso1" in nombre_lower:
                            orden = 6
                        elif "asw2" in nombre_lower or "acceso2" in nombre_lower:
                            orden = 7
                        elif "switch" in nombre_lower or re.fullmatch(r"sw\d+.*", nombre_lower):
                            orden = 3
                        else:
                            orden = 8

                        lista_dispositivos.append({
                            "nombre": nombre,
                            "ip": console_host,
                            "puerto_telnet": pto_consola,
                            "puertos": puertos_activos,
                            "estado": estado_texto,
                            "imagen": imagen_tipo,
                            "orden": orden
                        })
            
            lista_dispositivos.sort(key=lambda x: x["orden"])
            with open("devices.json", "w") as f:
                json.dump(lista_dispositivos, f, indent=4)

        except Exception as e:
            print(f"[GNS3 Sync Error]: {e}")

    def cargar_imagen_equipo(self, tipo_img):
        if tipo_img in self.imagenes_cache:
            return self.imagenes_cache[tipo_img]

        if not os.path.exists(tipo_img):
            w, h = 46, 46
            img_base = Image.new("RGBA", (w, h), (6, 10, 20, 0))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img_base)
            if "router" in tipo_img:
                draw.rounded_rectangle([4, 12, w - 4, h - 12], radius=4,
                                       fill=(15, 28, 54, 255),
                                       outline=(34, 211, 238, 230), width=2)
                draw.rounded_rectangle([5, 13, w - 5, 17], radius=2,
                                       fill=(11, 18, 36, 255))
                for (x, col) in [(9, (16, 185, 129, 255)),
                                 (16, (245, 158, 11, 255)),
                                 (23, (34, 211, 238, 255))]:
                    draw.ellipse([x, 25, x + 5, 30], fill=col)
                    draw.ellipse([x, 30.5, x + 5, 35.5], fill=col)
                draw.polygon([(w // 2, 3), (w // 2 - 4, 12), (w // 2 + 4, 12)],
                             fill=(34, 211, 238, 220))
                draw.polygon([(7, 3), (3, 12), (11, 12)], fill=(99, 102, 241, 200))
                draw.polygon([(w - 7, 3), (w - 3, 12), (w - 11, 12)], fill=(99, 102, 241, 200))
            elif "switch" in tipo_img:
                draw.rounded_rectangle([3, 15, w - 3, h - 15], radius=4,
                                       fill=(12, 26, 44, 255),
                                       outline=(52, 211, 153, 230), width=2)
                draw.rounded_rectangle([4, 16, w - 4, 20], radius=2,
                                       fill=(8, 14, 28, 255))
                cols = 8
                gap = (w - 9) / cols
                for i in range(cols):
                    x0 = 5 + i * gap
                    x1 = x0 + gap - 2
                    draw.rounded_rectangle([x0, 24, x1, 29], radius=1, fill=(16, 185, 129, 220))
                    draw.rounded_rectangle([x0, 31, x1, 36], radius=1, fill=(16, 185, 129, 220))
                draw.line([(w // 2, h - 14), (w // 2, h - 6)],
                          fill=(52, 211, 153, 220), width=2)
            else:
                draw.rounded_rectangle([6, 6, w - 6, 30], radius=4,
                                       fill=(22, 34, 65, 255),
                                       outline=(169, 179, 209, 220), width=2)
                draw.rounded_rectangle([9, 9, w - 9, 27], radius=2,
                                       fill=(11, 18, 36, 255))
                draw.rectangle([12, 31, w - 12, 34], fill=(79, 96, 125, 255))
                draw.rounded_rectangle([10, 34, w - 10, 40], radius=2,
                                       fill=(51, 65, 92, 255),
                                       outline=(100, 116, 139, 200), width=1)
                try:
                    from PIL import ImageFont
                    try:
                        f = ImageFont.truetype("Arial Bold.ttf", 9)
                    except Exception:
                        f = ImageFont.load_default()
                    draw.text((13, 11), "NOC", fill=(34, 211, 238, 230), font=f)
                except Exception:
                    pass

            ctk_img = ctk.CTkImage(light_image=img_base, dark_image=img_base, size=(w, h))
            self.imagenes_cache[tipo_img] = ctk_img
            return ctk_img
        else:
            try:
                img = Image.open(tipo_img).resize((42, 42))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                self.imagenes_cache[tipo_img] = ctk_img
                return ctk_img
            except Exception:
                return None

    def actualizar_dispositivos(self):
        self.sincronizar_con_gns3_local()

        for widget in self.scroll_rack.winfo_children():
            widget.destroy()

        if os.path.exists("devices.json"):
            try:
                with open("devices.json", "r") as f:
                    dispositivos = json.load(f)

                for d in dispositivos:
                    estado_disp = d.get('estado', 'Apagado')
                    online = (estado_disp == "Conectado")
                    color_borde = "#10B981" if online else "#EF4444"
                    nombre_disp = d.get('nombre', '')
                    tipo_img = d.get('imagen', 'router.png')

                    slot_frame = ctk.CTkFrame(
                        self.scroll_rack,
                        corner_radius=10,
                        border_width=2,
                        border_color=color_borde,
                        fg_color="#0E1630" if online else "#18121F",
                        height=72
                    )
                    slot_frame.pack(fill="x", padx=10, pady=5)
                    slot_frame.pack_propagate(False)

                    img_icon = self.cargar_imagen_equipo(tipo_img)
                    lbl_icono = ctk.CTkLabel(slot_frame, text="", image=img_icon)
                    lbl_icono.pack(side="left", padx=(12, 8), pady=6)

                    info_centro = ctk.CTkFrame(slot_frame, fg_color="transparent")
                    info_centro.pack(side="left", fill="both", expand=True, pady=5)

                    ip_actual = d.get('ip', '127.0.0.1')
                    pto_telnet = str(d.get('puerto_telnet', '5003'))

                    linea_superior = f"{nombre_disp.upper()}    ·    IP: {ip_actual}    ·    CLI: {pto_telnet}"
                    ctk.CTkLabel(info_centro, text=linea_superior,
                                 font=("Arial", 11, "bold"),
                                 text_color="#E6EEFB").pack(anchor="w", pady=(1, 0))

                    puertos_lista = d.get('puertos', ['Gi0/1', 'Gi0/2'])
                    estado_puerto_txt = "Up" if online else "Down"
                    color_puerto_txt = "#86EFAC" if online else "#FCA5A5"

                    ports_str = "    ·    ".join([f"{p}: {estado_puerto_txt}" for p in puertos_lista[:6]])
                    ctk.CTkLabel(info_centro, text=f"Puertos: {ports_str}",
                                 font=("Consolas", 9.5),
                                 text_color=color_puerto_txt).pack(anchor="w", pady=(0, 2))

                    action_frame = ctk.CTkFrame(slot_frame, fg_color="transparent")
                    action_frame.pack(side="right", padx=10, pady=6)

                    estado_label = "● Conectado" if online else "● Apagado"
                    lbl_est = ctk.CTkLabel(action_frame, text=estado_label,
                                           font=("Arial", 10, "bold"),
                                           text_color="#10B981" if online else "#EF4444",
                                           corner_radius=18,
                                           fg_color="#0E2C20" if online else "#2B1414",
                                           padx=10, pady=3)
                    lbl_est.pack(side="left", padx=(0, 10))

                    def crear_comando_putty(host=ip_actual, port=pto_telnet):
                        def abrir_putty():
                            try:
                                ruta_putty = r"C:\Program Files\PuTTY\putty.exe"
                                if not os.path.exists(ruta_putty):
                                    ruta_putty = r"C:\Program Files (x86)\PuTTY\putty.exe"
                                subprocess.Popen([ruta_putty, "-telnet", host, str(port)])
                            except Exception as ex:
                                messagebox.showerror("Error", f"No se pudo abrir PuTTY: {ex}")
                        return abrir_putty

                    btn_config = ctk.CTkButton(
                        action_frame,
                        text="🖥️  CLI Telnet",
                        command=crear_comando_putty(),
                        fg_color="#F97316",
                        hover_color="#EA580C",
                        font=("Arial", 10, "bold"),
                        corner_radius=8,
                        height=34,
                        width=112
                    )
                    btn_config.pack(side="left", padx=(6, 0))

            except Exception as e:
                print(f"[RACK] error actualizar: {e}")

        self.after(3000, self.actualizar_dispositivos)


if __name__ == "__main__":
    login = LoginApp()
    login.mainloop()