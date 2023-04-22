from downloader import Downloader

# https://dl.downloadly.ir/Files/Software/Neat_Download_Manager_1.1_macOS_Downloadly.ir.rar
# https://www.shahrekhabar.com/statics/svg/hot3.svg
# https://dl3.downloadly.ir/Files/Software/Java_SE_Development_Kit_20.0.1_macOS_x64_Downloadly.ir.rar
import ssl

from colorama import init

if __name__ == '__main__':
    init()

    url = input("Enter file url: ")
    d = Downloader(url)
    chunks = input("Enter connection count (leave empty for 2): ")
    if chunks and chunks.isdigit():
        d.setChunks(int(chunks))
    print(f"Downloading file in {d.chunks} chunks ...")
    d.download()
