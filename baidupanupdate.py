import time
import re
import csv
import urllib
import urllib3
import requests
from retry import retry

def url2id(url):
    return url.replace('https://pan.baidu.com/s/1', '')

@retry(tries=3, delay=1)
def get_bdstoken():
    url_base = 'https://pan.baidu.com/api/gettemplatevariable?'
    paras = {
        'clienttype': '0',
        'app_id'    : '250528',
        'web'       : '1',
        'fields'    : '["bdstoken"]',
    }
    url = url_base + urllib.parse.urlencode(paras) 
    response = session.get(url=url, headers=request_header,
            timeout=5, allow_redirects=True, verify=False)
    if response.json()['errno'] != 0:
        raise Exception('Cannot get Baidu bdstoken. Error code: ' \
            + str(response.json()['errno']))
    else:
        return response.json()['result']['bdstoken']

def check_exist_dir(dir, bdstoken):
    url_base = 'https://pan.baidu.com/api/list?'
    paras = {
        'dir'      : dir,
        'bdstoken' : bdstoken,
    }
    url = url_base + urllib.parse.urlencode(paras) 
    response = session.get(url=url, headers=request_header,
            timeout=15, allow_redirects=False, verify=False)
    if response.json()['errno'] != 0:
        return False
    else:
        return True


def create_dir(dir, bdstoken):
    if check_exist_dir(dir, bdstoken):
        return

    url_base = 'https://pan.baidu.com/api/create?'
    paras = {
        'a'        : 'commit',
        'bdstoken' : bdstoken,
    }
    url = url_base + urllib.parse.urlencode(paras) 
    post_data = {
        'path'       : '/' + dir,
        'isdir'      : '1',
        'block_list' : '[]',
    }
    response = session.post(url=url, headers=request_header,
            data=post_data, timeout=15, allow_redirects=False, verify=False)
    if response.json()['errno'] != 0:
        raise Exception('Failed in creating directory. Error code: ' \
            + str(response.json()['errno']))
    return

def get_link_request_header(link_id, pass_code, bdstoken):
    link_request_header = request_header
    if pass_code is None:
        return link_request_header
    url_base = 'https://pan.baidu.com/share/verify?'
    paras = {
        'surl'       : link_id,
        'bdstoken'   : bdstoken,
        't'          : str(int(round(time.time() * 1000))),
        'channel'    : 'chunlei',
        'web'        : '1',
        'clienttype' : '0',
    }
    url = url_base + urllib.parse.urlencode(paras) 
    post_data = {
        'pwd'       : pass_code,
        'vcode'     : '',
        'vcode_str' : '',
    }
    response = session.post(url=url, headers=request_header,
            data=post_data, timeout=10,
            allow_redirects=False, verify=False)
    if response.json()['errno'] != 0:
        raise Exception('Failed in checking link. Error code: '
                + str(response.json()['errno']))
    bdclnd = response.json()['randsk']
    if bool(re.search('BDCLND=', request_header['Cookie'], re.IGNORECASE)):
        link_request_header['Cookie'] = re.sub(r'BDCLND=(\S+);?',
                r'BDCLND=' + bdclnd + ';', link_request_header['Cookie'])
    else:
        link_request_header['Cookie'] += ';BDCLND=' + bdclnd
    return link_request_header

def get_link_ids(link_id, pass_code, bdstoken):
    link_request_header = get_link_request_header(link_id, pass_code, bdstoken)
    url = 'https://pan.baidu.com/s/1' + link_id
    response = session.get(url=url, headers=link_request_header,
            timeout=15, allow_redirects=True,
            verify=False).content.decode("utf-8")
    shareid = re.findall('"shareid":(\\d+?),"', response)[0]
    if shareid is None:
        raise Exception("Failed in getting shareid.")
    userid = re.findall('"share_uk":"(\\d+?)","', response)[0]
    if userid is None:
        raise Exception("Failed in getting user_id.")
    fsid_list = re.findall('"fs_id":(\\d+?),"', response)
    if not fsid_list:
        raise Exception("Failed in getting fs_id.")
    return shareid, userid, fsid_list

@retry(tries=3, delay=1)
def transfer_files(link_id, pass_code, dir, bdstoken):
    shareid, userid, fsid_list = get_link_ids(link_id, pass_code, bdstoken)
    create_dir(dir, bdstoken)

    url_base = 'https://pan.baidu.com/share/transfer?'
    paras = {
        'shareid'    : shareid,
        'from'       : userid,
        'ondup'      : 'overwrite',
        'bdstoken'   : bdstoken,
        'channel'    : 'chunlei',
        'web'        : '1',
        'clienttype' : '0',
    }
    url = url_base + urllib.parse.urlencode(paras) 
    post_data = {
        'fsidlist' : '[' + ','.join(i for i in fsid_list) + ']',
        'path'     : '/' + dir,
    }
    response = session.post(url=url, headers=request_header,
            data=post_data, timeout=15, allow_redirects=False, verify=False)

    if response.json()['errno'] != 0 and response.json()['errno'] != 4:
        raise Exception('Failed in transferring files. Error code: ' \
                + str(response.json()['errno']) )
    else:
        print(link_id + ' is saved to ' + dir + '.')
    return

# Main
request_header = {
    'Host': 'pan.baidu.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'navigate',
    'Referer': 'https://pan.baidu.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7,en-GB;q=0.6,ru;q=0.5',
}

urllib3.disable_warnings()
session = requests.session()
session.trust_env = False

with open('config.ini') as config_read:
    [cookie, user_agent] = config_read.readlines()
    request_header['Cookie'] = cookie.replace('\n','')
    request_header['User-Agent'] = user_agent.replace('\n','')

bdstoken = get_bdstoken()

with open('links.csv') as link_file:
    link_list = list(csv.reader(link_file))
    for [url, pass_code, dir] in link_list:
        try:
            id = url2id(url.strip())
            transfer_files(id, pass_code.strip(),
                    dir.strip(), bdstoken)
        except Exception as e:
            print("Error on URL: " + str(url.strip()))
            print("Error Message: \n\t" + str(e))
