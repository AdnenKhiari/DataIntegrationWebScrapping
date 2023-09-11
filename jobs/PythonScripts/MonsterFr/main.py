from prometheus_client import start_http_server
from selenium.webdriver import ChromeOptions
from time import sleep
import json
import os
import concurrent.futures
import numpy as np
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from enum import Enum
import math 
from ..BufferWriter import BufferWriter
from loguru import logger
import atexit
import threading
from selenium.common.exceptions import WebDriverException
from prometheus_client.metrics import Counter,Histogram

import argparse

# bounding_box = [
#     (37.412437,8.649578),
#     (37.412437,11.397994),
#     (32.813536,11.397994),
#     (32.813536,8.649578)
# ]

bounding_box = [
    (50,-5),
    (50,5),
    (43,5),
    (43,-5)
]
# bounding_box = [
#     (50,-20),
#     (50,20),
#     (-0,20),
#     (-0,-20)
# ]

bounding_box = [
    (50,-20),
    (50,20),
    (-0,20),
    (-0,-20)
]
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
    hostname = "localhost"
    for _ in range(3):
        try:
            return webdriver.Remote(command_executor="http://"+hostname+":4444/wd/hub",
        options=options)
            
        except WebDriverException as e:
            print(f"Session creation failed: {str(e)} , retying {_} ... ")
            if _ == 3:
                raise e   
def translate_latlong(lat,long,lat_translation_meters,long_translation_meters):
    ''' method to move any lat,long point by provided meters in lat and long direction.
    params :
        lat,long: lattitude and longitude in degrees as decimal values, e.g. 37.43609517497065, -122.17226450150885
        lat_translation_meters: movement of point in meters in lattitude direction.
                                positive value: up move, negative value: down move
        long_translation_meters: movement of point in meters in longitude direction.
                                positive value: left move, negative value: right move
        '''
    earth_radius = 6378.137

    #Calculate top, which is lat_translation_meters above
    m_lat = (1 / ((2 * math.pi / 360) * earth_radius)) / 1000;  
    lat_new = lat + (lat_translation_meters * m_lat)

    #Calculate right, which is long_translation_meters right
    m_long = (1 / ((2 * math.pi / 360) * earth_radius)) / 1000;  # 1 meter in degree
    long_new = long + (long_translation_meters * m_long) / math.cos(lat * (math.pi / 180));
    
    return lat_new,long_new
def generate_locations(rd: float,base_loc = None,locations : list = None):
    if(base_loc == None):
        base_loc = (36.8318827,10.2328137)
    if(base_loc[0] < bounding_box[3][0] or base_loc[0] > bounding_box[1][0]):
        return
    if(base_loc[1] < bounding_box[0][1] or base_loc[1] > bounding_box[1][1]):
        return 
    locations.append(base_loc)
    for i in range(6):
        dlatitude = math.cos(2*math.pi/6 * i) * rd * 2000 
        dlongitude = math.sin(2*math.pi/6 * i) * rd * 2000 
        new_loc = translate_latlong(base_loc[0],base_loc[1],dlatitude,dlongitude)
        found = False
        for old_loc in locations:
            if abs(new_loc[0]-old_loc[0]) + abs(new_loc[1]-old_loc[1]) < 0.5:
                found=True
        if(found == False):
            generate_locations(rd,new_loc,locations)
class DATE_FILTER(Enum):
    today = 'today'
    last_2_days= 'last 2 days'
    last_week = 'last week'
    last_2_weeks = 'last 2 weeks'
    last_month = 'last month'
def changeLocalisation(driver: WebDriver,url = 'https://www.example.com/some_path?&rd=some_value&adnene',rd: int = 100,latestDate: DATE_FILTER = None) -> str:       
    tokens = url.split("&")
    if(rd != None):
        tokens.append("rd="+str(rd))
    if(latestDate != None):
        tokens.append("recency="+str(latestDate))   
    return "&".join(tokens)
def init(driver: WebDriver):
    driver.get("https://www.monster.fr/")
    try:
        cookie_path = "html/body//div[@id='onetrust-banner-sdk']//button[@id='onetrust-accept-btn-handler']"
        WebDriverWait(driver,7).until(EC.presence_of_element_located((By.XPATH,cookie_path)))
        accept_cookies = driver.find_element(By.XPATH,cookie_path)
        accept_cookies.click()
    except:
        logger.trace("No need for cookies")
    logger.debug("Init completed")
def extract_result_set(rows : BufferWriter,driver: WebDriver,keyword : str,local : str,rd: float = 100) -> list:
    get_with_params = changeLocalisation(driver,driver.current_url,rd=rd)
    logger.info(f"Working on result set on current URL {get_with_params}")
    driver.get(get_with_params)
    # sleep(100)
    # driver.fullscreen_window()
    current_count = 0
    while True:
        logger.debug(f"Loading page with starting index : {current_count}")
        card_x = '//section//ul//li[position() > '+str(current_count)+' ]//article'
        try:
            WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,card_x)))
            current_page_counter.labels(keyword,local).inc()
        except:
            break
        cards=driver.find_elements(By.XPATH,card_x)
        if(len(cards) == 0):
            break            
        current_count += len(cards)
        for i,item_job in enumerate(cards):
            job_counter.labels(threading.currentThread().ident,keyword,local).inc()
            driver.execute_script("arguments[0].scrollIntoView();",item_job)
            with job_scrap_histogram.labels(threading.currentThread().ident,keyword,local).time():
                item_job.click()
                details_tab_x = "//div[@id='details-table']"
                WebDriverWait(driver,20).until(EC.presence_of_element_located((By.XPATH,details_tab_x)))
                header_details = driver.find_element(By.XPATH,"//div[@class='headerstyle__JobViewHeaderContent-sc-1ijq9nh-8 fpYqik']")
                job_details=driver.find_elements(By.XPATH,details_tab_x+"/div[contains(@class,'detailsstyles__DetailsTableRow-sc-1deoovj-2 gGcRmF') and not(contains(@class,'detailsstyles__DetailsTableRowBreak-sc-1deoovj-7'))]")
                job_free_text=driver.find_element(By.XPATH,"//div[@class='descriptionstyles__DescriptionContainer-sc-13ve12b-0 iCEVUR']/div")
                # sleep(1000)
                job_id = item_job.get_attribute("data-job-id")
                logger.debug(f"Found information of Job : {i+current_count} {job_id}")
                data={
                    "key": keyword,
                    "local": local,
                    "job_id": job_id,
                    'description':job_free_text.text,
                    **extractHeaderDetails(header_details),
                    **extractJobDetails(job_details),
                    'scrap_timestamp':pd.Timestamp.now()
                    }
                rows.add(data)
        rows.writeIfNeeded()
    logger.info("Finished working on result set")
    # print(len(rows))
    # print("--------------")
    # print(rows)
    return rows
def extractHeaderDetails(node: WebElement) -> dict:
    poste=node.find_element(By.TAG_NAME,'h2').text
    entreprise=node.find_element(By.TAG_NAME,'a').text
    localisation=node.find_element(By.TAG_NAME,'h3').text
    return {'poste':poste,'entreprise':entreprise,'localisation':localisation}
def extractJobDetails(node: WebElement) -> dict:
    def process_text(item):
        a = item.find_element(By.XPATH,'div[1]').text
        b = item.text.replace(a,"")
        return a,b

    # print([tuple(map(lambda d: d.text,item.find_elements(By.XPATH,'text()')))  for item in node])
    labels = ["TYPE DE CONTRAT,ADRESSE,DATE DE PUBLICATION,TAILLE DE LA SOCIÉTÉ,SECTEUR,SITE WEB,DATE DE CRÉATION,SALAIRE"]
    found= dict([process_text(item) for item in node])
    dc= dict()
    # print(dc)
    for k in labels:
        dc.setdefault(dc,np.nan)
        if(found.get(k) != None):
            dc[k] = found.get(k)
    return dc

@logger.catch      
def search_with_keyword(driver: WebDriver,keywords = None,geo : tuple = None,rd: float = 100,base_loc : tuple = None):
    localisations = geo
    logger.info(f"Searching In {localisations}")
    if(keywords == None):
        keywords = [""]
    for positionKeyword,key in enumerate(keywords):
        keyname = 'All' if len(key) == 0 else key
        logger.info(f"Searching for {keyname}")
        result = BufferWriter(base_name=keyname,subname=positionKeyword,max_buffer_size=None,folder_path="./output_monster_fr")
        for position,local in enumerate(localisations):
            logger.info(f"Searching for area {local}")
            # driver.get('chrome://settings/clearBrowserData')
            # driver.find_element(By.XPATH,'//settings-ui').send_keys(Keys.ENTER)
            if(driver != None):
                driver.close()
            driver = create_driver()
            send_commande(driver,"Emulation.setGeolocationOverride",{'latitude':local[0],'longitude':local[1],'accuracy':1})
            init(driver)
            # driver.get("https://www.monster.fr/")
            search_path = 'html/body//div[contains(@class,ds-search-bar)]//form/div[1]/div[1]//input'
            WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,search_path)))
            search_keyword_input = driver.find_element(By.XPATH,search_path)
            search_keyword_input.send_keys(key)
            search_keyword_input.send_keys(Keys.ENTER)
            extract_result_set(result,driver,key,local,rd)
            logger.success(f"Finished working on localisation {local} , Current : {position+1} / {len(localisations)}")
        if(driver != None):
            driver.close()
        result.writeToDisk()
        logger.success(f"Finished working on {keyname} ,  Current : {positionKeyword+1} / {len(keywords)}")
    logger.info(f"Finished Scrapping keywords {keywords} with locations :{localisations}")
# a=[]
# generate_locations(rd=100,locations=a,base_loc = (44.554271,1.102653))
# print(a)
import time
def closeAllThreads(executor: concurrent.futures.ThreadPoolExecutor,start_time):
    def exitfn():
        end_time = time.time_ns()
        logger.info(f"Total Time in ns {end_time - start_time}")
        executor.shutdown(wait=False)
    return exitfn
def main():
    # wait = WebDriverWait(driver, 10)
    # search_with_keyword(None,geo=[48.773388,-2.430871])  
    start_time = time.time_ns()

    # base_loc = [36.327711,9.642678]
    # keywords = [".net","bi","angular","react","data science","vue js","node js","java","c#","python","cloud","microsoft","marketing","buisness",""]
    logger.info(f"Using all localisation inside of the bounding box from the base {base_loc} using {rd}")
    logger.debug("COMPUTING LOCALISATIONS INSIDE THE BOUNDING BOX")
    localisations = []
    generate_locations(rd=rd,base_loc=base_loc,locations=localisations)
    logger.success(f"FINISHED COMPUTING LOCALISATIONS INSIDE THE BOUNDING BOX, FOUND {len(localisations)} , Result : {localisations} ")
    
    #Init threads
    logger.info(f"CPU count : {thread_num}")
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=thread_num)
    atexit.register(closeAllThreads(pool,start_time=start_time))

    c = Counter("scrap_worker_num","The number of thread workers for scrapping")
    c.inc(pool._max_workers)

    k = Counter("scrap_keywords","The number of keywords to scrap")
    k.inc(len(keywords))

    l = Counter("scrap_local","The number of positions to check")
    l.inc(len(localisations))

    #Distribute Work
    chunk_size = len(localisations) // thread_num
    if(chunk_size ==0):
        chunk_size = len(localisations)
    
    for key in keywords:
        for chunk_start in np.arange(0,len(localisations),chunk_size):
            pool.submit(search_with_keyword,**{'driver':None,'keywords':[key] if key != "" else None,'geo':localisations[chunk_start:chunk_start+chunk_size],"rd":rd})
            # search_with_keyword(**{'driver':None,'keywords':[key] if key != "" else None,'geo':[base_loc],"rd":rd})
    pool.shutdown(wait=True)        
    logger.success(f"Finished scrapping {keywords}")
    # search_with_keyword(None,keywords=None,geo=[base_loc])

import sys
if __name__ == "__main__":
    logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<magenta>Thread-[{thread}]</magenta> : <level>{message}</level>"
    )  # Default values
    logger.remove(0)
    logger.add("./logs/monster_fr/main_{time}.log",    
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
    with logger.catch():
        start_http_server(9777)
        # total_page_counter = Counter("scrap_pages","The number of pages found",labelnames=['keyword','local'])
        current_page_counter = Counter("scrap_pages_current","The number of pages found",labelnames=['keyword','local'])
        job_counter = Counter("scrap_scrapped_jobs","The number of jobs scrapped",labelnames=['thread_id','keyword','local'])
        job_scrap_histogram = Histogram("scrap_jobs_duration","The duration it takes to scrap a single job",labelnames=['thread_id','keyword','local'])
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--keywords",default="microsoft")
        parser.add_argument("--base-loc",default="48.043388,-1.730871")
        parser.add_argument("--thread-num",default=os.cpu_count())
        parser.add_argument("--rd",default="100")
        args = parser.parse_args()

        keywords = args.keywords.split(",")
        base_loc = args.bac_loc.split(",")
        thread_num = int(args.thread_num)
        rd = int(args.rd)

        main()