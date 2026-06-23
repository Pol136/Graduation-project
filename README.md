# Movie Reviews Analysis System

Веб-приложение для анализа пользовательских отзывов о фильмах и формирования персонализированных рекомендаций.

Система позволяет пользователям искать фильмы, оставлять отзывы, автоматически анализировать их содержание, определять тональность, выделять аспекты мнения и использовать результаты анализа для подбора фильмов с учётом индивидуальных предпочтений.

## Возможности

* регистрация и авторизация пользователей;
* поиск и просмотр фильмов;
* добавление текстовых отзывов и числовых оценок;
* автоматический анализ тональности отзыва;
* выделение аспектов фильма: сюжет, актёры, музыка, визуальная составляющая и др.;
* прогнозирование числовой оценки отзыва;
* формирование профиля предпочтений пользователя;
* персональные рекомендации фильмов;
* список «Смотреть позже».

## Технологический стек

**Backend:** Python, FastAPI, SQLAlchemy, Alembic, JWT
**Frontend:** React, TypeScript, Vite
**Database:** PostgreSQL, JSONB
**ML/NLP:** Hugging Face Transformers, RuBERT-tiny sentiment, mDeBERTa zero-shot
**DevOps:** Docker, Docker Compose

## Архитектура

Проект состоит из четырёх основных компонентов:

```text
Frontend → Backend → PostgreSQL
              ↓
          ML-сервис
```

* **Frontend** отвечает за пользовательский интерфейс.
* **Backend** реализует бизнес-логику, API, авторизацию и рекомендации.
* **ML-сервис** выполняет анализ отзывов.
* **PostgreSQL** хранит пользователей, фильмы, отзывы, результаты анализа и рекомендации.

## Как работает анализ отзыва

1. Пользователь добавляет отзыв к фильму.
2. Backend сохраняет отзыв и передаёт текст в ML-сервис.
3. ML-сервис определяет общую тональность, выделяет аспекты и прогнозирует оценку.
4. Результаты сохраняются в базе данных.
5. Данные используются для аналитики по фильму и персональных рекомендаций.

Пример результата анализа:

```json
{
  "sentiment": "positive",
  "predicted_score": 8.4,
  "aspects": [
    {
      "aspect": "сюжет",
      "sentiment": "positive"
    },
    {
      "aspect": "визуальная составляющая",
      "sentiment": "positive"
    },
    {
      "aspect": "темп повествования",
      "sentiment": "negative"
    }
  ]
}
```

## Запуск проекта

### Через Docker Compose

```bash
docker compose up --build
```

После запуска приложение будет доступно по адресам:

```text
Frontend: http://localhost:5173
Backend API: http://localhost:8000
Swagger: http://localhost:8000/docs
ML Service: http://localhost:8001
```

## Переменные окружения

Пример `.env` файла:

```env
POSTGRES_DB=movie_reviews
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql://postgres:postgres@db:5432/movie_reviews

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

ML_SERVICE_URL=http://ml-service:8001
TMDB_API_KEY=your_tmdb_api_key
```

## Основные API endpoints

```http
POST /api/auth/register
POST /api/auth/login

GET  /api/movies
GET  /api/movies/search
GET  /api/movies/{movie_id}
POST /api/movies/{movie_id}/reviews

GET  /api/recommendations
POST /api/recommendations/refresh

GET  /api/watchlist
POST /api/watchlist/{movie_id}
DELETE /api/watchlist/{movie_id}
```

## Оценка качества

Для оценки прогнозирования числовой оценки используется MAE:

```text
MAE = mean(|user_rating - predicted_rating|)
```

Для оценки рекомендаций используются пользовательские действия внутри приложения: добавление рекомендованного фильма в список «Смотреть позже».


## Статус проекта

Учебный дипломный проект.
Система реализована как прототип для комплексного анализа отзывов о фильмах и формирования персонализированных рекомендаций.
