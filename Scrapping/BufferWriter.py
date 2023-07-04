import pandas as pd
import sys
class BufferWriter:

    data : list = None
    max_buffer_size : int = None
    base_name : str = None
    append : bool = True
    counter = 0
    def __init__(self,base_name: str,max_buffer_size : int) -> None:
        self.data = []
        if(max_buffer_size != None):
            self.max_buffer_size = 200*1024*1024
        
    def add(self,row):
        self.data.append(row)
        if(self.max_buffer_size != None and sys.getsizeof(self.data) >= self.max_buffer_size):
            self.writeToDisk()

    
    def clear(self):
        self.data = [] 
    
    def writeToDisk(self):
        nm = self.name
        if not self.append:
            self.counter+= self.counter
            nm += "_"+str(self.counter)
        pd.DataFrame(self.row).to_csv(self.base_name,mode="a",header=self.counter == 0,index=False)
