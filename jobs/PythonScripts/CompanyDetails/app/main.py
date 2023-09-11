import atexit
from concurrent.futures import ThreadPoolExecutor
import contextlib
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from time import sleep 
import numpy as np
import pandas as pd
from selenium.webdriver.chrome.options import Options
import Levenshtein
from loguru import logger
import argparse
from prometheus_client import start_http_server,Counter,Histogram
import pyodbc

@contextlib.contextmanager
def getConn(cnn):
    try: 
        logger.info(f"Connecting to DB to insert fiche tech : {con_string} ")
        conn = pyodbc.connect(cnn)
        logger.info("Connected succesfully to DB")
        yield conn
    except Exception as e:
        raise e
    finally:
        conn.close()
        logger.info("DB connection closed succesfully")




def create_driver() -> WebDriver:
    logger.debug("CREATING CHROME DRIVER")
    options = ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument("--start-maximized")
    options.add_argument("--blink-settings=imagesEnabled=false")
    for _ in range(3):
        try:
            return webdriver.Remote(command_executor="http://"+hostname+":"+port+"/wd/hub",
        options=options)
            
        except WebDriverException as e:
            logger.error(f"Session creation failed: {str(e)} , retying {_} ... ")
            if _ == 3:
                raise e 
@logger.catch      
def informations_of_the_job(liste_of_all_societies):

#    wait = WebDriverWait(driver , 10)
    driver = create_driver()

    result1 = []    
    result2 = []
    for society in liste_of_all_societies : 
        driver.get("https://annuaire-entreprises.data.gouv.fr")

        search_field = driver.find_element(By.XPATH ,'//div[@id="search-input--lg"]//input' )
        search_field.send_keys(society)
        search_field.send_keys(Keys.ENTER)

        with job_scrap_histogram.labels(threading.currentThread().ident,run_id).time():

            nodes = driver.find_elements(By.XPATH , '//div[@class ="jsx-240357328 result-item"]')

            titres = []

            sous_categories = []
            for i in nodes : 

                titre = i.find_element(By.XPATH , './/div[1]/span[@class = "jsx-240357328"]')
                titres.append(titre.text)
            
                sous_categorie = i.find_element(By.XPATH , './/div[2]')
                sous_categories.append(sous_categorie.text)
            if(len(titres)):
                final_soc  = final_society(titres , sous_categories , society)
                company_details_counter.labels(run_id,"sucess").inc(1)
                link = nodes[titres.index(final_soc)].find_element(By.XPATH , './/a[@class="jsx-240357328 result-link no-style-link"]')
                link.click()
                table1 = driver.find_elements(By.XPATH , '//div[@id = "entreprise"]//div[1]//tr')
        
                d = {}
                for  i in table1 :
                    d[i.find_element( By.XPATH,".//td[1]").text] = i.find_element(By.XPATH, ".//td[2]").text
                sorted_dict_1 = dict(sorted(d.items()))
                sorted_dict_1["query"] = society
                result1.append(sorted_dict_1)
                
                donnes_financieres_existe = driver.find_elements(By.XPATH ,('//div[contains(@class,"title-tabs")]//*[text() = "Données financières"]'))
                if(len(donnes_financieres_existe) == 0):
                    logger.warning(f"there is no financial elements for the society {final_soc}")
                    company_financial_counter.labels(run_id,"failed").inc(1)
                    continue
                donnes_financieres = donnes_financieres_existe[0]
                donnes_financieres.click()
            
                rows = driver.find_elements(By.XPATH , '//table[@class="jsx-2305131526 full-table"]//tr')
                cells = driver.find_elements(By.XPATH  ,'//table[@class="jsx-2305131526 full-table"]//tr//td')
                nb_culumns = int(len(cells) / (len(rows)-1))
                #print(nb_culumns)
                if (nb_culumns == 0 ):
                    logger.warning(f"there is no financial elements for the society {final_soc}")
                    company_financial_counter.labels(run_id,"failed").inc(1)
                else : 
                    all_culumns = []
                    for p in range(nb_culumns):
                        culumns = []
                        for k in range(p,len(cells),nb_culumns) :
                            culumns.append(cells[k].text)
                        all_culumns.append(culumns)
                    #print(all_culumns)
            
                    
                    liste1 = all_culumns[0]
                    for  i in range(1,len(all_culumns)) : 
                        d1={}
                        for  j in range(len(all_culumns[i])) : 
                            d1[liste1[j]]= all_culumns[i][j]
                        #print(d1)

                        selec = '(//div[contains(@class,"title")]//div[1]//span[2])[3]'
                        WebDriverWait(driver,20).until(EC.presence_of_element_located((By.XPATH,selec)))
                        id = driver.find_element(By.XPATH , selec).text
                        d1["id"] = id
                        list_of_headers = ["SALAIRE","TYPE DE CONTRAT","ADRESSE","DATE DE PUBLICATION","TAILLE DE LA SOCIÉTÉ","SECTEUR","SITE WEB","description","DATE DE CRÉATION","AVANTAGES SOCIAUX EMPLOYÉ"]
                        for i in list_of_headers:
                            if (i not in d1.keys()):
                                d1[i] = None
                        sorted_dict_2 = dict(sorted(d1.items()))
                        result2.append(sorted_dict_2)

                    company_financial_counter.labels(run_id,"sucess").inc(1)
            else :
                logger.warning(f"there is no results for the society : {society}" )
                company_details_counter.labels(run_id,"failed").inc(1)

    donnees_financieres = pd.DataFrame(result2)[['id','Date de clôture','Excédent Brut d’Exploitation','Marge brute',"◆ Chiffre d’affaires",'◆ Résultat net']] if len(result2) > 0 else pd.DataFrame()
    fiche_tech =  pd.DataFrame(result1)[["query","Activité principale (NAF/APE)","Adresse postale ","Code NAF/APE","Date de création","Dernière modification des données Insee","Dénomination","Nature juridique","SIREN","SIRET du siège social","Taille de la structure","Tranche effectif salarié de la structure"]] if len(result1) > 0 else pd.DataFrame()
    write_financial_data(donnees_financieres.to_numpy())
    write_fiche_tech(fiche_tech.to_numpy())

def write_financial_data(fin_data):
    fin_data = list(map(lambda d: tuple(d),fin_data))
    if len(fin_data) > 0:
        with getConn(con_string) as conn:
            with conn.cursor() as curs:
                curs.executemany("INSERT INTO company_financials(siren,date_cloture,excedant_brut_exploitation,marge_brut,chiffre_affaire,resultat_net) VALUES (?,?,?,?,?,?)",fin_data) 
                conn.commit()
    logger.info("Inserted Financial data Sucesfully") 
def write_fiche_tech(fiche_tech):
    fiche_tech = list(map(lambda d: tuple(d),fiche_tech))
    if len(fiche_tech) > 0:
        with getConn(con_string) as conn:
            with conn.cursor() as curs:
                curs.executemany("INSERT INTO company_details(query,activite_principale,address_postal,code_naf,date_creation,derniere_modification,nom,forme_juridique,siren,siret_siege,taille_societe,tranche_effective) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",fiche_tech) 
                conn.commit()
    logger.info("Inserted fiche tech Sucesfully")       
def final_society (titres , sous_categories , job):
    distances = []
    for i in titres : 
        distances.append(Levenshtein.distance(job.upper(), i.upper()))
    

    keys = ["informatique" , "consulting" , "logiciels" , "developpement"  , "data"]
    result = []
    for  i in sous_categories : 
       
        somme = 0 
        final_somme = 0
        tokens = i.split(" ")
        for  j in keys :
            for t in tokens:
                somme+= Levenshtein.distance(j.upper(), t.upper())
        somme = somme/ len(keys) / len(tokens)
        final_somme = somme + distances[sous_categories.index(i)]
        result.append(final_somme)
    

 
    final_sc = titres[result.index(min(result))]
    return final_sc
def getCompanies():
    
    if companies_list != None:
        return companies_list

    companies = []
    with getConn(con_string) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT DISTINCT( {db_source_column} ) FROM {db_source}")
            companies = cur.fetchall()
    result = list(map(lambda d: d[0],companies))
    total_companies_counter.labels(run_id).inc(len(result))
    return result

def closeAllThreads(executor: ThreadPoolExecutor,start_time):
    def exitfn():
        end_time = time.time_ns()
        logger.info(f"Total Time in ns {end_time - start_time}")
        executor.shutdown(wait=False)
    return exitfn
def clearTable():
    with getConn(con_string) as conn:
        conn.execute("TRUNCATE TABLE company_details")
        conn.execute("TRUNCATE TABLE company_financials").commit()
        
        logger.info("Truncated Sucesfully")  

def main():
    companies = getCompanies()
    logger.debug(f"Found : {companies}")

    clearTable()

    pool = ThreadPoolExecutor(max_workers=thread_num)
    c.labels(run_id).inc(pool._max_workers)
    atexit.register(closeAllThreads(pool,time.time_ns()))
    splits = np.array_split(companies,thread_num)
    logger.info(f"Speperated companies into {thread_num} chunks")
    for chunk in splits:
        if(len(chunk) == 0):
            logger.warning("Empty Chunks , total number is lower than thread number")
            continue
        pool.submit(informations_of_the_job,list(chunk))
    pool.shutdown(wait=True)


import sys
import os
if __name__ == "__main__":
    logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<magenta>Thread-[{thread}]</magenta> : <level>{message}</level>"
    )  # Default values
    logger.remove(0)
    logger.add("./logs/companies/main_{time}.log",    
    enqueue=True,
    rotation="10 Mb",
    retention="4 weeks",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    format=logger_format)

    logger.add(sys.stderr,    
    enqueue=True,
    backtrace=True,
    diagnose=True,
    level="INFO",
    format=logger_format)
    start_http_server(9777)
    # total_page_counter = Counter("scrap_pages","The number of pages found",labelnames=['keyword','local'])
    total_companies_counter = Counter("company_count_total","The number of companies to scrap",labelnames=["run_id"])
    company_details_counter = Counter("company_details_scrapped_total","The number of companies details scrapped",labelnames=["run_id","status"])
    company_financial_counter = Counter("company_financial_scrapped_total","The number of comapnies financial scrapped",labelnames=["run_id","status"])
    job_scrap_histogram = Histogram("company_scrap_duration","The duration it takes to scrap a single company",labelnames=['thread_id',"run_id"])
    c = Counter("company_worker_num","The number of thread workers for scrapping",labelnames=["run_id"])
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies",default=None)
    parser.add_argument("--db-source",required=False,default="hello_work_processed")
    parser.add_argument("--db-source-column",required=False,default="cf_entreprise")
    parser.add_argument("--thread-num",default=os.cpu_count())
    args = parser.parse_args()

    companies_list = args.companies.split(",") if args.companies != None else None
    thread_num = int(args.thread_num)
    db_source = args.db_source
    db_source_column = args.db_source_column
    if(companies_list == None):
        assert db_source != None 
        assert db_source_column != None

    config = {
            "DB_HOST" : os.environ.get("DB_HOST","localhost"),
            "DB_NAME" :os.environ.get("DB_NAME","ods"),
            "DB_USER" : os.environ.get("DB_USER","sa"),
            "DB_PASSWORD" : os.environ.get("DB_PASSWORD","Adnen123456789!")
        }
    
    con_string = f'DRIVER={"ODBC Driver 18 for SQL Server"};SERVER={config["DB_HOST"]};DATABASE={config["DB_NAME"]};UID={config["DB_USER"]};PWD={config["DB_PASSWORD"]};TrustServerCertificate=yes;'

    hostname=os.environ.get("HUB_HOSTNAME","localhost")
    port=os.environ.get("HUB_PORT","4444")
    run_id=os.environ.get("RUN_ID",None)
    
    main()