import time
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import csv

PATH_TO_CHROME_PROFILE = r"user-data-dir=C:\\Users\\Victor\\AppData\\Local\\Google\\Chrome\\User Data\\"
PROFILE_DIR_NAME = '--profile-directory=Default'
SRC_URL = "https://market.yandex.ru/product--smartfon-apple-iphone-14-pro-max/1768738052/offers?glfilter=14871214%3A16048172_101813096786&glfilter=23476910%3A26684950_101813096786&glfilter=24938610%3A41821219_101813096786&glfilter=25879492%3A25879710_101813096786&cpa=1&grhow=supplier&sku=101813096786&resale_goods=resale_new&local-offers-first=0"
SHOP_NAME_XP = "//*[self::span[@class = 'Vu-M2 _3Xnho']|self::img[@class = '_2DwmZ']|self::span[@class = '_3BJUh _3kBZk']|self::img[@class = '_2DwmZ _19HY9']]"
PRICE_VAL_XP = "//div[contains(@class,'_3NaXx _1YKgk')]"
CAPTCHA_BUTTON_XP = "//input[contains(@class, 'CheckboxCaptcha-Button')]"
NEXT_PAGE_XP = "//a[contains(@class, '_2prNU _3OFYT')]"
TIMEOUT = 1


def init_browser():
    options = Options()
    options.binary_location = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--headless=new')
    return webdriver.Chrome(options=options)


def get_url_for_page(p_page_num):
    if p_page_num > 1:
        index = SRC_URL.find('local-offers-first=0')
        out_url = SRC_URL[:index] + 'page=' + str(p_page_num) + '&' + SRC_URL[index:]
    else:
        out_url = SRC_URL
    return out_url


def norm_price(p_price):
    return int(p_price.text.replace(" ", "").replace("₽", ""))


def norm_price_vals(p_price_vals):
    return list(map(norm_price, p_price_vals))


def norm_shop_names(p_shop_names):
    out_shop_names = []
    for i in range(len(p_shop_names)):
        if p_shop_names[i].text == '':
            title = p_shop_names[i].get_attribute('title')
            if title != '':
                out_shop_names.append(title)
        else:
            out_shop_names.append(p_shop_names[i].text)
    return out_shop_names


def save_to_csv(p_dict):
    header_lst = ['Название магазина', 'Цена на iphone']
    with open('out_data.csv', 'w', encoding='utf-8-sig') as path_to_file:
        wr = csv.writer(path_to_file)
        wr.writerow(header_lst)
        for sh_n, pr in p_dict.items():
            wr.writerow([sh_n, pr])


def get_page(p_browser, p_url):
    p_browser.get(p_url)
    time.sleep(TIMEOUT)
    if p_browser.find_elements(By.XPATH, CAPTCHA_BUTTON_XP):
        p_browser.find_element(By.XPATH, CAPTCHA_BUTTON_XP).click()
        time.sleep(TIMEOUT)
    return p_browser


def is_last_page(p_browser):
    return p_browser.find_elements(By.XPATH, NEXT_PAGE_XP) == []


def scan_page(p_url):
    p_browser = init_browser()
    p_browser = get_page(p_browser, p_url)
    out_shop_names = norm_shop_names(p_browser.find_elements(By.XPATH, SHOP_NAME_XP))
    out_price_vals = norm_price_vals(p_browser.find_elements(By.XPATH, PRICE_VAL_XP))
    return out_shop_names, out_price_vals


def main():
    t_start = time.perf_counter()
    m_browser = init_browser()  # вспомогательный экземпляр для проверки следующей страцниы
    shop_names = []
    price_vals = []
    futures_lst = []
    stop_scan = False
    page_num = 1
    with ThreadPoolExecutor() as executor:
        while not stop_scan:
            cur_url = get_url_for_page(page_num)
            if is_last_page(get_page(m_browser, cur_url)):
                stop_scan = True
                m_browser.close()
            else:
                futures_lst.append(executor.submit(scan_page, cur_url))
                page_num += 1
            wait(futures_lst)
            for future in futures_lst:
                shop_names += future.result()[0]
                price_vals += future.result()[1]

    print('Shop names len: ' + str(len(shop_names)))
    print('Price vals len: ' + str(len(price_vals)))
    print(shop_names)
    print(price_vals)
    m_data = dict(zip(shop_names, price_vals))
    sort_shops = sorted(m_data, key=m_data.get)
    m_sort_data = {sh_n: m_data[sh_n] for sh_n in sort_shops}
    print(len(m_sort_data))
    save_to_csv(m_sort_data)
    t_total = time.perf_counter() - t_start
    print('time: ' + str(t_total))


if __name__ == '__main__':
    main()
