#!/usr/bin/env python3
"""Заполнение БД тестовыми подразделениями и сотрудниками."""

import argparse
from datetime import date

from sqlalchemy import text

from app.database import SessionLocal
from app.models import Department, Employee


def seed_database(*, force: bool = False) -> None:
    db = SessionLocal()
    try:
        existing = db.query(Department).count()
        if existing > 0 and not force:
            print(
                f"В БД уже есть {existing} подразделений. "
                "Запустите с --force, чтобы пересоздать данные."
            )
            return

        if existing > 0:
            db.execute(text("TRUNCATE TABLE employees, departments RESTART IDENTITY CASCADE"))
            db.commit()
            print("Существующие данные удалены.")

        company = Department(name="Компания")
        db.add(company)
        db.flush()

        dev = Department(name="Разработка", parent_id=company.id)
        sales = Department(name="Продажи", parent_id=company.id)
        hr = Department(name="HR", parent_id=company.id)
        db.add_all([dev, sales, hr])
        db.flush()

        backend = Department(name="Backend", parent_id=dev.id)
        frontend = Department(name="Frontend", parent_id=dev.id)
        db.add_all([backend, frontend])
        db.flush()

        employees = [
            Employee(
                department_id=company.id,
                full_name="Анна Смирнова",
                position="Генеральный директор",
                hired_at=date(2020, 1, 15),
            ),
            Employee(
                department_id=dev.id,
                full_name="Иван Петров",
                position="Директор по разработке",
                hired_at=date(2021, 3, 10),
            ),
            Employee(
                department_id=backend.id,
                full_name="Алиса Козлова",
                position="Backend-разработчик",
                hired_at=date(2022, 6, 1),
            ),
            Employee(
                department_id=backend.id,
                full_name="Борис Волков",
                position="Backend-разработчик",
                hired_at=date(2023, 2, 20),
            ),
            Employee(
                department_id=frontend.id,
                full_name="Мария Соколова",
                position="Frontend-разработчик",
                hired_at=date(2022, 9, 5),
            ),
            Employee(
                department_id=sales.id,
                full_name="Дмитрий Орлов",
                position="Менеджер по продажам",
                hired_at=date(2021, 11, 12),
            ),
            Employee(
                department_id=sales.id,
                full_name="Елена Морозова",
                position="Менеджер по продажам",
                hired_at=date(2024, 1, 8),
            ),
            Employee(
                department_id=hr.id,
                full_name="Ольга Новикова",
                position="HR-специалист",
                hired_at=date(2020, 8, 30),
            ),
        ]
        db.add_all(employees)
        db.commit()

        print("Тестовые данные добавлены:")
        print(f"  Подразделений: {db.query(Department).count()}")
        print(f"  Сотрудников:   {db.query(Employee).count()}")
        print()
        print("Примеры запросов:")
        print(f"  GET http://localhost:8000/departments/{company.id}?depth=3")
        print(f"  GET http://localhost:8000/departments/{backend.id}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Заполнить БД тестовыми данными")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Удалить существующие данные и создать заново",
    )
    args = parser.parse_args()
    seed_database(force=args.force)


if __name__ == "__main__":
    main()
