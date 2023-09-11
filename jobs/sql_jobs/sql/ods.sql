-- CREATE DATABASE ods;

	CREATE TABLE ods.dbo.hello_work (
		id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
		keyword VARCHAR(100) NOT NULL,
		country varchar(10),
		job_id int NOT NULL,
		poste varchar(200),
		entreprise varchar(200),
		localisation varchar(200),
		contract varchar(200),
		salaire varchar(200),
		resume varchar(MAX),
		societe_recherche varchar(MAX),
		profile_demande varchar(MAX),
		scrap_timestamp varchar(200),
		insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
	);
	
	CREATE TABLE ods.dbo.hello_work_processed (
		job_offer_source_id int NOT NULL PRIMARY KEY,
		country varchar(10),
		keyword VARCHAR(100) NOT NULL,
		cf_entreprise varchar(200),
		cf_job varchar(200),
		cf_localisation varchar(200),
		cf_date_year INT NOT NULL,
		cf_date_month INT NOT NULL,
		cf_date_day INT NOT NULL,
		cf_teletravail VARCHAR(5),
		cf_regime VARCHAR(5),
		cf_type VARCHAR(5),
		contract varchar(200),
		salaire varchar(200),
		resume varchar(MAX),
		societe_recherche varchar(MAX),
		profile_demande varchar(MAX),
		scrap_timestamp DATETIME,
		insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
	);

CREATE TABLE ods.dbo.hello_work_skills (
	job_id VARCHAR(30) NOT NULL,
	skill VARCHAR(100) NOT NULL,
	CONSTRAINT pk_mixte_hello_work_skills PRIMARY KEY (job_id,skill)	
)



CREATE TABLE ods.dbo.company_details (
	id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
	query VARCHAR(250) NOT NULL,
	activite_principale VARCHAR(250),
	address_postal VARCHAR(250),
	code_naf VARCHAR(30),
	date_creation VARCHAR(15) NOT NULL,
	derniere_modification VARCHAR(15) NOT NULL,
	nom VARCHAR(250) NOT NULL,
	forme_juridique VARCHAR(250),
	siren VARCHAR(15) NOT NULL,
	siret_siege VARCHAR(50),
	taille_societe VARCHAR(250),
	tranche_effective VARCHAR(250),
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)

CREATE TABLE ods.dbo.company_financials (
	id BIGINT NOT NULL IDENTITY(1,1)  PRIMARY KEY,
	siren VARCHAR(15) NOT NULL,
	date_cloture VARCHAR(20) NOT NULL,
	excedant_brut_exploitation VARCHAR(10),
	marge_brut VARCHAR(10),
	chiffre_affaire VARCHAR(10),
	resultat_net VARCHAR(10),
	insertion_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)