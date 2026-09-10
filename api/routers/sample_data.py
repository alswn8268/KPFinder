"""시연용 샘플 폴더를 UI 버튼 한 번으로 만들 수 있게 하는 엔드포인트.

핵심 로직은 sample_data/generate_sample_data.py에 그대로 있고, 여기서는 그 함수를
호출할 뿐이다. 기존 폴더를 조용히 덮어쓰지 않는다는 원칙(§P0 12번)도 그대로 지킨다 —
force가 아니면 이미 있는 폴더는 건드리지 않고 그 사실만 알려준다.

부서별(개발팀/운영팀/회계팀 등) 데이터셋 중 하나를 골라 만들 수 있다 — 목록은
/datasets 에서 조회한다.
"""

import os

from fastapi import APIRouter, HTTPException

from sample_data.generate_sample_data import DATASETS, generate, list_datasets
from api.schemas import SampleDataRequest, SampleDataResponse, SampleDatasetInfo

router = APIRouter(prefix="/api/sample-data", tags=["sample-data"])


@router.get("/datasets", response_model=list[SampleDatasetInfo])
def get_datasets():
    return list_datasets()


@router.post("/generate", response_model=SampleDataResponse)
def generate_sample_data(req: SampleDataRequest):
    if req.dataset not in DATASETS:
        raise HTTPException(status_code=400, detail=f"알 수 없는 데이터셋입니다: {req.dataset}")
    spec = DATASETS[req.dataset]
    output_dir = req.output_dir or spec["output_dir"]
    already_existed = os.path.exists(output_dir)
    created = generate(output_dir, force=req.force, dataset=req.dataset)
    return SampleDataResponse(
        output_dir=output_dir,
        created_count=created,
        already_existed=already_existed and created == 0,
        dataset=req.dataset,
        label=spec["label"],
    )
