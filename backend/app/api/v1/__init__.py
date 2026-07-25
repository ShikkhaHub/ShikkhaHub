from fastapi import APIRouter
from app.api.v1.endpoints import (
    institutions, locations, search, admin, auth, chat,
    reviews, qa, comments, sitemap, analytics
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(chat.router, prefix="/ai", tags=["ai-assistant"])

# Community features
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])

# Analytics
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# SEO features
api_router.include_router(sitemap.router, prefix="", tags=["seo"])
