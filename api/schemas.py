"""
요청/응답 Pydantic 스키마 정의
"""

from pydantic import BaseModel, Field

MAX_DIM_CM = 10000


class OptimizeSingleRequest(BaseModel):
    length_cm: int = Field(..., gt=0, le=MAX_DIM_CM, description="밭 세로 길이 (cm)")
    width_cm:  int = Field(..., gt=0, le=MAX_DIM_CM, description="밭 가로 길이 (cm)")
    crop_key:  str = Field(..., description="작물 키 (예: rice, garlic, lettuce)")
    seed:      int = Field(default=42, description="난수 시드")
    num_reads: int = Field(default=120, ge=1, le=1000, description="SA 샘플링 횟수")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "length_cm": 300,
                    "width_cm": 200,
                    "crop_key": "rice",
                    "seed": 42,
                    "num_reads": 120,
                }
            ]
        }
    }


class OptimizeAllRequest(BaseModel):
    length_cm: int = Field(..., gt=0, le=MAX_DIM_CM, description="밭 세로 길이 (cm)")
    width_cm:  int = Field(..., gt=0, le=MAX_DIM_CM, description="밭 가로 길이 (cm)")
    seed:      int = Field(default=42, description="난수 시드")
    num_reads: int = Field(default=120, ge=1, le=1000, description="SA 샘플링 횟수")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "length_cm": 300,
                    "width_cm": 200,
                    "seed": 42,
                    "num_reads": 120,
                }
            ]
        }
    }