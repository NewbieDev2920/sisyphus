from abc import ABC, abstractmethod

def DataCleanerPort():

    @abstractmethod
    def delete_dirty_rows(self,df : pd.DataFrame):
        pass

    @abstractmethod
    def synthetic_dataframe(self, df: pd.DataFrame):
        pass