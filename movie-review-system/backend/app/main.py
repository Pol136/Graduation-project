from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, ml, movies, recommendations, reviews, users, watchlist
from app.core.config import settings

app = FastAPI(
    title="Movie Review System API",
    description="Backend for movie reviews, analysis, and recommendations",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(
    recommendations.router,
    prefix="/api/recommendations",
    tags=["recommendations"],
)
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(ml.router, prefix="/api/ml", tags=["ml"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
