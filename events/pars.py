from os import environ
import os
from dotenvy import load_env, read_file
from github import Github, Auth
import git
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import subprocess
import pathlib
import sys
import concurrent.futures

load_env(read_file('.env'))
auth_git = Auth.Token(environ.get("GIT_TOKEN"))  # gitHub
gitHubAuth = Github(auth=auth_git)
json_key = './small-394913-470a0e673114.json'  # Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(json_key, scope)
client = gspread.authorize(creds)  # URL к таблице Google Sheets
sheet_url = 'https://docs.google.com/spreadsheets/d/1OIkPzOv0DgJDtJUS_7W9bQ4ome9GMCKoIcLR8yQ9hOs/edit#gid=0'
sheet = client.open_by_url(sheet_url)  # Открываем таблицу по URL
worksheet = sheet.get_worksheet(0)
data = worksheet.get_all_values()[1:]  # Получаем все значения из таблицы кроме названия таблиц


def error(exception):
    bot_token = environ.get('BOT_TOKEN')
    chat_id = environ.get('CHAT_ID')
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
        subprocess.run(['pwd'], stdout=sys.stdout, cwd=repo_path)
        subprocess.run(['git', 'commit', '-am', commit_message], cwd=repo_path, check=True)
        subprocess.run(['git', 'push'], cwd=repo_path, check=True)
    except subprocess.CalledProcessError as e:
        error(e)


def start(event):
    try:
        repo_patha = str(pathlib.Path(os.getcwd()).parent) + '/peredelanoconf'
        event_path = repo_patha + '/upcoming-events'
        full_path = event_path + '/'
        number_of_line = 0
        your_price, partner_price = '', ''
        with open(full_path + event, 'r', encoding="utf8") as file:
            for line in file.readlines():
                number_of_line += 1
                if 'Цена' in line:
                    split_line = line.split(' ')
                    for count in range(len(split_line)):
                        if any(num in split_line[count] for num in
                               ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']):
                            if 'партнёр' in line.lower():
                                partner_price = split_line[count]
                            else:
                                your_price = split_line[count]
                    for row in data:
                        location = row[1]
                        price_table = row[2]
                        price_partner_table = row[3]
                        if event in location:
                            if your_price != '':
                                line = line.replace(your_price, price_table)
                            if partner_price != '':
                                line = line.replace(partner_price, price_partner_table)
                            with open(full_path + event, 'r', encoding="utf8") as file2:
                                files_line = file2.readlines()
                                files_line[number_of_line - 1] = line + '\n'
                                with open(full_path + event, 'w', encoding="utf8") as file3:
                                    file3.writelines(files_line)
        push(event, event_path)
    except Exception as e:
        error(e)


def main(event_path):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(start, [file for file in os.listdir(event_path) if file.endswith(".md")])


if __name__ == '__main__':
    repository_url = environ.get("URL_REPO")
    repo_path = str(pathlib.Path(os.getcwd()).parent) + '/peredelanoconf'
    if clone_repository(repository_url, repo_path):
        main(repo_path + '/upcoming-events')
