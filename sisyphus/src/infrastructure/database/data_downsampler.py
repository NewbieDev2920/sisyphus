from sisyphus.src.domain.ports.database_models.price_record import PriceRecord

class DataDownsampler:

    def __init__(self):
        pass

    def day_representative_price_record(self, date) -> PriceRecord:
        pass
    
    def compact_period(self, start_date, end_date):
        pass

    def purge_period(self,start_date, end_date):
        pass