from fastapi import APIRouter

from app import organizer
from api.schemas import CacheInfoModel, ClearAllCachesResponse, ClearCacheResponse

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/info", response_model=CacheInfoModel)
def cache_info(root: str):
    return organizer.cache_metadata(root)


@router.delete("/current", response_model=ClearCacheResponse)
def clear_current_cache(root: str):
    return ClearCacheResponse(cleared=organizer.clear_cache(root))


@router.delete("/all", response_model=ClearAllCachesResponse)
def clear_all_caches():
    return ClearAllCachesResponse(cleared_count=organizer.clear_all_caches())
