import requests
import json
import re
import os
from urllib.parse import quote
from urllib.parse import urlparse


TARGET_DIR = './download'


request_header = {
    'cookie': 'cna=gzdTFQ/swnUCAXwOjn0+77gz; hng=CN%7Czh-CN%7CCNY%7C156; lid=%E5%85%89%E5%A4%B4%E4%BE%A0fan; enc=f3IeAl5tlxZr1djaoOK2TE0SawBbKlRA5SLIQWozacKrmQWdmlBofj1QS1i%2B04kNo48PJyqUYEbdIkkzBJ%2Fttw%3D%3D; XSRF-TOKEN=ca3d58b5-9f29-4f37-81ee-02222b2c60a7; t=b852dc2dcf1a866534cb41473ec07610; tracknick=%5Cu5149%5Cu5934%5Cu4FA0fan; _tb_token_=5efe33de44e9b; cookie2=12734c46c9e2e14af6deb8b063c4b0db; isg=BJmZtQwoIJrJEvwOA5mWwlluqIWzjoy9A8HX4LtOFUA_wrlUA3adqAfUxMYRwSUQ',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9', 
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36', 
    'accept': 'application/json, text/plain, */*', 
    'referer': 'https://developer.alios.cn/?spm=a211jy.11095034.2932363122.19.4df92487CLVYZ2',
    'authority': 'developer.alios.cn',
    'x-requested-with': 'XMLHttpRequest',
}


def downloadMD(child):
    gitFilePath = child['gitFilePath']
    print("Downloading md " + gitFilePath)
    url = 'https://developer.alios.cn/content/get_md.do?bypath=1&version=0&path=' + quote(gitFilePath)
    resp = requests.get(url = url, headers = request_header)
    content = json.loads(resp.text)['data']['content']
    newContent = ''
    for line in content.split('\n'):
        line = line.replace(' &quot;&quot;)', ')') # md中语法错误特殊处理
        line = line.replace('&quot;', '"')
        wirtePath = os.path.join(TARGET_DIR, gitFilePath)

        # Alios中的错误md语法
        errorSyntaxs = re.findall(r'\[.*\]: (.+png|.+jpg|.+gif|.+zip)', line)
        for errorSyntax in errorSyntaxs:
            if errorSyntax.endswith('.zip'):
                line += '\n [%s](%s)\n' % (errorSyntax, errorSyntax)
            else:
                line += '\n ![%s](%s)\n' % (errorSyntax, errorSyntax)
        
        # 下载附件和图片
        attatchFileUrls = re.findall(r'\[.*\]\((.+png|.+jpg|.+gif|.+zip)\)', line)
        for attatchFile in attatchFileUrls:
            attatchFile = attatchFile.strip()
            if downloadMDAttatchFile(attatchFile, os.path.dirname(wirtePath)):
                parse = urlparse(attatchFile)
                line = line.replace(parse.scheme + "://" + parse.netloc + "/", "")
        
        # 处理相对链接
        if 'md/developercenter/' in line:
            slashCount = len(re.findall('/', gitFilePath))
            preDot = ''
            for _ in range(0, slashCount):
                preDot += '../'
            line = line.replace('md/developercenter/', preDot + 'md/developercenter/').replace('|local', '')

        newContent = newContent + line + "\n"
        # save md file
        f = open(file = wirtePath, mode = 'w', encoding = 'utf-8')
        f.write(newContent)
        f.close()

def downloadMDAttatchFile(url, dir):
    print("Downloading attatch file:" + url)
    try:
        if url.endswith('png'):
            resp = requests.get(url = url, headers = request_header, timeout = 2)
        else:
            resp = requests.get(url = url, headers = request_header)
    except Exception as e:
        print("Error download:" + url)
        print(e)
        return False
    
    parse = urlparse(url)
    outFile = os.path.join(dir, parse.path[1:])
    if not os.path.exists(os.path.dirname(outFile)):
        os.makedirs(os.path.dirname(outFile))
    f = open(file = outFile, mode = 'wb')
    f.write(resp.content)
    f.close()
    return True
    

def downloadHtml(child):
    gitFilePath = child['gitFilePath']
    print("Downloading html " + gitFilePath)
    url = 'https://developer.alios.cn/api/document' + gitFilePath + '_v2.do?docversion=' + child['version']
    
    sizePre = len('/develop/Reference/auto/')
    api_level_path = os.path.join(gitFilePath[:sizePre], 'Api Level ' + child['version'], gitFilePath[sizePre:])
    fileName = os.path.join(TARGET_DIR, api_level_path[1:] + '.html')
    print("fileName = " + fileName)

    resp = requests.get(url = url, headers = request_header)
    jsonData = json.loads(resp.text)['data']
    if not jsonData:
        print("Error: download " + url)
        return
    content = jsonData['content'].replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')

    if not os.path.exists(os.path.dirname(fileName)):
        os.makedirs(os.path.dirname(fileName))
    
    f = open(file = fileName, mode = 'w', encoding = 'utf-8')
    f.write(content)
    f.close

def downloadSample(child):
    gitFilePath = child['gitFilePath']
    print("Downloading Sample: " + gitFilePath)
    url = 'https://developer.alios.cn/content/get_md.do?bypath=1&version=0&path=' + quote(gitFilePath)
    resp = requests.get(url = url, headers = request_header)
    jsonData = json.loads(resp.text)['data']
    # zip file 
    zipUrl = jsonData['content']['download']
    parse = urlparse(zipUrl)
    preContent = """# %s
%s
[%s]""" % (jsonData['title'], jsonData['content']['overview'].replace('#', '\\#'), os.path.basename(parse.path))

    outFile = os.path.join(TARGET_DIR, gitFilePath + '.md')

    if downloadMDAttatchFile(zipUrl, os.path.dirname(outFile)):
        outContent = """
%s(%s)""" % (preContent, parse.path[1:])
    else:
        outContent = """
%s(%s)""" % (preContent, zipUrl)
    
    f = open(file = outFile, mode = 'w', encoding = 'utf-8')
    f.write(outContent)
    f.close()

def download(jsonData):
    children = jsonData['child']
    for child in children:
        type = child['type']
        gitFilePath = child['gitFilePath']

        # 特殊文档排除
        if gitFilePath == 'md/developercenter/下载.html':
            continue
        
        # if gitFilePath.startswith('/develop/Reference'):
        #     continue
        # if gitFilePath.startswith('md/developercenter/开发文档'):
        #     continue
        if type == 'catalog':
            dir = os.path.join(TARGET_DIR, gitFilePath)
            if not os.path.exists(dir):
                os.makedirs(dir)
            url = 'https://developer.alios.cn/api/document/get_nearest_child_v2.do?catalogId='+ child['id'] +'&docversion=0'
            resp = requests.get(url = url, headers = request_header)
            subData = json.loads(resp.text)['data']
            download(subData)
        elif type == 'md':
            downloadMD(child)
        elif type == 'html':
            downloadHtml(child)
            # pass
        elif type == 'sample':
            downloadSample(child)
        else:
            print("Error: Unknown type" + child)


index_url = 'https://developer.alios.cn/api/document/get_nearest_child_v2.do'
resp = requests.get(url = index_url, headers = request_header)
indexData = json.loads(resp.text)['data']


open_url = 'https://developer.alios.cn/api/document/get_nearest_child_v2.do?tab=open'
resp = requests.get(url = open_url, headers = request_header)
openData = json.loads(resp.text)['data']


if __name__ == "__main__":
    download(indexData)
    download(openData)