from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
import time
import sqlite3

conn = sqlite3.connect(r'C:\Users\DELL\Desktop\hospital.db')
c = conn.cursor()

geckodriver = r"C:\Users\DELL\geckodriver-v0.26.0-win64\geckodriver.exe"
url = 'https://sp1.hso.mohw.gov.tw/doctor/Index1.php'
options = Options()
options.add_argument('‐headless')
prof = webdriver.FirefoxProfile()
prof.set_preference("permissions.default.image",2)
driver = Firefox(executable_path = geckodriver, options=options, firefox_profile = prof)  
driver.get(url)
ul = driver.find_elements_by_css_selector('.topmenu > ul > li:nth-child(3) > ul > li > a')
l = len(ul)
for link in range(2, l):
    ele = driver.find_elements_by_css_selector(f'.topmenu > ul > li:nth-child(3) > ul > li:nth-child({link + 1}) > a')
    url = ele[0].get_attribute('href')
    driver.get(url)
    division = driver.find_elements_by_css_selector('#sidebar-body > ul > li:nth-child(1)')
    division = division[0].text
    print(division)
    qa = driver.find_elements_by_css_selector('#sidebar-body > ul > li:nth-child(2) > a')
    url = qa[0].get_attribute('href')
    #print(url)
    driver.get(url)
    pages = driver.find_elements_by_css_selector('#PageNo > option:last-child')[0].text
    for page in range(int(pages)):
        for num in range(20):
            num = num + 1
            qa_url = driver.find_elements_by_css_selector(f'#sidebar-content > div > div > div.main.col-md-11.col-sm-12.col-xs-12 > form > table > tbody > tr:nth-child({num}) > td:nth-child(7) > a')[0].get_attribute('href')
            driver.get(qa_url)
            time.sleep(0.3)
            title = driver.find_elements_by_css_selector('#sidebar-content > div > div > div > ul > li.subject')
            question = driver.find_elements_by_css_selector('#sidebar-content > div > div > div > ul > li.ask')
            answer = driver.find_elements_by_css_selector('#sidebar-content > div > div > div > ul > li.ans')
            title = title[0].text
            for i in range(len(title)):
                if title[i] == ' ':
                    id = title[:i]
                    print('id:', id)
                    title = title[i+1:]
                    break
            question = question[0].text
            answer = answer[0].text
            c.execute("INSERT INTO data VALUES (?, ?, ?, ?, ?)", (id, division, title, question, answer))
            driver.back()
            #print(title, question, answer, id)
        conn.commit()
        if page == 0:
            next_page = driver.find_elements_by_css_selector('#sidebar-content > div > div > div.main.col-md-11.col-sm-12.col-xs-12 > form > div:nth-child(4) > div:nth-child(2) > a')[0].get_attribute('href')
            driver.get(next_page)
        else:
            next_page = driver.find_elements_by_css_selector('#sidebar-content > div > div > div.main.col-md-11.col-sm-12.col-xs-12 > form > div:nth-child(4) > div:nth-child(2) > a:nth-child(3)')[0].get_attribute('href')
            driver.get(next_page)
    driver.get('https://sp1.hso.mohw.gov.tw/doctor/Index1.php')
driver.quit()
conn.close()