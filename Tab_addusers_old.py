# Api creates userid and assigns users to groups
# For Tableau Server 10.4
# REST API 2.7
# site id = feae689d-1700-48d1-9ec1-27388179a871 (for Tableau site, (not needed))
# Assumptions
# 1. Users are from active directory
# 2. Username must be filled (required field)
# 3. Group field must be filled (required field)

### --Enter in Terminal--- "python E:\Tableau_API\Tab_addusers.py" ###
# Tableau server address --- 'http://uhmc-tableau-p.uhmc.sunysb.edu:8000'
import logging  # for logging files
import sys  # sys.exit() function allows the developer to exit from Python
import json  # allows for for json
import argparse  # python for logging levels
import getpass  # hidden password
import smartsheet
import tableauserverclient as TSC  # server client library tableau

# Smartsheet doc link for pytyhon--- --- http://smartsheet-platform.github.io/smartsheet-python-sdk/smartsheet.models.html#module-smartsheet.models.cell_data_item
# Tableausmart token for smartsheet = mfhp230j8dc63jae7m7pxsjnni

# ----------------------User class-----------------------


class User:

    def __init__(self, username, site_role, group, row_id, Check):
        self.username = username
        self.site_role = site_role
        self.group = group
        self.row_id = row_id
        self.Check = Check


# -------------------Gets data from Smartsheets---------------------------------------
def smartsheet_data():
    # -------------------- Initialize client-----------------------------------
    admin_token = 'mfhp230j8dc63jae7m7pxsjnni'  # API token from smartsheet
    # Sheet id (look in doc to find where to locate)
    sheet_id = '1318178614732676'

    ss_client = smartsheet.Smartsheet(admin_token)
    ss_client.errors_as_exceptions(True)

    p = ss_client.Sheets.get_sheet(
        sheet_id).to_json()
    p = json.loads(p)
    # ------------------------List of user info----------------------------------
    username = [cells['cells'][0]['displayValue'] for cells in p['rows']]
    site_role = [cells['cells'][3]['displayValue'] for cells in p['rows']]
    group = [cells['cells'][4]['displayValue'] for cells in p['rows']]
    row_id = [cells['id'] for cells in p['rows']]
    # stored in the class attributes as a list
    Check = []
    for c in p['rows']:
        try:
            Check.append(c['cells'][7]['value'])
        except Exception as e:
            Check.append(False)

    user = User(username, site_role, group, row_id, Check)

    return (user)

# ---------------------Updates the status back to smartsheet------------------------


# defults to the column id of the "status" column in smartsheet
def update_rows(text, row_id, column_id=8024982304384900):

    admin_token = 'mfhp230j8dc63jae7m7pxsjnni'
    sheet_id = '1318178614732676'
    # ----------Initialize client---------------
    ss_client = smartsheet.Smartsheet(admin_token)
    ss_client.errors_as_exceptions(True)

    # column_six = 8024982304384900 in the function defult

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
        sheet_id,
        [new_row])

    def Check_box():

        check_column_id = 2245042581596036  # column 8 (check box)
        ss_client = smartsheet.Smartsheet(admin_token)
        ss_client.errors_as_exceptions(True)

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
            sheet_id,
            [new_row])

    Check_box()

# -------------Returns user id of existing users-------------


def check_user(server, u,):
    for id in TSC.Pager(server.users):  # check against all users in Tableau
        if id.name == u:
            return (id.name, id.id)

# ----------------Adds existing users to new groups------------


def adding_groups(server, group, u_id, g, r):

    column_id = 6815450794354564  # colum id of the group status in the smartsheet

    try:
        server.groups.add_user(group[0], u_id)  # adds users to groups
    except IndexError as e:
        text = '%s does not exist' % g
        update_rows(text, r, column_id)
    except ValueError as e:
        print(e)
    except TSC.ServerResponseError as e:
        logging.info('already a member of the group %s' % g)
        text = 'already a member of the group %s' % g
        update_rows(text, r, column_id)
    else:
        logging.info("added to group: %s" % g)
        text = "added to group: %s" % g
        update_rows(text, r, column_id)


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

    # ----------------Function Variables------------------------
    username = input("Username:")
    password = getpass.getpass("Password: ")
    tableau_auth = TSC.TableauAuth(username, password)
    server = TSC.Server(
        'http://uhmc-tableau-p.uhmc.sunysb.edu:8000')  # TODO: 443
    user_data = smartsheet_data()
    # ----------------Tableau Auth-----------------------
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

    def filterG(user_data):
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
                    u_name, u_id = check_user(server, u)
                    adding_groups(server, group, u_id, g, r)
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
                        adding_groups(server, group, newU.id, g, r)

    filterG(user_data)


if __name__ == '__main__':
    main()
