import os
import git
import concurrent.futures


def process_file(file_path):
    print("Processing:", file_path)


repo_path = './GitHub/Tasks'
repo = git.Repo(repo_path)
file_list = [os.path.join(dp, f) for dp, dn, filenames in os.walk(repo_path) for f in filenames]
max_threads = 4

with concurrent.futures.ProcessPoolExecutor(max_threads) as executor:
    executor.map(process_file, file_list)
