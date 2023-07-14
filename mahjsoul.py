import sys
import pathlib
import lz4.block
import json
from pypresence import Presence
import time

URL_MATCH = "https://mahjongsoul.game.yo-star.com"
CLIENT_ID = "1100743919324635218"
RPC_IMAGE = "ichihime-rage"
BROWSER_POLL_SECONDS = 30
DISCORD_POLL_SECONDS = 30

class Tab:
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def __str__(self):
        return f"{self.title} - {self.url}"

    def __repr__(self):
        return str(self)


def list_firefox_files():
    path = pathlib.Path.home().joinpath('.mozilla/firefox')
    return path.glob('*default*/sessionstore-backups/recovery.js*')


def decompress_firefox_json(path):
    data = path.read_bytes()
    raw = lz4.block.decompress(data[8:])  # Remove mozLz40\0 header
    return json.loads(raw)


def extract_tabs_from_json(json):
    buffer = []
    for window in json['windows']:
        for tab in window['tabs']:
            index = tab['index'] - 1
            url = tab['entries'][index]['url'].removesuffix("/")
            title = tab['entries'][index]['title']
            tab_struct = Tab(title, url)
            buffer.append(tab_struct)
    return buffer


def check_match(tab):
    return URL_MATCH == tab.url


def is_matching_tab_open():
    files = list(list_firefox_files())
    for f in files:
        json = decompress_firefox_json(f)
        matches = map(check_match, extract_tabs_from_json(json))
        if any(matches):
            return True

    return False


def set_rich_presence(rpc, start_time):
    rpc.update(large_image=RPC_IMAGE,
               details="Playing in browser", start=start_time)


def main():
    print("MahjongSoul RPC script init")
    rpc = Presence(CLIENT_ID)
    while True:
        try:
            rpc.connect()
        except ConnectionRefusedError:
            time.sleep(DISCORD_POLL_SECONDS)
            continue
        break
        
    print("Discord RPC connected")
    start_time = None
    while True:
        try:
            if is_matching_tab_open():
                start_time = int(
                    time.time()) if start_time is None else start_time
                set_rich_presence(rpc, start_time)
            else:
                rpc.clear()
                start_time = None
            time.sleep(BROWSER_POLL_SECONDS)
        except KeyboardInterrupt:
            break
    print("Closing RPC client...")
    rpc.close()
    print("Finished")


main()
