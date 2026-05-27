from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import Department, Employee
from app.schemas import (
    DepartmentCreate,
    DepartmentDetail,
    DepartmentRead,
    DepartmentTreeNode,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeRead,
)


class DepartmentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_department_or_404(self, department_id: int) -> Department:
        department = self.db.get(Department, department_id)
        if department is None:
            raise NotFoundError("Подразделение не найдено")
        return department

    def _ensure_unique_name(self, name: str, parent_id: int | None, exclude_id: int | None = None) -> None:
        query = select(Department).where(
            Department.name == name,
            Department.parent_id.is_(parent_id) if parent_id is None else Department.parent_id == parent_id,
        )
        if exclude_id is not None:
            query = query.where(Department.id != exclude_id)
        if self.db.scalar(query) is not None:
            raise ConflictError("Название подразделения должно быть уникальным в рамках одного родителя")

    def _ensure_parent_exists(self, parent_id: int | None) -> None:
        if parent_id is not None and self.db.get(Department, parent_id) is None:
            raise NotFoundError("Родительское подразделение не найдено")

    def _collect_descendant_ids(self, department_id: int) -> set[int]:
        descendants: set[int] = set()
        stack = [department_id]
        while stack:
            current = stack.pop()
            children = self.db.scalars(
                select(Department.id).where(Department.parent_id == current)
            ).all()
            for child_id in children:
                if child_id not in descendants:
                    descendants.add(child_id)
                    stack.append(child_id)
        return descendants

    def _ensure_no_cycle(self, department_id: int, new_parent_id: int | None) -> None:
        if new_parent_id is None:
            return
        if new_parent_id == department_id:
            raise ConflictError("Подразделение не может быть родителем самого себя")
        descendants = self._collect_descendant_ids(department_id)
        if new_parent_id in descendants:
            raise ConflictError("Нельзя переместить подразделение внутрь своего поддерева")

    def create_department(self, data: DepartmentCreate) -> DepartmentRead:
        self._ensure_parent_exists(data.parent_id)
        self._ensure_unique_name(data.name, data.parent_id)
        department = Department(name=data.name, parent_id=data.parent_id)
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return DepartmentRead.model_validate(department)

    def create_employee(self, department_id: int, data: EmployeeCreate) -> EmployeeRead:
        self.get_department_or_404(department_id)
        employee = Employee(
            department_id=department_id,
            full_name=data.full_name,
            position=data.position,
            hired_at=data.hired_at,
        )
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return EmployeeRead.model_validate(employee)

    def _get_department_employees(self, department_id: int) -> list[Employee]:
        return list(
            self.db.scalars(
                select(Employee)
                .where(Employee.department_id == department_id)
                .order_by(Employee.full_name)
            ).all()
        )

    def _load_department(self, department_id: int) -> Department:
        department = self.db.get(Department, department_id)
        if department is None:
            raise NotFoundError("Подразделение не найдено")
        return department

    def _load_children_by_parent_ids(self, parent_ids: list[int]) -> list[Department]:
        if not parent_ids:
            return []
        return list(
            self.db.scalars(
                select(Department)
                .where(Department.parent_id.in_(parent_ids))
                .order_by(Department.name)
            ).all()
        )

    def _build_children_tree(
        self,
        parent_ids: list[int],
        remaining_depth: int,
        include_employees: bool,
    ) -> list[DepartmentTreeNode]:
        if remaining_depth <= 0 or not parent_ids:
            return []

        children = self._load_children_by_parent_ids(parent_ids)
        nodes: list[DepartmentTreeNode] = []
        child_ids = [child.id for child in children]

        grandchildren_map: dict[int, list[DepartmentTreeNode]] = {}
        if remaining_depth > 1 and child_ids:
            grand_children = self._build_children_tree(child_ids, remaining_depth - 1, include_employees)
            for node in grand_children:
                grandchildren_map.setdefault(node.parent_id, []).append(node)

        for child in children:
            employees: list[EmployeeRead] = []
            if include_employees:
                employees = [EmployeeRead.model_validate(e) for e in self._get_department_employees(child.id)]
            nodes.append(
                DepartmentTreeNode(
                    id=child.id,
                    name=child.name,
                    parent_id=child.parent_id,
                    created_at=child.created_at,
                    employees=employees,
                    children=grandchildren_map.get(child.id, []),
                )
            )
        return nodes

    def get_department_detail(
        self,
        department_id: int,
        depth: int,
        include_employees: bool,
    ) -> DepartmentDetail:
        department = self._load_department(department_id)

        employees: list[EmployeeRead] = []
        if include_employees:
            employees = [EmployeeRead.model_validate(e) for e in self._get_department_employees(department_id)]

        children = self._build_children_tree([department_id], depth, include_employees)

        return DepartmentDetail(
            department=DepartmentRead.model_validate(department),
            employees=employees,
            children=children,
        )

    def update_department(self, department_id: int, data: DepartmentUpdate) -> DepartmentRead:
        department = self.get_department_or_404(department_id)

        if not data.model_fields_set:
            return DepartmentRead.model_validate(department)

        new_name = data.name if data.name is not None else department.name
        new_parent_id = department.parent_id

        if "parent_id" in data.model_fields_set:
            new_parent_id = data.parent_id
            self._ensure_parent_exists(new_parent_id)
            self._ensure_no_cycle(department_id, new_parent_id)

        if data.name is not None or "parent_id" in data.model_fields_set:
            self._ensure_unique_name(new_name, new_parent_id, exclude_id=department_id)

        if data.name is not None:
            department.name = data.name
        if "parent_id" in data.model_fields_set:
            department.parent_id = new_parent_id

        self.db.commit()
        self.db.refresh(department)
        return DepartmentRead.model_validate(department)

    def delete_department(
        self,
        department_id: int,
        mode: str,
        reassign_to_department_id: int | None,
    ) -> None:
        department = self.get_department_or_404(department_id)

        if mode == "reassign":
            if reassign_to_department_id is None:
                raise BadRequestError(
                    "Параметр reassign_to_department_id обязателен при mode=reassign"
                )
            if reassign_to_department_id == department_id:
                raise BadRequestError(
                    "Нельзя переводить сотрудников в удаляемое подразделение"
                )
            target = self.get_department_or_404(reassign_to_department_id)
            employees = self.db.scalars(
                select(Employee).where(Employee.department_id == department_id)
            ).all()
            for employee in employees:
                employee.department_id = target.id
            self.db.flush()
            children = self.db.scalars(
                select(Department).where(Department.parent_id == department_id)
            ).all()
            for child in children:
                self._ensure_unique_name(child.name, department.parent_id, exclude_id=child.id)
                child.parent_id = department.parent_id
            self.db.delete(department)
            self.db.commit()
            return

        if mode == "cascade":
            self.db.delete(department)
            self.db.commit()
            return

        raise BadRequestError("Параметр mode должен быть cascade или reassign")
