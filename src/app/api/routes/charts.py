"""Charts route — GET /api/v1/charts/{filename}.

Safe serving endpoint for deterministically generated chart artifacts.
Strictly validates filenames to prevent path traversal and only serves
from the controlled artifacts/charts directory.
"""

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from kit.charts.models import SAFE_FILENAME_REGEX

router = APIRouter(
    prefix="/charts",
    tags=["charts"],
)

CHART_OUTPUT_DIR = Path("artifacts/charts")


@router.get("/{filename}")
def get_chart(filename: str):
    if not re.match(SAFE_FILENAME_REGEX, filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid chart filename format.",
        )

    base_dir = CHART_OUTPUT_DIR.resolve()
    target_path = (base_dir / filename).resolve()

    # Prevent path traversal outside base_dir
    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        ) from None


    if not target_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Chart not found.",
        )

    return FileResponse(
        target_path,
        media_type="image/png",
    )
