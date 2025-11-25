# SportAuth – Documentación del Proyecto

SportAuth es una plataforma desarrollada en **Flask (Python)** con renderizado dinámico mediante **Jinja2**, orientada a la gestión integral de torneos deportivos. El sistema permite administrar jugadores, equipos, torneos, partidos, registros de acciones y módulos profesionales relacionados.

---

## Tecnologías Principales

### **Backend**

* **Python 3**
* **Flask**: Framework principal para el manejo de rutas, vistas, controladores y servicios.
* **Jinja2**: Motor de plantillas para renderizar HTML dinámico.
* **PostgreSQL**: Manejo de la base de datos mediante consultas SQL directas.

### **Frontend**

* HTML5, CSS
* Jinja2 para inserción dinámica de datos

### **Otras Librerías empleadas**

* `numpy`: Operaciones numéricas
* `sklearn.neural_network` (MLPClassifier): Cálculo y predicción de rendimiento de jugadores
* `python-dotenv`: Manejo de variables de entorno
* `gunicorn`: Servidor WSGI para despliegues en producción

---

## Estructura y Módulos del Sistema

A continuación, se describen los módulos principales del proyecto:

### ### **1. Módulo de Profesionalismos**

Permite gestionar la información profesional de los jugadores, como categorías, niveles o jerarquías asociadas. Facilita la clasificación dentro de un torneo.

### **2. Módulo de Jugadores**

* Crear, editar y listar jugadores
* Asociar jugadores a equipos y torneos
* Mostrar rendimiento individual
* Gestión de estados (activo/inactivo)

### **3. Módulo de Equipos**

* Crear equipos y administrarlos
* Validación de nombres duplicados
* Equipos marcados siempre como activos durante la creación
* Asociaciones con jugadores y torneos

### **4. Módulo de Torneos**

* Registrar torneos
* Definir parámetros como **mínimo de jugadores por equipo** para iniciar un partido
* Asociaciones con equipos y jugadores

### **5. Módulo de Partidos**

* Crear y gestionar partidos
* Validar que un partido solo pueda iniciar si los equipos tienen el número mínimo de jugadores registrados
* Registrar acciones dentro de cada partido

### **6. Módulo de Registros**

Registra las acciones dentro de un partido:

* Goles
* Faltas
* Asistencias
* Otras estadísticas

Cada registro está asociado a:

* Jugador
* Partido
* Torneo

Para obtener el equipo del jugador dentro de un torneo, se usan las tablas:

* `jugador_torneo`
* `equipo`

## Asociaciones dentro del Sistema

### Relaciones destacadas:

* **Jugador ↔ Equipo** (a través de jugador_torneo)
* **Equipo ↔ Torneo**
* **Jugador ↔ Partido** (por medio de registros de acciones)
* **Torneo ↔ Partido**
* **Partido ↔ Registros**

El sistema asegura integridad mediante validaciones y conteos dinámicos, especialmente al iniciar partidos.

## Archivos Importantes del Proyecto

### **Archivos Procfile**

Archivo utilizado para despliegues en **Heroku u otras plataformas PaaS**.

Indica el comando que debe ejecutarse para iniciar la aplicación, generalmente:

web: gunicorn app:app

Esto garantiza que la aplicación se levante con un servidor WSGI adecuado para producción.

### **archivo .env**

Contiene las variables de entorno de forma segura, tales como:

* Cadena de conexión a la base de datos
* Variables secretas (SECRET_KEY)
* Configuraciones de entorno

Este archivo **no debe subirse al repositorio**, protegiendo credenciales sensibles.

Se implementa un modelo de **red neuronal MLPClassifier** de Scikit-Learn para analizar:

* Rendimiento de jugadores
* Probabilidad de acciones futuras
* Clasificación de desempeño

El sistema usa estadísticas de registros para entrenar y ejecutar predicciones localmente.

## Estructura del Proyecto

SportAuth/
│   app.py
│   Procfile
│   .env
│   requirements.txt
│
├── modules/
│   ├── jugadores.py
│   ├── equipos.py
│   ├── torneos.py
│   ├── partidos.py
│   ├── registros.py
│   ├── home.py
│   ├── equipo_torneo.py
│   ├── jugador_torneo.py
│   ├── rendimiento_jugadores.py
│   └── profesionalismos.py
│
├── templates/
│
└── static/
    ├── css/
    ├── js/
    └── img/
