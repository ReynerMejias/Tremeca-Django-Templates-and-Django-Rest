Tremeca Backend – Django + DRF

Sistema backend diseñado para automatizar el registro, control y
facturación del servicio de agua en TREMECA M&M S.A. Reemplaza procesos
manuales basados en listas, papel y hojas de Excel.

El backend expone una API REST completa, con autenticación por roles,
manejo de clientes, lecturas, pagos y generación de recibos PDF.

Características principales

-   Gestión completa de clientes (lote, medidor, lectura anterior,
    sector)
-   Registro de lecturas desde app móvil (React Native)
-   Cálculo automático del consumo mensual
-   Generación de recibos PDF compatibles con impresoras térmicas
-   Control de pagos, historial y estado de cuenta
-   Sistema de usuarios y roles (Admin, Lector, Cajero)
-   Panel web administrativo (Bootstrap)
-   Base de datos relacional optimizada (MySQL)
-   Autenticación segura con permisos por vista

Tecnologías utilizadas

-   Django 5.x
-   Django REST Framework
-   MySQL
-   Bootstrap 5
-   React Native
-   ORM de Django
-   API REST con permisos por grupos

Arquitectura del proyecto

/tremeca-backend api/ clientes/ lecturas/ pagos/ usuarios/ lugares/
core/ settings/ templates/ static/ utils/ requirements.txt manage.py

Modelo de datos (ERD)

(Agregar imagen erd.png)

Diagramas de flujo

Proceso actual: - Uso de talonarios y listas impresas - 180 minutos por
ciclo - 20% de error

Proceso optimizado: - Registro desde app móvil - Cálculo automático -
Recibo digital

Impacto del sistema

-   Reducción de errores: 20% → <5%
-   Reducción del tiempo: 180 min → 30 min

Roles y permisos

Admin: CRUD total
Cajero: pagos
Lector: lecturas

Endpoints principales

Clientes: GET /api/clientes/ POST /api/clientes/ PUT /api/clientes/{id}/
DELETE /api/clientes/{id}/

Lecturas: POST /api/lecturas/ GET /api/lecturas/{cliente_id}/historial/

Pagos: POST /api/pagos/ GET /api/pagos/{cliente_id}/

Usuarios: POST /api/auth/login/ GET /api/usuarios/

Instalación

git clone repo pip install -r requirements.txt python manage.py migrate
python manage.py runserver
