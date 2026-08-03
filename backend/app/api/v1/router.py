from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.learner_profiles import router as learner_profiles_router
from app.api.v1.dataset import router as dataset_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(learner_profiles_router)
api_v1_router.include_router(dataset_router)
