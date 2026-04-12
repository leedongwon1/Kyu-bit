"""
/ 메인 웹 UI 라우터
"""

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from crops_data import CROPS

router = APIRouter(tags=["Web UI"])


@router.get("/", response_class=HTMLResponse)
def web_ui():
    """메인 웹 UI 페이지"""
    html_path = Path(__file__).parent.parent / "templates" / "index.html"
    html_content = html_path.read_text(encoding="utf-8")

    crops_js = json.dumps(
        {
            k: {
                'label': v['label'],
                'label_kr': v['label_kr'],
                'emoji': v['emoji'],
                'spacing_text': v['spacing_text'],
            }
            for k, v in CROPS.items()
        },
        ensure_ascii=False,
    )

    return html_content.replace('CROP_DATA_PLACEHOLDER', crops_js)