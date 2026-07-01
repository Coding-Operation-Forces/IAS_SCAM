import re
from datetime import datetime
from db.database import SessionLocal
from db.models import Requests, Applicants, RequestDetails, IssueType, Category, Status, Materials, StatusHistory, CriticalityLevels
import services.audit_service as audit_service

def get_active_requests(show_all=False):
    """Вибірка списку заявок зі зваженим багаторівневим сортуванням за станом та критичністю."""
    with SessionLocal() as db:
        try:
            query = db.query(Requests)
            if not show_all:
                query = query.join(Status).filter(
                    ~Status.status_name.ilike("%Виконан%"),
                    ~Status.status_name.ilike("%Скасован%")
                )
            requests = query.all()

            def request_sorting_key(r):
                s_name = r.status.status_name.lower() if r.status else ""
                c_name = r.criticality.level_name.lower() if r.criticality else ""
                if "нова" in s_name:
                    s_weight = 1
                elif "робот" in s_name:
                    s_weight = 2
                else:
                    s_weight = 3
                if "критич" in c_name:
                    c_weight = 1
                elif "висок" in c_name:
                    c_weight = 2
                elif "середн" in c_name:
                    c_weight = 3
                else:
                    c_weight = 4
                return (s_weight, c_weight, -(r.request_date.timestamp() if r.request_date else 0))

            requests.sort(key=request_sorting_key)
            result = []
            for r in requests:
                street_full = r.street or ""
                if getattr(r, 'house_number', None): street_full += f", {r.house_number}"
                result.append({
                    "id": r.id_request, "request_date": r.request_date, "completion_date": r.completion_date,
                    "applicant_last": r.applicant.last_name if r.applicant else "",
                    "applicant_first": r.applicant.first_name if r.applicant else "",
                    "street": street_full, "apartment": r.apartment or "",
                    "issue_type": r.issue_type.type_name if r.issue_type else "Не визначено",
                    "criticality": r.criticality.level_name if r.criticality else "Не визначено",
                    "status": r.status.status_name if r.status else "Нова",
                    "crew_number": r.crew.crew_number if r.crew else None,
                    "description": r.description or "Немає опису", "channel": r.channel or "-", "crew_id": r.crew_id
                })
            return result
        except Exception as e:
            print(f"Помилка завантаження заявок: {e}")
            return []

def update_requests_data(updates, current_user_id=None):
    """Групове оновлення параметрів стану та призначення робочих бригад на інциденти."""
    if not updates: return True, "Немає змін."
    user_id_log = current_user_id if current_user_id else 1
    with SessionLocal() as db:
        try:
            for u in updates:
                req = db.query(Requests).filter(Requests.id_request == u['req_id']).first()
                if req:
                    if 'status_id' in u and req.status_id != u['status_id']:
                        old_status_id = str(req.status_id)
                        req.status_id = u['status_id']

                        status_obj = db.query(Status).filter(Status.id_status == u['status_id']).first()
                        if status_obj and "виконан" in status_obj.status_name.lower():
                            if not req.completion_date: req.completion_date = datetime.now()
                        else:
                            req.completion_date = None

                        history_entry = StatusHistory(
                            request_id=req.id_request, status_id=u['status_id'],
                            user_id=current_user_id, change_date=datetime.now()
                        )
                        db.add(history_entry)

                        audit_service.log_action(
                            user_id=user_id_log, event_type="UPDATE",
                            table_name="requests.status_id", record_id=req.id_request,
                            old_value=old_status_id, new_value=str(u['status_id'])
                        )

                    if 'crew_id' in u:
                        new_crew_val = u['crew_id'] if u['crew_id'] != 0 else None

                        if req.crew_id != new_crew_val:
                            old_crew_id = str(req.crew_id or "0")
                            req.crew_id = new_crew_val

                            audit_service.log_action(
                                user_id=user_id_log, event_type="UPDATE",
                                table_name="requests.crew_id", record_id=req.id_request,
                                old_value=old_crew_id, new_value=str(u['crew_id'])
                            )

            db.commit()
            return True, "Зміни успішно збережено в базі!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка бази даних: {str(e)}"

def get_applicant_by_account(account_number):
    with SessionLocal() as db:
        try:
            applicant = db.query(Applicants).filter(Applicants.account_number == account_number).first()
            if applicant:
                full_street = applicant.street or ""
                if applicant.house_number: full_street += f" {applicant.house_number}"
                return {
                    "found": True, "applicant_id": applicant.id_applicant, "lname": applicant.last_name or "",
                    "fname": applicant.first_name or "", "mname": applicant.patronymic or "",
                    "phone": applicant.phone or "",
                    "email": applicant.email or "", "street": full_street.strip(),
                    "apartment": applicant.apartment or "",
                    "floor": str(applicant.floor) if applicant.floor else "",
                    "entrance": str(applicant.entrance) if applicant.entrance else ""
                }
            return {"found": False}
        except Exception:
            return {"found": False}

def register_new_request(app_data, req_data):
    """Реєстрація нової заявки клієнта, включно з автоматичним парсингом адреси регулярними виразами."""
    with SessionLocal() as db:
        try:
            floor_val = int(app_data["floor"]) if app_data["floor"].isdigit() else None
            entrance_val = int(app_data["entrance"]) if app_data.get("entrance", "").isdigit() else None
            full_address = app_data["street"].strip()
            match = re.search(r'[, ]+(\d+[-/a-zA-Zа-яА-ЯіІїЇєЄ]*)$', full_address)
            if match:
                house_number = match.group(1)
                street = full_address[:match.start()].strip(', ')
            else:
                street = full_address
                house_number = ""

            applicant_id = app_data.get("applicant_id")
            if not applicant_id:
                new_applicant = Applicants(
                    account_number=app_data["account"], last_name=app_data["lname"], first_name=app_data["fname"],
                    patronymic=app_data["mname"], phone=app_data["phone"], email=app_data["email"], city="Київ",
                    street=street, house_number=house_number, entrance=entrance_val, apartment=app_data["apartment"],
                    floor=floor_val
                )
                db.add(new_applicant)
                db.flush()
                applicant_id = new_applicant.id_applicant

            default_status = db.query(Status).filter(Status.status_name.ilike("%Нова%")).first()
            if not default_status: default_status = db.query(Status).first()
            if not default_status: return False, "У системі не налаштовано довідник статусів!"

            current_user_id = req_data.get("user_id")
            user_id_log = current_user_id if current_user_id else 1

            new_request = Requests(
                request_date=datetime.now(), applicant_id=applicant_id, issue_type_id=req_data["issue_type_id"],
                criticality_id=req_data["criticality_id"], status_id=default_status.id_status,
                channel=req_data["channel"],
                description=req_data["description"], city="Київ", street=street, house_number=house_number,
                entrance=entrance_val, apartment=app_data["apartment"], floor=floor_val, user_id=current_user_id
            )
            db.add(new_request)
            db.flush()

            first_history = StatusHistory(
                request_id=new_request.id_request, status_id=default_status.id_status,
                user_id=current_user_id, change_date=datetime.now()
            )
            db.add(first_history)

            issue_obj = db.query(IssueType).filter(IssueType.id_issue_type == req_data["issue_type_id"]).first()
            crit_obj = db.query(CriticalityLevels).filter(CriticalityLevels.id_criticality == req_data["criticality_id"]).first()

            fields_to_log = [
                ("account_number", "Не існувало", app_data['account']),
                ("applicant_name", "Не існувало", f"{app_data['lname']} {app_data['fname']}"),
                ("street", "Не існувало", street),
                ("house_number", "Не існувало", house_number),
                ("apartment", "Не існувало", app_data['apartment'] or "—"),
                ("channel", "Не існувало", req_data["channel"]),
                ("issue_type", "Не існувало", issue_obj.type_name if issue_obj else f"ID {req_data['issue_type_id']}"),
                ("criticality", "Не існувало", crit_obj.level_name if crit_obj else f"ID {req_data['criticality_id']}"),
                ("description", "Не існувало", req_data["description"]),
                ("status", "Не існувало", default_status.status_name)
            ]

            for field_name, old_f, new_f in fields_to_log:
                audit_service.log_action(
                    user_id=user_id_log,
                    event_type="INSERT",
                    table_name=f"requests.{field_name}",
                    record_id=new_request.id_request,
                    old_value=old_f,
                    new_value=str(new_f)
                )

            db.commit()
            return True, "Заявку успішно зареєстровано!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка: {str(e)}"

def get_used_materials_report():
    with SessionLocal() as db:
        try:
            records = db.query(RequestDetails).order_by(RequestDetails.id_detail.desc()).all()
            return [{
                "id": r.id_detail, "request_id": r.request_id,
                "material_name": r.material.material_name if r.material else "Невідомо",
                "quantity": r.quantity, "unit": r.material.unit if r.material else "", "total_cost": float(r.total_cost)
            } for r in records]
        except Exception:
            return []

def write_off_material(request_id, material_id, quantity, user_id=1):
    """Списання матеріалів під виконання робіт із декомпозицією полів у журнал системного аудиту."""
    with SessionLocal() as db:
        try:
            if not db.query(Requests).filter(Requests.id_request == request_id).first():
                return False, "Заявку не знайдено!"

            material = db.query(Materials).filter(Materials.id_material == material_id).first()
            if not material:
                return False, "Матеріал не знайдено!"

            qty_float = float(quantity)

            usage = RequestDetails(
                request_id=request_id,
                material_id=material_id,
                quantity=qty_float,
                total_cost=float(material.price) * qty_float
            )
            db.add(usage)
            db.flush()

            fields_to_log = [
                ("request_id", "Не існувало", request_id),
                ("material_id", "Не існувало", material_id),
                ("quantity", "Не існувало", f"{qty_float} {material.unit or ''}".strip())
            ]

            for field_name, old_f, new_f in fields_to_log:
                audit_service.log_action(
                    user_id=user_id,
                    event_type="WRITE_OFF",
                    table_name=f"request_details.{field_name}",
                    record_id=usage.id_detail,
                    old_value=old_f,
                    new_value=str(new_f)
                )

            db.commit()
            return True, "Матеріал успішно додано!"
        except Exception as e:
            db.rollback()
            return False, f"Помилка: {str(e)}"

def get_issue_mapping():
    """Складання словника відповідності категорій та специфічних типів аварій."""
    with SessionLocal() as db:
        try:
            categories = db.query(Category).outerjoin(IssueType).all()
            mapping = {}
            
            for c in categories:
                mapping[c.category_name] = []
                for t in c.issue_types:
                    mapping[c.category_name].append((t.id_issue_type, t.type_name))
                    
            return mapping
        except Exception as e:
            print(f"Помилка завантаження категорій: {e}")
            return {}