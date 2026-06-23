-- ==================================================
-- ПОВНИЙ БЕКАП БАЗИ ДАНИХ СКАМ (СТРУКТУРА + ДАНІ)
-- Створено: 22.06.2026 11:13:28
-- Сумісність: pgAdmin 4 / PostgreSQL Query Tool
-- ==================================================

-- --------------------------------------------------
-- ЧАСТИНА 1: СТВОРЕННЯ СХЕМИ ТА ТАБЛИЦЬ
-- --------------------------------------------------

DROP TABLE IF EXISTS public.status_history CASCADE;
DROP TABLE IF EXISTS public.request_details CASCADE;
DROP TABLE IF EXISTS public.requests CASCADE;
DROP TABLE IF EXISTS public.audit_log CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;
DROP TABLE IF EXISTS public.issue_type CASCADE;
DROP TABLE IF EXISTS public.crew CASCADE;
DROP TABLE IF EXISTS public.status CASCADE;
DROP TABLE IF EXISTS public.roles CASCADE;
DROP TABLE IF EXISTS public.materials CASCADE;
DROP TABLE IF EXISTS public.criticality_levels CASCADE;
DROP TABLE IF EXISTS public.crew_status CASCADE;
DROP TABLE IF EXISTS public.category CASCADE;
DROP TABLE IF EXISTS public.applicants CASCADE;

CREATE TABLE applicants (
	id_applicant SERIAL NOT NULL, 
	last_name VARCHAR(50), 
	first_name VARCHAR(50), 
	patronymic VARCHAR(50), 
	phone VARCHAR(20), 
	email VARCHAR(100), 
	account_number VARCHAR(45), 
	city VARCHAR(50), 
	street VARCHAR(100), 
	house_number VARCHAR(10), 
	entrance INTEGER, 
	floor INTEGER, 
	apartment VARCHAR(10), 
	PRIMARY KEY (id_applicant)
);

CREATE TABLE category (
	id_category SERIAL NOT NULL, 
	category_name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id_category)
);

CREATE TABLE crew_status (
	id_crew_status SERIAL NOT NULL, 
	status_name VARCHAR(45) NOT NULL, 
	PRIMARY KEY (id_crew_status)
);

CREATE TABLE criticality_levels (
	id_criticality SERIAL NOT NULL, 
	level_name VARCHAR(45) NOT NULL, 
	PRIMARY KEY (id_criticality)
);

CREATE TABLE materials (
	id_material SERIAL NOT NULL, 
	material_name VARCHAR(150) NOT NULL, 
	unit VARCHAR(20), 
	price NUMERIC(10, 2), 
	PRIMARY KEY (id_material)
);

CREATE TABLE roles (
	id_role SERIAL NOT NULL, 
	role_name VARCHAR(45) NOT NULL, 
	PRIMARY KEY (id_role)
);

CREATE TABLE status (
	id_status SERIAL NOT NULL, 
	status_name VARCHAR(45) NOT NULL, 
	PRIMARY KEY (id_status)
);

CREATE TABLE crew (
	id_crew SERIAL NOT NULL, 
	category_id INTEGER NOT NULL, 
	status_id INTEGER NOT NULL, 
	crew_number VARCHAR(45) NOT NULL, 
	PRIMARY KEY (id_crew), 
	FOREIGN KEY(category_id) REFERENCES category (id_category), 
	FOREIGN KEY(status_id) REFERENCES crew_status (id_crew_status)
);

CREATE TABLE issue_type (
	id_issue_type SERIAL NOT NULL, 
	category_id INTEGER NOT NULL, 
	type_name VARCHAR(150) NOT NULL, 
	PRIMARY KEY (id_issue_type), 
	FOREIGN KEY(category_id) REFERENCES category (id_category)
);

CREATE TABLE users (
	id_user SERIAL NOT NULL, 
	role_id INTEGER NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(100), 
	password_hash VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id_user), 
	FOREIGN KEY(role_id) REFERENCES roles (id_role)
);

CREATE TABLE audit_log (
	id_log SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	log_time TIMESTAMP WITHOUT TIME ZONE, 
	event_type VARCHAR(45), 
	table_name VARCHAR(45), 
	record_id INTEGER, 
	old_value VARCHAR(255), 
	new_value VARCHAR(255), 
	PRIMARY KEY (id_log), 
	FOREIGN KEY(user_id) REFERENCES users (id_user)
);

CREATE TABLE requests (
	id_request SERIAL NOT NULL, 
	applicant_id INTEGER, 
	issue_type_id INTEGER NOT NULL, 
	status_id INTEGER NOT NULL, 
	criticality_id INTEGER NOT NULL, 
	user_id INTEGER, 
	crew_id INTEGER, 
	request_date TIMESTAMP WITHOUT TIME ZONE, 
	channel VARCHAR(45), 
	description TEXT, 
	city VARCHAR(50), 
	street VARCHAR(100), 
	house_number VARCHAR(10), 
	entrance INTEGER, 
	floor INTEGER, 
	apartment VARCHAR(10), 
	completion_date TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id_request), 
	FOREIGN KEY(applicant_id) REFERENCES applicants (id_applicant), 
	FOREIGN KEY(issue_type_id) REFERENCES issue_type (id_issue_type), 
	FOREIGN KEY(status_id) REFERENCES status (id_status), 
	FOREIGN KEY(criticality_id) REFERENCES criticality_levels (id_criticality), 
	FOREIGN KEY(user_id) REFERENCES users (id_user), 
	FOREIGN KEY(crew_id) REFERENCES crew (id_crew)
);

CREATE TABLE request_details (
	id_detail SERIAL NOT NULL, 
	request_id INTEGER NOT NULL, 
	material_id INTEGER NOT NULL, 
	quantity NUMERIC(10, 2), 
	total_cost NUMERIC(10, 2), 
	PRIMARY KEY (id_detail), 
	FOREIGN KEY(request_id) REFERENCES requests (id_request) ON DELETE CASCADE, 
	FOREIGN KEY(material_id) REFERENCES materials (id_material)
);

CREATE TABLE status_history (
	id_history SERIAL NOT NULL, 
	request_id INTEGER NOT NULL, 
	status_id INTEGER NOT NULL, 
	user_id INTEGER, 
	change_date TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id_history), 
	FOREIGN KEY(request_id) REFERENCES requests (id_request) ON DELETE CASCADE, 
	FOREIGN KEY(status_id) REFERENCES status (id_status), 
	FOREIGN KEY(user_id) REFERENCES users (id_user)
);


-- --------------------------------------------------
-- ЧАСТИНА 2: НАПОВНЕННЯ ТАБЛИЦЬ ДАНИМИ
-- --------------------------------------------------

-- Дані таблиці: public.applicants
INSERT INTO public.applicants ("id_applicant", "last_name", "first_name", "patronymic", "phone", "email", "account_number", "city", "street", "house_number", "entrance", "floor", "apartment") VALUES (4, 'Іваненко', 'Сергій', 'Миколайович', '+380123456789', 'ivanchenko@scam.ua', '01234567890', NULL, 'Перемоги 5', NULL, NULL, 5, '52');
INSERT INTO public.applicants ("id_applicant", "last_name", "first_name", "patronymic", "phone", "email", "account_number", "city", "street", "house_number", "entrance", "floor", "apartment") VALUES (5, 'Шевчук', 'Кирил', 'Костянтинович', '+380123456784', 'kirils@scam.ua', '01234567891', NULL, 'Ковальський провулок 5', NULL, NULL, 5, '510');
INSERT INTO public.applicants ("id_applicant", "last_name", "first_name", "patronymic", "phone", "email", "account_number", "city", "street", "house_number", "entrance", "floor", "apartment") VALUES (6, 'Ков', 'пвпа', 'вавав', '+381234356783', 'bog@scam.ua', '', NULL, 'Автозаводська вулиця 5', NULL, NULL, 5, '59');

-- Дані таблиці: public.category
INSERT INTO public.category ("id_category", "category_name") VALUES (1, 'Газ');
INSERT INTO public.category ("id_category", "category_name") VALUES (3, 'Вода');

-- Дані таблиці: public.crew_status
INSERT INTO public.crew_status ("id_crew_status", "status_name") VALUES (1, 'Зайнята');
INSERT INTO public.crew_status ("id_crew_status", "status_name") VALUES (2, 'Вільна');

-- Дані таблиці: public.criticality_levels
INSERT INTO public.criticality_levels ("id_criticality", "level_name") VALUES (1, 'Низький');
INSERT INTO public.criticality_levels ("id_criticality", "level_name") VALUES (2, 'Середній');
INSERT INTO public.criticality_levels ("id_criticality", "level_name") VALUES (3, 'Високий');

-- Дані таблиці: public.materials
INSERT INTO public.materials ("id_material", "material_name", "unit", "price") VALUES (1, 'гвинт', 'шт', '2.00');

-- Дані таблиці: public.roles
INSERT INTO public.roles ("id_role", "role_name") VALUES (1, 'Адміністратор');
INSERT INTO public.roles ("id_role", "role_name") VALUES (2, 'Керівник');
INSERT INTO public.roles ("id_role", "role_name") VALUES (3, 'Диспетчер/Працівник');

-- Дані таблиці: public.status
INSERT INTO public.status ("id_status", "status_name") VALUES (1, 'Нова');
INSERT INTO public.status ("id_status", "status_name") VALUES (2, 'В роботі');
INSERT INTO public.status ("id_status", "status_name") VALUES (3, 'Виконано');
INSERT INTO public.status ("id_status", "status_name") VALUES (4, 'Скасовано');

-- Дані таблиці: public.crew
INSERT INTO public.crew ("id_crew", "category_id", "status_id", "crew_number") VALUES (1, 1, 1, '123');

-- Дані таблиці: public.issue_type
INSERT INTO public.issue_type ("id_issue_type", "category_id", "type_name") VALUES (1, 1, 'Прорвана труба');

-- Дані таблиці: public.users
INSERT INTO public.users ("id_user", "role_id", "full_name", "email", "password_hash") VALUES (4, 2, 'Коваль Богдан Русланович', 'manager@scam.ua', '$2b$12$S7i5AlR6QJgZVmZ/rMcKmORpYVZnqYyKcweJ1MfXUjX1QC.x6cXcm');
INSERT INTO public.users ("id_user", "role_id", "full_name", "email", "password_hash") VALUES (5, 3, 'Кіян Богдан Володимирович', 'worker@scam.ua', '$2b$12$pI5QXWnKUFKHTV8JDIIFce5FoI2xch0sB0tFyQ87mhPgNeRdLRx7q');
INSERT INTO public.users ("id_user", "role_id", "full_name", "email", "password_hash") VALUES (1, 1, 'Шевчук Кирил Костянтинович', 'admin@scam.ua', '$2b$12$2INLOgWSCXrmVf7Wjt4L7eV570/sBvHiZTKVETqQIBJD55vVHvj5O');

-- Дані таблиці: public.requests
INSERT INTO public.requests ("id_request", "applicant_id", "issue_type_id", "status_id", "criticality_id", "user_id", "crew_id", "request_date", "channel", "description", "city", "street", "house_number", "entrance", "floor", "apartment", "completion_date") VALUES (3, 4, 1, 2, 3, NULL, NULL, '2026-06-22T09:23:35.316220', 'Телефон', 'gg wp', NULL, 'Перемоги 5', NULL, NULL, 5, '52', NULL);
INSERT INTO public.requests ("id_request", "applicant_id", "issue_type_id", "status_id", "criticality_id", "user_id", "crew_id", "request_date", "channel", "description", "city", "street", "house_number", "entrance", "floor", "apartment", "completion_date") VALUES (4, 5, 1, 4, 2, NULL, NULL, '2026-06-22T09:46:27.347079', 'Особистий візит', 'навіть газу нема', NULL, 'Ковальський провулок 5', NULL, NULL, 5, '510', NULL);
INSERT INTO public.requests ("id_request", "applicant_id", "issue_type_id", "status_id", "criticality_id", "user_id", "crew_id", "request_date", "channel", "description", "city", "street", "house_number", "entrance", "floor", "apartment", "completion_date") VALUES (5, 6, 1, 4, 3, NULL, NULL, '2026-06-22T09:48:34.996099', 'Особистий візит', 'jasfhgkljasdhgkSDGsdg', NULL, 'Автозаводська вулиця 5', NULL, NULL, 5, '59', NULL);
INSERT INTO public.requests ("id_request", "applicant_id", "issue_type_id", "status_id", "criticality_id", "user_id", "crew_id", "request_date", "channel", "description", "city", "street", "house_number", "entrance", "floor", "apartment", "completion_date") VALUES (6, 4, 1, 4, 1, NULL, NULL, '2026-06-22T09:52:39.269681', 'Телефон', '', NULL, 'Жилянська вулиця 3', NULL, NULL, 5, '52', NULL);
INSERT INTO public.requests ("id_request", "applicant_id", "issue_type_id", "status_id", "criticality_id", "user_id", "crew_id", "request_date", "channel", "description", "city", "street", "house_number", "entrance", "floor", "apartment", "completion_date") VALUES (7, 4, 1, 4, 1, NULL, 1, '2026-06-22T09:57:43.877366', 'Особистий візит', 'ыа', NULL, 'Соломʼянська вулиця 13', NULL, NULL, 5, '52', NULL);
INSERT INTO public.requests ("id_request", "applicant_id", "issue_type_id", "status_id", "criticality_id", "user_id", "crew_id", "request_date", "channel", "description", "city", "street", "house_number", "entrance", "floor", "apartment", "completion_date") VALUES (8, 4, 1, 4, 1, NULL, NULL, '2026-06-22T11:02:54.246444', 'Телефон', 'Прорив труби у сусідей', NULL, 'Ковальський провулок 5', NULL, NULL, 5, '52', NULL);

-- Дані таблиці: public.request_details
INSERT INTO public.request_details ("id_detail", "request_id", "material_id", "quantity", "total_cost") VALUES (1, 4, 1, '23.00', '46.00');

