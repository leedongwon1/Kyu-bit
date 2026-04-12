"""
/health, /api/crops 라우터
"""

from fastapi import APIRouter
from crops_data import CROPS

router = APIRouter(tags=["Info"])


@router.get("/health")
def health():
    """서버 상태 확인"""
    return {"status": "ok", "message": "Kyu-bit API is running"}


@router.get("/api/crops")
def list_crops():
    """사용 가능한 12종 작물 목록 반환"""
    return [
        {
            "key": k,
            "label": v['label'],
            "label_kr": v['label_kr'],
            "emoji": v['emoji'],
            "spacing_text": v['spacing_text'],
            "spacing_row_cm": v['spacing_row_cm'],
            "spacing_col_cm": v['spacing_col_cm'],
        }
        for k, v in CROPS.items()
    ]