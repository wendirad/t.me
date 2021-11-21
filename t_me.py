#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
This module is created to export media message from  telegram, a freeware, cross-platform,
cloud-based instant messaging system (http://telegram.org).

@author: Wendirad Demelash
@website: https://wendirad.me
@telegram: https://t.me/abnos_yemikael
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

from telethon.errors.rpcerrorlist import FileReferenceExpiredError
from telethon.sync import TelegramClient
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
        media_type = self.media_type or "all"
        FILTERS = {
            "photos": InputMessagesFilterPhotos,
            "chat_photos": InputMessagesFilterChatPhotos,
            "document": InputMessagesFilterDocument,
            "gif": InputMessagesFilterGif,
            "music": InputMessagesFilterMusic,
            "photo_video": InputMessagesFilterPhotoVideo,
            "round_video": InputMessagesFilterRoundVideo,
            "round_voice": InputMessagesFilterRoundVoice,
            "video": InputMessagesFilterVideo,
            "voice": InputMessagesFilterVoice,
        }
        return FILTERS.get(media_type.lower(), None)

    def __extract_filename(self, file_name):
        if not file_name is None and "." in file_name:
            extracted = file_name.split(".")
            return ".".join(extracted[:-1])
        return file_name or "mte"

    def __get_file_name(self, media):
        if media.file is not None:
            file_name = self.__extract_filename(media.file.name)
            return f"{file_name}_{media.id}"
        return f"mte_{media.id}"

    def _get_media_messages(self, messages):
        media_messages = []
        for message in messages:
            if message.media is not None:
                media_messages.append(message)
        return media_messages

    def _get_file_path(self, media_message, file_type, root_dir):
        file_name = self.__get_file_name(media_message)
        return f"{root_dir}/{file_type}/{file_name}"

    def __animate_loading(self, current, total):
        percent = "{:.2%}".format(current / total)
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
                if media_message.file is not None
                else "other"
            )
            path = self._get_file_path(media_message, file_type, root_dir)
            if glob.glob(f"{path}.*"):
                self.__existing_file += 1
                continue
            try:
                task = self.loop.create_task(
                    media_message.download_media(
                        file=path, progress_callback=self.__animate_loading
                    )
                )
            except FileReferenceExpiredError:
                continue
            self.__new_download += 1
            logger.info("Export Complete! %s", path)
            await task

    async def export(self, channel_name):
        logger.info('Exporting channel "%s" start.', channel_name)
        root_dir = f"{channel_name}_{self.export_prefix}"

        print("\nExporting channel", f"'{channel_name}'")
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
                time.sleep(self.delay_time)
            except Exception as error:
                print("ERROR: ", error)


async def main(
    limit,
    delay_time,
    export_prefix,
    media_type,
    channel_name,
    sesison_name,
    api_id,
    api_hash,
):

    telegram_exporter = TelegramMediaExport(
        limit, delay_time, export_prefix, media_type, sesison_name, api_id, api_hash
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
    sesison_name = config["DEFAULT"]["session_name"]
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
                sesison_name,
                api_id,
                api_hash,
            )
        )
    except KeyboardInterrupt:
        print("\n STOP EXPORTING")
