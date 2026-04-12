"""
/api/optimize/single, /api/optimize/all 라우터
"""

from fastapi import APIRouter, HTTPException

from crops_data import CROPS
from schemas import OptimizeSingleRequest, OptimizeAllRequest
from optimizer import solve_sa_single, execute_all_crops

router = APIRouter(prefix="/api/optimize", tags=["Optimization"])


@router.post("/single")
def optimize_single(req: OptimizeSingleRequest):
    """단일 작물 최적화"""
    if req.crop_key not in CROPS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid crop_key '{req.crop_key}'. Valid: {list(CROPS.keys())}",
        )
    try:
        return solve_sa_single(
            req.length_cm, req.width_cm, req.crop_key,
            req.seed, req.num_reads,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/all")
def optimize_all(req: OptimizeAllRequest):
    """전체 작물 비교 최적화"""
    try:
        return execute_all_crops(
            req.length_cm, req.width_cm,
            req.seed, req.num_reads,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")