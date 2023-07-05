import pandas as pd
import sys
import os 
from time import timezone
class BufferWriter:

    data : list = None
    max_buffer_size : int = None
    path : str = None
    append : bool = False
    counter = 0
    def __init__(self,base_name: str,max_buffer_size : int = None,append : bool = True,folder_path : str = "./") -> None:
        self.append = append
        self.folder_path = folder_path
        self.data = []
        if(max_buffer_size == None):
            self.max_buffer_size = 200*1024*1024
        else:
            self.max_buffer_size = max_buffer_size
        self.path = os.path.join(os.getcwd(),folder_path,str(pd.Timestamp.now().isoformat()),base_name)
        os.makedirs(self.path,exist_ok=True)
    def add(self,row):
        self.data.append(row)
        print(self.max_buffer_size,sys.getsizeof(self.data))
        if(self.max_buffer_size != None and sys.getsizeof(self.data) >= self.max_buffer_size):
            self.writeToDisk()

    
    def clear(self):
        self.data = [] 
    
    def writeToDisk(self,newFile = False):
        nm = self.path+"/data"
        if not self.append or newFile:
            self.counter += 1
        nm += "_"+str(self.counter)
        header = os.path.exists(nm)
        pd.DataFrame(self.data).to_csv(nm+".csv",mode="a" if self.append else "w",header=not header,index=False)
        self.data = []
    
    def writeIfNeeded(self):
        if(self.append):
            self.writeToDisk()