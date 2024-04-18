import json
from urllib import parse
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


BASEURL = 'https://megamarket.ru'


def get_pages_html(url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    ITEMS = []
    try:
        for page in range(1, 10):
            print(f"[+] Страница {page}")
            driver.get(url=url.replace(f'page_num', f'page-{page}'))
            WebDriverWait(driver, 60).until(
                ec.presence_of_element_located((By.TAG_NAME, "html")))
            if not get_items(driver.page_source, ITEMS):
                break
    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()
    return ITEMS


def get_items(html, items):
    soup = BeautifulSoup(html, 'html.parser')
    items_divs = soup.find_all('div', class_='catalog-item')
    if len(items_divs) == 0:
        return False
    for item in items_divs:
        link = BASEURL + item.find('a', class_='ddl_product_link').get('href')
        item_price = item.find('div', class_='item-price')
        if item_price:
            item_price_result = item_price.find('span').get_text()
            item_bonus = item.find('div', class_='item-bonus')
            if item_bonus:
                item_bonus_percent = item.find('span', class_='bonus-percent').get_text()
                item_bonus_amount = item.find('span', class_='bonus-amount').get_text()
                item_title = item.find('div', class_='item-title').get_text()
                item_merchant_name = item.find('span', class_='merchant-info__name')
                if item_merchant_name:
                    item_merchant_name = item_merchant_name.get_text()
                else:
                    item_merchant_name = '-'

                bonus = int(item_bonus_amount.replace(' ', ''))
                price = int(item_price_result[0:-1].replace(' ', ''))
                bonus_percent = int(item_bonus_percent.replace('%', ''))
                total_price = price - bonus
                items.append({
                    'Наименование': item_title,
                    'Продавец': item_merchant_name,
                    'Цена': price,
                    'Сумма бонуса': bonus,
                    'Процент бонуса': bonus_percent,
                    'Итоговая цена': total_price,
                    'Ссылка на товар': link
                })
    return True


def save_excel(data: list, filename: str):
    """сохранение результата в excel файл"""
    df = pd.DataFrame(data)
    writer = pd.ExcelWriter(f'{filename}.xlsx')
    df.to_excel(writer, sheet_name='data', index=False)
    # указываем размеры каждого столбца в итоговом файле
    writer.sheets['data'].set_column(0, 1, width=50)
    writer.sheets['data'].set_column(1, 2, width=30)
    writer.sheets['data'].set_column(2, 3, width=8)
    writer.sheets['data'].set_column(3, 4, width=20)
    writer.sheets['data'].set_column(2, 3, width=8)
    writer.sheets['data'].set_column(4, 5, width=15)
    writer.close()
    print(f'Все сохранено в {filename}.xlsx')


def main():
    target = input('Введите название товара: ')
    min_price = input('Минимальная цена (enter, чтобы пропустить): ')
    min_price = min_price if min_price != '' else '0'
    max_price = input('Максимальная цена (enter, чтобы пропустить): ')
    max_price = max_price if max_price != '' else '9999999'
    target_url = f"{BASEURL}/catalog/page_num/?q={target}"
    if max_price and min_price and (max_price.isdigit() and min_price.isdigit()):
        filter = {
            "88C83F68482F447C9F4E401955196697": {"min": int(min_price), "max": int(max_price)},# фильтр по цене
            "4CB2C27EAAFC4EB39378C4B7487E6C9E": ["1"]}# фильтр по наличию товара
        json_data = json.dumps(filter)
        # Кодирование JSON строки для передачи через URL
        url_encoded_data = parse.quote(json_data)
        target_url += '#?filters=' + url_encoded_data

    items = get_pages_html(url=target_url)
    save_excel(items, target)


if __name__ == '__main__':
    main()
