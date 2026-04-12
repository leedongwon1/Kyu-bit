"""
Kyu-bit Agricultural Optimization API v2.0
QUBO + Simulated Annealing 기반 농업 작물 배치 최적화

Author: 이동원
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.web import router as web_router
from routes.info import router as info_router
from routes.optimization import router as optimization_router

# ── FastAPI 앱 초기화 ──
app = FastAPI(
    title="Kyu-bit Agricultural Optimization API",
    description=(
        "QUBO + Simulated Annealing 기반 농업 작물 배치 최적화 API.\n\n"
        "- **웹 UI**: `/` 에서 브라우저로 바로 사용\n"
        "- **API 문서**: `/docs` 에서 Swagger UI 확인\n"
        "- **작물 목록**: `GET /api/crops`\n"
        "- **단일 최적화**: `POST /api/optimize/single`\n"
        "- **전체 비교**: `POST /api/optimize/all`"
    ),
    version="2.0.0",
)

# ── CORS 설정 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 등록 ──
app.include_router(web_router)
app.include_router(info_router)
app.include_router(optimization_router)

# ── 로컬 실행 ──
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    print(f"\n🌾 Kyu-bit API starting on http://localhost:{port}")
    print(f"🖥️  Web UI:      http://localhost:{port}")
    print(f"📖 Swagger docs: http://localhost:{port}/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=port)