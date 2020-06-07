import json
import pandas as pd
from pandas.io.json import json_normalize
import numpy as np

class MessageExtractor:
    """
    Extract telegram messages for you
    """

    datetimes_columns = ['date']

    def __init__(self):
        """
        Work with Telegram export data
        """
        
        self.data = None
        self.people = np.array([])
        self.personal_only = True
        self.whitelist = []
        self.blacklist = []
        # self.names = {}
        self.columns = ['text', 'from', 'date',
                        'reply_to_message_id', 'chat_id']
        self.username = 'username'

    def __preprocess_data(self):
        """
        Remove messages without text and other bad content
        """
        data = self.data

        # set id as df index
        data = data.set_index('id')

        # filter personal chats only
        if self.personal_only:
            data = data[data['chat_type'] == "personal_chat"]

        #remove bad messages
        data = data[data['text'].apply(type) == str]
        data = data[data['text'] != '']

        #remove bad replies
        data['reply_to_message_id'] = data['reply_to_message_id'].apply(self.__check_reply)

        #NaN-like objects to None
        data = data.where(pd.notnull(data), None)

        #datetime str to datetime
        data['date'] = pd.to_datetime(data['date'])
        data['chat_id'] = data['chat_id'].astype('int64')

        self.data = data

    def __filter_names(self):
        """
        Filter names by whitelist and blacklist
        """
        people, data = self.people, self.data

        people = data['chat_name'].dropna().unique()
        people = np.setdiff1d(
            people,
            ['nan', 'None', 'NaN', 'Null'])

        if self.blacklist:
            people = np.setdiff1d(people, self.blacklist)
        if self.whitelist:
            people = np.intersect1d(people, self.whitelist)

        data = data[data['chat_name'].isin(people)]

        self.people, self.data = people, data

    def __change_names(self):
        """
        Replace chat names
        """
        if self.names:
            self.data['chat_name'] = self.data['chat_name'].replace(
                self.names)
            self.people = self.data['chat_name'].unique()

    def __check_reply(self, idx: int):
        """
        Checks that the reply contains text
        """
        return idx if idx and idx in self.data.index else None

    def __clean_data(self):
        """
        Remove bad columns
        """
        data = self.data
        data = data[self.columns]
        self.data = data

    def __anonymize(self):
        """
        Replacement of user names with pronouns
        """
        data = self.data

        data['from'][data['from'] != self.username] = 'other'
        data['from'][data['from'] == self.username] = 'me'

        self.data = data

    def extract_from_json(self, 
        file_path: str, 
        personal_only: bool = True,
        whitelist: list = None, 
        blacklist: list = None, 
        # names: dict = None, 
        clean: bool = True,
        columns: list = None,
        username: str = None
        ) -> pd.core.frame.DataFrame:
        """
        Export messages from raw json file to cozy pandas.DataFrame

        Parameters
        ----------
        file_path: str, required
            Path to telegram export json file

        whitelist: array-like, default None
            List of people whose messages will be in the data
            default: (All people will be in data)

        blacklist: array-like, default None
            List of people whose messages you do not want to see in the data
            default: (All people will be in data)
            
        personal_only: bool, default True
            Only private chats in data

        clean: bool, default True
            Delete unnecessary message information

        columns: array-like, default None
            The columns you want to keep

        username: str, default None
            Remove usernames

        Result
        ------
        data: pandas.DataFrame
            Database of your messages
        """

        self.blacklist = blacklist
        self.whitelist = whitelist
        self.personal_only = personal_only
        # self.names = names
        self.columns = columns if columns else self.columns
        self.username = username

        with open(file_path, encoding='utf8') as f:
            raw_json = json.load(f)

        self.data = json_normalize(
            data=raw_json['chats']['list'],
            record_path='messages', 
            meta=['type', 'name', 'id'],
            meta_prefix='chat_',
            errors='ignore')

        self.__preprocess_data()
        self.__filter_names()
        # self.__change_names()
        if clean:
            self.__clean_data()
        if username:
            self.__anonymize()

        return self.data

    def import_from_csv(self, 
        file_path: str) -> pd.core.frame.DataFrame:
        """
        Import ready data from csv file
        """

    def save_to_csv(self):
        """
        Save ready data to csv file
        """
