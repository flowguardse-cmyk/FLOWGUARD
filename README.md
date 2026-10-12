<div align="center">

# ⚡ FLOWGUARD · Network Operations Center (NOC)
### Consola de Monitoreo en Tiempo Real para Redes SDN con GNS3
**Versión 2.0 · Rediseño NOC Profesional**

</div>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white">
  <img alt="CustomTkinter" src="https://img.shields.io/badge/CustomTkinter-6.0-282C34">
  <img alt="GNS3" src="https://img.shields.io/badge/GNS3-API%20v2-C9092E?logo=gns3&logoColor=white">
  <img alt="Estado" src="https://img.shields.io/badge/Estado-Produccion%20Local-10B981">
  <img alt="Plataforma" src="https://img.shields.io/badge/Plataforma-Windows%2010/11-0078D6?logo=windows">
</p>

---

## 🎯 Descripción General

**FLOWGUARD** es un sistema de monitoreo de redes **SDN (Software Defined Networking)** desarrollado en Python que integra **GNS3** (API v2), **Cisco IOS CLI real (Telnet)**, **Ping ICMP** y alertas **Telegram** para ofrecer un **Network Operations Center (NOC)** unificado con **dos interfaces simultáneas**:

1. **Dashboard Desktop (CustomTkinter)** — ventana nativa de Windows con Rack 19" virtual
2. **Dashboard Web (Flask)** — panel responsive en `http://127.0.0.1:5000` con 3 gráficos Chart.js

Ambos paneles se actualizan automáticamente cada **3-5 segundos** sin necesidad de refrescar.

---

## ✨ Características Principales

| Funcionalidad | Detalle |
|---|---|
| 🔍 **Inventario automático** | Sincroniza todos los dispositivos del proyecto GNS3 abierto (routers, switches, hosts, servidores, Kali) |
| 🟢🔴 **Estado GNS3 en vivo** | Detecta encendido/apagado de nodos en segundos |
| 📡 **Ping ICMP real** | Monitoreo de latencia contra el IP de gestión de cada dispositivo |
| 🖥️ **Integración Cisco CLI** | Extrae interfaces, IPs, estado admin/link, CPU 5s/1m/5m, Hostname, Versión IOS, Uptime por Telnet |
| 🔔 **Alertas Telegram** | Avisa en el momento: login exitoso/fallido, encendido/apagado de nodos, interfaces UP/DOWN, ping offline |
| 🌐 **Rack 19" visual** | Representación gráfica de equipos igual que un rack físico (Desktop + Web) |
| 📊 **3 gráficos interactivos** | Doughnut equipos, Doughnut interfaces, Barras horizontales de Ping por equipo |
| 🔎 **Vista detalle por equipo** | Panel individual con 4 KPIs + Info General + Gráfico doughnut + Tabla interfaces |
| 🚀 **Apertura 1-click de CLI** | Integración nativa con PuTTY (x64/x86) vía Telnet |
| 🔐 **Login seguro** | Usuario/contraseña + 2FA visual (delay 450ms "Validando…") + aviso Telegram |
| ⚡ **Launcher 1-click** | `.bat` que evita problemas de ExecutionPolicy y alias Python de Microsoft Store |

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLOWGUARD (Python 3.10)                      │
├─────────────────────┬─────────────────────┬─────────────────────┤
│  LOGIN + DESKTOP    │   HILO MONITOREO    │  SERVIDOR WEB FLASK │
│  CustomTkinter 6.0  │   (Thread daemon)   │  :5000 / HTTP API   │
│  Panel + Rack 19"   │                     │  dashboard.html     │
└──────┬──────────────┴──┬──────────┬────────┴──┬──────────────────┘
       │                 │          │           │
       ├─────────────────┴──────────┴───────────┤
       ▼                ▼           ▼           ▼
   🟩 GNS3 API   📡 Ping ICMP  📞 Telnet    🤖 Telegram Bot
   :3080/v2       Windows      Cisco IOS    Bot API
```

### 🛠️ Stack Tecnológico
| Capa | Tecnología | Versión |
|---|---|---|
| **Lenguaje** | Python | >= 3.10 |
| **UI Desktop** | CustomTkinter | 6.0.0 |
| **UI Web** | Flask (Jinja2) + Chart.js | 3.1.3 |
| **Imágenes** | Pillow (CTkImage compatible HighDPI) | 12.3.0 |
| **APIs HTTP** | Requests | 2.34.2 |
| **Simulación de Red** | GNS3 (API v2) | >= 2.2 |
| **Dispositivos** | Cisco IOS (Dynamips/IOL/VIRL) | Cualquiera |
| **Notificaciones** | Telegram Bot API | HTTPS |
| **Cliente Telnet** | PuTTY | >= 0.70 |
| **Monitoreo Extra (Opcional)** | Grafana | :3000 |

---

## 🚀 Instalación y Primer Uso

### 📋 Prerrequisitos
1. **Windows 10/11** (el launcher `.bat` y paths de PuTTY son Windows-only)
2. **GNS3 >= 2.2** instalado y ejecutándose en `http://localhost:3080`
3. **PuTTY** instalado en una de estas rutas (auto-detectado):
   - `C:\Program Files\PuTTY\putty.exe` (x64)
   - `C:\Program Files (x86)\PuTTY\putty.exe` (x86)
4. **Bot de Telegram** (opcional pero recomendado para alertas)

### 1️⃣ Clonar / Preparar el proyecto
```powershell
# Si clonas de GitHub:
git clone https://github.com/TU_USUARIO/FLOWGUARD.git
cd FLOWGUARD

# O si usas la carpeta local actual:
cd c:\FLOWGUARD-PRUEBA
```

### 2️⃣ Crear entorno virtual e instalar dependencias
```powershell
# Crear entorno (solo 1 vez)
py -3.10 -m venv venv

# Instalar dependencias desde requirements.txt
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3️⃣ Configurar tokens Telegram *(paso opcional)*
Abre `flowguard.py` y actualiza estas líneas con tus credenciales reales (busca por `BOT_TOKEN`):
```python
TELEGRAM_BOT_TOKEN_LOGIN = "TU_TOKEN_AQUI"
TELEGRAM_CHAT_ID_LOGIN = "TU_CHAT_ID_AQUI"
TELEGRAM_BOT_TOKEN_PANEL = "TU_TOKEN_AQUI"
TELEGRAM_CHAT_ID_PANEL = "TU_CHAT_ID_AQUI"
```

### 4️⃣ Arrancar GNS3
1. Abre GNS3 y carga tu proyecto
2. Arranca los dispositivos Cisco y espera hasta que aparezca el prompt (`R1#`, `SW1#`)
3. Verifica manualmente que `http://localhost:3080/v2/projects` responda con tu proyecto

### 5️⃣ Lanzar FLOWGUARD (¡2 opciones!)

#### 🥇 Método Recomendado: **Doble clic**
Solo haz **doble clic** en el archivo:
👉 **`▶ EJECUTAR_FLOWGUARD.bat`**

*Evita todos los problemas de ExecutionPolicy y alias Python de Windows.*

#### 🥈 Método Consola PowerShell
```powershell
cd c:\FLOWGUARD-PRUEBA
& .\venv\Scripts\python.exe .\flowguard.py
```

### 6️⃣ ¡Listo para usar!
```
Usuario:      admin
Contraseña:   sdn2026
```

---

## 🖥️ Interfaz Desktop (CustomTkinter)

### Login
```
┌───────────────────────┬───────────────────────────────────┐
│  ⚡ FLOWGUARD · NOC   │  🔐 INICIAR SESIÓN                │
│  (fondo NOC con nodos │  • Usuario                        │
│   + estado servicios) │    [admin          (foco cian ✨)] │
│                       │  • Contraseña                     │
│  ● MONITOREO 24h      │    [••••••••••]                    │
│  v2 · NOC R1          │  ⚡ Acceder al Sistema            │
└───────────────────────┴───────────────────────────────────┘
```

### Panel Principal
```
┌─ TOPBAR ──────────────────────────────────────────────────────┐
│  ⚡ FLOWGUARD     🟢 GNS3 OK  🔵 MONITOR LIVE  👤 admin   🕒  │
├─ KPI STRIP (6) ───────────────────────────────────────────────┤
│  Equipos 4  │  UP 2  │  DOWN 2  │  Ping 14ms │ Alertas 0 │ … │
├─ RACK 19" VIRTUAL ───────────────────────────────────────────┤
│  ┌─ R1 (Router) ─────────────────────────────────┐            │
│  │ 📡 FLOW1  · 192.168.50.2  CPU 1%   ● UP       │ 🖥️ CLI │  │
│  └────────────────────────────────────────────────┘            │
│  ┌─ SW1 (Switch) ─────────────────────────────────┐           │
│  │ 🔁 FLOWGUARD-SW01 · 192.168.56.109:5001 ● UP  │ 🖥️ CLI │  │
│  └────────────────────────────────────────────────┘            │
│  (Kali Linux, Windows Server — rojo ● OFFLINE)                 │
├─ BARRA INFERIOR ──────────────────────────────────────────────┤
│  ● Telegram OK  ● Polling 5s  ● Dashboard Web :5000  [Grafana][Dashboard Web] │
└───────────────────────────────────────────────────────────────┘
```

---

## 🌐 Interfaz Web (Flask)

Abre tu navegador en **http://127.0.0.1:5000** luego de iniciar sesión en Desktop.

### Rutas HTTP Disponibles
| Ruta | Método | Descripción |
|---|---|---|
| `/` | `GET` | Dashboard principal (Rack + KPIs + 3 gráficos + Inventario + Alertas) |
| `/detalle/<node_id>` | `GET` | Panel detalle individual por equipo |
| `/api/estado` | `GET` | JSON completo con telemetría global (equipos, KPIs, alertas) |
| `/api/equipo/<node_id>` | `GET` | JSON de un único equipo con interfaces CLI |
| `/api/abrir-cli?host=&port=` | `GET` | Abre PuTTY local y devuelve JSON con link `telnet://` |
| `/api/abrir-grafana` | `GET` | Abre Grafana :3000 en nueva pestaña |

---

## 🔔 Eventos Avisados por Telegram

FLOWGUARD envía un mensaje a tu bot de Telegram en estos casos:

| Evento | Prioridad |
|---|---|
| 🔓 **Login exitoso** | Informativa |
| ❌ **Login fallido** | Alta (credenciales mal) |
| 🟢 **Nodo encendido** | Informativa |
| 🔴 **Nodo apagado / inactivo** | Alta |
| 🟠 **Ping OFFLINE 2 ciclos** | Media |
| 🔵 **Interfaz cambia DOWN / UP** | Alta |

---

## 📁 Estructura del Repositorio

```
FLOWGUARD/
├── 📄 flowguard.py                     # Código principal (Login + Panel + Flask + Hilo Monitoreo)
├── 📄 requirements.txt                 # Dependencias Python (17 paquetes)
├── 📄 .gitignore                       # Reglas ignore de Git
├── 📄 README.md                        # Este archivo
├── 📁 static/
│   └── style.css                       # Paleta NOC + layout responsive + tokens de diseño
├── 📁 templates/
│   ├── dashboard.html                  # Panel principal web (Chart.js + Rack Grid 2-col)
│   └── detalle_equipo.html             # Panel detalle individual por equipo
├── 🖼️ router.png                      # Ícono router Rack Desktop
├── 🖼️ switch.png                      # Ícono switch Rack Desktop
└── 📄 ▶ EJECUTAR_FLOWGUARD.bat         # Launcher Windows 1-click (sin PowerShell)
```

---

## 🧪 Cómo Probar la Aplicación

### Checklist Básico de Validación
- [ ] **Login Desktop** se abre sin warnings de `intro.gif`
- [ ] Hacer **focus** en los inputs → borde CIÁN `#22D3EE` + fondo oscuro
- [ ] Botón "Acceder" → se pone **púrpura "Validando…" 450ms** antes de entrar
- [ ] **Topbar** del panel muestra badges: `🟢 GNS3 API: OK · 🔵 MONITOR LIVE · 👤 admin`
- [ ] **KPIs Strip**: aparecen los 6 indicadores en menos de 10s
- [ ] **Rack virtual**: equipos Cisco aparecen con borde **VERDE**, hosts apagados en **ROJO**
- [ ] Clic en **🖥️ CLI** → abre PuTTY correctamente al host:puerto de GNS3
- [ ] Dashboard Web `http://127.0.0.1:5000`: 2 columnas Rack + Alertas y 3 gráficos se ven bien
- [ ] Clic en **🔍 DETALLES** del SW1 → se ven **32 interfaces** en la tabla + doughnut 32UP/11DOWN
- [ ] En GNS3, **apagar R1**: alerta Telegram + cambia a rojo en Desktop + Web en 5s

---

## 🖼️ Recursos de Imagen Opcionales

**Ninguna es obligatoria** (el código genera íconos vectoriales por Pillow y fondos CSS por defecto). Pero si quieres un acabado premium, agrega:

| Archivo | Medida | Propósito |
|---|---|---|
| `intro.gif` | 380 × 420 | Fondo animado del panel izquierdo del login (reemplaza dibujo Pillow) |
| `pc.png` | 48 × 48 · RGBA transparente | Ícono alternativo para dispositivos host en el rack |

---

## 🔐 Seguridad y Buenas Prácticas

1. **Tokens Telegram**: Antes de subir a repositorio PÚBLICO, mueve los hardcodeados a un archivo `.env` usando `python-dotenv` (ya instalado):
   ```python
   # .env (NO SUBIR A GITHUB)
   TELEGRAM_BOT_TOKEN=123456:ABC...
   TELEGRAM_CHAT_ID=987654321
   ```
2. `.gitignore` ya incluye `.env` para evitar fugas de credenciales.
3. El sistema usa `textContent` + `escapeHtml` en plantillas para evitar XSS en nombres de equipos.
4. Login solo permite credenciales hardcodeadas (para laboratorio local). Para producción, integra Flask-Login.

---

## 🗺️ Roadmap y Mejoras Futuras

- [ ] **Login Web** paralelo al desktop
- [ ] **Topología visual** (grafo de nodos interconectados con D3.js o vis.js)
- [ ] **Exportar PDF**: informe de estado de red por email
- [ ] **Base de datos SQLite**: historial de métricas + gráficos de tendencia de CPU/ping
- [ ] **Soporte Linux**: desacoplar PuTTY y usar telnetlib/PyTe para CLI web embebido
- [ ] **Sistema de usuarios multi-rol**: administrador / operador / solo lectura

---

## 🤝 Contribución

¿Encontraste un bug o quieres agregar una feature?
1. Haz **Fork** del repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Haz commit de tus cambios: `git commit -m 'feat: agrega X funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abre un **Pull Request** describiendo el cambio

---

## 📝 Notas de Versión

### `v2.0 (2026-10-08)` — Rediseño NOC
- ✅ **NUEVA paleta de colores profesional** (tokens CSS: `--fg-primary/#22D3EE`, estados semánticos)
- ✅ **NUEVO layout dashboard web**: 2 columnas (Rack + Alertas) + 3 columnas (gráficos) + scroll interno
- ✅ **NUEVOS KPIs compactos** reutilizables (Desktop + Web)
- ✅ **NUEVO topbar** con badges de estado + timestamp de actualización
- ✅ **NUEVA vista detalle**: error amigable cuando la telemetría tarda en cargar (spinner cian + 4 soluciones)
- ✅ **Fix crítico CustomTkinter 6.0**: reemplazo de `focus_border_color` (no existe en v6) por eventos `FocusIn/Out`
- ✅ **Fix crítico HighDPI**: reemplazo de `ImageTk.PhotoImage` por `CTkImage` para íconos del rack + login GIF
- ✅ **NUEVO launcher `▶ EJECUTAR_FLOWGUARD.bat`** a prueba de tontos (no requiere Activate.ps1)
- ✅ Fix `RuntimeError main thread` cuando se destruye el widget antes de un `after()`

### `v1.0` — Versión Base
- Login Desktop básico
- Monitoreo GNS3 + Ping + Alertas Telegram
- Dashboard web inicial (6 KPIs + Rack + Alertas)
- Vista detalle por equipo

---

## 📄 Licencia

Este proyecto se distribuye bajo licencia **MIT** — libre para uso educativo y profesional.

```
Copyright (c) 2026 FLOWGUARD TEAM

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">
  Hecho con 💙 usando Python, CustomTkinter, Flask y GNS3.
  <br>
  <strong>⚡ FLOWGUARD — Network Operations Center</strong>
</div>
