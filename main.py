from downloader import Downloader

from colorama import init
import os

if __name__ == '__main__':
    init()  # initialize colorama

    if not os.path.exists('./pdm_data'):  # pdm stands for python-download-manager
        os.mkdir('./pdm_data')

    url = input("Enter file url: ")
    d = Downloader(url)
    chunks = input("Enter connection count (leave empty for 2): ")
    if chunks and chunks.isdigit() and int(chunks) <= 20:
        d.setChunks(int(chunks))
    d.download()
