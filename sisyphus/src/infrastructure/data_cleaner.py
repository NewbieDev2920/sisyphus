from domain.ports.data_cleaner_port import DataCleanerPort

class DataCleaner(DataCleanerPort):

    def delete_dirty_rows(self, df : pd.DataFrame, dirty_index_list : list):
        return df.drop(dirty_index_list)

    def delete_dirty_rows(self,df : pd.DataFrame):
        df = df.drop_duplicates()
        return df.dropna()

    def synthetic_dataframe(self, df: pd.DataFrame, target_column : str, synthetic_data):
        df =  df.fillna({target_column:synthetic_data})
