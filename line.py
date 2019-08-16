import random
from flask import Flask, request, abort
import requests
import time
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('KNmT6d0YvRVBv3ytX+DpLFh/2/WjSv6/Q8WI/c1xbfMzUsXOvAqJWtzIqBxDPQtlWO3JPqqjnVtZFKbLd4Cyo6akNvhU8/cGzx7qWbXcOZkwJmJXHunQfcqPk3nv+EQ/knZY1Rgucaw6JHm2Ehx5ygdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('96c0d33fa900023916dfb2b6f527f632')

@app.route('/')
def index():
    return "<p>Hello World!</p>"

#收訊息
# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature) #幫你判斷要用剛剛設定的哪個 event 來作回應
    except InvalidSignatureError:  # Line sdk 會檢查你的資料是否正確(用你的CHANNEL_ACCESS_TOKEN)
        abort(400)
    return 'OK'


#####爬蟲開始#####
##Trivago依評分排名 
def trivagoRank(place,checkin_date,checkout_date,roomtype):
    driver = webdriver.Chrome("C:/Users/AmyHsia/pytest/chromedriver.exe")  #將瀏覽器開啟
    driver.get("https://www.trivago.com.tw/") #取得頁面的結果
    try:
        elem = driver.find_element_by_id("horus-querytext")
    except:
        elem = driver.find_element_by_id("querytext")
    elem.send_keys(place)
    #點擊入住日期欄位
    driver.find_element_by_xpath("//*[@id=\"js-fullscreen-hero\"]/div/div[2]/div[2]/button").click()
    time.sleep(5)
    #抓取點擊後顯示的日曆文字
    date = driver.find_element_by_xpath("//*[@id=\"cal-heading-month\"]/span").text
    dateYear = int(date[0:4])
    dateMonth = int(date[5:7])
    #入住日期分割
    checkin_year = int(checkin_date.split('-')[0])
    checkin_month = int(checkin_date.split('-')[1])
    clickTimes = abs(checkin_month-dateMonth)
    times=0
    if checkin_year==dateYear and checkin_month==dateMonth:
        times=0
    elif checkin_month>dateMonth:
        times=clickTimes
    else:
        times=6+clickTimes
    #點擊換月份鈕
    for k in range(times):
        button = driver.find_element_by_class_name("cal-btn-next")
        button.click()
    for k in driver.find_elements_by_css_selector("table > tbody time"):
        if k.get_attribute('datetime')==checkin_date:
            k.click()
            break
    ######退房日期選擇  ######### 最多兩個月後
    date = driver.find_element_by_css_selector(".cal-heading-month span").text
    dateYear = int(date[0:4])
    dateMonth = int(date[5:7])
    #退房日期分割
    checkout_year = int(checkout_date.split('-')[0])
    checkout_month = int(checkout_date.split('-')[1])
    clickTimes = abs(checkout_month-dateMonth)
    times=0
    if checkout_year==dateYear and checkout_month==dateMonth:
        times=0
    elif checkout_month>dateMonth:
        times=clickTimes
    else:
        times=6+clickTimes
    #點擊換月鈕至指定月份
    for k in range(times):
        button = driver.find_element_by_class_name("cal-btn-next")
        button.click()  
    #點擊指定日期
    for k in driver.find_elements_by_css_selector("table > tbody time"):
        if k.get_attribute('datetime')==checkout_date:
            k.click()
            break
    #房型選擇
    for k in driver.find_elements_by_css_selector(".roomtype-btn .roomtype-btn__label"):
        if k.text==roomtype:
            k.click()
            break
    #搜尋
    try:
        driver.find_element_by_class_name("horus-btn-search").click()
    except:
        driver.find_element_by_class_name("search-button__label").click()
    time.sleep(5)
    #依評分排序
    driver.find_element_by_xpath("//select[@id='mf-select-sortby']/option[@value='4']").click()
    time.sleep(5)
    #最初依評分獲得的網址
    link_current = driver.current_url
    linkList1 = []
    for k in driver.find_elements_by_css_selector('.deal__wrapper button'):
        k.click()
        time.sleep(5)
        driver.switch_to_window(driver.window_handles[-1])
        link = driver.current_url
        linkList1.append(link)
        if len(linkList1)==5:
            break
        driver.switch_to_window(driver.window_handles[0])
    driver.get(link_current) #取得頁面的結果
    html_score = driver.find_element_by_css_selector("*").get_attribute("outerHTML")
    doc_score = pq(html_score)
    dataset1 = [] 
    i=0
    for eachItem in doc_score('.item__wrapper').items():
        if not eachItem(".rating-pill span").text()=='/':
            dataDict = {}
            dataDict["Name"] = eachItem("span.item-link").text()
            dataDict["Price"] = eachItem(".item__best-price").text()
            dataDict["Rank"] = eachItem(".rating-pill span").text()
            dataDict["link"] = linkList1[i]
            if eachItem("img.lazy-image__image").attr('src') is None:
                dataDict["Img"] = str(eachItem("meta[itemprop='url']").attr('content'))
            else:
                dataDict["Img"] = 'https:'+str(eachItem("img.lazy-image__image").attr('src'))
            dataset1.append(dataDict)
            i+=1
            if len(dataset1)==5:
                break
    #關閉瀏覽器
    driver.quit()
    return dataset1

#Airbnb 依評價排名
def airbnbRank(place,checkin_date,checkout_date,roomtype):
    driver = webdriver.Chrome("C:/Users/AmyHsia/pytest/chromedriver.exe")  #將瀏覽器開啟
    driver.get("https://www.airbnb.com.tw/") 
    ##按掉cookie
    driver.find_element_by_class_name("accept-cookies-button").click()
    driver.maximize_window()
    #填入地點
    elem = driver.find_element_by_class_name("_up0kwni")
    elem.clear()
    elem.send_keys(place)
    elem.send_keys(Keys.ENTER)
    #點擊入住日期
    driver.find_element_by_id("checkin_input").click()
    #顯示文字
    date = driver.find_element_by_xpath("//div[2]/div/div/strong").text
    date = date.split('月')
    dateMonth,dateYear = date[0],int(date[1])
    monthDict = {"一":"1","二":"2","三":"3","四":"4","五":"5","六":"6","七":"7","八":"8","九":"9","十":"10","十一":"11","十二":"12"}
    dateMonth = int(monthDict[dateMonth])
    checkin_year = int(checkin_date.split('-')[0])
    checkin_month = int(checkin_date.split('-')[1])
    checkin_day = int(checkin_date.split('-')[2])
    clickTimes = abs(checkin_month-dateMonth)
    ##times為點擊下個月的那個鈕的次數 
    times=0
    if checkin_year==dateYear and checkin_month==dateMonth:
        times=0
    elif checkin_month>dateMonth:
        times=clickTimes
    else:
        times=6+clickTimes
    for k in range(times):
        button = driver.find_element_by_class_name("_1h5uiygl") #下個月的鈕
        button.click()
        time.sleep(5)
    #下拉
    js="var q=document.documentElement.scrollTop=300"
    driver.execute_script(js)
    #點擊入住日期 
    for k in driver.find_elements_by_xpath('//*[@id=\"MagicCarpetSearchBar\"]/div[2]/div/div/div/div[2]/div/div/div/div/div/div[2]/div[2]/div/div[2]/div/table/tbody/tr/td'):
        if k.text==str(checkin_day):
            k.click()
            break
    #退房日期選擇
    #退房日期顯示文字
    date = driver.find_element_by_xpath("//div[2]/div/div/strong").text
    date = date.split('月')
    dateMonth,dateYear = date[0],int(date[1])
    dateMonth = int(monthDict[dateMonth])
    #退房日期分割
    checkout_year = int(checkout_date.split('-')[0])
    checkout_month = int(checkout_date.split('-')[1])
    checkout_day = int(checkout_date.split('-')[2])
    clickTimes = abs(checkout_month-dateMonth)
    times=0
    if checkout_year==dateYear and checkout_month==dateMonth:
        times=0
    elif checkout_month>dateMonth:
        times=clickTimes
    else:
        times=6+clickTimes  
    for k in range(times):
        button = driver.find_element_by_class_name("cal-btn-next")
        button.click() 
    for k in driver.find_elements_by_xpath('//*[@id="MagicCarpetSearchBar"]/div[2]/div/div/div/div[3]/div/div/div/div/div/div[2]/div[2]/div/div[2]/div/table/tbody/tr/td'):
        if k.text==str(checkout_day):
            k.click()
            break
    #房型:單人房/雙人房/家庭房
    button = driver.find_element_by_class_name("_7ykwo4") 
    button.click()
    #下拉
    js="var q=document.documentElement.scrollTop=300"
    driver.execute_script(js)
    roomList = ['單人房','雙人房','家庭房']
    for k in range(len(roomList)):
        if roomList[k]==roomtype:
            number = k+1
    #點擊成人數目(假設都點選成人)
    for i in range(number):
        button = driver.find_element_by_xpath("//*[@id=\"MagicCarpetSearchBar\"]/div[3]/div/div[2]/div/div/div[1]/div[1]/div/div/div/div[2]/div/div[3]/button") 
        button.click() 
    #套用 
    try:
        button = driver.find_element_by_class_name("_1dv8bs9v") 
    except:
        button = driver.find_element_by_class_name("_b0ybw8s") 
    button.click()
    #搜尋鈕
    button = driver.find_element_by_class_name("_ftj2sg4") 
    button.click()
    html_score = driver.find_element_by_css_selector("*").get_attribute("outerHTML")
    doc_score = pq(html_score)
    #Name欄位有時會改變
    dataset = [] 
    for eachItem in doc_score('._gig1e7').items():
        dataDict = {}
        dataDict["Name"] = eachItem("._1p0spma2 ._36rlri").text()
        if dataDict["Name"]=='':
            dataDict["Name"] = eachItem("._b9qfkc2 ._1dss1omb").text()
        if eachItem("._1p3joamp>._1p3joamp>._1p3joamp").text()[:3]=='折扣前':
            continue
        dataDict["Price"] = eachItem("._1p3joamp>._1p3joamp>._1p3joamp").text().lstrip('價格$').rstrip(' TWD')
        if eachItem("span._1p2weln").text()=='新推出':
            continue
        if eachItem("._rs3rozr").attr('aria-label') is None:
            continue
        dataDict["Rank"] = eachItem("._rs3rozr").attr('aria-label').lstrip('評分是').replace('（滿分為5）','')
        dataDict["link"] = 'https://zh.airbnb.com'+eachItem("._1szwzht a").attr('href')
        dataset.append(dataDict)
        ####因為有的連結裡面打開會出抓不到圖片所以要做例外處理
    for k in range(len(dataset)):
        lvl1Res= driver.get(dataset[k]['link'])
        time.sleep(8)
        try:
            img = driver.find_element_by_class_name("_uttz43").get_attribute('src')
        except:
            img = driver.find_element_by_class_name("_139od7js").get_attribute('src')
        dataset[k]['Img'] = img
    #Rank轉成浮點數以便排序(乘以2是為了與trivago做比較)
    for i in range(len(dataset)):
        dataset[i]['Rank']=float(dataset[i]['Rank'])*2
        dataset[i]['Price'] = int(dataset[i]['Price'].replace(',',''))
    #依照價格(由小到大)
    def rule(item):
        return item["Price"]
    dataset1 = sorted(dataset,key=rule)
    #依照評分(由大到小)
    def rule(item):
        return item["Rank"]
    dataset2 = sorted(dataset,key=rule,reverse=True)
    driver.quit()
    return dataset2

#####綜合Trivago以及Airbnb依評分排序由大到小#####
def RANK(place,checkin_date,checkout_date,roomtype):
    list_airbnb = trivagoRank(place,checkin_date,checkout_date,roomtype)
    list_trivago = airbnbRank(place,checkin_date,checkout_date,roomtype)
    big_rank = list_airbnb + list_trivago
    def rule(item):
        return item["Rank"]
    big_rank_2 = sorted(big_rank, key = rule,reverse=True)
    return big_rank_2     

##Trivago依價格排名 
def trivagoPrice(place,checkin_date,checkout_date,roomtype):
    driver = webdriver.Chrome("C:/Users/AmyHsia/pytest/chromedriver.exe")  #將瀏覽器開啟
    driver.get("https://www.trivago.com.tw/") #取得頁面的結果
    #填入地區
    try:
        elem = driver.find_element_by_id("horus-querytext")
    except:
        elem = driver.find_element_by_id("querytext")
    elem.send_keys(place)
    #點擊入住日期欄位
    driver.find_element_by_xpath("//*[@id=\"js-fullscreen-hero\"]/div/div[2]/div[2]/button").click()
    time.sleep(5)
    #抓取點擊後顯示的日曆文字
    date = driver.find_element_by_xpath("//*[@id=\"cal-heading-month\"]/span").text
    dateYear = int(date[0:4])
    dateMonth = int(date[5:7])
    #入住日期分割
    checkin_year = int(checkin_date.split('-')[0])
    checkin_month = int(checkin_date.split('-')[1])
    clickTimes = abs(checkin_month-dateMonth)
    times=0
    if checkin_year==dateYear and checkin_month==dateMonth:
        times=0
    elif checkin_month>dateMonth:
        times=clickTimes
    else:
        times=6+clickTimes
    #點擊換月份鈕
    for k in range(times):
        button = driver.find_element_by_class_name("cal-btn-next")
        button.click()
    #點擊指定日期
    for k in driver.find_elements_by_css_selector("table > tbody time"):
        if k.get_attribute('datetime')==checkin_date:
            k.click()
            break    
    date = driver.find_element_by_css_selector(".cal-heading-month span").text
    dateYear = int(date[0:4])
    dateMonth = int(date[5:7])
    #退房日期分割
    checkout_year = int(checkout_date.split('-')[0])
    checkout_month = int(checkout_date.split('-')[1])
    clickTimes = abs(checkout_month-dateMonth)
    times=0
    if checkout_year==dateYear and checkout_month==dateMonth:
        times=0
    elif checkout_month>dateMonth:
        times=clickTimes
    else:
        times=6+clickTimes
    #點擊換月鈕至指定月份
    for k in range(times):
        button = driver.find_element_by_class_name("cal-btn-next")
        button.click()
    #點擊指定日期
    for k in driver.find_elements_by_css_selector("table > tbody time"):
        if k.get_attribute('datetime')==checkout_date:
            k.click()
            break
    #房型選擇
    for k in driver.find_elements_by_css_selector(".roomtype-btn .roomtype-btn__label"):
        if k.text==roomtype:
            k.click()
            break
    #搜尋 
    try:
        driver.find_element_by_class_name("horus-btn-search").click()
    except:
        driver.find_element_by_class_name("search-button__label").click()
    time.sleep(5)
     #依價格排序
    driver.find_element_by_xpath("//select[@id='mf-select-sortby']/option[@value='2']").click()
    time.sleep(5)
    #獲取當前url，以便之後使用
    link_current = driver.current_url
    rating =driver.find_elements_by_css_selector(".rating-pill span")
    result=[]
    count=0
    for k in rating:
        if not k.text=='/':
            result.append(count)
        count+=1
    #查看是否真的抓到當個連結
    linkList2 = []
    button = driver.find_elements_by_css_selector('.deal__wrapper button')
    for k in result:
        button[k].click()
        time.sleep(5)
        driver.switch_to_window(driver.window_handles[-1])
        link = driver.current_url
        print(link)
        linkList2.append(link)
        if len(linkList2)==5:
            break
        driver.switch_to_window(driver.window_handles[0]) 
    linkList2
    driver.get(link_current) #取得頁面的結果
    html =driver.find_element_by_css_selector("*").get_attribute("outerHTML")
    doc = pq(html)
    dataset2 = [] 
    i=0
    for eachItem in doc('.item__wrapper').items():
        if not eachItem(".rating-pill span").text()=='/':
            dataDict = {}
            dataDict["Name"] = eachItem("span.item-link").text()
            dataDict["Price"] = eachItem(".item__best-price").text()
            dataDict["Rank"] = eachItem(".rating-pill span").text()
            dataDict["link"] = linkList2[i]
            if eachItem("img.lazy-image__image").attr('src') is None:
                dataDict["Img"] = str(eachItem("meta[itemprop='url']").attr('content'))
            else:
                dataDict["Img"] = 'https:'+str(eachItem("img.lazy-image__image").attr('src'))
            dataset2.append(dataDict)
            i+=1
            if len(dataset2)==5:
                break
    driver.quit()
    return dataset2

##Airbnb依價格排名 
def airbnbPrice(place,checkin_date,checkout_date,roomtype):
    driver = webdriver.Chrome("C:/Users/AmyHsia/pytest/chromedriver.exe")  #將瀏覽器開啟
    driver.get("https://www.airbnb.com.tw/") 
    ##按掉cookie
    driver.find_element_by_class_name("accept-cookies-button").click()
    driver.maximize_window()
    #填入地點
    elem = driver.find_element_by_class_name("_up0kwni")
    elem.clear()
    elem.send_keys(place)
    elem.send_keys(Keys.ENTER)
    #點擊入住日期
    driver.find_element_by_id("checkin_input").click()
    #顯示文字
    date = driver.find_element_by_xpath("//div[2]/div/div/strong").text
    date = date.split('月')
    dateMonth,dateYear = date[0],int(date[1])
    monthDict = {"一":"1","二":"2","三":"3","四":"4","五":"5","六":"6","七":"7","八":"8","九":"9","十":"10","十一":"11","十二":"12"}
    dateMonth = int(monthDict[dateMonth])
    checkin_year = int(checkin_date.split('-')[0])
    checkin_month = int(checkin_date.split('-')[1])
    checkin_day = int(checkin_date.split('-')[2])
    clickTimes = abs(checkin_month-dateMonth)
    #times為點擊下個月的那個鈕的次數 
    times=0
    if checkin_year==dateYear and checkin_month==dateMonth:
        times=0
    elif checkin_month>dateMonth:
        times=clickTimes
    else:
        times=6+clickTimes
    for k in range(times):
        button = driver.find_element_by_class_name("_1h5uiygl") #下個月的鈕
        button.click()
        time.sleep(5)
    #下拉
    js="var q=document.documentElement.scrollTop=300"
    driver.execute_script(js)
    #點擊入住日期 
    for k in driver.find_elements_by_xpath('//*[@id=\"MagicCarpetSearchBar\"]/div[2]/div/div/div/div[2]/div/div/div/div/div/div[2]/div[2]/div/div[2]/div/table/tbody/tr/td'):
        if k.text==str(checkin_day):
            k.click()
            break
    #退房日期選擇
    #退房日期顯示文字
    date = driver.find_element_by_xpath("//div[2]/div/div/strong").text
    date1 = date.split('月')
    dateMonth1,dateYear = date1[0],int(date1[1])
    dateMonth2 = int(monthDict[dateMonth1])
    #退房日期分割
    checkout_year = int(checkout_date.split('-')[0])
    checkout_month = int(checkout_date.split('-')[1])
    checkout_day = int(checkout_date.split('-')[2])
    clickTimes = abs(checkout_month-dateMonth)
    times=0
    if checkout_year==dateYear and checkout_month==dateMonth:
        times=0
    elif checkout_month>dateMonth:
        times=clickTimes
    else:
        times=6+clickTimes  
    for k in range(times):
        button = driver.find_element_by_class_name("cal-btn-next")
        button.click()   
    for k in driver.find_elements_by_xpath('//*[@id="MagicCarpetSearchBar"]/div[2]/div/div/div/div[3]/div/div/div/div/div/div[2]/div[2]/div/div[2]/div/table/tbody/tr/td'):
        if k.text==str(checkout_day):
            k.click()
            break
    #房型:單人房/雙人房/家庭房
    button = driver.find_element_by_class_name("_7ykwo4") 
    button.click()
    #下拉
    js="var q=document.documentElement.scrollTop=300"
    driver.execute_script(js)
    roomList = ['單人房','雙人房','家庭房']
    for k in range(len(roomList)):
        if roomList[k]==roomtype:
            number = k+1
    #點擊成人數目
    for i in range(number):
        button = driver.find_element_by_xpath("//*[@id=\"MagicCarpetSearchBar\"]/div[3]/div/div[2]/div/div/div[1]/div[1]/div/div/div/div[2]/div/div[3]/button") 
        button.click()
    #套用 
    try:
        button = driver.find_element_by_class_name("_1dv8bs9v") 
    except:
        button = driver.find_element_by_class_name("_b0ybw8s") 
    button.click()
    #搜尋鈕
    button = driver.find_element_by_class_name("_ftj2sg4") 
    button.click()
    html_score = driver.find_element_by_css_selector("*").get_attribute("outerHTML")
    doc_score = pq(html_score)
    #Name欄位有時會改變 
    dataset = [] 
    for eachItem in doc_score('._gig1e7').items():
        dataDict = {}
        dataDict["Name"] = eachItem("._1p0spma2 ._36rlri").text()
        if dataDict["Name"]=='':
            dataDict["Name"] = eachItem("._b9qfkc2 ._1dss1omb").text()
        if eachItem("._1p3joamp>._1p3joamp>._1p3joamp").text()[:3]=='折扣前':
            continue
        dataDict["Price"] = eachItem("._1p3joamp>._1p3joamp>._1p3joamp").text().lstrip('價格$').rstrip(' TWD')
        if eachItem("span._1p2weln").text()=='新推出':
            continue
        if eachItem("._rs3rozr").attr('aria-label') is None:
            continue
        dataDict["Rank"] = eachItem("._rs3rozr").attr('aria-label').lstrip('評分是').replace('（滿分為5）','')
        dataDict["link"] = 'https://zh.airbnb.com'+eachItem("._1szwzht a").attr('href')
        dataset.append(dataDict)
        ####因為有的連結裡面打開會出抓不到圖片所以要做例外處理(有兩種可能性)
    for k in range(len(dataset)):
        lvl1Res= driver.get(dataset[k]['link'])
        time.sleep(8)
        try:
            img = driver.find_element_by_class_name("_uttz43").get_attribute('src')
        except:
            img = driver.find_element_by_class_name("_139od7js").get_attribute('src')
        dataset[k]['Img'] = img
    #Rank轉成浮點數以便排序(乘以2是為了與trivago做比較)
    for i in range(len(dataset)):
        dataset[i]['Rank']=float(dataset[i]['Rank'])*2
        dataset[i]['Price'] = int(dataset[i]['Price'].replace(',',''))
    #依照價格(由小到大)
    def rule(item):
        return item["Price"]
    dataset1 = sorted(dataset,key=rule)
    #依照評分(由大到小)
    def rule(item):
        return item["Rank"]
    dataset2 = sorted(dataset,key=rule,reverse=True)
    driver.quit()
    return dataset1

#####綜合Trivago以及Airbnb依價格排序由小到大#####
def PRICE(place,checkin_date,checkout_date,roomtype):
    list_airbnb1 = trivagoPrice(place,checkin_date,checkout_date,roomtype)
    list_trivago1 = airbnbPrice(place,checkin_date,checkout_date,roomtype)
    big_price = list_airbnb1 + list_trivago1
    def rule(item):
        return item["Price"]
    big_price_2 = sorted(big_price, key = rule)
    return big_price_2   

#####爬蟲結束#####

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	# get user id when reply
    user_id = event.source.user_id
    print("user_id =", user_id)

    placeSet = {"基隆市","嘉義市","台北市","嘉義縣","新北市","台南市","桃園縣","高雄市","新竹市","屏東縣","新竹縣","台東縣","苗栗縣","花蓮縣","台中市","宜蘭縣","彰化縣","澎湖縣","南投縣","金門縣","雲林縣","連江縣"}
    carousel_template_message1 = TemplateSendMessage(
        alt_text='價格排名template',  #Template訊息在電腦版的Line是顯示不出來的，會用alt_text替代
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=big_price_2[0]['Img'],
                    title=big_price_2[0]['Name'],
                    text='NT$'+big_price_2[0]['Price'],
                    actions=[

                        URIAction(
                            label='來去訂房',
                            uri=big_price_2[0]['link']
                        )
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url=big_price_2[1]['Img'],
                    title=big_price_2[1]['Name'],
                    text='NT$'+big_price_2[1]['Price'],
                    actions=[
              
                        URIAction(
                            label='來去訂房',
                            uri=big_price_2[1]['link']
                        )
                 
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url=big_price_2[2]['Img'],
                    title=big_price_2[2]['Name'],
                    text='NT$'+big_price_2[2]['Price'],
                    actions=[

                        URIAction(
                            label='來去訂房',
                            uri=big_price_2[2]['link']
                        )

                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url=big_price_2[3]['Img'],
                    title=big_price_2[3]['Name'],
                    text='NT$'+big_price_2[3]['Price'],
                    actions=[

                        URIAction(
                            label='來去訂房',
                            uri=big_price_2[3]['link']
                        )

                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url=big_price_2[4]['Img'],
                    title=big_price_2[4]['Name'],
                    text='NT$'+big_price_2[4]['Price'],
                    actions=[

                        URIAction(
                            label='來去訂房',
                            uri=big_price_2[4]['link']
                        )

                    ]
                )
            ]
        )
    )

    carousel_template_message2 = TemplateSendMessage(
        alt_text='評分排名template',  #Template訊息在電腦版的Line是顯示不出來的，會用alt_text替代
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=big_rank_2[0]['Img'],
                    title=big_rank_2[0]['Name'],
                    text='評分'+big_rank_2[0]['Rank'],
                    actions=[
                        # MessageAction(
                        #     label='開始玩',
                        #     text='開始玩'
                        # ),
                        URIAction(
                            label='來去訂房',
                            uri=big_rank_2[0]['link']
                        )
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url=big_rank_2[1]['Img'],
                    title=big_rank_2[1]['Name'],
                    text='評分'+big_rank_2[1]['Rank'],
                    actions=[
              
                        URIAction(
                            label='來去訂房',
                            uri=big_rank_2[1]['link']
                        )
                 
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url=big_rank_2[2]['Img'],
                    title=big_rank_2[2]['Name'],
                    text='評分'+big_rank_2[2]['Rank'],
                    actions=[

                        URIAction(
                            label='來去訂房',
                            uri=big_rank_2[2]['link']
                        )

                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url=big_rank_2[3]['Img'],
                    title=big_rank_2[3]['Name'],
                    text='評分'+big_rank_2[3]['Rank'],
                    actions=[

                        URIAction(
                            label='來去訂房',
                            uri=big_rank_2[3]['link']
                        )

                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url=big_rank_2[4]['Img'],
                    title=big_rank_2[4]['Name'],
                    text='評分'+big_rank_2[4]['Rank'],
                    actions=[

                        URIAction(
                            label='來去訂房',
                            uri=big_rank_2[4]['link']
                        )

                    ]
                )
            ]
        )
    )


    if event.message.text == "呼叫小比":
        message = '請問您想訂哪裡的飯店呢?'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = message))

    elif event.message.text in placeSet:
        message = '請輸入入住日期(格式為西元-月-日)，例如:2019-07-08'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = message))
        place = event.message.text

    elif event.message.text[0] == "2" :
        message = '請輸入退房日期(格式為西元-月-日)，例如:2019-07-08'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = message))
        checkin_date = event.message.text

    elif event.message.text[0] == "2" :
        buttons_template = TemplateSendMessage(
            alt_text='房型 template',
            template=ButtonsTemplate(
                title='房型',
                text='請選擇',
                thumbnail_image_url='https://www.house108.com.tw/uploads/design/576-1.jpg',
                actions=[
                    MessageTemplateAction(
                        label='單人房',
                        text='單人房'
                    ),
                    MessageTemplateAction(
                        label='雙人房',
                        text='雙人房'
                    ),
                    MessageTemplateAction(
                        label='家庭房',
                        text='家庭房'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token,buttons_template)
        # return 0
        checkout_date = event.message.text


    elif event.message.text == '單人房':
        message = '飯店小幫手已經為您挑選出理想中的飯店囉'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = message))
        buttons_template = TemplateSendMessage(
            alt_text='排名方式 template',
            template=ButtonsTemplate(
                title='排名方式',
                text='請選擇',
                thumbnail_image_url='https://previews.123rf.com/images/nalinn/nalinn1504/nalinn150400299/38532284-%EA%B8%88-%EC%9D%80-%EB%8F%99%EB%A9%94%EB%8B%AC%EC%9D%80-%EB%A0%88%EB%93%9C-%EB%B8%94%EB%A3%A8-%EC%8B%A4%EB%B2%84-%EB%AF%B9%EC%8A%A4-%EC%BB%AC%EB%9F%AC-%EB%A6%AC%EB%B3%B8%EC%9C%BC%EB%A1%9C-%EC%84%A4%EC%A0%95.jpg',
                actions=[
                    MessageTemplateAction(
                        label='價格排名',
                        text='價格排名'
                    ),
                    MessageTemplateAction(
                        label='評分排名',
                        text='評分排名'
                    )
                ]
            )
        )
        line_bot_api.push_message(user_id, buttons_template)
        # return 0
        roomtype = event.message.text

    elif event.message.text == '雙人房':
        message = '飯店小幫手已經為您挑選出理想中的飯店囉'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = message))
        buttons_template = TemplateSendMessage(
            alt_text='排名方式 template',
            template=ButtonsTemplate(
                title='排名方式',
                text='請選擇',
                thumbnail_image_url='https://previews.123rf.com/images/nalinn/nalinn1504/nalinn150400299/38532284-%EA%B8%88-%EC%9D%80-%EB%8F%99%EB%A9%94%EB%8B%AC%EC%9D%80-%EB%A0%88%EB%93%9C-%EB%B8%94%EB%A3%A8-%EC%8B%A4%EB%B2%84-%EB%AF%B9%EC%8A%A4-%EC%BB%AC%EB%9F%AC-%EB%A6%AC%EB%B3%B8%EC%9C%BC%EB%A1%9C-%EC%84%A4%EC%A0%95.jpg',
                actions=[
                    MessageTemplateAction(
                        label='價格排名',
                        text='價格排名'
                    ),
                    MessageTemplateAction(
                        label='評分排名',
                        text='評分排名'
                    )
                ]
            )
        )
        line_bot_api.push_message(user_id, buttons_template)
        # return 0
        roomtype = event.message.text

    elif event.message.text == '家庭房':
        message = '飯店小幫手已經為您挑選出理想中的飯店囉'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = message))
        buttons_template = TemplateSendMessage(
            alt_text='排名方式 template',
            template=ButtonsTemplate(
                title='排名方式',
                text='請選擇',
                thumbnail_image_url='https://previews.123rf.com/images/nalinn/nalinn1504/nalinn150400299/38532284-%EA%B8%88-%EC%9D%80-%EB%8F%99%EB%A9%94%EB%8B%AC%EC%9D%80-%EB%A0%88%EB%93%9C-%EB%B8%94%EB%A3%A8-%EC%8B%A4%EB%B2%84-%EB%AF%B9%EC%8A%A4-%EC%BB%AC%EB%9F%AC-%EB%A6%AC%EB%B3%B8%EC%9C%BC%EB%A1%9C-%EC%84%A4%EC%A0%95.jpg',
                actions=[
                    MessageTemplateAction(
                        label='價格排名',
                        text='價格排名'
                    ),
                    MessageTemplateAction(
                        label='評分排名',
                        text='評分排名'
                    )
                ]
            )
        )
        line_bot_api.push_message(user_id, buttons_template)
        # return 0
        roomtype = event.message.text 

    elif event.message.text == "價格排名":
    	PRICE(place,checkin_date,checkout_date,roomtype)
    	line_bot_api.reply_message(event.reply_token, carousel_template_message1)

    	# return 0

    elif event.message.text == "評分排名":
    	RANK(place,checkin_date,checkout_date,roomtype)
	    line_bot_api.reply_message(event.reply_token, carousel_template_message2)
	    # return 0

	else:
		message = '小比聽不懂，請重新輸入~'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = message))



#貼圖處理(每個貼圖都有一個id)
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    print("package_id:", event.message.package_id)
    print("sticker_id:", event.message.sticker_id)
     # ref. https://developers.line.me/media/messaging-api/sticker_list.pdf
    sticker_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100, 101, 115, 116, 117, 119, 120, 121, 122, 124, 125]
    index_id = random.randint(0, len(sticker_ids) - 1)
    sticker_id = str(sticker_ids[index_id])
    print(index_id)
    # 貼圖在LINE之中是以兩組號碼代表，第一組號碼是該貼圖屬於那個系列的貼圖，在event物件中為event.message.package_id，第二組號碼是該貼圖在系列中的第幾張，為event.message.sticker_id物件
    sticker_message = StickerSendMessage( package_id='1', sticker_id=sticker_id)
    line_bot_api.reply_message(event.reply_token,sticker_message)


import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
