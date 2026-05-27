from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import DepartmentService


def get_department_service(db: Session = Depends(get_db)) -> Generator[DepartmentService, None, None]:
    yield DepartmentService(db)
