# 💈 Barber Agenda API

Backend profesional para la gestión de citas en una barbería.

Construido con **FastAPI**, **SQLAlchemy**, **PostgreSQL**, **Alembic** y autenticación JWT.

---

## 🚀 Features

- 🔐 Autenticación JWT
- 👑 Roles (admin / barber)
- 📅 Gestión de citas
- 👤 Gestión de clientes
- ✂️ Gestión de servicios
- 🗑 Soft delete (`is_active`)
- 📊 Filtros avanzados
- 📦 Paginación
- 🧪 Tests con Pytest
- 🛠 Migraciones con Alembic

---

## 🧱 Arquitectura

API → Service → Repository → Database

Separación clara de responsabilidades:

- `api/` → Endpoints
- `services/` → Reglas de negocio
- `repositories/` → Acceso a datos
- `models/` → SQLAlchemy models
- `schemas/` → Pydantic schemas

---

## 🛠 Instalación

### 1️⃣ Clonar repositorio

```bash
git clone https://github.com/tuusuario/barber_agenda.git
cd barber_agenda

2️⃣ Crear entorno virtual

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

3️⃣ Instalar dependencias

pip install -r requirements.txt

4️⃣ Configurar variables de entorno

Crear archivo .env:

DATABASE_URL=postgresql://user:password@localhost:5432/barberdb
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

5️⃣ Aplicar migraciones

alembic upgrade head

6️⃣ Ejecutar servidor

uvicorn app.main:app --reload

📖 Documentación

Swagger UI disponible en:

http://localhost:8000/docs

🧪 Ejecutar tests

pytest -v

📌 Próximas mejoras

Rol Cliente

Reportes financieros

Dashboard admin

Integración con WhatsApp

Dockerización

CI/CD

👨‍💻 Autor

[Josue Blanco]
Proyecto desarrollado como backend profesional con arquitectura escalable.

```
