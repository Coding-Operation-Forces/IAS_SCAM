# services/dictionary_service.py
from db.database import SessionLocal
from db.models import Category, IssueType, Materials, Crew, Roles, Status, CriticalityLevels, CrewStatus

# ==========================================
# ЧИТАННЯ ДАНИХ (READ)
# ==========================================
def get_categories():
    with SessionLocal() as db:
        try:
            items = db.query(Category).order_by(Category.id_category.asc()).all()
            return [{"id": i.id_category, "name": i.category_name} for i in items]
        except Exception: return []

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
        except Exception: return []

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
        except Exception: return []

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
        except Exception: return []

def get_roles():
    with SessionLocal() as db:
        try:
            items = db.query(Roles).order_by(Roles.id_role.asc()).all()
            return [{"id": i.id_role, "name": i.role_name} for i in items]
        except Exception: return []

def get_statuses():
    with SessionLocal() as db:
        try:
            items = db.query(Status).order_by(Status.id_status.asc()).all()
            return [{"id": i.id_status, "name": i.status_name} for i in items]
        except Exception: return []

def get_criticalities():
    with SessionLocal() as db:
        try:
            items = db.query(CriticalityLevels).order_by(CriticalityLevels.id_criticality.asc()).all()
            return [{"id": i.id_criticality, "name": i.level_name} for i in items]
        except Exception: return []

def get_crew_statuses():
    with SessionLocal() as db:
        try:
            items = db.query(CrewStatus).order_by(CrewStatus.id_crew_status.asc()).all()
            return [{"id": i.id_crew_status, "name": i.status_name} for i in items]
        except Exception: return []


# ==========================================
# ДОДАВАННЯ ТА РЕДАГУВАННЯ (CUD OPERATORS)
# ==========================================
def save_directory_item(tab_index, data, item_id=None):
    with SessionLocal() as db:
        try:
            # === ЗАХИСНИЙ ЩИТ ПРОТИ NoneType ПОМИЛОК ===
            if data is None:
                data = {}
            if tab_index == 0:
                model = db.query(Category).filter(Category.id_category == item_id).first() if item_id else Category()
                model.category_name = data.get("name", "")
            elif tab_index == 1:
                model = db.query(IssueType).filter(IssueType.id_issue_type == item_id).first() if item_id else IssueType()
                model.category_id = data["category_id"]
                model.type_name = data["incident_name"]
            elif tab_index == 2:
                model = db.query(Materials).filter(Materials.id_material == item_id).first() if item_id else Materials()
                model.material_name = data["name"]
                model.unit = data["unit"]
                model.price = data["price"]
            elif tab_index == 3:
                model = db.query(Crew).filter(Crew.id_crew == item_id).first() if item_id else Crew()
                model.crew_number = data["crew_number"]
                model.category_id = data["category_id"]
                # ТЕПЕР СТАТУС БЕРЕТЬСЯ З ІНТЕРФЕЙСУ (як при створенні, так і при редагуванні)
                model.status_id = data["status_id"]
            elif tab_index == 4:
                model = db.query(Roles).filter(Roles.id_role == item_id).first() if item_id else Roles()
                model.role_name = data["name"]
            elif tab_index == 5:
                model = db.query(Status).filter(Status.id_status == item_id).first() if item_id else Status()
                model.status_name = data["name"]
            elif tab_index == 6:
                model = db.query(CriticalityLevels).filter(CriticalityLevels.id_criticality == item_id).first() if item_id else CriticalityLevels()
                model.level_name = data["name"]
            elif tab_index == 7:
                model = db.query(CrewStatus).filter(CrewStatus.id_crew_status == item_id).first() if item_id else CrewStatus()
                model.status_name = data["name"]
            else:
                return False, "Невідомий довідник"

            if not item_id:
                db.add(model)
            db.commit()
            return True, "Дані успішно збережено!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка бази даних: {str(e)}"

def delete_directory_item(tab_index, item_id):
    with SessionLocal() as db:
        try:
            if tab_index == 0: target = db.query(Category).filter(Category.id_category == item_id).first()
            elif tab_index == 1: target = db.query(IssueType).filter(IssueType.id_issue_type == item_id).first()
            elif tab_index == 2: target = db.query(Materials).filter(Materials.id_material == item_id).first()
            elif tab_index == 3: target = db.query(Crew).filter(Crew.id_crew == item_id).first()
            elif tab_index == 4: target = db.query(Roles).filter(Roles.id_role == item_id).first()
            elif tab_index == 5: target = db.query(Status).filter(Status.id_status == item_id).first()
            elif tab_index == 6: target = db.query(CriticalityLevels).filter(CriticalityLevels.id_criticality == item_id).first()
            elif tab_index == 7: target = db.query(CrewStatus).filter(CrewStatus.id_crew_status == item_id).first()
            else: return False, "Невідомий довідник"

            if target:
                db.delete(target)
                db.commit()
                return True, "Запис успішно видалено з системи!"
            return False, "Запис не знайдено."
        except Exception as e:
            db.rollback()
            return False, f"Неможливо видалити елемент (він пов'язаний з іншими таблицями): {str(e)}"