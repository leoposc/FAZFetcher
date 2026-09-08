from dotenv import load_dotenv, find_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from email import encoders
from typing import Any
from pathlib import Path
import smtplib, ssl
import requests
import argparse
import os

_ = load_dotenv(find_dotenv())

KINDLE_MAILLIST = os.environ['KINDLE_MAILLIST']
MAIL_USER = os.environ['MAIL_USER']
MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
MAIL_FAZ = os.environ['MAIL_FAZ']
PASSWORD_FAZ = os.environ['PASSWORD_FAZ']

def send_mail(attachment):
    port = 587  # FOR TSL
    context = ssl.create_default_context()

    try:
        server = smtplib.SMTP('smtp.web.de', port)
        _ = server.ehlo()
        _ = server.starttls(context=context)
        _ = server.ehlo()
        _ = server.login(MAIL_USER, MAIL_PASSWORD)
    
        for receiver in KINDLE_MAILLIST.split(','):
            filename = 'FAZ_' + datetime.today().strftime('%d.%m.%Y')
            msg = MIMEMultipart()
            msg['From'] = MAIL_USER
            msg['To'] = receiver
            msg['Subject'] = filename
            msg.attach(MIMEText('Test', 'plain'))
            record = MIMEBase('application', 'epub+zip')
            record.set_payload(attachment)
            encoders.encode_base64(record)
            value=f'attachment; filename={filename}.epub'
            record.add_header('Content-Disposition', value)
            msg.attach(record)
            server.sendmail(MAIL_USER, receiver, msg.as_string())
            print(datetime.now().strftime('[%d.%m.%Y:%H:%M]: ') + 'Email sent to ' + receiver)
    except Exception as e:
        print(datetime.now().strftime('[%d.%m.%Y:%H:%M]: ') + 'Something went wrong when trying to send the email')
        print(e)
    finally:
        server.quit()


# returns date of the last sunday, except it is saturday or sunday, 
# then return the date of the sunday this week
# since every saturday the new FAZ is available
def get_sunday_as_date():
    today = datetime.today()
    days_behind = today.weekday() + 1
    if days_behind == 6: # if today is saturday
        days_behind = -1
    elif days_behind == 7: # if today is sunday
        days_behind = 0
    sunday = today - timedelta(days=days_behind)
    return sunday.strftime('%d.%m.%Y')


def get_weekday_as_datetime() -> datetime:
    return datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

def get_saturday_as_datetime():
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    days_behind = today.weekday() + 2
    if days_behind == 7: # if today is saturday
        days_behind = 0
    elif days_behind == 8: # if today is sunday
        days_behind = 1
    return today - timedelta(days=days_behind)

# fetch the latest newspaper from FAZ (weekday)
def get_weekday_newspaper():
    options = webdriver.ChromeOptions()
    options.headless = True

    # Set up Selenium WebDriver (e.g., ChromeDriver)
    driver = webdriver.Chrome(options=options)

    # Navigate to the login page
    driver.get(url="https://aktion.faz.net/epub")

    # Find the email and password input fields and the submit button
    email_input = driver.find_element(by=By.NAME, value="email")
    password_input = driver.find_element(By.NAME, value="password")

    # Enter the credentials
    email_input.send_keys(MAIL_FAZ)
    password_input.send_keys(PASSWORD_FAZ)

    # Submit the form
    password_input.send_keys(Keys.RETURN)

    # wawit for the login to complete
    driver.implicitly_wait(1)

    # Navigate the page to scrape 
    date = get_weekday_as_datetime().strftime('%d.%m.%Y')
    download_link_id = 'EPUB+FAZ+Magazin+' + date
    download_link: str | None = driver.find_element(
        By.ID, download_link_id
    ).get_attribute("href")
    
    if download_link is None:
        raise RuntimeError(
        f"Download link element '{download_link_id}' has no href attribute"
    )


    # Download the file and send the cookies along with the request
    cookies = driver.get_cookies()
    driver.quit()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    response = session.get(download_link)
    return response.content



# fetch the latest newspaper from FAZ (sunday edition)
def get_newspaper():
    options = webdriver.ChromeOptions()
    options.headless = True

    # Set up Selenium WebDriver (e.g., ChromeDriver)
    driver = webdriver.Chrome(options=options)

    # Navigate to the login page
    driver.get("https://aktion.faz.net/epub")
    
    # Find the email and password input fields and the submit button
    email_input = driver.find_element(by=By.NAME, value="email")
    password_input = driver.find_element(By.NAME, "password")
    # login_button = driver.find_element(By.TAG_NAME, "button")

    # Enter your credentials
    email_input.send_keys(MAIL_FAZ)
    password_input.send_keys(PASSWORD_FAZ)

    # Submit the form
    password_input.send_keys(Keys.RETURN)

    # Wait for the login to complete
    driver.implicitly_wait(1)

    # Navigate to the page you want to scrape
    download_link_id = 'EPUB+FAS+Magazin+' + get_sunday_as_date()
    download_link: str | None = driver.find_element(
        By.ID, download_link_id
    ).get_attribute("href")
    
    if download_link is None:
        raise RuntimeError(
        f"Download link element '{download_link_id}' has no href attribute"
    )

    # Download the file and send the cookies along with the request
    cookies: list[dict[Any, Any]] = driver.get_cookies()
    driver.quit()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    response = session.get(download_link)
    return response.content

def get_last_run(edition: str) -> datetime:
    file = Path(f'last_run_{edition}.txt')
    # check if the file exists
    if not file.exists():
        file.touch()
    with open(file, mode='r') as file:
        last_run = file.read()
    # handle case when file is empty
    if last_run == '':
        return datetime.min
    return datetime.strptime(last_run, '%d.%m.%Y')

def write_last_run(edition: str):
    filename: str = f'last_run_{edition}.txt'
    with open(filename, 'w+') as file:
        if edition == 'sunday':
            _ = file.write(get_saturday_as_datetime().strftime('%d.%m.%Y'))
        else:
            _ = file.write(get_weekday_as_datetime().strftime('%d.%m.%Y'))

def check_for_new_weekdaypaper()-> bool:
    # Skip sundays 
    if get_weekday_as_datetime().weekday() == 6:
        return False 

    if get_last_run('weekday') < get_weekday_as_datetime():
        return True
    else:
        return False

def check_for_new_sundaypaper():
    if get_last_run(edition='sunday') < get_saturday_as_datetime():
        return True
    else:
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='FAZFetcher',
        description='Fetch the latest Frankfurter Allgemeine Zeitung. Use the parameters' + 
                    'to specify which news papers should be sent to your kindle. '
    )
    _ = parser.add_argument(
        '-e',
        '--editions',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help=(
            'Specify which edition should be fetched. '
            '0 = Frankfurter Allgemeine Zeitung; '
            '1 = Frankfurter Allgemeine Sonntagszeitung; '
            '2 = Both'
        )
    )
    args = parser.parse_args()

    if args.editions in (0, 2): 
        if check_for_new_weekdaypaper():
            send_mail(get_weekday_newspaper())
            write_last_run(edition='weekday')
        else:
            print(datetime.now().strftime('[%d.%m.%Y:%H:%M]: ') + 'No new FAZ available for today.')

    if args.editions in (1, 2):
        if check_for_new_sundaypaper():
            send_mail(get_newspaper())
            write_last_run(edition='sunday')
        else:
            print(datetime.now().strftime('[%d.%m.%Y:%H:%M]: ') + 'No new FAS available for this week.')

