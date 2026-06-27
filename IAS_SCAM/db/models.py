import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.database import Base

class Category(Base):
    __tablename__ = "category"

    id_category = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), nullable=False)

    # Зв'язки типу "один-до-багатьох" з типами інцидентів та бригадами
    issue_types = relationship("IssueType", back_populates="category")
    crews = relationship("Crew", back_populates="category")


class Roles(Base):
    __tablename__ = "roles"

    id_role = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(45), nullable=False)

    # Зв'язок з користувачами системи
    users = relationship("Users", back_populates="role")


class Status(Base):
    __tablename__ = "status"

    id_status = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String(45), nullable=False)

    # Зв'язки з поточними заявками та журналами зміни статусів
    requests = relationship("Requests", back_populates="status")
    histories = relationship("StatusHistory", back_populates="status")


class CriticalityLevels(Base):
    __tablename__ = "criticality_levels"

    id_criticality = Column(Integer, primary_key=True, autoincrement=True)
    level_name = Column(String(45), nullable=False)

    # Зв'язок із таблицею заявок для визначення пріоритету виконання
    requests = relationship("Requests", back_populates="criticality")


class CrewStatus(Base):
    __tablename__ = "crew_status"

    id_crew_status = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String(45), nullable=False)

    # Зв'язок із станом робочих бригад
    crews = relationship("Crew", back_populates="status")


class Materials(Base):
    __tablename__ = "materials"

    id_material = Column(Integer, primary_key=True, autoincrement=True)
    material_name = Column(String(150), nullable=False)
    unit = Column(String(20))
    price = Column(Numeric(10, 2))

    # Зв'язок із деталізацією витрачених матеріалів у заявках
    request_details = relationship("RequestDetails", back_populates="material")


class Applicants(Base):
    __tablename__ = "applicants"

    id_applicant = Column(Integer, primary_key=True, autoincrement=True)
    last_name = Column(String(50))
    first_name = Column(String(50))
    patronymic = Column(String(50))
    phone = Column(String(20))
    email = Column(String(100))
    account_number = Column(String(45))
    city = Column(String(50))
    street = Column(String(100))
    house_number = Column(String(10))
    entrance = Column(Integer)
    floor = Column(Integer)
    apartment = Column(String(10))

    # Зв'язок із поданими заявками від клієнта
    requests = relationship("Requests", back_populates="applicant")


class IssueType(Base):
    __tablename__ = "issue_type"

    id_issue_type = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("category.id_category"), nullable=False)
    type_name = Column(String(150), nullable=False)

    category = relationship("Category", back_populates="issue_types")
    requests = relationship("Requests", back_populates="issue_type")


class Users(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id_role"), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100))
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1, nullable=False)

    role = relationship("Roles", back_populates="users")
    requests = relationship("Requests", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    histories = relationship("StatusHistory", back_populates="user")


class Crew(Base):
    __tablename__ = "crew"

    id_crew = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("category.id_category"), nullable=False)
    status_id = Column(Integer, ForeignKey("crew_status.id_crew_status"), nullable=False)
    crew_number = Column(String(45), nullable=False)

    category = relationship("Category", back_populates="crews")
    status = relationship("CrewStatus", back_populates="crews")
    requests = relationship("Requests", back_populates="crew")


class Requests(Base):
    __tablename__ = "requests"

    id_request = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id_applicant"))
    issue_type_id = Column(Integer, ForeignKey("issue_type.id_issue_type"), nullable=False)
    status_id = Column(Integer, ForeignKey("status.id_status"), nullable=False)
    criticality_id = Column(Integer, ForeignKey("criticality_levels.id_criticality"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id_user"))
    crew_id = Column(Integer, ForeignKey("crew.id_crew"))

    request_date = Column(DateTime, default=datetime.datetime.utcnow)
    channel = Column(String(45))
    description = Column(Text)
    city = Column(String(50))
    street = Column(String(100))
    house_number = Column(String(10))
    entrance = Column(Integer)
    floor = Column(Integer)
    apartment = Column(String(10))
    completion_date = Column(DateTime, nullable=True)

    applicant = relationship("Applicants", back_populates="requests")
    issue_type = relationship("IssueType", back_populates="requests")
    status = relationship("Status", back_populates="requests")
    criticality = relationship("CriticalityLevels", back_populates="requests")
    user = relationship("Users", back_populates="requests")
    crew = relationship("Crew", back_populates="requests")

    # Конфігурація каскадного видалення пов'язаних сутностей історії та специфікацій
    details = relationship("RequestDetails", back_populates="request", cascade="all, delete-orphan")
    history = relationship("StatusHistory", back_populates="request", cascade="all, delete-orphan")


class RequestDetails(Base):
    __tablename__ = "request_details"

    id_detail = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("requests.id_request", ondelete="CASCADE"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id_material"), nullable=False)
    quantity = Column(Numeric(10, 2))
    total_cost = Column(Numeric(10, 2))

    request = relationship("Requests", back_populates="details")
    material = relationship("Materials", back_populates="request_details")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id_history = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("requests.id_request", ondelete="CASCADE"), nullable=False)
    status_id = Column(Integer, ForeignKey("status.id_status"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id_user"))
    change_date = Column(DateTime, default=datetime.datetime.utcnow)

    request = relationship("Requests", back_populates="history")
    status = relationship("Status", back_populates="histories")
    user = relationship("Users", back_populates="histories")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id_log = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    log_time = Column(DateTime, default=datetime.datetime.utcnow)
    event_type = Column(String(45))
    table_name = Column(String(45))
    record_id = Column(Integer)
    old_value = Column(String(255))
    new_value = Column(String(255))

    user = relationship("Users", back_populates="audit_logs")