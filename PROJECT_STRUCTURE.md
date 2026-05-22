# Estructura del Proyecto

Última actualización: 2026-05-22

```
/
├── app/                        # Código principal de la aplicación FastAPI
│   ├── config/                 # Configuración: settings, logging, OAuth, LLM
│   ├── db/                     # Modelos SQLAlchemy y conexión a base de datos
│   ├── routes/                 # Endpoints FastAPI organizados por recurso
│   └── utils/                  # Utilidades: auth, CRUD, AI, email, validación
│
├── alembic/                    # Migraciones de base de datos
│   └── versions/               # Scripts de migración individuales
│
├── static/                     # Archivos estáticos servidos al frontend
│   ├── css/                    # Estilos CSS
│   ├── favicon/                # Iconos de sitio
│   ├── images/                 # Imágenes estáticas
│   ├── js/                     # JavaScript vanilla (ES6+)
│   ├── service-worker.js       # PWA service worker
│   ├── robots.txt              # Directivas para crawlers
│   └── sitemap.xml             # Mapa del sitio
│
├── templates/                  # Plantillas Jinja2 para renderizado server-side
│   ├── *.html                  # Páginas completas
│   └── _*.html                 # Partial templates (footer, navbar, etc.)
│
├── tests/                      # Suite de tests pytest
│   ├── config/                 # Tests para configuración
│   ├── routes/                 # Tests para endpoints
│   ├── utils/                  # Tests para utilidades
│   └── conftest.py             # Fixtures compartidos
│
├── scripts/                    # Scripts de utilidad para desarrollo/mantenimiento
│
├── .github/
│   └── workflows/              # Pipelines de CI/CD (GitHub Actions)
│
├── alembic.ini                 # Configuración de Alembic
├── pyproject.toml              # Dependencias y configuración del proyecto (uv)
├── Dockerfile                  # Imagen Docker para producción
├── README.md                   # Documentación principal
├── AGENTS.md                   # Reglas para agentes de IA
├── DATABASE.md                 # Documentación de base de datos
├── CONTRIBUTING.md             # Guía de contribución
└── CODE_OF_CONDUCT.md          # Código de conducta
```
