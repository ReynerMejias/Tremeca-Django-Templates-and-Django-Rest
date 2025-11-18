🚀 Tremeca Backend – Django + Django REST Framework

Sistema backend diseñado para automatizar el registro, control y facturación del servicio de agua en TREMECA M&M S.A., reemplazando procesos manuales basados en talonarios, listas en papel y hojas de Excel.

Este backend expone una API REST completa para administrar clientes, lecturas, pagos y generación de recibos, e integra autenticación por roles para proteger cada módulo del sistema.

💡 Características principales

📌 Gestión de clientes (lotes, medidores, lectura anterior, sector)

📈 Registro de lecturas mensuales desde app móvil (React Native)

🧾 Generación automática de recibos PDF

💰 Control de pagos, historial y estado de cuenta

👤 Sistema de usuarios y roles (Admin, Lector, Cajero)

🗄️ Modelo relacional optimizado (MySQL)

🔐 Autenticación por tokens / JWT

📊 Panel web administrativo (Bootstrap)

📱 Integración con app móvil para registro en campo

🧠 Tecnologías utilizadas

Django 5.x

Django REST Framework

MySQL

Bootstrap 5 (panel web)

React Native (módulo móvil complementario)

ORM de Django

API REST con permisos por vista

📦 Arquitectura del sistema
/tremeca-backend
│── api/
│   ├── clientes/
│   ├── lecturas/
│   ├── pagos/
│   ├── usuarios/
│   └── lugares/
│
│── core/
│── settings/
│── templates/ (panel admin)
│── static/
│── utils/ (generación de PDFs y helpers)
│── requirements.txt
│── manage.py

🗃️ Modelo de datos (ERD)

Basado en el diseño relacional de la tesis y optimizado para Django ORM.

Incluye entidades clave:

Cliente

Lectura

Pago

Lugar

Solicitud

Usuario

👉 (Agregar aquí la imagen del ERD: docs/erd.png)

🔁 Diagramas de flujo
Proceso actual (antes del sistema)

Uso de listas, papel y Excel

180 minutos por ciclo

20% de error en facturación

👉 (Agregar imagen: docs/flujo-actual.png)

Proceso optimizado con Tremeca

Lectura desde app móvil

Cálculo automático del total

Recibos generados digitalmente

Sin duplicación de datos ni pérdidas

👉 (Agregar imagen: docs/flujo-mejorado.png)

📊 Resultados obtenidos
✔ Reducción de errores:

20% → menor al 5%

✔ Reducción del tiempo de facturación:

180 minutos → 30 minutos

👉 (Agregar gráficos: docs/errores.png, docs/tiempos.png)

🔐 Autenticación y Roles

El sistema implementa control de permisos basado en grupos:

Rol	Permisos principales
Admin	CRUD completo de clientes, lecturas, pagos, usuarios, lugares
Cajero	Registrar pagos, ver historial y estado de cuenta
Lector	Registrar lecturas, ver clientes asignados
🧾 Endpoints principales (API REST)

(Ejemplos abreviados; puedo generar la documentación completa en Swagger si querés)

Clientes
GET    /api/clientes/
POST   /api/clientes/
PUT    /api/clientes/{id}/
DELETE /api/clientes/{id}/

Lecturas
POST   /api/lecturas/
GET    /api/lecturas/{cliente_id}/historial/

Pagos
POST   /api/pagos/
GET    /api/pagos/{cliente_id}/

Usuarios
POST   /api/auth/login/
GET    /api/usuarios/

🧾 Generación de Recibos

El backend genera automáticamente un PDF térmico de 80mm compatible con impresoras POS.

Características:

Monto calculado en base al valor por metro cúbico del lugar

Nombre del cliente, lote y medidor

Última y nueva lectura

Fecha de emisión

Espacio para impresión térmica

⚙️ Instalación
git clone https://github.com/reynerMG/tremeca-backend.git
cd tremeca-backend

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

🤝 Contribuciones

Este proyecto forma parte de la modernización operativa de TREMECA M&M S.A., pero está abierto a mejoras en arquitectura, seguridad y optimización.

👨‍💻 Autor

Reyner Mejías
Desarrollador Backend – Django / DRF
📍 Costa Rica
📧 (tu correo o red social)
