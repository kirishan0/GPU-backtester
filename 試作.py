import os
import random
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options


# ルートフォルダと一時フォルダの設定
root_folder = r"C:\Users\kiris\OneDrive\デスクトップ\kakak"

# フォルダが存在するか確認
if not os.path.exists(root_folder):
    print(f"エラー: 指定されたルートフォルダが見つかりません: {root_folder}")
else:
    print(f"ルートフォルダが見つかりました: {root_folder}")



# Chromeオプションの設定
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--remote-debugging-port=9222")  # 必要に応じて追加
chrome_options.add_argument("--headless")  # GUI不要であればheadlessモードで

# WebDriverの初期設定
driver = webdriver.Chrome()
driver.set_window_position(-3, 0)
driver.set_window_size(1114, 1047)

# Bufferにログイン
driver.get('https://publish.buffer.com/all-channels')
# emailフィールドが表示されるまで待機
email_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "email")))
email_field.send_keys("kegunari555@gmail.com")
# passwordフィールドが表示されるまで待機
password_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "password")))
password_field.send_keys("kiRITO2486")
# ログインボタンが表示されるまで待機してクリック
login_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[text()='Log In']")))
login_button.click()

print("ログイン完了")


# 各アカウント項目を取得
account_items = WebDriverWait(driver, 50).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.publish_item_ua650[id]"))
)

# New Postボタンをクリック
def 各NewPostボタン(account):
    WebDriverWait(driver, 10).until(EC.visibility_of(account))
    hover = ActionChains(driver).move_to_element(account)
    hover.perform()
    new_post_button = WebDriverWait(account, 10).until(
        EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class, 'publish_newPostButton_5mOHJ')]"))
    )
    new_post_button.click()

# テキスト入力
def テキスト入力(text_to_input):
    text_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@role='textbox' and @contenteditable='true']"))
    )

    # 確定のためにEnterキーを送信
    text_box.send_keys(text_to_input)


# メディアアップロード
def メディアアップロード(file_paths):
    for file_path in file_paths:
        upload_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][data-testid='uploads-dropzone-input']"))
        )
        # アップロード前にinput要素をクリア
        driver.execute_script("arguments[0].value = '';", upload_input)
        
        print(file_path)
        upload_input.send_keys(file_path)
        print(f"{file_path}のアップロードが開始されました")

        # アップロードが完了するまでの待機
        WebDriverWait(driver, 50).until(アップロード完了待機)

    # 全体のアップロード完了の待機
    WebDriverWait(driver, 20).until(lambda d: メディアアップロード待機(file_paths))
    print("メディアのアップロード完了")


def アップロード完了待機(driver):
    try:
        # アップロードの進行状況を確認する要素を取得
        progress_circle = driver.find_element(By.CSS_SELECTOR, "circle.publish_circle_Pnqgz")
        progress_text = driver.find_element(By.CSS_SELECTOR, "span.publish_progressText_1f6x-")

        # stroke-dashoffsetが0になり、かつテキストが「Finishing up…」になるのを確認
        circle_offset = progress_circle.get_attribute("style")
        text_content = progress_text.text

        print(f"{text_content}\n{circle_offset}")

        # アップロードが完了すると条件が一致し、要素がすぐに消えるので、完了後の消失を確認
        return "stroke-dashoffset: 0;" in circle_offset and text_content == "Finishing up…"
    except:
        # 要素が消えた場合もアップロードが完了したとみなす
        return True

# アップロード完了を確認する関数
def メディアアップロード待機(file_paths):
    time.sleep(2)
    uploaded_images = driver.find_elements(By.CSS_SELECTOR, "img.publish_thumbnailImage_FPqna")
    return len(uploaded_images) == len(file_paths)

# カレンダーを開く
def カレンダー開く():

    #メニューから "Schedule Draft" を選択してクリック
    schedule_draft_option = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "SCHEDULE_POST"))
    )
    # JavaScriptを使用して直接クリック
    driver.execute_script("arguments[0].click();", schedule_draft_option)

# カレンダーの日付を設定
def カレンダー設定(target_year, target_month, target_day):
    date_obj = datetime.date(target_year, target_month, target_day)
    weekday = date_obj.strftime("%a")
    month_name = date_obj.strftime("%B")
    padded_day = f"{target_day:02}" 

    current_month_year = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@class='DayPicker-Month']//span"))
    ).text

    while f"{month_name} {target_year}" != current_month_year:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@style='float: right;']/button"))
        )
        next_button.click()
        current_month_year = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@class='DayPicker-Month']//span"))
        ).text

    target_date = f"{weekday} {date_obj.strftime('%b')} {padded_day} {target_year}"
    print(target_date)
    date_element = WebDriverWait(driver, 500).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"div[aria-label='{target_date}']"))
    )
    date_element.click()

target_date = datetime.date.today()

# ランダム日時設定
def ランダム日時設定():
    global target_date
    day_increment = 1 if random.random() < 0.3 else 2
    target_date += datetime.timedelta(days=day_increment)
    
    hour = random.choice([0, 1, 2, 21, 22, 23])  # 0-2時または21-23時
    minute = random.randint(0, 59)

    カレンダー設定(target_date.year, target_date.month, target_date.day)
    時間設定(str(hour), str(minute))

# 時間設定
def 時間設定(target_hour, target_minute):

        # 時間セレクトボックスが見つかるまで待機
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "select.sc-jztukc.sc-jhJOaJ.eGgwrh.jZYDGj"))
    )

    hour_select = Select(driver.find_elements(By.CSS_SELECTOR, "select.sc-jztukc.sc-jhJOaJ.eGgwrh.jZYDGj")[0])
    hour_select.select_by_value(target_hour)
    minute_select = Select(driver.find_elements(By.CSS_SELECTOR, "select.sc-jztukc.sc-jhJOaJ.eGgwrh.jZYDGj")[1])
    minute_select.select_by_value(target_minute)

# ドラフト追加ボタンをクリック
def キュー追加():
    add_draft_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".sc-kgvGAC.dzYuwC .publish_base_GTmOA"))
    )
    add_draft_button.click()

# メイン処理
def ツイート予約(account_items):
    global target_date
    for account in account_items:
        # 処理済みリストの初期化
        processed_folders = []
        target_date = datetime.date.today()
        # 各アカウントで未処理フォルダのリストを取得
        folder_list = [os.path.join(root_folder, d) for d in os.listdir(root_folder)
                        if os.path.isdir(os.path.join(root_folder, d)) and d.isdigit()]
        
        random.shuffle(folder_list)

        for folder in folder_list:
            folder_name = os.path.basename(folder)
            if folder_name in processed_folders:
                continue

            # テキストと画像の収集
            combined_text = ""
            image_files = []
            for file_name in os.listdir(folder):
                file_path = os.path.join(folder, file_name)
                if file_name.endswith(".txt"):
                    with open(file_path, "r", encoding="utf-8") as txt_file:
                        combined_text += txt_file.read()
                elif file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                    image_files.append(file_path)

            # 投稿処理
            各NewPostボタン(account)
            print(combined_text)
            テキスト入力(combined_text)
            メディアアップロード(image_files)
            カレンダー開く()
            ランダム日時設定()
            キュー追加()

            # 処理済みフォルダを追加
            processed_folders.append(folder_name)
            print(f"フォルダ '{folder_name}' の内容がアカウント '{account}' に投稿されました。")
            time.sleep(0.5)  # 各投稿間の待機時間

        print(f"アカウント {account} の処理が完了しました")

# 実行
ツイート予約(account_items)
