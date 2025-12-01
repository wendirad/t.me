#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
This module is created to export media message from  telegram, a freeware, cross-platform,
cloud-based instant messaging system (http://telegram.org).

@author: Wendirad Demelash
@website: https://wendirad.me
@github: https:://github.com/wendirad
@linked-in: https://linkedin.com/in/wendirad-demelash
@upwork: https://www.upwork.com/freelancers/~01d7c50a0d48f865a4

"""

import asyncio
import configparser
import glob
import logging
import sys
import time
import os

from telethon.errors.rpcerrorlist import FileReferenceExpiredError
from telethon import TelegramClient
from telethon.tl.types import (InputMessagesFilterChatPhotos,
                               InputMessagesFilterDocument,
                               InputMessagesFilterGif,
                               InputMessagesFilterMusic,
                               InputMessagesFilterPhotos,
                               InputMessagesFilterPhotoVideo,
                               InputMessagesFilterRoundVideo,
                               InputMessagesFilterRoundVoice,
                               InputMessagesFilterVideo,
                               InputMessagesFilterVoice)

logging.basicConfig(
    filename=".my_tg_export.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read("config.ini")


class TelegramMediaExport(TelegramClient):
    def __init__(
        self,
        limit=200,
        delay_time=10,
        export_prefix="export",
        media_type=None,
        *args,
        **kwargs,
    ):
        # setup before initializing the client
        self.setup(limit, delay_time, export_prefix, media_type)
        logger.info("Client created.")
        super().__init__(*args, **kwargs)

    def setup(self, limit, delay_time, export_prefix, media_type):
        self.limit = limit
        self.delay_time = delay_time
        self.last_offset = 0
        self.export_prefix = export_prefix
        self.__new_download = 0
        self.__existing_file = 0
        self.media_type = media_type

    def get_filter(self):
        media_type = (self.media_type or "all").lower()
        FILTERS = {
            "photos": InputMessagesFilterPhotos(),
            "chat_photos": InputMessagesFilterChatPhotos(),
            "document": InputMessagesFilterDocument(),
            "gif": InputMessagesFilterGif(),
            "music": InputMessagesFilterMusic(),
            "photo_video": InputMessagesFilterPhotoVideo(),
            "round_video": InputMessagesFilterRoundVideo(),
            "round_voice": InputMessagesFilterRoundVoice(),
            "video": InputMessagesFilterVideo(),
            "voice": InputMessagesFilterVoice(),
        }
        # Return None when 'all' or unknown to fetch everything
        return FILTERS.get(media_type, None)

    def __extract_filename(self, file_name):
        if file_name is not None and "." in file_name:
            extracted = file_name.split(".")
            return ".".join(extracted[:-1])
        return file_name or "mte"

    def __get_file_name(self, media):
        if getattr(media, "file", None) is not None:
            file_name = self.__extract_filename(media.file.name)
            return f"{file_name}_{media.id}"
        return f"mte_{media.id}"

    def _get_media_messages(self, messages):
        media_messages = []
        for message in messages:
            if getattr(message, "media", None) is not None:
                media_messages.append(message)
        return media_messages

    def _get_file_path(self, media_message, file_type, root_dir):
        file_name = self.__get_file_name(media_message)
        return f"{root_dir}/{file_type}/{file_name}"

    def __animate_loading(self, current, total):
        # progress callback: current bytes downloaded, total bytes
        percent = "{:.2%}".format(current / total) if total else "N/A"
        sys.stdout.write(
            "\r  Total exports: ["
            + str(self.__new_download + self.__existing_file)
            + "] | "
            + "New exports: ["
            + str(self.__new_download)
            + "] | "
            + "Current progress: "
            + percent
        )
        sys.stdout.flush()

    async def _download_media_messages(self, media_messages, root_dir):
        logger.info("Exporting media messages")
        for media_message in media_messages:
            file_type = (
                media_message.file.mime_type.split("/")[0]
                if getattr(media_message, "file", None) is not None and getattr(media_message.file, "mime_type", None)
                else "other"
            )
            # ensure directory exists
            target_dir = os.path.join(root_dir, file_type)
            os.makedirs(target_dir, exist_ok=True)

            path = self._get_file_path(media_message, file_type, root_dir)
            # check for existing files with any extension
            if glob.glob(f"{path}.*"):
                self.__existing_file += 1
                continue
            try:
                # download_media is a coroutine; await it to perform the download
                await media_message.download_media(
                    file=path, progress_callback=self.__animate_loading
                )
            except FileReferenceExpiredError:
                # skip expired file references
                logger.warning("FileReferenceExpired for message id %s", getattr(media_message, "id", "unknown"))
                continue
            except Exception as exc:
                logger.exception("Failed to download media for message %s: %s", getattr(media_message, "id", "unknown"), exc)
                continue
            self.__new_download += 1
            logger.info("Export Complete! %s", path)

    async def export(self, channel_name):
        logger.info('Exporting channel "%s" start.', channel_name)
        root_dir = f"{channel_name}_{self.export_prefix}"

        print("\nExporting channel", f"'{channel_name}'")
        # connect if not already connected; calling connect() when already connected is harmless
        await self.connect()
        while True:
            try:
                messages = await self.get_messages(
                    channel_name,
                    reverse=False,
                    limit=self.limit,
                    filter=self.get_filter(),
                    offset_id=self.last_offset,
                )

                media_messages = (
                    self._get_media_messages(messages)
                    if self.media_type is None
                    else messages
                )
                await self._download_media_messages(media_messages, root_dir)
                if messages:
                    self.last_offset = messages[-1].id
                else:
                    print("EXPORT COMPLETE")
                    break
                # Use non-blocking sleep so event loop isn't blocked
                await asyncio.sleep(self.delay_time)
            except Exception as error:
                print("ERROR: ", error)
                logger.exception("Export loop error: %s", error)


async def main(
    limit,
    delay_time,
    export_prefix,
    media_type,
    channel_name,
    session_name,
    api_id,
    api_hash,
):

    telegram_exporter = TelegramMediaExport(
        limit, delay_time, export_prefix, media_type, session_name, api_id, api_hash
    )
    await telegram_exporter.start()
    await telegram_exporter.export(channel_name)


if __name__ == "__main__":
    print(
        """
#     ___    ___                                                
#      | |\\/|__
#      |.|  |___
#
#  _____   _____  __               _____        ___  __ __ ____
#   |__|  |__/ _`|__) /\\|\\/|   |\\/|__|  \\/\\    |__\\_/__)  \\__)
#   |__|__|__\\__>|  \\/~~\\  |   |  |__|__/~~\\   |__/ \\  \\__/  \\
#
#
    """
    )
    logger.info("Program start!")
    session_name = config["DEFAULT"]["session_name"]
    api_id = config["ACCOUNT"]["api_id"]
    api_hash = config["ACCOUNT"]["api_hash"]
    channel_name = config["MAIN"]["channel_name"]
    limit = int(config["DEFAULT"]["limit"])
    delay_time = int(config["DEFAULT"]["delay_time"])
    export_prefix = config["DEFAULT"]["export_prefix"]
    media_type = config["DEFAULT"]["media_type"]
    logger.info("Configuration loaded.")

    try:
        asyncio.run(
            main(
                limit,
                delay_time,
                export_prefix,
                media_type,
                channel_name,
                session_name,
                api_id,
                api_hash,
            )
        )
    except KeyboardInterrupt:
        print("\n STOP EXPORTING")
