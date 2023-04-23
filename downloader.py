import asyncio
import os
import time

from aiohttp import ClientSession

import util
import json


class Downloader:
    STATUS_NOT_STARTED = 0
    STATUS_PENDING = 1
    STATUS_FAILED = 2
    STATUS_CANCELED = 4

    def __init__(self, url, chunks=2):
        self.url = url
        self.file_size = -1
        self.file_name = ""
        self.headers = None
        self.chunks = chunks
        self.chunk_size = -1
        self.fetched_size = [0 for _ in range(chunks)]
        self.status = self.STATUS_NOT_STARTED
        self.tagged_time = -1
        self.tagged_size = 0
        self.download_speed = 0
        self.chunk_starts = []

    def download(self):
        asyncio.run(self._download())
        self._clean_up_files()
        self._print_progress()
        print()  # go to new line

    async def _download(self):

        self.status = Downloader.STATUS_PENDING

        try:
            async with ClientSession() as session:

                await self._fetch_header(session)

                self._load_progress()

                print(f"file {self.file_name} \nwill be downloaded in {self.chunks} chunks.")

                self.tagged_time = time.time()

                fetchers = []

                if self.chunks == 1:
                    fetchers.append(asyncio.create_task(self._fetch_whole(session)))
                else:
                    for i in range(self.chunks):
                        start_i = self.chunk_starts[i] + self.fetched_size[i]
                        end_i = self.chunk_starts[i] + self.chunk_size - 1
                        if end_i > self.file_size:
                            end_i = self.file_size
                        fetchers.append(asyncio.create_task(self._fetch_part(session, i, start_i, end_i)))

                # run tasks concurrently:

                pending = fetchers
                while pending:
                    done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_EXCEPTION)
                    for done_task in done:
                        if done_task.exception():
                            self.status = Downloader.STATUS_FAILED
                            pending = []

                for task in pending:
                    task.cancel()
        except asyncio.CancelledError:
            self.status = self.STATUS_CANCELED

    async def _fetch_part(self, session: ClientSession, part_index, start, end):
        CHUNK_SIZE = 4096
        with open(self._get_chunk_file_path(part_index), "ab") as f:
            headers = {"range": f"bytes={start}-{end}"}
            if self.chunks == 1:
                headers = {}
            async with session.get(self.url, headers=headers) as resp:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    BYTES_WRITTEN = f.write(chunk)
                    self.fetched_size[part_index] += BYTES_WRITTEN
                    self._print_progress()
                    self._save_progress()

    async def _fetch_header(self, session: ClientSession):
        async with session.get(self.url) as resp:
            self.headers = resp.headers
            self.file_size = util.getFileSize(self.headers)
            self.file_name = util.getFileName(self.headers, self.url)
            self.chunk_size = int(self.file_size / self.chunks)
            if self.file_size <= 0:
                self.setChunks(1)
            if ("Accept-Ranges" not in self.headers) or (self.headers["Accept-Ranges"] != "bytes"):
                self.setChunks(1)

    async def _fetch_whole(self, session: ClientSession):
        """this is used when the header doesn't have a file size property"""
        CHUNK_SIZE = 4096
        with open(self._get_chunk_file_path(0), "wb") as f:
            async with session.get(self.url) as resp:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    BYTES_WRITTEN = f.write(chunk)
                    self.fetched_size[0] += BYTES_WRITTEN
                    self._print_progress()

    def _clean_up_files(self):

        if self.status == self.STATUS_NOT_STARTED:
            return

        elif self.status == self.STATUS_CANCELED:
            pass  # do not delete parts
        elif self.status == self.STATUS_FAILED:
            pass  # do not delete downloaded parts
        else:  # successful download
            with open(self._get_main_file_path(), 'wb') as f:
                for i in range(self.chunks):
                    with open(self._get_chunk_file_path(i), 'rb') as f_i:
                        contents = f_i.read()
                        f.write(contents)
                    os.unlink(self._get_chunk_file_path(i))  # delete it, no longer needed
            if os.path.exists(self._get_progress_file_path()):
                os.unlink(self._get_progress_file_path())  # delete it, no longer needed

    def setChunks(self, chunks):
        self.chunks = chunks
        self.fetched_size = [0 for _ in range(chunks)]
        self.chunk_size = int(self.file_size / self.chunks)

    def _save_progress(self):
        with open(self._get_progress_file_path(), 'w') as f:
            d = {"chunk_starts": self.chunk_starts,
                 "fetched_size": self.fetched_size,
                 "chunks": self.chunks}
            json.dump(d, f)

    def _load_progress(self):
        if os.path.exists(self._get_progress_file_path()):
            with open(self._get_progress_file_path(), 'r') as f:
                d = json.load(f)
                self.chunk_starts = d["chunk_starts"]
                self.fetched_size = d["fetched_size"]
                self.chunks = d["chunks"]
                self.chunk_size = int(self.file_size / self.chunks)
        else:
            self.chunk_starts = [i * int(self.file_size / self.chunks) for i in range(self.chunks)]
            self.fetched_size = [0 for _ in range(self.chunks)]

    def _get_project_data_directory(self):
        return os.path.join(os.getcwd(), 'pdm_data')

    def _get_main_file_path(self):
        return os.path.join(os.getcwd(), self.file_name)

    def _get_progress_file_path(self):
        return os.path.join(self._get_project_data_directory(), self.file_name + '_progress.json')

    def _get_chunk_file_path(self, chunk_index=0):
        return os.path.join(self._get_project_data_directory(), f'_{chunk_index}_{self.file_name}')

    def _print_progress(self):
        end = time.time()
        time_passed = end - self.tagged_time

        total_downloaded_size = sum(self.fetched_size)
        if time_passed >= 1.0:
            amount_downloaded = total_downloaded_size - self.tagged_size
            self.download_speed = amount_downloaded / time_passed
            self.tagged_size = total_downloaded_size
            self.tagged_time = end

        size_text = "?"
        if self.file_size > 0:
            size_text = f"{util.readable_file_size(self.file_size, justify_left=True)}"
        t = f'{util.readable_file_size(total_downloaded_size, justify_left=False)}/{size_text}@' \
            f'{util.readable_file_size(self.download_speed, suffix="Bps", justify_left=True)}'
        util.print_progress(self.chunks, self.file_size, self.chunk_size, self.fetched_size, extra_text=t)
