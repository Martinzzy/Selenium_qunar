import time
import datetime
import pymongo
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#配置mongod数据库
client = pymongo.MongoClient('localhost')
db = client['qunar']
keyword = '南京'

#声明浏览器对象
browser = webdriver.Chrome()
wait = WebDriverWait(browser,10)

#进行定位，输入信息，完成首页的部分搜索
def search(city,fromdata,todata):
    try:
        browser.get('http://hotel.qunar.com/')
        elect_city = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#toCity')))
        elect_fromdata = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#fromDate')))
        elect_todata = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#toDate')))
        button_search = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainlandForm > div.search-btn-list.clrfix > div.search-btn > a')))
        elect_city.clear()
        elect_city.send_keys(city)
        elect_fromdata.clear()
        elect_fromdata.send_keys(fromdata)
        elect_todata.clear()
        elect_todata.send_keys(todata)
        button_search.click()
    except TimeoutException:
        return search(city,fromdata,todata)


#获得第一页，因为去哪网需要两次加载才能完成这个页面的内容，第一次加载15条，第二次加载15条
def get_one_page(city):
    try:
        wait.until(EC.title_contains((city)))
    except Exception as e:
        print(e)
    time.sleep(5)
    js = "window.scrollTo(0,document.body.scrollHeight);"
    browser.execute_script(js)
    time.sleep(5)
    parse_one_page()


#通过selenium进行翻页
def get_next_page(city):
    try:
        #特别注意这个翻页的地方
        next_page = wait.until(EC.visibility_of(browser.find_element_by_css_selector('.item.next')))
        next_page.click()
        # time.sleep(5)
        wait.until(EC.title_contains((city)))
        time.sleep(3)
        js = "window.scrollTo(0,document.body.scrollHeight);"
        browser.execute_script(js)
        time.sleep(5)
        parse_one_page()
    except TimeoutException:
        return get_next_page(keyword)


#用pyquery解析网页，获取有关酒店的一下信息
def parse_one_page():
    html = browser.page_source
    doc = pq(html)
    items = doc('#jxContentPanel .item_hotel_info').items()
    for item in items:
        hotel_name = item.find('.hotel_item > a.e_title.js_list_name').text()
        hotel_type = item.find('.hotel_item > em').text()
        hotel_price = item.find('.js_list_price > p > a > b').text()
        hotel_site = item.find('.adress .area_contair').text()
        hotel_score = item.find('.hotel_facilities .score').text()
        hotel_facilties = item.find('.hotel_facilities .facily_cont').text()
        hotel_committer = item.find('.hotel_facilities .user_comment').text()
        hotel_experice_sleeper = item.find('.sleeper .icon_cursor .num').text()
        # print(hotel_name,hotel_type,hotel_price,hotel_site,hotel_score,hotel_facilties,hotel_committer,hotel_experice_sleeper)
        data = {
            'hotel_name':hotel_name,
            'hotel_type':hotel_type,
            'hotel_price':hotel_price,
            'hotel_site':hotel_site,
            'hotel_score':hotel_score,
            'hotel_facilties':hotel_facilties,
            'hotel_committer':hotel_committer,
            'hotel_exper_sleeper':hotel_experice_sleeper
        }
        save_to_mongo(data)

#存储到mongodb数据库
def save_to_mongo(result):
    if result:
        if db['hotel'].insert(result):
            print('存储到MongoDB数据库成功',result)
        else:
            print('存储失败到mongodb数据库',result)


def main():
    page = 1
    today = datetime.date.today().strftime('%Y-%m-%d')
    tomorrow = datetime.date.today()+datetime.timedelta(days=1)
    tomorrow = tomorrow.strftime('%Y-%m-%d')
    search(keyword,today,tomorrow)
    get_one_page(keyword)
    while page<302:
        print('正在爬取第{}页'.format(page))
        get_next_page(keyword)
        page+=1


if __name__ == '__main__':
    main()
