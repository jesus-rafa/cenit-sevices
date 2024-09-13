# °Cenit Services

## Deployment Status
### Production
![production](https://info.deployment.emeraldigital.com/deployed/cenit-production/cenit/services/semantic) ![hub-production](https://info.deployment.emeraldigital.com/hub/cenit-production/cenit/services/semantic)

## Target: Aplicacion para generar certificados pdf y añadir futuros endpoints
## Created by [Emeral Digital]

## Animations: https://lottiefiles.com/es/
## Extract Colors: https://pypi.org/project/extcolors/#toc-entry-6

## Commads
    **************** Django / Django Rest Framework **********************
    
    ==================== Crear base de datos =============================
    shell postgresql

    username=postgres;
    pass=root2020;

    CREATE DATABASE name_db;
    CREATE USER user_db;
    \c name_db;
    ALTER ROLE user_db WITH PASSWORD 'root2020';

    # Generar respaldos de la base de datos
    python manage.py dumpdata
    python manage.py dumpdata > name_db.json

    # Montar respaldo en la base de datos
    python manage.py loaddata name_db.json

    ======================== Instalar paquetes ============================
    pip install django
    pip install package_name

    ======================== Crear Entorno ==============================
    python -m venv name_env
    pip install -r requirements.txt

    # Muestra las librerias instaladas
    pip freeze
    pip freeze > requirements.txt
    
    =======================cls= Crear Proyecto =============================
    django-admin startproject name_proyect

    ======================== Crear App ==================================
    django-admin startapp name_app

    ======================== Ejecutar Servidor ==========================
    python manage.py runserver

    ======================== Archivos estaticos ==========================
    python manage.py collectstatic

    ======================== Actualizar pip =============================
    python -m pip install --upgrade pip

    ======================== Crear Tablas ===============================
    python manage.py makemigrations
    python manage.py migrate

    ======================== Crear SuperUsuario =========================
    python manage.py createsuperuser
    python manage.py changepassword correo_usuario

