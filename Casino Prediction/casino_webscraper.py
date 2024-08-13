import re
from playwright.sync_api import Playwright, sync_playwright, expect
import pandas as pd
from bs4 import BeautifulSoup
import time

username = " "
password= " "


def extract_data(soup):
    data = []
    rows = soup.find_all('div', class_='van-row')

    for row in rows:
        period = row.find('div', class_='van-col van-col--8')
        period = int(period.text.strip()) if period else None

        sum_value = row.find('div', class_='van-col van-col--1')
        sum_value = sum_value.find('span').text.strip() if sum_value and sum_value.find('span') else None

        big_small = row.find_all('div', class_='van-col van-col--4')
        big_small = big_small[0].find('span').text.strip() if len(big_small) > 0 and big_small[0].find('span') else None

        odd_even = row.find_all('div', class_='van-col van-col--4')
        odd_even = odd_even[1].find('span').text.strip() if len(odd_even) > 1 and odd_even[1].find('span') else None

        data.append([period, sum_value, big_small, odd_even])

    # Create DataFrame
    df = pd.DataFrame(data, columns=['Period', 'Sum', 'Big_Small', 'Odd_Even']).dropna()
    df = df.set_index('Period')

    return df


def page_no(soup):
    pg = soup.find("div", class_ ="GameRecord__C-foot-page")
    page = pg.get_text().split("/")[0]

    return int(page)

def check_index_overlap(df, main_df):
  common_indices = df.index.intersection(main_df.index)
  return not common_indices.empty


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    # page.goto("https://91club-4.com/#/home/AllLotteryGames/K3?id=2")
    page.goto("https://91club-4.com/#/login")
    page.get_by_placeholder("Please enter the phone number").click()
    page.get_by_placeholder("Please enter the phone number").fill(username)
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("checkbox", name=" Remember password").click()
    page.get_by_role("button", name="Log in").click()
    page.get_by_role("button", name="Confirm").click()
    page.locator(".close").click()
    page.get_by_text("K3Guess NumberBig/Small/Odd/").click()

    page.is_visible('div.van-row')   

    time.sleep(2)

    main_df = pd.DataFrame()

    last_page = 1
    max_page = 1
    adjustment_no = 0

    start_time = time.time()
    run_time = 45

    try:

        while (time.time() - start_time) < run_time*60:

            while not page.is_visible('div.van-row'):
                pass

            while page.is_visible('div.van-toast--unclickable'):
                pass
            
            html = page.inner_html('#app')
            soup = BeautifulSoup(html, 'html5lib')
            curr_pg = page_no(soup)
            
            if last_page > curr_pg:
                adjustment_no += 1

            while last_page > curr_pg:

                while not page.is_visible('div.GameRecord__C-foot-next'):
                    pass

                while page.is_visible('div.van-toast--unclickable'):
                    pass
                
                page.locator("i").nth(2).click()

                while not page.is_visible('div.van-row'):
                    pass

                html = page.inner_html('#app')
                soup = BeautifulSoup(html, 'html5lib')
                curr_pg = page_no(soup)

            df = extract_data(soup)

            while len(main_df.index) > 1 and 50 > (abs(int(min(main_df.index))-int(max(df.index)))) > 1 and not check_index_overlap(df, main_df):
                page.locator("i").nth(1).click() # go to previous page again
                html = page.inner_html('#app')
                soup = BeautifulSoup(html, 'html5lib')
                curr_pg = page_no(soup)
                df = extract_data(soup)
                print("Reversing to page: ",curr_pg)


            max_page = max(max_page, curr_pg)

                
            df = extract_data(soup)

            main_df = pd.concat([main_df, df])
            main_df = main_df[~main_df.index.duplicated(keep='first')]

            print(f"Page:{curr_pg} complete, DataFrame size: {len(main_df)}")

            while not page.is_visible('div.GameRecord__C-foot-next'):
                pass
  
            page.locator("i").nth(2).click() # proceed to next page
            last_page = curr_pg
            
            time.sleep(2)
        
    except Exception as e: 
        print("!!! ERROR !!!", e)
        

    main_df = main_df.sort_index(ascending=False)
    main_df.to_excel("K3_data.xlsx")


    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
