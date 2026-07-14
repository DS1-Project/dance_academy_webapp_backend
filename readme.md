# ⚙️ DanceAcademyApp - Backend API 🛡️

## Descripción

DanceAcademyApp - Backend API es la API REST que soporta todo el ecosistema de DanceAcademyApp. Está diseñada para ofrecer una arquitectura segura, escalable y modular, permitiendo la autenticación de usuarios, el control de acceso basado en roles (RBAC), la gestión transaccional de compras de coreografías y la generación de reportes estadísticos mediante consultas optimizadas sobre bases de datos relacionales.

---

## Tecnologías Utilizadas

- Python 3.11+
- Django 5
- Django REST Framework (DRF)
- PostgreSQL
- Supabase
- JWT (JSON Web Tokens)
- djangorestframework-simplejwt
- Django Test Framework

---

## Estructura del Proyecto

```text
backend/
├── core/                        # Configuración global de Django (settings, urls, wsgi, asgi)
├── apps/                        # Aplicaciones modulares del dominio de negocio
│   ├── authentication/          # Gestión de usuarios, registro, inicio de sesión, JWT y RBAC
│   ├── choreography/            # Catálogo de coreografías, registros de visualización, reseñas y estadísticas
│   └── sales/                   # Facturación, ventas, detalles de compra y simulación de pasarela de pago
├── env/                         # Entorno virtual del proyecto
├── .env                         # Variables de entorno y credenciales locales
├── .env.example                 # Plantilla de variables de entorno requeridas
├── manage.py                    # Interfaz de línea de comandos de Django
└── requirements.txt             # Dependencias del proyecto
```

---

## Configuración e Instalación Local

Siga los pasos descritos a continuación para configurar el entorno y ejecutar el servidor de desarrollo.

### 1. Ingresar al directorio del backend

```bash
cd dance_academy_webapp_backend
```

### 2. Activar el entorno virtual

En Windows (CMD):

```cmd
env\Scripts\activate
```

En Windows (PowerShell):

```powershell
.\env\Scripts\Activate.ps1
```

En macOS, Linux o Git Bash:

```bash
source env/bin/activate
```

Una vez activado el entorno virtual, observará el prefijo `(env)` al inicio de la terminal.

### 3. Instalar las dependencias del proyecto

Actualice `pip` e instale las dependencias requeridas:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

Cree un archivo llamado `.env` en la raíz del proyecto utilizando `.env.example` como referencia.

Ejemplo:

```env
DEBUG=True
SECRET_KEY=your_custom_django_secret_key_here

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_secure_supabase_password
DB_HOST=your_project_reference.supabase.co
DB_PORT=5432
```

Asegúrese de reemplazar los valores de ejemplo por las credenciales correspondientes a su entorno.

### 5. Ejecutar las migraciones

Genere y aplique las migraciones necesarias para crear la estructura de la base de datos:

```bash
python manage.py makemigrations authentication choreography sales
python manage.py migrate
```

### 6. Iniciar el servidor de desarrollo

Ejecute el siguiente comando:

```bash
python manage.py runserver
```

La API estará disponible en:

```text
http://127.0.0.1:8000/api/
```

---

## Pruebas Automatizadas

Para verificar la integridad del sistema, las restricciones de acceso, los permisos definidos por roles y el correcto funcionamiento de los endpoints, ejecute la suite de pruebas:

```bash
python manage.py test
```

---

## Principales Funcionalidades

- Autenticación basada en JWT.
- Control de acceso basado en roles (RBAC).
- Administración de usuarios y perfiles.
- Gestión de coreografías y catálogo musical.
- Registro de visualizaciones y actividad de usuarios.
- Sistema de ventas y facturación.
- Simulación de pasarela de pagos.
- Generación de estadísticas e indicadores comerciales.
- API REST documentada y preparada para integraciones.

---

## Roles del Sistema

La plataforma implementa un modelo de permisos basado en roles para garantizar la seguridad y el acceso adecuado a los recursos.

Roles disponibles:

- Administrador
- Director
- Profesor
- Cliente

Cada rol cuenta con permisos específicos de acuerdo con sus responsabilidades dentro de la plataforma.

---

## Equipo de Desarrollo Backend

- Camilo Andrés Riscanevo Cotrina
- Brayan Fernando Cruz Puerta
- Freddy Alexander Melo Buitrago
- Victoria Yuan Chen
- Yiseiri Yanua Satizábal Ortiz

---

## Licencia

Este proyecto forma parte de DanceAcademyApp y su uso está sujeto a las políticas, acuerdos y condiciones establecidas por el equipo de desarrollo y la organización propietaria del software.
