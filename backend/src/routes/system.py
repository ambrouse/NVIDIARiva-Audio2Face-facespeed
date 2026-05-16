from fastapi import APIRouter, Depends

from src.dependencies import getSystemCheckService
from src.services.system_check import SystemCheckService

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/checks")
def getSystemChecks(systemCheckService: SystemCheckService = Depends(getSystemCheckService)) -> list[dict[str, str | bool]]:
    return systemCheckService.getChecks()
