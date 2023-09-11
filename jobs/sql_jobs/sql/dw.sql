-- CREATE DATABASE jobs_dw;

CREATE TABLE jobs_dw.dbo.contract_regime_dim (
	regime_id BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
	regime_code VARCHAR(5) NOT NULL,
	regime VARCHAR(50) NOT NULL,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
);
SET IDENTITY_INSERT jobs_dw.dbo.contract_regime_dim ON;
INSERT INTO jobs_dw.dbo.contract_regime_dim (regime_id,regime_code,regime) VALUES (0,'N/A','N/A');
SET IDENTITY_INSERT jobs_dw.dbo.contract_regime_dim OFF;

CREATE TABLE jobs_dw.dbo.contract_teletravail_dim (
	teletravail_id BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
	teletravail_code VARCHAR(4) NOT NULL,
	teletravail VARCHAR(50) NOT NULL,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
);


SET IDENTITY_INSERT jobs_dw.dbo.contract_teletravail_dim ON;
INSERT INTO jobs_dw.dbo.contract_teletravail_dim (teletravail_id,teletravail_code,teletravail) VALUES (0,'N/A','N/A');
SET IDENTITY_INSERT jobs_dw.dbo.contract_teletravail_dim OFF;

CREATE TABLE jobs_dw.dbo.contract_type_dim (
	type_id BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
	type_code VARCHAR(5) NOT NULL,
	type VARCHAR(50) NOT NULL,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
);

SET IDENTITY_INSERT jobs_dw.dbo.contract_type_dim ON;
INSERT INTO jobs_dw.dbo.contract_type_dim (type_id,type_code,type) VALUES (0,'N/A','N/A');
SET IDENTITY_INSERT jobs_dw.dbo.contract_type_dim OFF;

CREATE TABLE jobs_dw.dbo.company_dim (
	company_id BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
	company_identifier VARCHAR(50),
	nom VARCHAR(100) NOT NULL,
	employee_num_min INTEGER,
	employee_num_max INTEGER,
	secteur_societe VARCHAR(250),
	forme_juridique VARCHAR(250),
	taille_societe VARCHAR(250),
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
);

CREATE TABLE jobs_dw.dbo.localisation (
	localisation_id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
	address VARCHAR(100) NOT NULL,
	region VARCHAR(100) NOT NULL,
	city VARCHAR(100) NOT NULL,
	score FLOAT NOT NULL,
	latitude  FLOAT NOT NULL,
	longitude  FLOAT NOT NULL,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
);


SET IDENTITY_INSERT jobs_dw.dbo.localisation ON;
INSERT INTO jobs_dw.dbo.localisation (localisation_id,address,region,city,score,latitude,longitude) VALUES (0,'N/A','N/A','N/A',0,0,0);
SET IDENTITY_INSERT jobs_dw.dbo.localisation OFF;


CREATE TABLE jobs_dw.dbo.date_dim (
	date_id DATE NOT NULL PRIMARY KEY,
	year INT NOT NULL,
	month INT NOT NULL,
	day INT NOT NULL,
	day_of_week INT NOT NULL,
	day_of_year INT NOT NULL,
	quarter INT NOT NULL,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)

CREATE TABLE jobs_dw.dbo.job (
	job_id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
	nom VARCHAR(200) NOT NULL,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
)


CREATE TABLE jobs_dw.dbo.skills (
	skill_id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
	nom VARCHAR(200) NOT NULL,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
)


CREATE TABLE jobs_dw.dbo.job_offers_fact  (
	job_offer_id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
	source_job_id VARCHAR(50) NOT NULL UNIQUE,
	job_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.job(job_id),
	company_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.company_dim(company_id),
	date_id DATE NOT NULL REFERENCES jobs_dw.dbo.date_dim(date_id),
	localisation_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.localisation(localisation_id),
	type_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.contract_type_dim(type_id),
	teletravail_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.contract_teletravail_dim(teletravail_id),
	regime_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.contract_regime_dim(regime_id),
	years_experience VARCHAR(30),
	education VARCHAR(40),
	min_salary INT,
	max_salary INT,
	duree INT,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
)

CREATE TABLE jobs_dw.dbo.job_skills_fact  (
	job_skill_id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
	source_job_id VARCHAR(50) NOT NULL,
	job_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.job(job_id),
	company_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.company_dim(company_id),
	date_id DATE NOT NULL REFERENCES jobs_dw.dbo.date_dim(date_id),
	localisation_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.localisation(localisation_id),
	skill_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.skills(skill_id),
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
)

CREATE TABLE jobs_dw.dbo.company_financials_fact (
	id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
	company_id BIGINT NOT NULL REFERENCES jobs_dw.dbo.company_dim(company_id),
	date_id DATE NOT NULL REFERENCES jobs_dw.dbo.date_dim(date_id),
	excedant_brut_exploitation float,
	marge_brut  float,
	chiffre_affaire  float,
	resultat_net  float,
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_update_timestamp DATETIME DEFAULT NULL
);
	