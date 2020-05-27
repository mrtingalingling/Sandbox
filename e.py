#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Author: Ting
Get all stock information'''
import logging
import traceback
from argparse import ArgumentParser
import datetime
# from pprint import pprint
# from subprocess import call
# import re
from collections import defaultdict
# from os.path import join, abspath, dirname, isfile
import csv
import codecs
import urllib.request
# import matplotlib.pyplot as plt
import psycopg2
import time
from sshtunnel import SSHTunnelForwarder
import importlib
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import random
import pprint

log = logging.getLogger(name=__file__)
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


class Scrap:
	today_str = str(datetime.date.today()).replace("-", "")

	def __init__(self, *args, **kwargs):
		# super().__init__(self, config=None, *args, **kwargs)

		self.parse_args = self._parse_args()

	def _parse_args(self):
		parser = ArgumentParser()
		args, trash = parser.parse_known_args()

		return args

	# MMoney Starts
	def randelay(self): 
		'''Make the delay more realistic by randomizing the wait time'''
		return random.randrange(500000, 1500000)/100000

	def MMoneyByDate(self, driver, date_value='07', delay=10):
		'''Use Selenium to expand Table by air date'''
		# date_selector = '#airdate'
		# table_selector = '#stockTable'

		# https://stackoverflow.com/questions/49939123/scrape-dynamic-contents-created-by-javascript-using-python
		try:
			# Wait for date selector to be loaded
			WebDriverWait(driver, self.randelay()).until(
				EC.presence_of_element_located((By.ID, 'airdate'))
			)
			select = Select(driver.find_element_by_id('airdate'))
			
			# Select by visible text
			# select.select_by_visible_text(date_value)
			# Select by selector attr value
			select.select_by_value(date_value)

		except TimeoutException:
			print('Loading took too much time!')
		else:
			html = driver.page_source

			# Check if the page is condensed 
			if '* Displaying' in html: 
				try:
					# Wait for Show All button to be loaded
					WebDriverWait(driver, self.randelay()).until(
						EC.presence_of_element_located((By.CSS_SELECTOR, '#leftPanel > a.expandLink.showAll'))
					)
					# Click to Show All tickers
					driver.find_element_by_css_selector('#leftPanel > a.expandLink.showAll').click()

					# Load html from the expanded table 
					html = driver.page_source
				except TimeoutException:
					print('Loading took too much time!')
		# finally:
		# 	driver.quit()

		if html:
			return self.htmlMMoney2Dict(html, date_value)
		else: 
			print('No html found.')

	def htmlMMoney2Dict(self, html, date_value): 
		'''Yellow Brick Road using the Soup Recipe.
		Convert html data into dictionary
		'''
		soup = BeautifulSoup(html, 'lxml')

		# MMoney
		master_call_list = []
		call_list = soup.find('table').find_all('tr')
		call_date = soup.select_one('#leftPanel > p').text
		print(call_date)
		for call_list_item in call_list:
			if not call_list_item.find('td'): 
				continue

			ticker = call_list_item.find_all('td')[0].find('a').text
			call_list_items_dict[ticker][date_value] = {
				'Company Name': call_list_item.find_all('td')[0].text, 
				'Segment': call_list_item.find_all('td')[2].find('img')['alt'], 
				'Call': call_list_item.find_all('td')[3].find('img')['alt'], 
				'Call Price': call_list_item.find_all('td')[4].text
			}
			master_call_list.append([
				ticker, 
				call_list_items_dict[ticker][date_value]['Company Name'], 
				date_value, 
				call_list_items_dict[ticker][date_value]['Segment'], 
				call_list_items_dict[ticker][date_value]['Call'], 
				call_list_items_dict[ticker][date_value]['Call Price']
			])
		# print(call_list_items_dict)

		return call_list_items_dict, master_call_list


if __name__ == '__main__':
	from _cred_private_links import links
	from gsht_connect import Google_API_Connect
	gsht = Google_API_Connect()

	url=links['mmoney']
	# print(url)
	page = requests.get(url)
	soup_dates = BeautifulSoup(page.text, 'lxml').find(id='airdate').find_all('option')  # date_selector = '#airdate'
	i = 0
	driver.get(url)
	for call_date in soup_dates: 
		# value="2020-05-21"
		if '-' in call_date['value']: 
			print('-------')
			print('Getting... ')
			# print('Getting Call Date on:', call_date['value'])
			soup_du_jour, alphabet_soup = Scrap().MMoneyByDate(driver=driver, date_value=call_date['value'])
			# pprint.pprint(soup_du_jour)

			print(alphabet_soup)
			gsht.gsht_update(spreadsheetId=links['google_sheet_id'], action='Add', data_values=alphabet_soup, rangeName=links['sheet_name'], sheet_title_string=links['sheet_name'])

			time.sleep(Scrap().randelay())
			i += 1
		else: 
			print('Skipping:', call_date.text)
			continue
		# if i > 2: 
		# 	break

	pprint.pprint(soup_du_jour)
	driver.quit()  # alphabet_soup

# http://meumobi.github.io/stocks%20apis/2016/03/13/get-realtime-stock-quotes-yahoo-finance-api.html

