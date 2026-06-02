# 🧸 PequeMundo Muebles – Plataforma E-Commerce (ASY5131)

Plataforma de comercio electrónico de punta a punta (End-to-End) desarrollada con **Django** para la empresa **PequeMundo Muebles**. El sistema está diseñado para optimizar la venta de muebles infantiles y automatizar todo su flujo logístico, administrativo y financiero, reemplazando por completo el uso de planillas Excel manuales bajo los requerimientos del caso corporativo 2026.

---

## 🚀 Requisitos e Instalación Local

Sigue estos pasos para clonar, configurar y levantar el entorno de desarrollo en tu máquina:

### 1. Clonar el repositorio e instalar dependencias
Abre tu terminal en la carpeta de proyectos y ejecuta:
```bash
# Instalar los paquetes y librerías requeridas
pip install -r requirements.txt

# Aplicar las migraciones de Django
python manage.py migrate

# Iniciar el servidor local de desarrollo
python manage.py runserver

💳 Entorno de Pruebas (Pasarela de Pago Webpay / Transbank)
Para evaluar y simular el flujo del carrito de compras y el Checkout en la pasarela de certificación, utiliza las siguientes tarjetas de prueba:

🟩 Transacción Aprobada
Tarjeta: VISA

Número: 4051 8856 0044 6623

CVV: 123

Fecha de expiración: Cualquier fecha futura

Resultado: El sistema registra el pago y cambia el estado automáticamente a "Pedido recibido".

🟥 Transacción ">Rechazada
Tarjeta: MASTERCARD

Número: 5186 0595 5959 0568

CVV: 123

Fecha de expiración: Cualquier fecha futura

Resultado: Transbank deniega el pago, la transacción se cancela y se notifica el error en pantalla.

🔒 Autenticación Bancaria Simulada (Transbank):
Si la pasarela despliega el formulario de autenticación del banco, utiliza estas credenciales:

RUT: 11.111.111-1

Clave: 123