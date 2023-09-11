# imports
import threading
import pyodbc
import os
import spacy
from spacy.matcher import PhraseMatcher
# load default skills data base
from skillNer.general_params import SKILL_DB
# import skill extractor
from skillNer.skill_extractor_class import SkillExtractor
from skillNer.cleaner import Cleaner
from prometheus_client import start_http_server, Counter, Histogram
from loguru import logger
import sys
import argostranslate.package
import argostranslate.translate as tr

def get_skills(cleaner,skill_extractor,inp: str,lang: str = "fr") -> list:
    input_en = tr.translate(inp,lang,"en")
    cleaned = cleaner(input_en)
    res_annot = skill_extractor.annotate(cleaned,0.99)
    
    skills_found=  [k["doc_node_value"] for k in res_annot["results"]["full_matches"] + res_annot["results"]["ngram_scored"]] 
    logger.debug(f"Skills Found : {skills_found}")
    return skills_found
    
def main():

    argostranslate.package.install_from_path("./tr-fr-en.argosmodel")

    # tr = GoogleTranslator(source='fr', target='en')
    cleaner = Cleaner(
                    to_lowercase=True,
                    include_cleaning_functions=["remove_punctuation", "remove_extra_space"]
                )
    logger.info(f"Loading SkillExtractor model")
    # init params of skill extractor
    nlp = spacy.load("en_core_web_lg")
    # logger.info( "Using GPU" if spacy.prefer_gpu() else "Using CPU")

    # init skill extractor
    skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)
    logger.info(f"Initialised SkillExtractor model")

    con_string = f'DRIVER={"ODBC Driver 18 for SQL Server"};SERVER={config["DB_HOST"]};DATABASE={config["DB_NAME"]};UID={config["DB_USER"]};PWD={config["DB_PASSWORD"]};TrustServerCertificate=yes;'
    logger.info(f"Connecting to DB : {con_string}")
    conn = pyodbc.connect(con_string)
    logger.info("DB connected")
    batch_size = int(config["BATCH_SIZE"])
    offset = 0
    with conn.cursor() as curs:
        curs.execute("TRUNCATE TABLE hello_work_skills")
        curs.execute("SELECT COUNT(job_id) FROM hello_work")
        all_jobs = curs.fetchone()
        rows_total.labels(run_id).inc(all_jobs[0])
        while True:
            curs.execute("SELECT job_id,COALESCE(profile_demande,societe_recherche,'') FROM hello_work ORDER BY job_id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",(offset,batch_size))
            descriptions = curs.fetchall()
            logger.debug(f"Feteched Rows , found : {len(descriptions)}")
            if(len(descriptions) == 0):
                break
            bfw = []
            for desc in descriptions:
                with total_time.labels(run_id).time():
                    skills = get_skills(cleaner,skill_extractor,desc[1])
                for skill in set(skills):
                    val = (desc[0] , skill[:100])
                    bfw.append(val)
                rows_processed.labels(run_id).inc()
            logger.debug(f"Writing current Batch : {bfw}")
            if(len(bfw) != 0):
                curs.executemany("INSERT INTO hello_work_skills VALUES (?,?) ",bfw)
            logger.info(f"Finished current Batch , made {rows_processed.labels(run_id)._value.get()} rows")
            offset += batch_size
            conn.commit()
        logger.info("Finished skill extracting") 
        logger.debug("Commited changes to DB")
    conn.close()
    logger.debug("Connection Closed")
    # push_to_gateway(f'{config["PUSH_GATEWAY_HOSTNAME"]}:{config["PUSH_GATEWAY_PORT"]}', job='skill_extractor', registry=registry)


if __name__ == "__main__":

    logger.remove(0)
    logger.add("./logs/skillnier/main_{time}.log",    
    enqueue=True,
    rotation="10 Mb",
    retention="4 weeks",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    )

    logger.add(sys.stderr,    
    enqueue=True,
    backtrace=True,
    diagnose=True,
    level="INFO",
    )
    
    rows_total = Counter('ske_rows','Total Number of rows to process',labelnames=["run_id"])
    rows_processed = Counter('ske_rows_processed','Number of rows processed by the skill extractor',labelnames=["run_id"])
    total_time = Histogram('ske_time',"The time it takes to process the skills of a given description",labelnames=["run_id"])

    config = {
        "METRICS_PORT" : int(os.environ.get("METRICS_PORT","9987")),
        "DB_HOST" : os.environ.get("DB_HOST","localhost"),
        "DB_NAME" :os.environ.get("DB_NAME","ods"),
        "DB_USER" : os.environ.get("DB_USER","sa"),
        "DB_PASSWORD" : os.environ.get("DB_PASSWORD","Adnen123456789!"),
        "BATCH_SIZE" : os.environ.get("BATCH_SIZE","500")
    }
    run_id = os.environ.get("RUN_ID",None)
    logger.info(f"Loaded configuration : {config}")
    start_http_server(config["METRICS_PORT"])
    main()