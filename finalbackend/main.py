from fastapi import FastAPI
from .routers.user_router import router as user_router
from .routers.auth_router import router as auth_router
from .routers.stock_router import router as stock_router
from .routers.portfolio_router import router as portfolio_router
from .routers.watchlist_router import router as watchlist_router
from .routers.dashboard_router import router as dashboard_router
from .routers.learnings_router import router as learnings_router
from .routers.recommend_router import router as recommend_router

app = FastAPI()

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(stock_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)
app.include_router(dashboard_router)
app.include_router(learnings_router)
app.include_router(recommend_router)
