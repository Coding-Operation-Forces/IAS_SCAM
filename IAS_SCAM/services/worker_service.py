# services/worker_service.py
from datetime import datetime
from db.database import SessionLocal
from db.models import (Requests, Applicants, RequestDetails, 
                       IssueType, Category, CriticalityLevels, Status, Materials, Crew)

# ==========================================
# 1. ПРИЙОМ ЗАЯВОК (Зчитування)
# ==========================================
def get_active_requests():
    """Отримує список всіх звернень для таблиці разом з описом та ID бригади."""
    with SessionLocal() as db:
        try:
            requests = db.query(Requests).order_by(Requests.request_date.desc()).all()
            result = []
            for r in requests:
                applicant = f"{r.applicant.last_name} {r.applicant.first_name}" if r.applicant else "Невідомо"
                address = f"{r.street or ''}, кв. {r.apartment or ''}".strip(", ")
                if not address: address = "Не вказано"
                
                issue_type = r.issue_type.type_name if r.issue_type else "Не визначено"
                criticality = r.criticality.level_name if r.criticality else "Не визначено"
                status = r.status.status_name if r.status else "Нова"
                crew_num = f"Бригада №{r.crew.crew_number}" if r.crew else "Не призначено"
                
                request_time = r.request_date.strftime("%d.%m.%Y %H:%M") if r.request_date else ""
                
                result.append([
                    r.id_request,                  # 0
                    request_time,                  # 1
                    applicant,                     # 2
                    address,                       # 3
                    issue_type,                    # 4
                    criticality,                   # 5
                    status,                        # 6
                    crew_num,                      # 7
                    r.description or "Немає опису",# 8 -> НОВИЙ СТОВПЕЦЬ ОПИСУ
                    r.channel or "-",              # 9
                    r.crew_id                      # 10 -> Прихований ID бригади для UI
                ])
            return result
        except Exception as e:
            print(f"Помилка завантаження заявок: {e}")
            return []

# ==========================================
# МОДИФІКАЦІЯ: МАСОВЕ ОНОВЛЕННЯ ДАНИХ ЗАЯВКИ (СТАТУС + БРИГАДА)
# ==========================================
def update_requests_data(updates):
    """
    Масово оновлює статуси та призначені бригади для заявок.
    updates - це список словників: [{'req_id': 1, 'status_id': 3, 'crew_id': 2}, ...]
    """
    if not updates:
        return True, "Немає змін для збереження."
        
    with SessionLocal() as db:
        try:
            for u in updates:
                req = db.query(Requests).filter(Requests.id_request == u['req_id']).first()
                if req:
                    if 'status_id' in u:
                        req.status_id = u['status_id']
                    if 'crew_id' in u:
                        # Якщо обрано 0 (значення "Не призначено"), записуємо NULL (None)
                        req.crew_id = u['crew_id'] if u['crew_id'] != 0 else None
            db.commit()
            return True, "Зміни (статуси та бригади) успішно збережено в базі!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка оновлення бази даних: {str(e)}"


# ==========================================
# 2. РЕЄСТРАЦІЯ ЗВЕРНЕНЬ (Створення)
# ==========================================
def get_applicant_by_account(account_number):
    """Шукає заявника за особовим рахунком."""
    with SessionLocal() as db:
        try:
            applicant = db.query(Applicants).filter(Applicants.account_number == account_number).first()
            if applicant:
                return {
                    "found": True,
                    "applicant_id": applicant.id_applicant,
                    "lname": applicant.last_name or "",
                    "fname": applicant.first_name or "",
                    "mname": applicant.patronymic or "",
                    "phone": applicant.phone or "",
                    "email": applicant.email or "",
                    "street": applicant.street or "",
                    "apartment": applicant.apartment or "",
                    "floor": str(applicant.floor) if applicant.floor else ""
                }
            return {"found": False}
        except Exception as e:
            print(f"Помилка пошуку за рахунком: {e}")
            return {"found": False}

def register_new_request(app_data, req_data):
    """Створює заявку, за необхідності створюючи нового заявника."""
    with SessionLocal() as db:
        try:
            floor_val = int(app_data["floor"]) if app_data["floor"].isdigit() else None

            applicant_id = app_data.get("applicant_id")
            if not applicant_id:
                new_applicant = Applicants(
                    account_number=app_data["account"],
                    last_name=app_data["lname"],
                    first_name=app_data["fname"],
                    patronymic=app_data["mname"],
                    phone=app_data["phone"],
                    email=app_data["email"],
                    street=app_data["street"],
                    apartment=app_data["apartment"],
                    floor=floor_val
                )
                db.add(new_applicant)
                db.flush()
                applicant_id = new_applicant.id_applicant

            default_status = db.query(Status).filter(Status.status_name.ilike("%Нова%")).first()
            if not default_status:
                default_status = db.query(Status).first()
                
            if not default_status:
                db.rollback()
                return False, "У системі не налаштовано довідник статусів! Заповніть таблицю 'status'."

            status_id = default_status.id_status

            new_request = Requests(
                request_date=datetime.now(),
                applicant_id=applicant_id,
                issue_type_id=req_data["issue_type_id"],
                criticality_id=req_data["criticality_id"],
                status_id=status_id,
                channel=req_data["channel"],
                description=req_data["description"],
                street=app_data["street"],
                apartment=app_data["apartment"],
                floor=floor_val
            )
            db.add(new_request)
            db.commit()
            return True, "Заявку успішно зареєстровано!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка бази даних: {str(e)}"

# ==========================================
# 3. ВИКОНАННЯ РОБІТ ТА СПИСАННЯ
# ==========================================
def get_used_materials_report():
    """Повертає список вже списаних матеріалів (RequestDetails)."""
    with SessionLocal() as db:
        try:
            records = db.query(RequestDetails).order_by(RequestDetails.id_detail.desc()).all()
            return [
                [
                    r.id_detail, 
                    f"Заявка #{r.request_id}", 
                    r.material.material_name if r.material else "Невідомо", 
                    f"{r.quantity} {r.material.unit if r.material else ''}", 
                    f"{float(r.total_cost):.2f} грн"
                ] for r in records
            ]
        except Exception:
            return []

def write_off_material(request_id, material_id, quantity):
    """Списує матеріал на конкретну заявку (RequestDetails)."""
    with SessionLocal() as db:
        try:
            request_exists = db.query(Requests).filter(Requests.id_request == request_id).first()
            if not request_exists:
                return False, "Заявку з таким ID не знайдено!"

            material = db.query(Materials).filter(Materials.id_material == material_id).first()
            if not material:
                return False, "Матеріал не знайдено!"

            qty_float = float(quantity)
            total_cost = float(material.price) * qty_float

            usage = RequestDetails(
                request_id=request_id,
                material_id=material_id,
                quantity=qty_float,
                total_cost=total_cost
            )
            db.add(usage)
            db.commit()
            return True, "Матеріал успішно додано до звіту!"
        except ValueError:
            return False, "Некоректний формат кількості!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка БД: {str(e)}"

def get_issue_mapping():
    """Генерує словник {Категорія: [(id_типу, Назва_типу), ...]} для динамічних комбобоксів."""
    with SessionLocal() as db:
        try:
            types = db.query(IssueType).join(Category).all()
            mapping = {}
            for t in types:
                cat_name = t.category.category_name
                if cat_name not in mapping:
                    mapping[cat_name] = []
                mapping[cat_name].append((t.id_issue_type, t.type_name))
            return mapping
        except Exception:
            return {}