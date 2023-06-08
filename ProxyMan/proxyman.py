import enum
import math
import os
import asyncio
import aiohttp
import time
from random import choice


class Filter(enum.Enum):
    """
    Filter enum for the proxy manager
    """
    US = "US"
    FR = "FR"
    UK = "UK"
    ALL = "ALL"


class AuthType(enum.Enum):
    IP = "ip"
    USERNAME_PASSWORD = "username:password"


class ProxyMan:
    def __init__(self, api_key: str = None, proxies_to_scrape: int = 3000, auth=AuthType.IP, file_path="../proxies.txt", fail_count=3, scrape_filter=Filter.ALL):
        self.api_key = api_key
        self.proxies_to_scrape = proxies_to_scrape
        self.parsed_proxies = []
        self.bad_proxies = []
        self.file_path = file_path
        self.proxies_to_ping = set()
        self.auth = auth
        self.fail_count = fail_count
        self.scrape_filter = scrape_filter

        self.__setup()

    def __setup(self):
        # Prepare proxies
        try:
            with open(self.file_path, "r") as proxy_file:
                proxies = proxy_file.readlines()
        except FileNotFoundError:
            main_dir = os.path.dirname(os.path.realpath(__file__))
            main_dir = os.path.dirname(main_dir)
            if not main_dir.endswith("/"):
                main_dir = main_dir + "/"

            with open(main_dir + self.file_path) as proxy_file:
                proxies = proxy_file.readlines()

        if len(proxies) == 0:
            print(">> Proxy file is empty. Please add proxies to the file")
            exit(1)

        if self.auth == AuthType.USERNAME_PASSWORD:
            for proxy in proxies:
                """
                Prepare proxies for requests for auth username-pass
                """
                formatted = proxy.strip().split(":")
                ip, port, username, password = formatted[:4]
                self.parsed_proxies.append(f"http://{username}:{password}@{ip}:{port}")

        elif self.auth == AuthType.IP:
            for proxy in proxies:
                """
                Prepare proxies for requests
                """
                formatted = proxy.strip().split(":")
                ip, port = formatted[:2]
                self.parsed_proxies.append(f"http://{ip}:{port}")

    def increment_bad_proxies(self, proxy):
        """
        Increments bad proxies. If a proxy is appended 3 times, remove it from self.parsed_proxies.
        """
        if proxy.startswith("http://") or proxy.startswith("https://"):
            proxy = proxy.split("://")[1]

        self.bad_proxies.append(proxy)

        if self.bad_proxies.count(proxy) == self.fail_count:
            if proxy in self.parsed_proxies:
                self.parsed_proxies.remove(proxy)

            if proxy in self.bad_proxies:
                self.bad_proxies.remove(proxy)

            with open(self.file_path, "r") as f:
                lines = f.readlines()

            with open(self.file_path, "w") as f:
                for line in lines:
                    if line.strip("\n") != proxy:
                        f.write(line)

            if proxy not in self.proxies_to_ping:
                self.proxies_to_ping.add(proxy)
                with open("removed_proxies.txt", "a") as file_removals:
                    file_removals.write(proxy + "\n")

    async def _get_proxies(self, page: int):
        if self.api_key is None:
            raise Exception("API Key is not set. Please set it before calling this method.")

        headers = {"Authorization": self.api_key}
        proxies = []

        url = f"https://proxy.webshare.io/api/proxy/list/?page={page}"

        if self.scrape_filter == Filter.US:
            url += "&country_code=US"
        elif self.scrape_filter == Filter.UK:
            url += "&country_code=UK"
        elif self.scrape_filter == Filter.FR:
            url += "&country_code=FR"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200 and 'json' in resp.headers['Content-Type']:
                    data = await resp.json()
                    if 'results' in data:
                        results = data['results']
                        for result in results:
                            valid = result['valid']
                            if not valid:
                                continue

                            proxy_ip = result['proxy_address']
                            ports = result['ports']['http']
                            proxies.append(f"{proxy_ip}:{ports}")
                else:
                    print(f"Error on page {page}: Response={resp.status}")

        return proxies

    async def update_proxies(self):
        time_now = time.time()
        request_count = math.ceil(self.proxies_to_scrape / 250) # 250 proxies per page
        tasks = []
        print(f">> [PROXYMAN] Refreshing proxies... (This may take a while)")
        for i in range(1, int(request_count)):
            tasks.append(asyncio.create_task(self._get_proxies(i)))

        all_proxies = await asyncio.gather(*tasks)
        proxies = [item for sublist in all_proxies for item in sublist]

        proxies = list(set(proxies))

        if len(proxies) == 0:
            print(">> [PROXYMAN] No proxies found. Please try again later")
            return

        print(f">> [PROXYMAN] Found {len(proxies)} proxies")

        with open("proxies.txt", "w") as f:
            f.write("\n".join(proxies))

        time_then = time.time()

        self.parsed_proxies = proxies
        self.bad_proxies = []

        print(f">> [PROXYMAN] Refreshed {len(proxies)} proxies in {round(time_then - time_now, 2)} seconds.")

    def random(self):
        """
        Returns a random proxy.
        """
        if len(self.parsed_proxies) == 0:
            print(">> Proxy file is empty. Please add proxies to the file")
            exit(1)

        rn = choice(self.parsed_proxies)
        proxy = {
            "http": rn,
            "https": rn
        }
        return proxy


async def test_update():
    pm = ProxyMan(auth=AuthType.IP, file_path="proxies.txt", fail_count=3, scrape_filter=Filter.US)
    await pm.update_proxies()


if __name__ == "__main__":
    # Testing
    asyncio.run(test_update())