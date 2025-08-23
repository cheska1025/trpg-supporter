from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="trpg-supporter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# (필요 시) 라우터 포함 예시
# from backend.app.api.v1.characters import router as characters_router
# from backend.app.api.v1.health import router as health_router
# app.include_router(health_router, prefix="/api/v1")
# app.include_router(characters_router, prefix="/api/v1")
