import configparser
import praw
import webbrowser
from config.praw_config import CredKeys, OAUTH_CRED_KEYS, set_reddit_oauth_refresh_token, PRAW_FILE_PATH, get_reddit_oath_credentials


def get_sites_with_scopes(_parser=None):
    cp = _parser or configparser.ConfigParser()
    if not _parser:
        cp.read(PRAW_FILE_PATH)
    scope_config_key = "oauth_scope"
    return [(site_name, cp[site_name][scope_config_key]) for site_name in cp if site_name != "DEFAULT"]


def get_sites_without_refresh_tokens():
    cp = configparser.ConfigParser()
    cp.read(PRAW_FILE_PATH)
    refresh_config_key = OAUTH_CRED_KEYS[CredKeys.refresh]
    return [(site_name, scope) for (site_name, scope) in get_sites_with_scopes(cp)if not cp[site_name][refresh_config_key]]


def set_oauth_refresh_token(account_name, oauth_scope):
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

    ap = argparse.ArgumentParser(description="Set refresh tokens for new accounts in the PRAW config file.")
    ap.add_argument("--new-accounts", "-n", dest="only_new_accounts", action="store_true", help="Find all new accounts in the config file, and set their refresh tokens.")
    ap.add_argument("--account-names", "-a", dest="account_names", nargs="+", default=[], choices=choices)
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
