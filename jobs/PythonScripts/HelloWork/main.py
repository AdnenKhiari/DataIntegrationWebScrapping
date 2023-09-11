from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import json
import threading
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from datetime import date, timezone 
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import re
from enum import Enum
from BufferWriter.BufferWriter import BufferWriter
from loguru import logger
import atexit
from datetime import datetime
from prometheus_client import Counter, Histogram
from prometheus_client import start_http_server
from dateutil import parser as date_parser

def get_date_index(dt: datetime):
    if(dt == None):
        return 0
    nw = datetime.now(timezone.utc)
    diff = nw - dt
    if(diff.days == 0):
        return 1
    elif (diff.days <= 3):
        return 2
    elif (diff.days <= 7):
        return 3
    elif (diff.days <= 28):
            return 4
    return 0

def send_commande(driver : WebDriver , cmd :str, params : dict ={}):
  resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
  url = driver.command_executor._url + resource
  body = json.dumps({'cmd': cmd, 'params': params})
  response = driver.command_executor._request('POST', url, body)
  return response.get('value')

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
            print(f"Session creation failed: {str(e)} , retying {_} ... ")
            if _ == 3:
                raise e    
def goToUrl(driver:WebDriver,page: str):
    uri = driver.current_url
    new_uri=re.sub("p=\d+","p="+str(page),uri)
    driver.get(new_uri)
    logger.debug(f"Going to Page : {page} , {uri} => {new_uri}")
    # sleep(400)
def init(driver: WebDriver,code: str,key: str,checkPagination = True):
    driver.get("https://www.hellowork.com/fr-fr/emploi/recherche.html?k=bi&p=1&mode=pagination")
    cks_path = '//div[@class="hw-cc-modal__body"]/button'
    #$x("//button[@id='hw-cc-notice-accept-btn']")
    
    try:
        WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,cks_path)))
        ignore_cookie = driver.find_element(By.XPATH,cks_path)
        ignore_cookie.click()
        lang_select_path ='//form//div[@class="tw-relative"]//select'
        WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,lang_select_path)))
        select = driver.find_element(By.XPATH,lang_select_path)
        select.find_element(By.XPATH,"//option[@value='"+code.upper()+"']").click()
        ok_btn = driver.find_element(By.XPATH,'//form//div[@class="tw-relative"]//following-sibling::button')
        ok_btn.click()
        error_text = driver.find_elements(By.XPATH,'//form//div[@class="tw-relative"]//following-sibling::div')
        if(len(error_text) > 0):
            raise Exception("Language "+ code + " not supported")
    except:
        logger.debug("Location and cookie are set")
    
    search_btn = driver.find_element(By.XPATH,"(//div[@class='whatinput']//input)[2]")
    search_btn.click()
    search_btn.clear()
    search_btn.send_keys(key)
    search_btn.send_keys(Keys.ENTER)

    date_xpath ="(//main/section/div/div[1]/div[2]/div[7]/div)"
    dates_btn = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,date_xpath)))
    dates_btn.click()
    date_index = get_date_index(latest_date) +  1
    selecte_date = driver.find_element(By.XPATH,f"{date_xpath}/..//ul//li[{date_index}]")
    driver.execute_script("arguments[0].scrollIntoView();",selecte_date)
    driver.execute_script("window.scrollBy(0, -300);")
    selecte_date.click()
    driver.refresh()
    count_txt = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//main/section/div/div[1]/h1/span[1]"))).text
    total_count_xpath = int(re.sub(r'[^0-9]', '', count_txt))
    start = 1
    end = 1
    if(total_count_xpath > 20):
        first_path = "//div[@id='pagin']//ul//li[not(contains(@class,'previous')) and not(contains(@class,'next'))][1]//label"
        WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,first_path)))
        first_node = driver.find_element(By.XPATH,first_path)
        start = int(first_node.text)
        end = int(driver.find_element(By.XPATH,"//div[@id='pagin']//ul//li[not(contains(@class,'previous')) and not(contains(@class,'next')) ][last()]//label").text)
        first_node.click()
        driver.refresh()
    if checkPagination:
        logger.debug(f"PAGES {start} - {end} on {key}")
        logger.debug("Init completed ; choose language  "+code+f" correctly and found pages {start} ; {end}")
    return (start,end)

def extract_detail(driver: WebDriver,item_job: WebElement,rows: BufferWriter,keyword: str,local: str):
    details_tab_x = "//section[contains(@class,'campagne centered')]"
    description_path = "//main/section[1]/section[(@data-job-description) and not(contains(@class,'retrait'))]"
    resume = "//main/section[1]/section[(@data-job-description) and (contains(@class,'retrait'))]"
    WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,details_tab_x)))
    header_details = driver.find_element(By.XPATH,details_tab_x)
    job_free_text=driver.find_elements(By.XPATH,description_path)
    resume=driver.find_element(By.XPATH,resume)
    job_id = driver.find_elements(By.XPATH,"//section[@data-offerid]")[0].get_attribute("data-offerid")
    data={
        "key": keyword,
        "country": local,
        "job_id": job_id,
        **extractHeaderDetails(header_details),
        "resume": resume.text,
        "societe_recherche": job_free_text[0].text,
        "profile_demande": np.nan,
        'scrap_timestamp':pd.Timestamp.now()
    }
    if(len(job_free_text) > 1):
        data["profile_demande"] =job_free_text[1].text

    logger.debug(f"Extracted Job Detail : {job_id}")
    rows.add(data)

@logger.catch      
def extract_result_set(index: int,keyword : str,local : str,start: int = 100,end: int = 100) -> list:
    rows = BufferWriter(base_name=keyword,subname=str(index),max_buffer_size=None,folder_path="./output_hello_work")
    driver = create_driver()
    
    init(driver,key=keyword,code=local,checkPagination=False)
    # local_logger = logger.bind(thread_id =  threading.get_ident())
    logger.info(f"Extracting results set from {start} to {end} on {keyword} in {local}")
    page = start
    while page < end:
        goToUrl(driver,page)
        logger.debug(f"Loading page : {page} on {keyword} and local {local} : {driver.current_url}")
        card_x = "//section//ul[@data-teleport-target='destination']//li"
        try:
            WebDriverWait(driver,50).until(EC.presence_of_all_elements_located((By.XPATH,card_x)))
        except:
            logger.warning(f"Found no items in page : {page} for keyword : {keyword} in {local}")
            break
        cards=driver.find_elements(By.XPATH,card_x)
        if(len(cards) == 0):
            logger.warning(f"Found page {page} with no data on {keyword} in {local}")
            break            
        cur_handler = driver.current_window_handle
        logger.info(f"Found {len(cards)} jobs in this page {page} ")
        for i,item_job in enumerate(cards):
            driver.execute_script("arguments[0].scrollIntoView();",item_job)
            with job_scrap_histogram.labels(threading.currentThread().ident,keyword,local).time():
                ActionChains(driver).move_to_element(item_job).key_down(Keys.CONTROL).click(item_job).perform()
                driver.implicitly_wait(0.2)
                for handler in driver.window_handles:
                    if handler != driver.current_window_handle:
                        driver.switch_to.window(handler)
                        extract_detail(driver,item_job,rows,keyword,local)
                        job_counter.labels(threading.currentThread().ident,keyword,local).inc()
                        driver.close()
                driver.switch_to.window(cur_handler)
        rows.writeIfNeeded()
        page+= 1
        
        current_page_counter.labels(keyword,local).inc()
    logger.success(f"Finished working on  result set {keyword} in {local} : s={start},e={end}")
    if(driver != None):
        driver.quit()
    rows.writeToDisk()
    # print(len(rows))
    # print("--------------")
    # print(rows)
    return rows
def extractHeaderDetails(node: WebElement) -> dict:
    poste_nom=node.find_element(By.XPATH,'.//h1/span').text
    entreprise=node.find_element(By.TAG_NAME,'h1').text.replace(poste_nom,"")

    localisation=node.find_element(By.XPATH,'.//ul/li[1]').text
    contract=node.find_element(By.XPATH,'.//ul/li[2]').text
    sal=node.find_elements(By.XPATH,'.//ul/li[3]')

    dicts= {'poste':poste_nom,'entreprise':entreprise,'localisation':localisation,"contract":contract}
    if(len(sal)>0):
        dicts["salaire"] = sal[0].text
    else:
        dicts["salaire"] = None
    return dicts

def extractJobDetails(node: WebElement) -> dict:
    def process_text(item):
        a = item.find_element(By.XPATH,'div[1]').text
        b = item.text.replace(a,"")
        return a,b

    # print([tuple(map(lambda d: d.text,item.find_elements(By.XPATH,'text()')))  for item in node])
    dc= dict([process_text(item) for item in node])
    # print(dc)
    return dc

def search_with_keyword(executor: ThreadPoolExecutor,keywords = None,localisations : tuple = None):
    logger.info(f"Searching In {localisations}")
    if(keywords == None):
        keywords = [""]
    for positionKeyword,key in enumerate(keywords):
        keyname = 'All' if len(key) == 0 else key
        logger.info(f"Searching for {keyname}")
        for position,local in enumerate(localisations):
            logger.info(f"Searching for area {local}")
            # driver.get('chrome://settings/clearBrowserData')
            # driver.find_element(By.XPATH,'//settings-ui').send_keys(Keys.ENTER)
            driver = create_driver()
            start,end=init(driver,key=key,code=local)
            driver.quit()

            total_page_counter.labels(key,local).inc(end - start + 1)

            #Init threads
            logger.info(f"CPU count : {executor._max_workers}")
            chunk_sizes = np.arange(start,end+1+executor._max_workers,executor._max_workers) 
            for i in range(len(chunk_sizes)-1):
                try:
                    s = min(end,chunk_sizes[i])
                    e = min(end+1,chunk_sizes[i+1])
                    executor.submit(extract_result_set,i,key,local,s,e)
                except Exception as err:
                    logger.error(err)
                    logger.error(f"Could not finish Scrapping keywords {key} with location {local} for pages : {s} - {e}")
            # logger.success(f"Finished working on localisation {local} , Current : {position+1} / {len(localisations)}")
    executor.shutdown(wait=True)
    logger.info(f"Finished Scrapping keywords {keywords} with locations :{localisations}")
# a=[]
# generate_locations(rd=100,locations=a,base_loc = (44.554271,1.102653))
# print(a)
def closeAllThreads(executor: ThreadPoolExecutor,start_time):
    def exitfn():
        end_time = time.time_ns()
        logger.info(f"Total Time in ns {end_time - start_time}")
        executor.shutdown(wait=False)
    return exitfn
import time
def main():
    # search_with_keyword(None,geo=[48.773388,-2.430871])  
    start_time = time.time_ns()
    #Init params  

    # base_loc = [36.327711,9.642678]
    # keywords = [".net","angular","react","data science","vue js","node js","java","c#","python","cloud","microsoft"]
    # keywords = ["vue js","node js","java","c#","python","cloud","microsoft"]
    

  
    # pool = concurrent.futures.ThreadPoolExecutor(max_workers=thread_num)
    
    #Distribute Work
    # thread_num = 1
    executor = ThreadPoolExecutor(thread_num)
    atexit.register(closeAllThreads(executor,start_time))

    c = Counter("scrap_worker_num","The number of thread workers for scrapping")
    c.inc(executor._max_workers)

    k = Counter("scrap_keywords","The number of keywords to scrap")
    k.inc(len(keywords))

    l = Counter("scrap_local","The number of locals to check")
    l.inc(len(localisations))
    # sleep(100)
    search_with_keyword(executor,keywords=keywords,localisations=localisations)


if __name__ == "__main__":
    logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<magenta>Thread-[{thread}]</magenta> : <level>{message}</level>"
    )  # Default values
    logger.remove(0)


    stdout_level=os.environ.get("LOG_STDOUT_LEVEL","INFO")
    log_file_level=os.environ.get("LOG_FILE_LEVEL","INFO")

    logger.add("./logs/hello_work/main_{time}.log",    
    enqueue=True,
    rotation="10 Mb",
    retention="4 weeks",
    encoding="utf-8",
    level=log_file_level,
    backtrace=True,
    diagnose=True,
    format=logger_format)

    logger.add(sys.stderr,    
    enqueue=True,
    backtrace=True,
    diagnose=True,
    level=stdout_level,
    format=logger_format)
    os.environ["PROMETHEUS_DISABLE_CREATED_SERIES"]= "False"

    start_http_server(9777)
    total_page_counter = Counter("scrap_pages","The number of pages found",labelnames=['keyword','local'])
    current_page_counter = Counter("scrap_pages_current","The number of pages found",labelnames=['keyword','local'])
    job_counter = Counter("scrap_scrapped_jobs","The number of jobs scrapped",labelnames=['thread_id','keyword','local'])
    job_scrap_histogram = Histogram("scrap_jobs_duration","The duration it takes to scrap a single job",labelnames=['thread_id','keyword','local'])
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords",default="java")
    parser.add_argument("--localisations",default="fr")
    parser.add_argument("--thread-num",default=os.cpu_count())
    parser.add_argument("--ds",default=None)

    args = parser.parse_args()

    keywords = args.keywords.split(',')
    localisations =args.localisations.split(',')
    thread_num = int(args.thread_num)
    # latest_date = datetime.strptime(args.ds,"%Y-%m-%d %H:%M:%S") if args.ds != None and args.ds != "None" else None
    latest_date = date_parser.parse(args.ds) if args.ds != None and args.ds != "None" else None

    hostname=os.environ.get("HUB_HOSTNAME","localhost")
    port=os.environ.get("HUB_PORT","4444")
    run_id=os.environ.get("RUN_ID",None)
    main()