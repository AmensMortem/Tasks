import os
import git
import concurrent.futures


def process_file(file_path):
    print("Processing:", file_path)


script_dir = os.path.dirname(os.path.abspath(__file__))
repo_path = os.path.join(script_dir, '')
repo = git.Repo(repo_path)
file_list = [os.path.join(dp, f) for dp, dn, filenames in os.walk(repo_path) for f in filenames]


def main():
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(process_file, file_list)


if __name__ == '__main__':
    main()
