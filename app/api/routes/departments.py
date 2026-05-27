from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_department_service
from app.schemas import (
    DepartmentCreate,
    DepartmentDetail,
    DepartmentRead,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeRead,
)
from app.services import DepartmentService

router = APIRouter()


@router.post("/", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentRead:
    return service.create_department(data)


@router.post(
    "/{department_id}/employees/",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    department_id: int,
    data: EmployeeCreate,
    service: DepartmentService = Depends(get_department_service),
) -> EmployeeRead:
    return service.create_employee(department_id, data)


@router.get("/{department_id}", response_model=DepartmentDetail)
def get_department(
    department_id: int,
    depth: int = Query(
        default=1,
        ge=1,
        le=5,
        description="Число уровней вложенных подразделений в поле children (1 — только прямые дочерние)",
    ),
    include_employees: bool = Query(default=True, description="Включать списки сотрудников"),
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentDetail:
    return service.get_department_detail(department_id, depth, include_employees)


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentRead:
    return service.update_department(department_id, data)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    mode: Literal["cascade", "reassign"] = Query(...),
    reassign_to_department_id: int | None = Query(default=None),
    service: DepartmentService = Depends(get_department_service),
) -> Response:
    service.delete_department(department_id, mode, reassign_to_department_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
