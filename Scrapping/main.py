from selenium.webdriver.chrome.webdriver import ChromiumDriver
from time import sleep
from datetime import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.timeouts import Timeouts
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from urllib.parse import urlparse
from urllib.parse import parse_qs
import re
from enum import Enum
import math 
from BufferWriter import BufferWriter
from loguru import logger
import signal

# bounding_box = [
#     (37.412437,8.649578),
#     (37.412437,11.397994),
#     (32.813536,11.397994),
#     (32.813536,8.649578)
# ]
bounding_box = [
    (89,-150),
    (89,179),
    (-30,179),
    (-30,-150)
]
def create_driver() -> ChromiumDriver:
    logger.debug("RECREATING CHROME DRIVER")
    return webdriver.Chrome()
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
def generate_tunisian_locations(rd: float,base_loc = None,locations : list = None):
    if(base_loc == None):
        base_loc = (36.8318827,10.2328137)
    if(base_loc[0] < bounding_box[3][0] or base_loc[0] > bounding_box[1][0]):
        return
    if(base_loc[1] < bounding_box[0][1] or base_loc[1] > bounding_box[1][1]):
        return 
    locations.append(base_loc)
    for i in range(6):
        dlatitude = math.cos(2*math.pi/6 * i) * rd * 2000
        dlongitude = math.cos(2*math.pi/6 * i) * rd * 2000
        new_loc = translate_latlong(base_loc[0],base_loc[1],dlatitude,dlongitude)
        found = False
        for old_loc in locations:
            if abs(new_loc[0]-old_loc[0]) + abs(new_loc[1]-old_loc[1]) < 1:
                found=True
        if(found == False):
            generate_tunisian_locations(rd,new_loc,locations)
class DATE_FILTER(Enum):
    today = 'today'
    last_2_days= 'last 2 days'
    last_week = 'last week'
    last_2_weeks = 'last 2 weeks'
    last_month = 'last month'
def changeLocalisation(driver: ChromiumDriver,url = 'https://www.example.com/some_path?&rd=some_value&adnene',rd: int = 100,latestDate: DATE_FILTER = None) -> str:       
    tokens = url.split("&")
    if(rd != None):
        tokens.append("rd="+str(rd))
    if(latestDate != None):
        tokens.append("recency="+str(latestDate))   
    return "&".join(tokens)
def init(driver: ChromiumDriver):
    driver.get("https://www.monster.fr/")
    try:
        cookie_path = "html/body//div[@id='onetrust-banner-sdk']//button[@id='onetrust-accept-btn-handler']"
        WebDriverWait(driver,7).until(EC.presence_of_element_located((By.XPATH,cookie_path)))
        accept_cookies = driver.find_element(By.XPATH,cookie_path)
        accept_cookies.click()
    except:
        logger.debug("No need for cookies")
    logger.debug("Init completed")
def extract_result_set(rows : BufferWriter,driver: ChromiumDriver,rd: float = 100) -> list:
    get_with_params = changeLocalisation(driver,driver.current_url,rd=rd)
    logger.info(f"Working on result set on current URL {get_with_params}")
    driver.get(get_with_params)
    # sleep(100)
    driver.fullscreen_window()
    current_count = 0
    while True:
        logger.debug(f"Loading page with starting index : {current_count}")
        card_x = '//section//ul//li[position() > '+str(current_count)+' ]//article'
        try:
            WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,card_x)))
        except:
            break
        cards=driver.find_elements(By.XPATH,card_x)
        if(len(cards) == 0):
            break            
        current_count += len(cards)
        for i,item_job in enumerate(cards):
            driver.execute_script("arguments[0].scrollIntoView();",item_job)
            item_job.click()
            details_tab_x = "//div[@id='details-table']"
            WebDriverWait(driver,4).until(EC.presence_of_element_located((By.XPATH,details_tab_x)))
            header_details = driver.find_element(By.XPATH,"//div[@class='headerstyle__JobViewHeaderContent-sc-1ijq9nh-8 fpYqik']")
            job_details=driver.find_elements(By.XPATH,details_tab_x+"/div[contains(@class,'detailsstyles__DetailsTableRow-sc-1deoovj-2 gGcRmF') and not(contains(@class,'detailsstyles__DetailsTableRowBreak-sc-1deoovj-7'))]")
            job_free_text=driver.find_element(By.XPATH,"//div[@class='descriptionstyles__DescriptionContainer-sc-13ve12b-0 iCEVUR']/div")
            # sleep(1000)
            job_id = item_job.get_attribute("data-job-id")
            logger.debug(f"Found information of Job : {i+current_count} {job_id}")
            data={"job_id": job_id,
                'description':job_free_text.text,
                **extractHeaderDetails(header_details),
                **extractJobDetails(job_details),
                'scrap_timestamp':pd.Timestamp.now()}
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
    dc= dict([process_text(item)  for item in node])
    # print(dc)
    return dc
def search_with_keyword(driver: ChromiumDriver,keywords = None,geo : tuple = None,rd: float = 100,base_loc : tuple = None):
    localisations = []
    if(geo == None):
        logger.info(f"Using all localisation inside of the bounding box from the base {base_loc}")
        logger.debug("COMPUTING LOCALISATIONS INSIDE THE BOUNDING BOX")
        generate_tunisian_locations(rd=100,base_loc=base_loc,locations=localisations)
        logger.success(f"FINISHED COMPUTING LOCALISATIONS INSIDE THE BOUNDING BOX, FOUND {len(localisations)} , Result : {localisations} ")
    else:
        logger.info(f"Using only one localisation {geo}")
        localisations = [geo]
    if(keywords == None):
        keywords = [""]
    for positionKeyword,key in enumerate(keywords):
        keyname = 'All' if len(key) == 0 else key
        logger.info(f"Searching for {keyname}")
        result = BufferWriter(base_name=keyname,max_buffer_size=None,folder_path="./output")
        for position,local in enumerate(localisations):
            logger.info(f"Searching for area {local}")
            # driver.get('chrome://settings/clearBrowserData')
            # driver.find_element(By.XPATH,'//settings-ui').send_keys(Keys.ENTER)
            driver.close()
            driver = create_driver()
            init(driver)
            driver.execute_cdp_cmd("Emulation.setGeolocationOverride",{'latitude':local[0],'longitude':local[1],'accuracy':1})
            driver.get("https://www.monster.fr/")
            driver.implicitly_wait(1)
            search_keyword_input = driver.find_element(By.XPATH,'html/body//div[contains(@class,ds-search-bar)]//form/div[1]/div[1]//input')
            search_keyword_input.send_keys(key)
            search_keyword_input.send_keys(Keys.ENTER)
            extract_result_set(result,driver,rd)
            logger.success(f"Finished working on localisation {local} , Current : {position+1} / {len(localisations)}")
        result.writeToDisk()
        logger.success(f"Finished working on {keyname} ,  Current : {positionKeyword+1} / {len(keywords)}")
# a=[]
# generate_tunisian_locations(rd=100,locations=a,base_loc = (44.554271,1.102653))
# print(a)
def main():
    driver = create_driver()
    # wait = WebDriverWait(driver, 10)
    search_with_keyword(driver,base_loc=[48.773388,-2.430871])
if __name__ == "__main__":
    logger.add("./logs/main_{time}.log",    
    enqueue=True,
    rotation="5 Mb",
    retention="4 weeks",
    encoding="utf-8",
    backtrace=True,
    diagnose=True)
    main()