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
table = {'Location': 0, 'Github': 1, 'Price': 2, 'Partner price': 3, 'Discount': 4, 'Date': 5}


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


def rewrite(path, number_of_line, delete, line):
    try:
        with open(path, 'r', encoding="utf8") as file_r:
            if delete:
                lines = file_r.readlines()
                del lines[number_of_line]
                del lines[number_of_line - 1]
                with open(path, 'w', encoding="utf8") as file:
                    file.writelines(lines)
            elif delete is None:
                lines = file_r.readlines()
                lines.insert(number_of_line, line + '\n')
                lines.insert(number_of_line + 1, '\n')
                with open(path, 'w', encoding="utf8") as file:
                    file.writelines(lines)
            else:
                lines = file_r.readlines()
                lines[number_of_line] = line
                with open(path, 'w', encoding="utf8") as file_w:
                    file_w.writelines(lines)
    except Exception as e:
        error(e)


def add_details(event):
    try:
        repo_patha = str(pathlib.Path(os.getcwd()).parent) + '/peredelanoconf'
        event_path = repo_patha + '/upcoming-events'
        full_path = event_path + '/'
        number_of_line = -1
        for row in data:
            location = row[table['Github']]
            if event in location:
                with open(full_path + event, 'r', encoding="utf8") as file:
                    for line in file.readlines():
                        number_of_line += 1
                        if 'Цена' in line or 'скидка' in line:
                            if 'участия' in line:
                                with open(full_path + event, 'r', encoding="utf8") as read:
                                    read_list = read.readlines()
                                    if 'скидка' in read_list[number_of_line + 2]:
                                        if 'партнёр' not in read_list[number_of_line + 4]:
                                            add_line_partner = 'Цена для вашего партнёра 0$'
                                            rewrite(full_path + event, number_of_line + 4, None, add_line_partner)
                                    elif 'партнёр' in read_list[number_of_line + 2]:
                                        add_line_discount = 'Для тех, кто уже был хотя бы на одной из наших конф, ' \
                                                            'до восьмого августа действует скидка: билет будет стоить 0$'
                                        rewrite(full_path + event, number_of_line + 2, None, add_line_discount)
                                    elif ('партнёр' not in read_list[number_of_line + 4] or 'партнёр' not in read_list[
                                        number_of_line + 2]) and \
                                            'скидка' not in read_list[number_of_line + 2]:
                                        add_line_partner = 'Цена для вашего партнёра 0$'
                                        add_line_discount = 'Для тех, кто уже был хотя бы на одной из наших конф, ' \
                                                            'до восьмого августа действует скидка: билет будет стоить 0$'
                                        rewrite(full_path + event, number_of_line + 2, None, add_line_discount)
                                        rewrite(full_path + event, number_of_line + 4, None, add_line_partner)
    except Exception as e:
        error(e)


def start(event):
    try:
        repo_patha = str(pathlib.Path(os.getcwd()).parent) + '/peredelanoconf'
        event_path = repo_patha + '/upcoming-events'
        full_path = event_path + '/'
        number_of_line = -1
        for row in data:
            location = row[table['Github']]
            price_table = row[table['Price']]
            price_partner_table = row[table['Partner price']]
            price_discount_table = row[table['Discount']]
            main_line_price = 0
            if event in location:
                with open(full_path + event, 'r', encoding="utf8") as file:
                    for line in file.readlines():
                        number_of_line += 1
                        split_line = line.split(' ')
                        if 'Цена' in line or 'скидка' in line:
                            for count in range(len(split_line)):
                                if any(num in split_line[count] for num in
                                       ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']):
                                    if 'партнёр' in line.lower():
                                        if price_partner_table == 'None':
                                            rewrite(full_path + event, number_of_line, True, line)
                                        else:
                                            if price_discount_table == 'None' and number_of_line == main_line_price + 2:
                                                partner_price = split_line[count][:-1]
                                                line = line.replace(partner_price, price_partner_table)
                                                rewrite(full_path + event, main_line_price + 2, False, line)
                                            else:
                                                partner_price = split_line[count][:-1]
                                                line = line.replace(partner_price, price_partner_table)
                                                rewrite(full_path + event, number_of_line, False, line)
                                    elif 'скидка' in line.lower():
                                        if price_discount_table == 'None':
                                            rewrite(full_path + event, number_of_line, True, line)
                                            number_of_line -= 2
                                        else:
                                            discount_price = split_line[count][:-1]
                                            line = line.replace(discount_price, price_discount_table)
                                            rewrite(full_path + event, number_of_line, False, line)
                                    elif 'участия' in line.lower():
                                        main_line_price += number_of_line
                                        your_price = split_line[count][:-1]
                                        line = line.replace(your_price, price_table)
                                        rewrite(full_path + event, number_of_line, False, line)
        push(event, event_path)
    except Exception as e:
        error(e)


def main(event_path):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(add_details, [file for file in os.listdir(event_path) if file.endswith(".md")])
        executor.map(start, [file for file in os.listdir(event_path) if file.endswith(".md")])


if __name__ == '__main__':
    repository_url = environ.get("URL_REPO")
    repo_path = str(pathlib.Path(os.getcwd()).parent) + '/peredelanoconf'
    if clone_repository(repository_url, repo_path):
        main(repo_path + '/upcoming-events')
