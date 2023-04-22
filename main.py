from downloader import Downloader

from colorama import init

if __name__ == '__main__':
    init()  # initialize colorama

    url = input("Enter file url: ")
    d = Downloader(url)
    chunks = input("Enter connection count (leave empty for 2): ")
    if chunks and chunks.isdigit():
        d.setChunks(int(chunks))
    print(f"Downloading file in {d.chunks} chunks ...")
    d.download()
