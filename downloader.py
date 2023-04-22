import asyncio
import os
import time

import aiohttp.web
from aiohttp import ClientSession

import util


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
        self.status = Downloader.STATUS_NOT_STARTED
        self.start_time = -1

    def download(self):
        asyncio.run(self._download())
        self._clean_up_files()
        self._print_progress()
        print()  # go to new line

    def setChunks(self, chunks):
        self.chunks = chunks
        self.fetched_size = [0 for _ in range(chunks)]
        self.chunk_size = int(self.file_size / self.chunks)

    def _clean_up_files(self):
        if self.status == self.STATUS_NOT_STARTED:
            return
        elif self.status == self.STATUS_CANCELED:  # TODO: if  resumption implemented, change this!
            for i in range(self.chunks):
                f_i_name = f'_{i}_{self.file_name}'
                os.unlink(os.path.join(os.getcwd(), f_i_name))
        elif self.status == self.STATUS_FAILED:
            for i in range(self.chunks):
                f_i_name = f'_{i}_{self.file_name}'
                os.unlink(os.path.join(os.getcwd(), f_i_name))
        else:  # successful download
            with open(self.file_name, 'wb') as f:
                for i in range(self.chunks):
                    f_i_name = f'_{i}_{self.file_name}'
                    with open(f_i_name, 'rb') as f_i:
                        contents = f_i.read()
                        f.write(contents)
                    os.unlink(os.path.join(os.getcwd(), f_i_name))

    def _print_progress(self):
        end = time.time()
        time_passed = end - self.start_time
        download_speed = sum(self.fetched_size) / time_passed
        t = util.readable_file_size(download_speed, suffix="Bps")
        util.print_progress(self.chunks, self.file_size, self.chunk_size, self.fetched_size, extra_text=t)

    async def _download(self):
        self.status = Downloader.STATUS_PENDING

        try:

            async with ClientSession() as session:

                await self._fetch_header(session)

                self.start_time = time.time()

                fetchers = []
                for i in range(self.chunks):
                    start_i = i * int(self.file_size / self.chunks)
                    end_i = (i + 1) * int(self.file_size / self.chunks) - 1
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

    async def _fetch_header(self, session: ClientSession):
        async with session.head(self.url) as resp:
            self.headers = resp.headers
            self.file_size = util.getFileSize(self.headers)
            self.file_name = util.getFileName(self.headers, self.url)
            self.chunk_size = int(self.file_size / self.chunks)
            if "Accept-Ranges" in self.headers:
                if self.headers["Accept-Ranges"] != "bytes":
                    self.setChunks(1)

    async def _fetch_part(self, session: ClientSession, part_index, start, end):
        CHUNK_SIZE = 4096
        with open(f"_{part_index}_" + self.file_name, "wb") as f:
            headers = {"range": f"bytes={start}-{end}"}
            if self.chunks == 1:
                headers = {}
            async with session.get(self.url, headers=headers) as resp:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    BYTES_WRITTEN = f.write(chunk)
                    self.fetched_size[part_index] += BYTES_WRITTEN
                    self._print_progress()
