#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Author  : Ting
Contact : ???
Version : 1
Purpose : Google Sheet I/O
'''
from __future__ import print_function
import httplib2
import os

from googleapiclient.discovery import build
from oauth2client import client, tools
from oauth2client.file import Storage
from oauth2client.service_account import ServiceAccountCredentials
# https://developers.google.com/identity/protocols/OAuth2ServiceAccount
# https://github.com/burnash/gspread/blob/c0a5a6d83083c467a647ab91bf1caaa1f829b5c7/tests/test.py


class Google_API_Connect:
	try:
		import argparse
		flags, unknown_flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_known_args()
	except ImportError:
		flags = None

	# If modifying these scopes, delete your previously saved credentials
	# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
	SCOPES = 'https://www.googleapis.com/auth/spreadsheets'  # .readonly'
	DRIVE_SCOPES = 'https://www.googleapis.com/auth/drive'
	CLIENT_SECRET_FILE = 'client_secret.json'
	APPLICATION_NAME = 'GoogleSheet_DB_Sync'

	def __init__(self):
		self.gsht_service, self.gdrv_service = self.check_credentials()

	def get_credentials(self):
		"""Gets valid user credentials from storage.

		If nothing has been stored, or if the stored credentials are invalid,
		the OAuth2 flow is completed to obtain the new credentials.

		Returns:
			Credentials, the obtained credential.
		"""
		home_dir = os.path.expanduser('~')
		credential_dir = os.path.join(home_dir, '.credentials')
		if not os.path.exists(credential_dir):
			os.makedirs(credential_dir)
		credential_path = os.path.join(credential_dir, 'sheets.googleapis.com-python-db-sync.json')

		store = Storage(credential_path)
		credentials = store.get()
		if not credentials or credentials.invalid:
			flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
			flow.user_agent = self.APPLICATION_NAME
			if self.flags:
				credentials = tools.run_flow(flow, store, self.flags)
			else:  # Needed only for compatibility with Python 2.6
				credentials = tools.run(flow, store)
			print('Storing credentials to ' + credential_path)
		return credentials

	def check_credentials(self):
		if 'user' in self.unknown_flags:
			credentials = self.get_credentials()
			http = credentials.authorize(httplib2.Http())
			discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?' 'version=v4')
			service = build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)
			drive_service = build('drive', 'v3', http=http)
		else:
			try:
				SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
				SERVICE_ACCOUNT_FILE = os.path.join(SCRIPT_DIR, '_cred.json')
				# SERVICE_ACCOUNT_FILE = '_cred.json'
				credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, self.SCOPES)
				drive_credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, self.DRIVE_SCOPES)
				service = build('sheets', 'v4', credentials=credentials)
				drive_service = build('drive', 'v3', credentials=drive_credentials)
				# service = build('sheets', 'v4', developerKey=api_key)
			except Exception as e:
				print(e)
				return None

		return service, drive_service

	# Added Function #
	# @classmethod
	# def google_sheet_connect(cls, spreadsheetId, rangeName, access='r'):
	def google_sheet_connect(self, spreadsheetId, rangeName, access='r'):
		'''Test and/or read a specific spreadsheet'''
		if access == 'w':
			print("Can't change to write privilege yet. Sorry :(")
			return

		# result = cls.gsht_service.spreadsheets().values().get(
		result = self.gsht_service.spreadsheets().values().get(
			spreadsheetId=spreadsheetId, range=rangeName).execute()
		return result

	def gsht_update_body_builder(self, sheet_title_string):
		# https://developers.google.com/sheets/api/guides/batchupdate
		# Config Sheet Properties
		SheetProperties = {
			# "sheetId": sheetId_number,
			"title": sheet_title_string,
			# "index": sheet_index_number
		}

		AddSheetRequest = {
			# {object(SheetProperties)}
			"properties": SheetProperties
		}

		add_sheet_request = [
			{
				# {object(AddSheetRequest)}
				"addSheet": AddSheetRequest
			},
			# UpdateCellsRequest
		]

		request_body = {
			"requests": add_sheet_request,
		}

		return request_body

	def gsht_values_body_builder(self, value_input_option, value_range_body):
		# https://developers.google.com/sheets/api/guides/values
		values_batchupdate_body = {
			"valueInputOption": value_input_option,
			"data": [value_range_body]
		}

		return values_batchupdate_body

	def gsht_body_builder(self, action, data_values=[[]], rangeName='', sheet_title_string='Test_Tab', value_input_option='USER_ENTERED'):
		value_range_body = {
			"range": rangeName,
			"majorDimension": "ROWS",
			"values": data_values
		}

		if action == 'AddSheet':
			return self.gsht_update_body_builder(sheet_title_string)
		elif action == 'Write':
			return self.gsht_values_body_builder(value_input_option, value_range_body)
		elif action == 'Add':
			return {"values": data_values}

	def gsht_update(self, spreadsheetId, action, data_values=[[]], rangeName='', sheet_title_string='Test_Tab', value_input_option='USER_ENTERED'):
		if not rangeName:
			rangeName = sheet_title_string

		data_body = self.gsht_body_builder(action, data_values, rangeName, sheet_title_string)

		try:
			if action == 'AddSheet':
				# Create New Sheet to SpreadSheet
				response = self.gsht_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=data_body).execute()
				print(response)
			elif action == 'Write':
				# Add Values to Sheet
				response = self.gsht_service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheetId, body=data_body).execute()
				print(response)
			elif action == 'Read':
				# Read Values to Sheet
				response = self.gsht_service.spreadsheets().values().batchGet(spreadsheetId=spreadsheetId, range=rangeName).execute()
				print(response)
			elif action == 'Add':
				# Append Values to Sheet
				response = self.gsht_service.spreadsheets().values().append(spreadsheetId=spreadsheetId, range=rangeName, valueInputOption=value_input_option, body=data_body).execute()
				print(response)
		except Exception as e:
			print(e)


def main():
	"""Shows basic usage of the Sheets API.

	Creates a Sheets API service object and prints the names and majors of
	students in a sample spreadsheet:
	https://docs.google.com/spreadsheets/d/1f9qY7VW8mwIopLVJzmKKzTD8Qxxt33rcJOrbH-Yx-bs/edit#gid=0
	"""
	gsht = Google_API_Connect()
	service = gsht.gsht_service
	# drive_service = gsht.gdrv_service

	spreadsheetId = ''
	rangeName = 'Sheet2!A2:E'
	result = service.spreadsheets().values().get(
		spreadsheetId=spreadsheetId, range=rangeName).execute()
	values = result.get('values', [])

	if not values:
		print('No data found.')
	else:
		print('Name, Major:')
		max_row_size = 1
		for row in values:
			max_row_size = len(row) if len(row) > max_row_size else max_row_size
			if len(row) == 0:
				continue
			for rn in range(max_row_size):
				if rn > len(row):
					row[rn] = ''
			# Print columns A and E, which correspond to indices 0 and 4.
			print('%s, %s' % (row[0], row[4]))

	value_input_option = 'USER_ENTERED'
	value_range_body = {'values': [['hahaha', '5678'], ['lolol']]}
	request = service.spreadsheets().values().update(spreadsheetId=spreadsheetId, range=rangeName, valueInputOption=value_input_option, body=value_range_body)
	response = request.execute()
	print(response)


if __name__ == '__main__':
	main()