import pandas as pd
import os 
from loguru import logger
import atexit
import sys
def on_exit(buf):
    def exit():
        if(buf != None):
            if(buf.size() > 0):
                buf.writeToDisk()
        logger.warning("Closing")
    return exit
class BufferWriter:
    data : list = None
    max_buffer_size : int = None
    path : str = None
    subname : str = None
    append : bool = False
    counter = 0
    def __init__(self,base_name: str,subname: str = None,max_buffer_size : int = None,append : bool = False,folder_path : str = "./") -> None:
        # logger.add("./logs/writer_{time}.log",    
        #     enqueue=True,
        #     rotation="5 Mb",
        #     retention="4 weeks",
        #     encoding="utf-8",
        #     backtrace=True,
        #     diagnose=True)
        self.append = False
        self.subname = subname
        self.folder_path = folder_path
        self.data = []
        if(max_buffer_size == None):
            self.max_buffer_size = 20000*1024*1024
        else:
            self.max_buffer_size = max_buffer_size
        # self.path = os.path.join(os.getcwd(),folder_path,base_name,str(pd.Timestamp.date(pd.Timestamp.now())),str(pd.Timestamp.time(pd.Timestamp.now())).replace(":","-"))
        self.path = os.path.join(os.getcwd(),folder_path,base_name)
        os.makedirs(self.path,exist_ok=True)
        logger.info(f"Output available at {self.path}")
        atexit.register(on_exit(self))
    def add(self,row):
        self.data.append(row)
        logger.trace(f"Adding: {row}")
        if(self.max_buffer_size != None and sys.getsizeof(self.data) >= self.max_buffer_size):
            self.writeToDisk(newFile=True)

    def clear(self):
        logger.debug(f"Clearing buffer")
        self.data.clear()
    
    def size(self):
        return len(self.data)
    
    def writeToDisk(self,newFile = False):
        nm = self.path+"/data"
        if not self.append or newFile:
            self.counter += 1
        if(self.subname):
            nm += self.subname
        nm += "_"+str(self.counter)
        header = os.path.exists(nm)
        logger.debug(f"Writing Buffer to : {nm}  with {len(self.data)} ")
        pd.DataFrame(self.data).to_csv(nm+".csv",mode="a" if self.append else "w",header=not header,index=False,encoding="utf-8")
        self.data.clear()
        logger.success(f"Data saved to : {nm}")

    
    def writeIfNeeded(self):
        if(self.append):
            self.writeToDisk()