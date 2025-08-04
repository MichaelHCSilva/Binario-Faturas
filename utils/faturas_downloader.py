from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException, TimeoutException,
    NoSuchElementException, ElementClickInterceptedException
)
import time
import os
import shutil
import zipfile

TEMP_DOWNLOAD_FOLDER = os.path.join(
    os.path.expanduser("~"), "OneDrive", "Documentos", "Binario-Faturas", "faturas_temp"
)

def close_generic_popups(driver, max_wait=2):
    selectors = [
        "button[data-qsi-creative-button-type='close']",
        "button[data-test-dialog-button='cancelar-download']"
    ]
    for sel in selectors:
        try:
            btn = WebDriverWait(driver, max_wait).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click()
            print("✅ Popup closed:", sel)
            return True
        except TimeoutException:
            continue
    return False

def wait_for_new_file(folder, previous_files, timeout=20, extension=".pdf"):
    start = time.time()
    while time.time() - start < timeout:
        new_files = set(os.listdir(folder)) - previous_files
        for f in new_files:
            if f.endswith(extension) and not f.endswith(".crdownload"):
                return f
        time.sleep(0.2)
    return None

def wait_for_download_complete(path, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(path) and not path.endswith(".crdownload"):
            return True
        time.sleep(0.2)
    return False

def process_invoice_menu_button(driver, target_folder):
    try:
        menu_btn = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-open-dropdown-button='true']"))
        )
        menu_btn.click()
        dropdown = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu"))
        )

        before_files = set(os.listdir(TEMP_DOWNLOAD_FOLDER))

        # Corrigido: procurar pelo link com texto "Boleto (.pdf)"
        links = dropdown.find_elements(By.CSS_SELECTOR, "a")
        boleto_link = next((a for a in links if "Boleto (.pdf)" in a.text), None)

        if boleto_link:
            boleto_link.click()
            pdf_name = wait_for_new_file(TEMP_DOWNLOAD_FOLDER, before_files, extension=".pdf")
            if pdf_name:
                pdf_path = os.path.join(TEMP_DOWNLOAD_FOLDER, pdf_name)
                wait_for_download_complete(pdf_path)
                shutil.move(pdf_path, os.path.join(target_folder, f"vivo_{pdf_name}"))
                print(f"✅ Fatura PDF movida: {pdf_name}")
        else:
            print("⚠️ Link 'Boleto (.pdf)' não encontrado no menu suspenso.")

    except Exception as e:
        print(f"⚠️ Erro ao tentar baixar via menu suspenso: {type(e).__name__} - {e}")



def download_invoices_from_page(driver, target_folder, cnpj):
    try:
        try:
            rows = WebDriverWait(driver, 6).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.mve-grid-row"))
            )
        except TimeoutException:
            print("⚠️ Nenhum grid de faturas encontrado, tentando menu suspenso.")
            process_invoice_menu_button(driver, target_folder)
            return

        pending = [
            r for r in rows
            if not r.find_elements(By.CSS_SELECTOR, ".invoice-due-date-label-paid")
            and r.find_elements(By.XPATH, ".//button[contains(., 'Baixar agora')]")
        ]
        if not pending:
            print("✅ No pending invoices")
            return

        for i, invoice in enumerate(pending, 1):
            print(f"📌 Invoice {i}/{len(pending)}")
            for attempt in range(2):
                try:
                    close_generic_popups(driver)
                    btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    WebDriverWait(driver, 3).until(EC.element_to_be_clickable(btn)).click()
                    WebDriverWait(driver, 4).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu.show"))
                    )

                    before_files = set(os.listdir(TEMP_DOWNLOAD_FOLDER))
                    try:
                        zip_btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Todas em boleto (.zip)')]")
                        zip_btn.click()
                        zip_name = wait_for_new_file(TEMP_DOWNLOAD_FOLDER, before_files, extension=".zip")
                        if not zip_name:
                            break

                        zip_path = os.path.join(TEMP_DOWNLOAD_FOLDER, zip_name)
                        wait_for_download_complete(zip_path)

                        with zipfile.ZipFile(zip_path, 'r') as z:
                            z.extractall(TEMP_DOWNLOAD_FOLDER)
                        os.remove(zip_path)

                        customer = invoice.find_element(By.CSS_SELECTOR, "div[data-test-secondary-info] span").text.strip()
                        due = invoice.find_element(By.CSS_SELECTOR, "div[data-test-invoice-due-date]").text.strip().replace("/", "")
                        for f in os.listdir(TEMP_DOWNLOAD_FOLDER):
                            if f.endswith(".pdf"):
                                shutil.move(
                                    os.path.join(TEMP_DOWNLOAD_FOLDER, f),
                                    os.path.join(target_folder, f"vivo_{customer}_{due}.pdf")
                                )
                        break

                    except NoSuchElementException:
                        pdf_btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Boleto (.pdf)')]")
                        pdf_btn.click()
                        pdf_name = wait_for_new_file(TEMP_DOWNLOAD_FOLDER, before_files, extension=".pdf")
                        if not pdf_name:
                            break

                        pdf_path = os.path.join(TEMP_DOWNLOAD_FOLDER, pdf_name)
                        wait_for_download_complete(pdf_path)

                        customer = invoice.find_element(By.CSS_SELECTOR, "div[data-test-secondary-info] span").text.strip()
                        due = invoice.find_element(By.CSS_SELECTOR, "div[data-test-invoice-due-date]").text.strip().replace("/", "")
                        shutil.move(pdf_path, os.path.join(target_folder, f"vivo_{customer}_{due}.pdf"))
                        break

                except ElementClickInterceptedException:
                    print("⚠️ Click blocked, retrying...")
                    close_generic_popups(driver)
                except Exception as e:
                    print("⚠️ Error:", type(e).__name__, e)
                    break

    except Exception as e:
        print("❌ General failure:", type(e).__name__, e)

def download_all_paginated_invoices(driver, base_folder, cnpj):
    target_folder = os.path.join(base_folder, "Vivo", cnpj.replace(".", "").replace("/", "-"))
    os.makedirs(target_folder, exist_ok=True)
    os.makedirs(TEMP_DOWNLOAD_FOLDER, exist_ok=True)

    try:
        WebDriverWait(driver, 4).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[data-test-dont-have-account-message-wireline]")
        ))
        driver.find_element(By.CSS_SELECTOR, "button[data-test-redirect-dashboard-button]").click()
        print("✅ No invoices available")
        return
    except TimeoutException:
        pass

    try:
        first = WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span"))
        ).text.strip()
    except Exception:
        first = ""

    page = 1
    while True:
        print(f"📄 Page {page}")
        download_invoices_from_page(driver, target_folder, cnpj)
        close_generic_popups(driver)

        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.button--pagination-next > button"))
            )
            if not btn.is_enabled():
                break
            driver.execute_script("arguments[0].scrollIntoView(false);", btn)
            btn.click()

            WebDriverWait(driver, 8).until(
                lambda d: d.find_element(By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span").text.strip() != first
            )
            first = driver.find_element(By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span").text.strip()
            page += 1
        except Exception:
            break
