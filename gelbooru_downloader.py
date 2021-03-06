#coding: utf-8
import downloader
import re
import os
from utils import Downloader, urljoin, parse_range, query_url, Soup
from fucking_encoding import clean_title
from translator import tr_
import urllib
import sys
from time import sleep
from constants import clean_url
LIMIT = 100


def get_tags(url):
    url = clean_url(url)
    qs = query_url(url)
    if 'page=favorites' in url:
        id = qs.get('id', ['N/A'])[0]
        id = u'fav_{}'.format(id)
    else:
        tags = qs.get('tags', [])
        tags.sort()
        id = u' '.join(tags)
    if not id:
        id = u'N/A'
    return id


class Downloader_gelbooru(Downloader):
    type = 'gelbooru'
    URLS = ['gelbooru.com']
    MAX_CORE = 32
    def init(self):
        self._id = None
        self.type = 'gelbooru'
        self.single = False
        #self.user_agent = downloader.hdr['User-Agent']
        self.url = self.url.replace('gelbooru_', '')
        if 'gelbooru.com' in self.url.lower():
            self.url = self.url.replace('http://', 'https://')
        else:
            url = self.url
            url = url.replace(' ', '+')
            while '++' in url:
                url = url.replace('++', '+')
            url = urllib.quote(url)
            url = url.replace('%2B', '+')
            self.url = u'https://gelbooru.com/index.php?page=post&s=list&tags={}'.format(url)

    @property
    def id(self):
        if self._id is None:
            tags = get_tags(self.url)
            self._id = tags
        return self._id

    @property
    def name(self):
        return clean_title(self.id)

    def read(self):
        self.title = self.name

        imgs = get_imgs(self.url, self.name, customWidget=self.customWidget)

        for img in imgs:
            self.urls.append(img.url)
            self.filenames[img.url] = img.filename

        sleep(.1)
        self.title = self.name
Downloader.register(Downloader_gelbooru)


class Image(object):
    def __init__(self, id, url, local=False):
        self.id = id
        self.filename = None
        if local:
            self.filename = os.path.basename(url)
            self.url = url
            return

        ext = os.path.splitext(url)[1]
        self.filename = u'{}{}'.format(id, ext)
        self.url = url


def setPage(url, page):
    # Always use HTTPS
    url = url.replace('http://', 'https://')

    # Change the page
    if 'pid=' in url:
        url = re.sub('pid=[0-9]*', 'pid={}'.format(page), url)
    else:
        url += '&pid={}'.format(page)

    return url


def get_imgs(url, title=None, customWidget=None):
    url = clean_url(url)
    if 's=view' in url and 'page=favorites' not in url:
        raise NotImplementedError('Not Implemented')

    if 'page=dapi' not in url.lower():
        tags = get_tags(url).replace(' ', '+')
        tags = urllib.quote(tags)
        url = "https://gelbooru.com/index.php?page=dapi&s=post&q=index&tags={}&pid={}&limit={}".format(tags, 0, LIMIT)

    if customWidget is not None:
        print_ = customWidget.print_
    else:
        def print_(*values):
            sys.stdout.writelines(values + ('\n',))

    # Range
    if customWidget is not None:
        range_pid = customWidget.range
    else:
        range_pid = None
    if range_pid is not None:
        max_pid = max(parse_range(range_pid, max=100000))
    else:
        max_pid = 2000

    imgs = []
    url_imgs = set()
    for p in range(100):
        url = setPage(url, p)
        print_(url)
        html = downloader.read_html(url)

        soup = Soup(html)
        posts = soup.findAll('post')
        if not posts:
            break
        for post in posts:
            url_img = post.attrs['file_url']
            if url_img in url_imgs:
                print 'already exists', url_img
            else:
                url_imgs.add(url_img)
                id = post.attrs['id']
                img = Image(id, url_img)
                imgs.append(img)
        if len(imgs) >= max_pid:
            break

        if customWidget is not None:
            if not customWidget.alive:
                break
            customWidget.setTitle(u'{}  {} - {}'.format(tr_(u'읽는 중...'), title, len(imgs)))
    return imgs
