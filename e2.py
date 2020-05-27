#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Author: Ting
Get all stock information'''
from _cred_private_links import links
from gsht_connect import Google_API_Connect
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from collections import defaultdict
import logging
import traceback
import requests
import pprint
from e import Scrap

log = logging.getLogger(name=__file__)
gsht = Google_API_Connect()
chrome_options = Options()
chrome_options.binary_location = '/usr/bin/google-chrome-stable'
chrome_options.add_argument('--no-sandbox')  # Bypass OS security model
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
chrome_options.add_argument("start-maximized")  # Open Browser in maximized mode
chrome_options.add_argument("disable-infobars")  # Disabling infobars
chrome_options.add_argument("--disable-extensions")  # Disabling extensions
driver = webdriver.Chrome(executable_path='/home/ting/Envs/chromedriver', options=chrome_options)
call_list_items_dict = defaultdict(dict)  # Making this Global Variable 
url=links['mmoney']


if __name__ == '__main__':
	# print(url)
	page = requests.get(url)
	soup_dates = BeautifulSoup(page.text, 'lxml').find(id='airdate').find_all('option')  # date_selector = '#airdate'
	driver.get(url)
	print('Getting... ')
	soup_du_jour, master_call_list = Scrap().MMoneyByDate(driver=driver, date_value=soup_dates[4]['value'])
	gsht.gsht_update(spreadsheetId=links['google_sheet_id'], action='Add', data_values=master_call_list, rangeName=links['sheet_name'], sheet_title_string=links['sheet_name'])

	pprint.pprint(soup_du_jour)
	driver.quit()  # alphabet_soup

# http://meumobi.github.io/stocks%20apis/2016/03/13/get-realtime-stock-quotes-yahoo-finance-api.html

