import platform
import json
import requests
from typing import Literal
import os


# Global request Timeout Option in seconds, leaving it here for now but may make it into a setting in the future
TIMEOUT = 5

# TODO: Refactor to read from external file
VERSION = '0.1.0'
CLIENT = 'Jellyfin Transcoded Downloader'
CLIENTID = 'definitelynotaplaceholder'

# Use device name as Jellyfin device name
DEVICE = platform.node()

# Load authentication info from previous session(s)
try:
    with open('./data/auth.json', 'r', encoding='utf8') as authFile:
        auth = json.load(authFile)

except:
    # Load file failed: blank token and IP, start over
    serverIp: str = ''
    _token: str = ''

else:
    # Use the items present to authenticate
    if 'serverIp' in auth:
        serverIp = auth['serverIp']

    if 'token' in auth:
        _token = auth['token']


def loginUsername(server: str, username: str, password: str) -> Literal['Success', 'BadCredentials', 'UnknownError', 'InvalidUrl']:
    server = server.strip('/')
    if not server.startswith('http'):
        server = 'http://' + server

    try:
        res = requests.post(f'{server}/Users/AuthenticateByName', headers=buildHeader(), timeout=TIMEOUT, json={
                'Username': username,
                'Pw': password
            }
        )
    except requests.exceptions.ConnectTimeout:
        return 'UnknownError'
    except requests.exceptions.InvalidURL:
        return 'InvalidUrl'

    # print(res)
    match res.status_code:
        case 200:
            global serverIp, _token
            serverIp = server
            _token = res.json()['AccessToken']
            try:
                if not os.path.exists('./data'):
                    os.mkdir('./data')
                with open('./data/auth.json', 'w', encoding='utf8') as authFile:
                    body = json.dumps({
                            'serverIp': serverIp,
                            'token': _token
                    })
                    authFile.write(body)
                return 'Success'
            except:
                pass

        case 401:
            return 'BadCredentials'
        case 404:
            return 'InvalidUrl'
        case _:
            return 'UnknownError'


def buildHeader():
    headers = {
        "Authorization": f'MediaBrowser Client="{CLIENT}", Device="{DEVICE}", DeviceId="{CLIENTID}", Version="{VERSION}"'
    }
    if _token:
        headers["Authorization"] += f', Token="{_token}"'

    return headers


def validateCurrentSession():
    try:
        res = requests.get(f'{serverIp}/Users/Me', headers=buildHeader(), timeout=TIMEOUT)
        return res.status_code == 200
    except:
        return False


def get(endpoint: str, params: dict = None, rjson: dict = None) -> requests.models.Response:
    endpoint = endpoint.strip('/')
    return requests.get(f'{serverIp}/{endpoint}', params=params, json=rjson, headers=buildHeader(), timeout=TIMEOUT)


def post(endpoint: str, params: dict = None, rjson: dict = None) -> requests.models.Response:
    endpoint = endpoint.strip('/')
    return requests.post(f'{serverIp}/{endpoint}', params=params, json=rjson, headers=buildHeader(), timeout=TIMEOUT)

