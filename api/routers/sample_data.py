"""시연용 샘플 폴더를 UI 버튼 한 번으로 만들 수 있게 하는 엔드포인트.

핵심 로직은 sample_data/generate_sample_data.py에 그대로 있고, 여기서는 그 함수를
호출할 뿐이다. 기존 폴더를 조용히 덮어쓰지 않는다는 원칙(§P0 12번)도 그대로 지킨다 —
force가 아니면 이미 있는 폴더는 건드리지 않고 그 사실만 알려준다.
"""

import os

from fastapi import APIRouter

from sample_data.generate_sample_data import OUTPUT_DEFAULT, generate
from api.schemas import SampleDataRequest, SampleDataResponse

router = APIRouter(prefix="/api/sample-data", tags=["sample-data"])


@router.post("/generate", response_model=SampleDataResponse)
def generate_sample_data(req: SampleDataRequest):
    output_dir = req.output_dir or OUTPUT_DEFAULT
    already_existed = os.path.exists(output_dir)
    created = generate(output_dir, force=req.force)
    return SampleDataResponse(
        output_dir=output_dir,
        created_count=created,
        already_existed=already_existed and created == 0,
    )
