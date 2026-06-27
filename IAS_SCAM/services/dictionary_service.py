from db.database import SessionLocal
from db.models import Category, IssueType, Materials, Crew, Roles, Status, CriticalityLevels, CrewStatus
import services.audit_service as audit_service

TAB_TABLE_MAPPING = {
    0: "category", 1: "issue_type", 2: "materials", 3: "crew",
    4: "roles", 5: "status", 6: "criticality_levels", 7: "crew_status"
}


def get_categories():
    with SessionLocal() as db:
        try:
            items = db.query(Category).order_by(Category.id_category.asc()).all()
            return [{"id": i.id_category, "name": i.category_name} for i in items]
        except Exception: 
            return []


def get_incident_types():
    with SessionLocal() as db:
        try:
            items = db.query(IssueType).join(Category).order_by(IssueType.id_issue_type.asc()).all()
            return [{
                "id": i.id_issue_type,
                "category_name": i.category.category_name,
                "incident_name": i.type_name,
                "category_id": i.category_id
            } for i in items]
        except Exception: 
            return []


def get_materials():
    with SessionLocal() as db:
        try:
            items = db.query(Materials).order_by(Materials.id_material.asc()).all()
            return [{
                "id": i.id_material,
                "name": i.material_name,
                "unit": i.unit,
                "price": float(i.price) if i.price else 0.0
            } for i in items]
        except Exception: 
            return []


def get_crews():
    with SessionLocal() as db:
        try:
            items = db.query(Crew).join(Category).order_by(Crew.id_crew.asc()).all()
            return [{
                "id": i.id_crew,
                "crew_number": i.crew_number,
                "category_name": i.category.category_name,
                "status": i.status.status_name if i.status else "Не визначено",
                "category_id": i.category_id
            } for i in items]
        except Exception: 
            return []


def get_roles():
    with SessionLocal() as db:
        try:
            items = db.query(Roles).order_by(Roles.id_role.asc()).all()
            return [{"id": i.id_role, "name": i.role_name} for i in items]
        except Exception: 
            return []


def get_statuses():
    with SessionLocal() as db:
        try:
            items = db.query(Status).order_by(Status.id_status.asc()).all()
            return [{"id": i.id_status, "name": i.status_name} for i in items]
        except Exception: 
            return []


def get_criticalities():
    with SessionLocal() as db:
        try:
            items = db.query(CriticalityLevels).order_by(CriticalityLevels.id_criticality.asc()).all()
            return [{"id": i.id_criticality, "name": i.level_name} for i in items]
        except Exception: 
            return []


def get_crew_statuses():
    with SessionLocal() as db:
        try:
            items = db.query(CrewStatus).order_by(CrewStatus.id_crew_status.asc()).all()
            return [{"id": i.id_crew_status, "name": i.status_name} for i in items]
        except Exception: 
            return []


def save_directory_item(tab_index, data, item_id=None, admin_id=1):
    """Створює або атомарно оновлює рядок у будь-якому системному довіднику з логуванням змін подій."""
    with SessionLocal() as db:
        try:
            if data is None: 
                data = {}
            t_name = TAB_TABLE_MAPPING.get(tab_index, "unknown_directory")
            event = "UPDATE" if item_id else "INSERT"

            if tab_index == 0:
                model = db.query(Category).filter(Category.id_category == item_id).first() if item_id else Category()
                old_val = model.category_name if item_id else "Не існувало"
                new_val = data.get("name", "")
                model.category_name = new_val
                fields_to_log = [("category_name", old_val, new_val)]

            elif tab_index == 1:
                model = db.query(IssueType).filter(IssueType.id_issue_type == item_id).first() if item_id else IssueType()
                old_cat = str(model.category_id) if item_id else "Не існувало"
                old_name = model.type_name if item_id else "Не існувало"
                model.category_id = data.get("category_id")
                model.type_name = data.get("incident_name", "")
                fields_to_log = [
                    ("category_id", old_cat, data.get("category_id")),
                    ("type_name", old_name, data.get("incident_name"))
                ]

            elif tab_index == 2:
                model = db.query(Materials).filter(Materials.id_material == item_id).first() if item_id else Materials()
                old_name = model.material_name if item_id else "Не існувало"
                old_unit = model.unit if item_id else "Не існувало"
                old_price = str(model.price) if item_id else "Не існувало"
                model.material_name = data.get("name", "")
                model.unit = data.get("unit", "")
                model.price = data.get("price", 0.0)
                fields_to_log = [
                    ("material_name", old_name, data.get("name")),
                    ("unit", old_unit, data.get("unit")),
                    ("price", old_price, data.get("price"))
                ]

            elif tab_index == 3:
                model = db.query(Crew).filter(Crew.id_crew == item_id).first() if item_id else Crew()
                old_num = model.crew_number if item_id else "Не існувало"
                old_cat = str(model.category_id) if item_id else "Не існувало"
                old_stat = str(model.status_id) if item_id else "Не існувало"
                model.crew_number = data.get("crew_number", "")
                model.category_id = data.get("category_id")
                model.status_id = data.get("status_id")
                fields_to_log = [
                    ("crew_number", old_num, data.get("crew_number")),
                    ("category_id", old_cat, data.get("category_id")),
                    ("status_id", old_stat, data.get("status_id"))
                ]

            elif tab_index == 4:
                model = db.query(Roles).filter(Roles.id_role == item_id).first() if item_id else Roles()
                old_val = model.role_name if item_id else "Не існувало"
                new_val = data.get("name", "")
                model.role_name = new_val
                fields_to_log = [("role_name", old_val, new_val)]

            elif tab_index == 5:
                model = db.query(Status).filter(Status.id_status == item_id).first() if item_id else Status()
                old_val = model.status_name if item_id else "Не існувало"
                new_val = data.get("name", "")
                model.status_name = new_val
                fields_to_log = [("status_name", old_val, new_val)]

            elif tab_index == 6:
                model = db.query(CriticalityLevels).filter(CriticalityLevels.id_criticality == item_id).first() if item_id else CriticalityLevels()
                old_val = model.level_name if item_id else "Не існувало"
                new_val = data.get("name", "")
                model.level_name = new_val
                fields_to_log = [("level_name", old_val, new_val)]

            elif tab_index == 7:
                model = db.query(CrewStatus).filter(CrewStatus.id_crew_status == item_id).first() if item_id else CrewStatus()
                old_val = model.status_name if item_id else "Не існувало"
                new_val = data.get("name", "")
                model.status_name = new_val
                fields_to_log = [("status_name", old_val, new_val)]
            else:
                return False, "Невідомий довідник"

            if not item_id:
                db.add(model)
                db.flush()
                rec_id = getattr(model, f"id_{t_name}", None) or getattr(model, "id_issue_type", None) or getattr(model, "id_criticality", None)
            else:
                rec_id = item_id

            for f_name, old_f, new_f in fields_to_log:
                if str(old_f) != str(new_f):  
                    audit_service.log_action(
                        user_id=admin_id,
                        event_type=event,
                        table_name=f"{t_name}.{f_name}",
                        record_id=rec_id,
                        old_value=str(old_f) if old_f is not None else "—",
                        new_value=str(new_f) if new_f is not None else "—"
                    )

            db.commit()
            return True, "Дані успішно збережено!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка бази даних: {str(e)}"


def delete_directory_item(tab_index, item_id, admin_id=1):
    """Остаточно вилучає запис із системного довідника із попереднім логуванням події в аудит."""
    with SessionLocal() as db:
        try:
            t_name = TAB_TABLE_MAPPING.get(tab_index, "unknown_directory")
            if tab_index == 0: target = db.query(Category).filter(Category.id_category == item_id).first()
            elif tab_index == 1: target = db.query(IssueType).filter(IssueType.id_issue_type == item_id).first()
            elif tab_index == 2: target = db.query(Materials).filter(Materials.id_material == item_id).first()
            elif tab_index == 3: target = db.query(Crew).filter(Crew.id_crew == item_id).first()
            elif tab_index == 4: target = db.query(Roles).filter(Roles.id_role == item_id).first()
            elif tab_index == 5: target = db.query(Status).filter(Status.id_status == item_id).first()
            elif tab_index == 6: target = db.query(CriticalityLevels).filter(CriticalityLevels.id_criticality == item_id).first()
            elif tab_index == 7: target = db.query(CrewStatus).filter(CrewStatus.id_crew_status == item_id).first()
            else: 
                return False, "Невідомий довідник"

            if target:
                audit_service.log_action(
                    user_id=admin_id, event_type="DELETE", table_name=t_name,
                    record_id=item_id, old_value=f"Елемент вилучено остаточно"
                )
                db.delete(target)
                db.commit()
                return True, "Запис успішно видалено з системи!"
            return False, "Запис не знайдено."
        except Exception as e:
            db.rollback()
            return False, f"Неможливо видалити елемент (він пов'язаний з іншими таблицями): {str(e)}"