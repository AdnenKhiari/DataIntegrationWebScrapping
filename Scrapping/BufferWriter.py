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
    append : bool = False
    counter = 0
    def __init__(self,base_name: str,max_buffer_size : int = None,append : bool = False,folder_path : str = "./") -> None:
        logger.add("./logs/writer_{time}.log",    
            enqueue=True,
            rotation="5 Mb",
            retention="4 weeks",
            encoding="utf-8",
            backtrace=True,
            diagnose=True)
        self.append = False
        self.folder_path = folder_path
        self.data = []
        if(max_buffer_size == None):
            self.max_buffer_size = 200*1024*1024
        else:
            self.max_buffer_size = max_buffer_size
        self.path = os.path.join(os.getcwd(),folder_path,base_name,str(pd.Timestamp.date(pd.Timestamp.now())),str(pd.Timestamp.time(pd.Timestamp.now())).replace(":","-"))
        os.makedirs(self.path,exist_ok=True)
        logger.success(f"Output available at {self.path}")
        atexit.register(on_exit(self))
    def add(self,row):
        self.data.append(row)
        logger.trace(f"Adding: {row}")
        if(self.max_buffer_size != None and sys.getsizeof(self.data) >= self.max_buffer_size):
            self.writeToDisk(newFile=True)

    
    def clear(self):
        logger.debug(f"Clearing buffer")
        self.data = [] 
    
    def size(self):
        return len(self.data)
    
    def writeToDisk(self,newFile = False):
        nm = self.path+"/data"
        if not self.append or newFile:
            self.counter += 1
        nm += "_"+str(self.counter)
        header = os.path.exists(nm)
        logger.debug(f"Writing Buffer to : {nm}")
        pd.DataFrame(self.data).to_csv(nm+".csv",mode="a" if self.append else "w",header=not header,index=False)
        self.data = []
        logger.success(f"Data saved to : {nm}")

    
    def writeIfNeeded(self):
        if(self.append):
            self.writeToDisk()