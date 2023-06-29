import logging  # for logging files
import sys  # sys.exit() function allows the developer to exit from Python
import json  # allows for for json
import argparse  # python for logging levels
import smartsheet
import tableauserverclient as TSC  # server client library tableau
from dotenv import load_dotenv  # loads.env file
from dotenv import dotenv_values  # loads values from .env file

# TODO: for testing purposes will use dotenv
load_dotenv()
config = dotenv_values(".env")


# all tokens needed for script execution
SS_ADMIN_TOKEN = config['SMARTSHEETS_ADMIN_TOKEN']
SS_SHEET_ID = config['SMARTSHEETS_SHEET_ID']
TABLEAU_SERVER_USERNAME = config['TABLEAU_SERVER_USERNAME']
TABLEAU_SERVER_PASSWORD = config['TABLEAU_SERVER_PASSWORD']
TABLEAU_SERVER_ADDRESS = config['TABLEAU_SERVER_ADDRESS']

# ----------------------User class-----------------------
class User:
    def __init__(self, username, site_role, group, row_id, Check):
        self.username = username
        self.site_role = site_role
        self.group = group
        self.row_id = row_id
        self.Check = Check


# TODO: define a variable (df) for data w/ class User
# UNIVERSAL VARIABLES
ss_client = smartsheet.Smartsheet(SS_ADMIN_TOKEN)
ss_client.errors_as_exceptions(True)  # makes errors return as exceptions

p = ss_client.Sheets.get_sheet(
    SS_SHEET_ID).to_json()
df = json.loads(p)
# print(df['rows'][0])
# print('----------------------DEBUG----------------------------')


# TODO: index all necessary values needed from smartsheet
# contains list comprehension (for loops)
username = [cells['cells'][0]['displayValue'] for cells in df['rows'] if cells['cells'][7]['value'] == False]
site_role = [cells['cells'][3]['displayValue'] for cells in df['rows'] if cells['cells'][7]['value'] == False]
group = [cells['cells'][4]['displayValue'] for cells in df['rows'] if cells['cells'][7]['value'] == False]
row_id = [cells['id'] for cells in df['rows'] if cells['cells'][7]['value'] == False]
Check = []
for c in df['rows']:
    try:
        if c['cells'][7]['value'] == False:
            Check.append(c['cells'][7]['value'])
    except Exception as e:
        Check.append(False)

USER = User(username, site_role, group, row_id, Check)

# print(USER.username, USER.site_role, USER.group, USER.row_id, USER.Check)
# print('----------------------DEBUG----------------------------')


# TODO: define a function to update rows in Smartsheets
def update_rows(text, row_id, column_id=8024982304384900):
    # ----Build the cell to update-------
    new_cell = ss_client.models.Cell()
    new_cell.column_id = column_id
    new_cell.value = text
    new_cell.strict = False

    # ---Build the row to update------
    new_row = ss_client.models.Row()
    new_row.id = row_id
    new_row.cells.append(new_cell)

    # -----Update rows--------------
    updated_row = ss_client.Sheets.update_rows(
        SS_SHEET_ID,
        [new_row])
    # TODO: define a function to check the checkbox once task is complete
    def check_box():
        check_column_id = 2245042581596036  # column 8 (check box column)
        new_cell = ss_client.models.Cell()
        new_cell.column_id = check_column_id
        new_cell.value = True
        new_cell.strict = False

        # Build the row to update
        new_row = ss_client.models.Row()
        new_row.id = row_id
        new_row.cells.append(new_cell)

        # Update rows
        updated_row = ss_client.Sheets.update_rows(
            SS_SHEET_ID,
            [new_row])
    check_box()


# TODO: define a function that checks the user against the tableau active directory
def check_user_tad(server, u):
    for id in TSC.Pager(server.user):
        if id.name == USER:
            return (id.name, id.id)


# TODO: define a function that adds users to their respective groups
def add_to_group(server, group, u_id, g, r):
    group_column_id = 6815450794354564 # column for current group status

    try:
        server.groups.add_user(group[0], u_id)  # adds users to groups
    except IndexError as e:
        text = '%s does not exist' % g
        update_rows(text, r, group_column_id)
    except ValueError as e:
        print(e)
    except TSC.ServerResponseError as e:
        logging.info('already a member of the group %s' % g)
        text = 'already a member of the group %s' % g
        update_rows(text, r, group_column_id)
    else:
        logging.info("added to group: %s" % g)
        text = "added to group: %s" % g
        update_rows(text, r, group_column_id)



# TODO: define a function to filter user group data
def filterG(user_data, all_users, server):
    for u, s, g, r, c in zip(user_data.username, user_data.site_role, user_data.group, user_data.row_id, user_data.Check):
        if c == False:
            # ----------Group is Filtered--------------------------
            # checks groups against all groups in Tableau and gets groups id
            filter_group_name = g
            options = TSC.RequestOptions()  # filter option to get the group from the server
            options.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name,
                                            TSC.RequestOptions.Operator.Equals,
                                            filter_group_name))  # the args are passing through this filter to see if they are in the server
            group, _ = server.groups.get(req_options=options)
    # ---------Creating New Users--------------------------------------
        # If users already exists it adds them to the group
            if u in all_users:
                logging.info("%s is already created" % u)
                text = "%s is already created" % u
                update_rows(text, r)
                u_name, u_id = check_user_tad(server, u)
                add_to_group(server, group, u_id, g, r)
        # If the user doesn't exists it creates the user
            else:
                try:
                    newU = TSC.UserItem(u, s)
                    newU = server.users.add(newU)  # creates new users
                except Exception as e:
                    logging.info(
                        "Username %s does not exist in Active Directory" % u)
                    text = "Username %s does not exist in Active Directory" % u
                    update_rows(text, r)
                else:
                    logging.info("%s was created" % newU.name)
                    text = "%s was created" % newU.name
                    update_rows(text, r)
                    add_to_group(server, group, newU.id, g, r)


# TODO: use all functions to create a script to add users from Smartsheet to Tablea Server (will use test server for now)
def main():
    # -------------- setting logging levels (defults as info)
    parser = argparse.ArgumentParser(
        description='Creates Users and adds them to specified groups.')
    parser.add_argument('--logging-level', '-l', choices=['debug', 'info', 'error'], default='info',
                        help='desired logging level (set to error by default)')
    args = parser.parse_args()

    logging_level = getattr(logging, args.logging_level.upper())
    logging.basicConfig(filename='E:\Tableau_API\Log_File.log', level=logging_level,
                        format='{%(asctime)s || %(levelname)s-\nMessage: %(message)s}')

    # set variable to connect to Tableau Server
    tableau_auth = TSC.TableauAuth(TABLEAU_SERVER_USERNAME, TABLEAU_SERVER_PASSWORD)
    server = TSC.Server(
        'http://uhmc-tableau-t.uhmc.sbuh.stonybrook.edu:8000')  # TODO: ask about the proper ip address to connect to test server
    print('------------------DEBUG------------------')

    # DEBUG to sign in to test server
    # with server.auth.sign_in(tableau_auth):
    #     all_datasources, pagination_item = server.datasources.get()
    #     print("\nThere are {} datasources on site: ".format(pagination_item.total_available))
    #     print([datasource.name for datasource in all_datasources])

    # server = TSC.Server(TABLEAU_SERVER_ADDRESS)
    user_data = USER

    # Tableau Auth
    try:
        server.auth.sign_in(tableau_auth)
    except Exception as e:
        print(e)
        logging.critical(e)
        sys.exit(2)
    else:
        pass

    server.use_server_version()  # sets to latest version of TSC library
    # list of usernames in Tableau
    all_users = [au.name for au in TSC.Pager(server.users)]

    # filterG(user_data, all_users, server)
    pass

if __name__ == '__main__':
    main()
