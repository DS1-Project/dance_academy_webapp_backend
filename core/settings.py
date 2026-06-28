import environ
from pathlib import Path

# 1. Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Inicializar y cargar variables de entorno desde el archivo .env en la raíz
env = environ.Env()
environ.Env.read_env(env_file=str(BASE_DIR / '.env'))

# 3. Configuraciones de Seguridad (Tomadas de forma segura desde el .env)
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.get_value('DEBUG', cast=bool, default=False)
ALLOWED_HOSTS = ['*']  # En desarrollo local permite cualquier host, ideal para pruebas

# 4. Registro de Aplicaciones (Estructura modular con prefijo 'apps.')
INSTALLED_APPS = [
    # Aplicaciones nativas de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Librerías de terceros (API REST y Seguridad)
    'rest_framework',
    'corsheaders',
    
    # Tus módulos de negocio unificados en inglés
    'apps.authentication',  # Maneja Login, Registro, Roles y CRUD interno de usuarios
    'apps.choreography',    # Catálogo de canciones, videos y streaming seguro
    'apps.sales',           # Modelado de Facturación, Ventas y Pasarela simulada
]

# 5. Capa de Seguridad Intermedia (Middlewares)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Debe ir estrictamente arriba para interceptar peticiones CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 6. Enrutamiento y Servidores de Aplicación (Apuntando a la nueva carpeta 'core')
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# 7. Conexión limpia y segura a tu base de datos Supabase (PostgreSQL) via variables del .env
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),  # Pooler Supavisor (IPv4): aws-0-<region>.pooler.supabase.com
        'PORT': env('DB_PORT'),  # 5432 session mode (Django local) o 6543 transaction mode
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# 8. Validadores de contraseñas por defecto de Django
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 9. Apuntar Django a tu modelo de Usuario Personalizado con UUID que crearemos en apps.authentication
AUTH_USER_MODEL = 'authentication.User'

# 10. Configuración Regional (Alineado con Univalle en Cali, Colombia)
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# 11. Configuración de Archivos Estáticos (CSS, JavaScript, Imágenes de la interfaz)
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 12. Permitir conexiones desde tu servidor Front-End de React (usando Vite por defecto)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Puerto estándar de desarrollo de Vite
    "http://127.0.0.1:5173",
]

# Opcional: Permitir credenciales (Cookies, Tokens) si son necesarias en el flujo con React
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

RECAPTCHA_SECRET_KEY = env('RECAPTCHA_SECRET_KEY', default='')