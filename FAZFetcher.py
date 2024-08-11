from dotenv import load_dotenv, find_dotenv
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import smtplib, ssl
from email import encoders
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

load_dotenv(find_dotenv())

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
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(MAIL_USER, MAIL_PASSWORD)
    
        for receiver in KINDLE_MAILLIST.split(','):
            msg = MIMEMultipart()
            msg['From'] = MAIL_USER
            msg['To'] = receiver
            msg['Subject'] = 'FAZ'
            msg.attach(MIMEText('Test', 'plain'))
            record = MIMEBase('application', 'epub+zip')
            record.set_payload(attachment)
            encoders.encode_base64(record)
            record.add_header('Content-Disposition', 'attachment; filename=FAZ.epub')
            msg.attach(record)
            server.sendmail(MAIL_USER, receiver, msg.as_string())
            print('Email sent to ' + receiver)
    except Exception as e:
        print('Something went wrong when trying to send the email')
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


# fetch the latest newpaper from FAZ (sunday edition)
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
    download_link = driver.find_element(By.ID, download_link_id).get_attribute('href')

    # Download the file and send the cookies along with the request
    cookies = driver.get_cookies()
    driver.quit()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    response = session.get(download_link)
    return response.content


if __name__ == '__main__':
    send_mail(get_newspaper())

