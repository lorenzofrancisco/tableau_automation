import logging  # for logging files
import sys  # sys.exit() function allows the developer to exit from Python
import json  # allows for for json
import argparse  # python for logging levels
import getpass  # hides all server credentials
import smartsheet
import tableauserverclient as TSC  # server client library tableau
from dotenv import load_dotenv  # loads.env file
from dotenv import dotenv_values  # loads values from .env file

load_dotenv()
config = dotenv_values(".env")


# all tokens needed for script execution
ss_admin_token = config['SMARTSHEETS_ADMIN_TOKEN']
ss_sheet_id = config['SMARTSHEETS_SHEET_ID']
tableau_server_username = config['TABLEAU_SERVER_USERNAME']
tableau_server_password = config['TABLEAU_SERVER_PASSWORD']
tableau_server_address = config['TABLEAU_SERVER_ADDRESS']

# ----------------------User class-----------------------


class User:
    def __init__(self, username, site_role, group, row_id, Check):
        self.username = username
        self.site_role = site_role
        self.group = group
        self.row_id = row_id
        self.Check = Check


# TODO: create variable (df) for data w/ class User
ss_client = smartsheet.Smartsheet(ss_admin_token)
ss_client.errors_as_exceptions(True)  # makes errors return as exceptions

p = ss_client.Sheets.get_sheet(
    ss_sheet_id).to_json()
df = json.loads(p)
# print(df['rows'][0])
# print('----------------------DEBUG----------------------------')


# TODO: index all necessary values needed from smartsheet
# contains list comprehension (for loops)
username = [cells['cells'][0]['displayValue'] for cells in df['rows']]
site_role = [cells['cells'][3]['displayValue'] for cells in df['rows']]
group = [cells['cells'][4]['displayValue'] for cells in df['rows']]
row_id = [cells['id'] for cells in df['rows']]
Check = []
for c in df['rows']:
    try:
        Check.append(c['cells'][7]['value'])
    except Exception as e:
        Check.append(False)

user = User(username, site_role, group, row_id, Check)

# print(user.username[6], user.Check[6])
# print('----------------------DEBUG----------------------------')


# TODO: write a function to return a list of row_id where check is not marked for completion or False
def grab_unchecked():
    unchecked = []
    for i in range(len(user.username) - 1):
        if user.Check[i] == False:
            unchecked.append(user.row_id[i])
            print(user.row_id[i])
            return unchecked


def main():
    pass


if __name__ == '__main__':
    main()
