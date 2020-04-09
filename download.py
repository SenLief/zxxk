# coding=utf-8

import os
import json
import argparse
import re

from requests import Session
from requests_html import HTML

from zxxkdb import db, select_db, create_or_update_info, create_or_update_album

username = os.getenv('UN')
password = os.getenv('PASSWORD')


class ZXXK:
    '''
    实例化
    '''
    def __init__(self):
        '''
        初始化Session
        '''
        self.session = Session()
        self.headers_phone = {
           'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
           'Sec-Fetch-Dest': 'document',
           'Sec-Fetch-Mode': 'navigate',
           'Sec-Fetch-Site': 'none',
           'Sec-Fetch-User': '?1',
           'Upgrade-Insecure-Requests': '1',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        }
        self.headers_pc = {
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4090.0 Safari/537.36 Edg/83.0.467.0'
        }


    def login(self):
        '''
        登录获取session
        '''
        self.session.headers.update(self.headers_phone)
        url_login = 'https://sso.zxxk.com/login'

        # 获取登录所需的lt和execution
        r = self.session.get(url_login)
        html = HTML(html=r.text)
        lt = html.find('input')[3].attrs['value']
        execution = html.find('input')[4].attrs['value']

        # 构造登录数据
        data = {
            'username': username,
            'password': password,
            'lt': lt,
            'execution': execution,
            '_eventId': 'submit',
            'rememberMe': 'true'
        }
        resp = self.session.post(url_login, data=data)
        # print(resp.text)
        
        if '系统检测到该账号近期登录异常' not in resp.text:
            # 获取下载Cookies
            url_auth = 'https://sso.zxxk.com/'     
            params = {
            'service': 'https://auth.zxxk.com/callback'
            }
            self.session.get(url_auth, params=params)

            #保存cookies
            with open('auth.json', 'w+') as f:
                json.dump(self.session.cookies.get_dict(), f)
            
            return self.session
        else:
            print('需要验证账号！')
            raise
            

    
    def auth(self):
        '''
        下载前验证本地cookie是否可用，可用则使用本地cookie，否则重新登录。目前验证有些问题
        '''
        # 读取本地cookies
        with open('auth.json', 'r+') as f:
            cookies = json.load(f)
            self.session.cookies.update(cookies)
        
        # 利用后台获取，有些小问题，这个接口判断的有时候有延迟。
        url_auth = 'http://m.zxxk.com/user/Mail/Count'
        self.session.headers.update({'X-Requested-With': 'XMLHttpRequest'})
        resp = self.session.post(url_auth)
        code = resp.json()['Code']
        if code == 0:
            # print('使用cookie登录')
            return self.session
        else:
            # print('重新登录')
            self.session.headers.update({'X-Requested-With': None})
            self.session = self.login()
            return self.session
    

    def get_info(self, url):
        '''
        获取下载文件信息
        '''

        id = re.search('\w{8}', url).group(0)
        url_info = 'http://m.zxxk.com/api/v1/soft/info/'
        resp = self.session.get(url_info + str(id))
        resp.encoding = 'utf-8'
        info = resp.json()
        return info
   

    def parse_id(self, url):
        '''
        解析文档链接获取链接内所有文档的info_id

        Args:
            url: 文档链接，可以是soft/zj/tj链接

        Return:
            info_ids: 链接内所有文档的id列表， Type: list
        '''

        info_ids = []
        if 'soft' in url:
            id = re.search('\w{8}', url).group(0)
            info_ids.append(id)
        else:
            resp = self.session.get(url)
            html_id = HTML(html=resp.text)
            ids = html_id.find('.tree-node')
            for id in ids[1:]:
                info_ids.append(id.attrs['data-softid'])
        return info_ids


    def download_urls(self, url):
        '''
        获取多个文档的直链，没有处理验证码信息。

        Args:
            url: 文档的下载链接，可以是soft/zj/tj链接。
        
        Return:
            donwload_url: 下载的直链, type: json
        '''
        # 专辑id
        if 'soft' not in url:
            albumid = re.search('\w{6}', url).group(0)
        else:
            # 获取下载文件信息
            info = self.get_info(url)
            channelid = info['channelId']
            displayprice = info['displayPrice'] #str
            filetype = info['fileType']
            intro = info['intro']
            softid = info['softId']
            softname = info['softName']
            softsize = info['softSize']
            updatetime = info['updateTime']

        # 获取下载链接
        info_ids = self.parse_id(url)
        dict_id = {}
        if len(info_ids) > 10:
            n = round(len(info_ids)/10)
            for index, i in enumerate(range(0, len(info_ids), n)):
                info_id = ','.join(info_ids[i: i+n])
                url_d = self.download_url(info_id)
                dict_id['Url'+ str(index)] = url_d
            create_or_update_album(albumid=albumid, softids=info_ids, downloadurls=dict_id)
        elif len(info_ids) > 1 and len(info_ids) <= 10:
            url_d = self.download_url(info_ids)
            dict_id['Url'] = url_d
            create_or_update_album(albumid=albumid, softids=info_ids, downloadurls=dict_id)
        else:
            info_id = ','.join(info_ids)
            url_d = self.download_url(info_id)
            dict_id['Url'] = url_d
            # 保存到数据库
            create_or_update(softid=softid, softname=softname, channelid=channelid, downloadurls=dict_id, displayprice=displayprice, filetype=filetype, intro=intro, softsize=softsize, updatetime=updatetime)

        return json.dumps(dict_id)


    def download_url(self, info_id):
        '''
        下载单个url地址专用, 没有处理验证码信息。

        Args:
            soft_url: 下载的链接, type: str, eg: http://www.zxxk.com/soft/13073171.html
        
        Return:
            下载直链， type: str
        '''
        session = self.auth()
        # 提取user key
        url_key = r'http://resourcedownload.zxxk.com/download/getscripts?&userid=0&iscart=0&source=0&ext=&pageType=2&isGaoKao=false'
        params_key = {'softids': info_id}
        r_key = session.get(url_key, params=params_key)
        
        # re提取key，为第三个
        user_key = re.findall('key=\w{32}', r_key.text)[2].split('=')[1]
        
        # 获取 userid
        user_id = r_key.cookies['ASP.NET_SessionId']
        
        # 验证提取下载链接
        params_ver = {
            'user_id': user_id,
            'key': user_key,
            'infoIds': info_id
        }
        url_ver = 'http://resourcedownload.zxxk.com/Download/Verification?resType=0&source=0&isGaoKao=False&pagetype=2'
        r_ver = session.get(url_ver, params=params_ver)
        r_ver.encoding='utf-8'
        # print(r_ver.text)
        html_ver = HTML(html=r_ver.text)
        return html_ver.find('.suc')[0].text
    

    def get_url(self, url):
        '''
        获取数据库中的url下载链接
        '''
        try:
            info_id = re.search('\w{8}', url).group(0)
            info = select_db(info_id)
        except:
            info_id = re.search('\w{6}', url).group(0)
            info = select_db(info_id)
        return json.dumps(info.downloadurls)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='获取学科网下载直链，需要账号支持！')
    parser.add_argument('--info', '-i', action='store_true', help="文档信息")
    parser.add_argument('--login', action='store_true', help='登录')
    parser.add_argument('--durl', action='store_true', help='获取数据库中的下载链接！')
    parser.add_argument('url', help="文档地址")
    args = parser.parse_args()

    zxxk = ZXXK()
    if args.durl:
        print(zxxk.get_url(args.url))
    elif args.info:
        print(zxxk.get_info(args.url))
    elif args.login:
        print(zxxk.login())   
    else:
        print(zxxk.download_urls(args.url))




    
