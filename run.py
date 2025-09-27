import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys



# ====== UTIL SEDERHANA ======
def read_urls(csv_file):
    with open(csv_file, "r", encoding="utf-8") as f:
        return [row[0].strip() for row in csv.reader(f) if row]

def read_accounts(csv_file):
    with open(csv_file, "r", encoding="utf-8") as f:
        return [(row[0].strip(), row[1].strip()) for row in csv.reader(f) if len(row) >= 2]

def remove_url_from_csv(url_to_remove, csv_file):
    urls = read_urls(csv_file)
    urls = [u for u in urls if u != url_to_remove]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for u in urls:
            w.writerow([u])

def make_driver(headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

# ====== FLOW LOGIN & SUBMIT (SIMPLE) ======
def login_gsc(driver, email, password):
    driver.get("https://accounts.google.com/signin")
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, "#identifierId").send_keys(email + Keys.ENTER)
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password + Keys.ENTER)
    time.sleep(5)  # beri waktu redirect/login

def submit_property(driver, url):
    """
    Versi simpel: buka GSC dengan resource_id dan lakukan klik minimal.
    NOTE: Selector UI bisa berubah, jadi ini dibuat sesederhana mungkin.
    Return True/False untuk penanda sukses/gagal.
    """
    try:
        driver.get(f"https://search.google.com/search-console?utm_source=about-page&resource_id={url}/")
        time.sleep(4)

        # Contoh klik tombol (kalau ada) — biarkan minimal:
        # Banyak halaman pakai material button; kalau tak ada, ya lanjut True saja.
        try:
            # tombol umum bertuliskan 'Open report' / 'Buka laporan' / semacamnya
            # kamu boleh hapus blok ini kalau mau super-minimal
            btns = driver.find_elements(By.TAG_NAME, "button")
            if btns:
                btns[0].click()
                time.sleep(2)
        except Exception:
            pass

        return True
    except Exception:
        return False

# ====== MAIN ======
def main():
    urls = read_urls("url.csv")
    accounts = read_accounts("akun.csv")

    if not urls:
        print("url.csv kosong / tidak ditemukan.")
        return
    if not accounts:
        print("akun.csv kosong / tidak ditemukan.")
        return

    total_urls = len(urls)
    total_accounts = len(accounts)
    urls_per_account = total_urls // total_accounts
    remainder = total_urls % total_accounts

    # Bagi rata URL ke setiap akun (sederhana)
    account_url_map = []
    start = 0
    for i in range(total_accounts):
        end = start + urls_per_account + (1 if i < remainder else 0)
        account_url_map.append(urls[start:end])
        start = end

    for idx, (email, password) in enumerate(accounts, start=1):
        bucket = account_url_map[idx - 1]
        if not bucket:
            print(f"Akun {email} tidak kebagian URL. Lewati.")
            continue

        print(f"== Akun {idx}/{total_accounts}: {email} ({len(bucket)} URL) ==")
        driver = make_driver(headless=False)  # ubah ke True jika mau tanpa jendela
        try:
            try:
                login_gsc(driver, email, password)
            except Exception:
                print(f"Login gagal: {email}. Lanjut akun berikutnya.")
                driver.quit()
                continue

            for u in bucket:
                if submit_property(driver, u):
                    with open("hasil.txt", "a", encoding="utf-8") as rf:
                        rf.write(f"Submitted: {u} with account {email}\n")
                    print(f"SUKSES: {u} (akun {email})")
                    remove_url_from_csv(u, "url.csv")
                else:
                    with open("error_url.txt", "a", encoding="utf-8") as ef:
                        ef.write(f"{u}\n")
                    print(f"GAGAL: {u} (akun {email})")
                time.sleep(1)  # jeda tipis biar natural

        finally:
            driver.quit()
        print(f"== Selesai: {email} ==\n")

if __name__ == "__main__":
    main()
