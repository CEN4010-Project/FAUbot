import configparser
import praw
import webbrowser
from config.praw_config import CredKeys, OAUTH_CRED_KEYS, set_reddit_oauth_refresh_token, PRAW_FILE_PATH, get_reddit_oath_credentials


def get_sites_with_scopes(_parser=None):
    """
    Helper function to get each sitename (Reddit user name) and the Oauth scopes associated with it.
    :param _parser: An existing ConfigParser that has read praw.ini, or None
    :return: A list of tuples containing site name and scopes, e.g. [('FAUbot', 'identity edit wikiread')]
    """
    cp = _parser or configparser.ConfigParser()
    if not _parser:
        cp.read(PRAW_FILE_PATH)
    scope_config_key = "oauth_scope"
    return [(site_name, cp[site_name][scope_config_key]) for site_name in cp if site_name != "DEFAULT"]


def get_sites_without_refresh_tokens():
    """
    Helper function to get all the site names (Reddit user names) that don't have Oauth refresh tokens saved.
    :return: Same as get_sites_with_scopes, but only for those without refresh tokens.
    """
    cp = configparser.ConfigParser()
    cp.read(PRAW_FILE_PATH)
    refresh_config_key = OAUTH_CRED_KEYS[CredKeys.refresh]
    return [(site_name, scope) for (site_name, scope) in get_sites_with_scopes(cp)if not cp[site_name][refresh_config_key]]


def set_oauth_refresh_token(account_name, oauth_scope):
    """
    Triggers the login process to generate a refresh token, and saves the token. The process steps are:
    1. Connect to Reddit, and make the user enter the username and password.
    2. Redirect to a callback URL. Since no web server is running, the page will 404. However, the code in the URL's
       query parameters must be copied and pasted into the Python console to continue the login process.
    3. Save the refresh token in the praw.ini config file.
    :param account_name: The Reddit user who will be logged in.
    :param oauth_scope: A string of Oauth permissions that the automated program will have on behalf of the Reddit user.
    """
    oauth_credentials = get_reddit_oath_credentials(account_name)
    r = praw.Reddit("Getting first OAuth refresh token for /u/{}".format(account_name))
    r.set_oauth_app_info(client_id=oauth_credentials[OAUTH_CRED_KEYS[CredKeys.client]],
                         client_secret=oauth_credentials[OAUTH_CRED_KEYS[CredKeys.secret]],
                         redirect_uri=oauth_credentials[OAUTH_CRED_KEYS[CredKeys.uri]])

    url = r.get_authorize_url(state=account_name, scope=oauth_scope, refreshable=True)
    webbrowser.open(url)
    code = input("Enter code: ")
    print("Getting access information.")
    access_information = r.get_access_information(code)
    refresh_token = access_information['refresh_token']
    print("Saving refresh token.")
    set_reddit_oauth_refresh_token(account_name, refresh_token)


def register_new_accounts():
    """
    High-level helper function that gets all Reddit users in praw.ini that have no refresh token, and triggers the login
    process for each of them.
    """
    new_accounts = get_sites_without_refresh_tokens()
    if not new_accounts:
        print("No new accounts are in the PRAW config file.")
    else:
        for (account, scope) in new_accounts:
            set_oauth_refresh_token(account, scope)


def main():
    import argparse
    accounts = get_sites_with_scopes()
    choices = [site for site, scope in accounts]
    scopes = {account: scope for account, scope in accounts}

    # use argparse to define and parse command line arguments when running this script.
    ap = argparse.ArgumentParser(description="Set refresh tokens for new accounts in the PRAW config file.")
    ap.add_argument("--new-accounts", "-n", dest="only_new_accounts", action="store_true",
                    help="Find all new accounts in the config file, and set their refresh tokens.")
    ap.add_argument("--account-names", "-a", dest="account_names", nargs="+", default=[], choices=choices,
                    help="Only set refresh tokens for specific accounts.")
    args = ap.parse_args()

    if args.only_new_accounts and args.account_names:
        print("You cannot have both new-accounts and account-names set.")
    elif args.only_new_accounts:
        print("Registering all new accounts")
        register_new_accounts()
    elif args.account_names:
        print("Registering accounts: {}".format(", ".join(account for account in args.account_names)))
        for account in args.account_names:
            scope = scopes[account]
            set_oauth_refresh_token(account, scope)
    else:
        print("You have chosen to do nothing.")
    print("Done.")

if __name__ == '__main__':
    main()
