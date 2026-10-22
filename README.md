# LINK X Sistemas — Control de asistencia en Python

Aplicación web local para laptop desarrollada con Python, Flask y SQLite, con tema azul/amarillo inspirado en Walmart. Es una propuesta independiente; no es un sistema oficial ni implica autorización de Walmart.

## Funciones
- Inicio de sesión con contraseña guardada como hash.
- Registro de entrada, salida, inicio de comida y fin de comida.
- Dashboard con KPI y tabla de movimientos.
- Módulo de usuarios para que el administrador cree cuentas y asigne roles.
- **Código de reportes separado** en `admin_reports.py`, con reportes por rango de fechas y exportación CSV compatible con Excel.
- Seguridad por rol en el servidor: solo `admin` puede entrar a reportes y exportación. Si un colaborador escribe la URL directamente, el servidor responde HTTP 403.

## Instalar en Windows
1. Instala Python 3.10 o posterior.
2. Extrae el ZIP, por ejemplo en `C:\LINKX\asistencia`.
3. Abre PowerShell en esa carpeta y ejecuta:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   py app.py
   ```
4. Abre `http://127.0.0.1:5000` en Chrome o Edge.

## Cuenta inicial de administrador
- Correo: `admin@linkx.local`
- Contraseña temporal: `Admin123!`

La base de datos `asistencia.db` se crea al ejecutar por primera vez. Inicia sesión como administrador y abre **Usuarios** para crear cuentas de colaboradores. Cambia la contraseña temporal antes de usar datos reales.

## Permisos
- **Administrador:** dashboard, usuarios, reportes y exportación CSV.
- **Colaborador:** dashboard y registro de sus movimientos; no ve enlaces de administración y no puede abrir esas rutas directamente.

## Antes de producción
Configura una clave secreta larga con `LINKX_SECRET_KEY`, cambia la contraseña inicial y limita el acceso de red. Este prototipo no incluye MFA, recuperación de contraseña ni integración real con Teams/Excel. No publiques la base de datos ni datos personales en GitHub.
