# ProxyMan 🌐

A simple Proxy manager for Python

## Features

✨ Proxy Management:
- Load proxies from a file
- Support for IP-based and username-password authentication

🔄 Proxy Refresh:
- Automatically refresh the proxy list from a remote source
- Filter proxies based on location (US, UK, FR, or all)

🔀 Random Proxy:
- Retrieve a random proxy from the loaded list

## Installation

ProxyMan can be installed using `pip`:

```shell
pip install ProxyMan
```

## Usage


### Loading proxies from a file
```python
from ProxyMan import ProxyMan

# Load proxies from a file
pm = ProxyMan(file_path="proxies.txt")
```

### Configuring ProxyMan
```python
from ProxyMan import ProxyMan, Filter, AuthType

# Create a ProxyMan instance
webshare_api_key: str = "" # Optional (required to use the refresh feature)
scrape_filter: Filter = Filter.ALL # Optional (default: Filter.ALL) Filter proxies based on location
fail_count: int = 3 # Optional (default: 3) Remove a proxy from the list after it fails this many times
proxies_to_scrape: int = 3000 # Optional (default: 3000)
auth_type: AuthType = AuthType.IP # Optional (default: AuthType.IP) The type of authentication to use (IP or USER_PASS)

pm = ProxyMan(api_key=webshare_api_key, auth=auth_type, scrape_filter=scrape_filter, fail_count=fail_count, proxies_to_scrape=proxies_to_scrape)

# Get a random proxy
proxy: dict = pm.random()

print(proxy) # { "http": "http://0.0.0.0:8080"", "https": "http://0.0.0.0:8080" }
```

### Failing a proxy
```python
# If proxy fails somewhere in your code, call the fail method
# It will be removed from the list after it fails 3 times (or whatever you set fail_count to)

pm.increment_bad_proxies(proxy['http'])
```

### Refreshing the proxy list
```python
# Refresh the proxy list from the remote source
# This will overwrite the current list and update proxies.txt with the new list
await pm.update_proxies()
```

### Getting a random proxy
```python
# Get a random proxy from the list
proxy: dict = pm.random()

# Make a request 
requests.get("https://example.com", proxies=proxy)
```

