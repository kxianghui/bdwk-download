#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File  : bdwk_doc_spider.py
@Author: kuangxianghui
@Date  : 2020/4/28 21:25
@Desc  : download doc of bdwk
@Python Version: 3.6.2
BeautifulSoup version: 4.9.0
selenium version: 3.141.0
"""

import os
import time
import re
import atexit
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


# only download words, can't download other type
# need to download doc url
url = '/path/to/yours'
# save path, modify it by yourself
path = "test.txt"
# drop head and tail
drop_head_tail = True
# Driver
browser = webdriver.Chrome()


@atexit.register
def clean():
    browser.quit()


def handle_per_page(page_source, page_id):
    soup = BeautifulSoup(page_source, 'lxml')
    div = soup.find(id=page_id)
    p_list = div.select(".ie-fix > p")
    data = {}
    for p in p_list:
        style = p['style']
        top_px = int(re.search('top:(.*?)px', style).group(1))
        text = p.get_text()
        content_list = data.get(top_px)
        if content_list is None:
            content_list = []
            data[top_px] = content_list
        content_list.append(text)
    px_list = data.keys()
    if drop_head_tail:
        head_top_px = min(px_list)
        tail_top_px = max(px_list)
        px_list = filter(lambda key: key != head_top_px and key != tail_top_px, px_list)
    result_list = map(lambda x: ''.join(data.get(x)), px_list)
    return os.linesep.join(result_list)


def main():
    browser.get(url)
    browser.maximize_window()
    wait = WebDriverWait(browser, 10)
    # wait reader go more div appear
    wait.until(EC.presence_of_element_located((By.ID, 'html-reader-go-more')))
    # 继续阅读按钮
    go_more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#html-reader-go-more span[class=fc2e]')))
    go_more_div = browser.find_element(By.ID, 'html-reader-go-more')
    # 页面调试的时候情况总是起伏
    # 需要将按钮滚动到能看见继续阅读才能进行点击，不然会出现not clickable
    browser.execute_script('arguments[0].scrollIntoView();', go_more_div)
    # sleep avoid
    time.sleep(3)
    # 滚到可视位置，进行点击
    go_more_button.click()
    # 等待刷新全部内容
    time.sleep(5)
    try:
        # 因为百度不会缓存全部页，一页一页滚动
        page_template = "pageNo-{}"
        logfile = open(path, 'a', encoding='utf-8')
        total_page_element = browser.find_element_by_xpath('//div[contains(@class, "reader-tools-bar-wrap")]'
                                                           '//div[@class="center"]//span[@class="page-count"]')
        total_page = int(re.search("\\d+", total_page_element.text).group()) + 1
        for i in range(1, total_page):
            page_index = page_template.format(i)
            page = browser.find_element(By.ID, page_index)
            browser.execute_script('arguments[0].scrollIntoView();', page)
            time.sleep(2)
            # handle per page
            page_content = handle_per_page(browser.page_source, page_index)
            logfile.write(page_content)
            logfile.write(os.linesep)
            time.sleep(2)
            if i % 3 == 0:
                time.sleep(3)
    except Exception as e:
        print(traceback.format_exc(), e)
    finally:
        logfile.close()


main()
