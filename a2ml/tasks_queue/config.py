import os

class Config:
    def __init__(self):
        self.review_data_path = os.environ.get('REVIEW_DATA_PATH', 's3://review-data/')
