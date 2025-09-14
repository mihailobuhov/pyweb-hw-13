# goit-pyweb-hw-13

# Реалізація проекту

Для роботи проекта необхідний файл `.env` зі змінними оточення.
Створіть його з таким вмістом і підставте свої значення.

```dotenv
# Database PostgreSQL
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_PORT=
POSTGRES_DOMAIN=

DB_URL = postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_DOMAIN}:${POSTGRES_PORT}/${POSTGRES_DB}

# JWT authentication
SECRET_KEY_JWT=
ALGORITHM=

# Email service
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=
MAIL_SERVER=

# Redis
REDIS_HOST=
REDIS=

# Cloud Storage
CLD_NAME=
CLD_API_KEY=
CLD_API_SECRET=
```

Запуск баз даних

```bash
docker-compose up -d
```

Запуск застосунку

```
uvicorn main:app --reload
```
