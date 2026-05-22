from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import getServiceManager
from src.models.service import ServiceAction, ServiceName, ServiceStatus
from src.services.service_manager import ServiceManager

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=list[ServiceStatus])
def listServices(serviceManager: ServiceManager = Depends(getServiceManager)) -> list[ServiceStatus]:
    return serviceManager.listServices()


@router.get("/{serviceName}/status", response_model=ServiceStatus)
def getServiceStatus(serviceName: ServiceName, serviceManager: ServiceManager = Depends(getServiceManager)) -> ServiceStatus:
    return serviceManager.getStatus(serviceName)


@router.post("/{serviceName}/{action}", response_model=ServiceStatus)
def runServiceAction(
    serviceName: ServiceName,
    action: ServiceAction,
    serviceManager: ServiceManager = Depends(getServiceManager),
) -> ServiceStatus:
    try:
        return serviceManager.runAction(serviceName, action)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/{serviceName}/logs", response_model=list[str])
def getServiceLogs(
    serviceName: ServiceName,
    maxLines: int = 200,
    serviceManager: ServiceManager = Depends(getServiceManager),
) -> list[str]:
    return serviceManager.readLogs(serviceName, maxLines)
