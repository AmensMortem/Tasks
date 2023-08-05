from os import environ
import os
from dotenvy import load_env, read_file
from github import Github, Auth
import git
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import subprocess

load_env(read_file('src/.env'))
auth_git = Auth.Token(environ.get("GitToken"))  # gitHub
gitHubAuth = Github(auth=auth_git)
json_key = 'src/small-394913-470a0e673114.json'  # Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(json_key, scope)
client = gspread.authorize(creds)  # URL к таблице Google Sheets
sheet_url = 'https://docs.google.com/spreadsheets/d/1OIkPzOv0DgJDtJUS_7W9bQ4ome9GMCKoIcLR8yQ9hOs/edit#gid=0'
sheet = client.open_by_url(sheet_url)  # Открываем таблицу по URL
worksheet = sheet.get_worksheet(0)
data = worksheet.get_all_values()[1:]  # Получаем все значения из таблицы кроме названия таблиц


def error(exception):
    bot_token = environ.get('botToken')
    chat_id = environ.get('chat_id')
    message = str(exception)
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.get(url, params=params)


def clone_repository(repo_url, repo_path):
    try:
        repo = git.Repo.clone_from(repo_url, repo_path)
        print("Репозиторий успешно склонирован.")
        return True
    except git.exc.GitCommandError as e:
        try:
            repo = git.Repo(repo_path)
            repo.remotes.origin.pull()
            print("Репозиторий успешно обновлен.")
            return True
        except git.exc.GitCommandError as e:
            error(e)
    return False


def push(title, repo_path):
    file_path = f'{repo_path}/{title}'
    commit_message = 'update'
    try:
        subprocess.run(['git', 'add', file_path], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=repo_path, check=True)
        subprocess.run(['git', 'push'], cwd=repo_path, check=True)
    except subprocess.CalledProcessError as e:
        error(e)


def start(event_path):
    try:
        events = [file for file in os.listdir(event_path) if file.endswith(".md")]
        for i in events:
            numerate = 0
            with open(event_path + i, 'r', encoding="utf8") as file:
                your_price = ''
                partner_price = ''
                for line in file:
                    if 'Цена участия' in line:
                        list_line = line.split(' ')
                        for number in range(len(list_line)):
                            if any(num in list_line[number] for num in ['1', '2', '3', '4', '5', '6', '7', '8', '9']):
                                if 'партнёр' in list_line[number + 3]:
                                    partner_price = list_line[number]
                                else:
                                    your_price = line.split(' ')[number]
                        for k in data:
                            location = k[1]
                            price_table = k[2]
                            price_partner_table = k[3]
                            if i in location:
                                line = line.replace(your_price, price_table)
                                line = line.replace(partner_price, price_partner_table)
                                with open(event_path + i, 'r', encoding='utf-8') as file2:
                                    files_line = file2.readlines()
                                    files_line[numerate - 1] = line + '\n'
                                    with open(event_path + i, 'w', encoding='utf-8') as file3:
                                        file3.writelines(files_line)
                                push(i, event_path)
    except Exception as e:
        error(e)


if __name__ == '__main__':
    repository_url = environ.get("url_repo")
    repo_path = './project'
    if clone_repository(repository_url, repo_path):
        start(repo_path + '/upcoming-events/')
