import os
import shutil
import zipfile
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException, TimeoutException,
    NoSuchElementException, ElementClickInterceptedException
)

from utils.popUpClaro import PopupHandler
from utils.sessionManager import ensure_logged_in  

TEMP_DOWNLOAD_FOLDER = os.path.join(
    os.path.expanduser("~"), "OneDrive", "Documentos", "Binario-Faturas", "faturas_temp"
)

def wait_for_new_file(folder, previous_files, timeout=15, extension=".pdf"):
    end_time = time.time() + timeout
    while time.time() < end_time:
        files = set(os.listdir(folder)) - previous_files
        for f in files:
            if f.endswith(extension) and not f.endswith(".crdownload"):
                return f
        time.sleep(0.1)
    return None

def wait_for_download_complete(path, timeout=15):
    end_time = time.time() + timeout
    while time.time() < end_time:
        if os.path.exists(path) and not path.endswith(".crdownload"):
            return True
        time.sleep(0.1)
    return False

def process_invoice_menu_button(driver, popup_handler, target_folder):
    try:
        menu_btn = WebDriverWait(driver, 3, 0.1).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-open-dropdown-button='true']"))
        )
        driver.execute_script("arguments[0].click();", menu_btn)
        dropdown = WebDriverWait(driver, 3, 0.1).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu"))
        )

        before_files = set(os.listdir(TEMP_DOWNLOAD_FOLDER))
        links = dropdown.find_elements(By.CSS_SELECTOR, "a")
        boleto_link = next((a for a in links if "Boleto (.pdf)" in a.text), None)

        if boleto_link:
            driver.execute_script("arguments[0].click();", boleto_link)
            pdf_name = wait_for_new_file(TEMP_DOWNLOAD_FOLDER, before_files)
            if pdf_name:
                pdf_path = os.path.join(TEMP_DOWNLOAD_FOLDER, pdf_name)
                wait_for_download_complete(pdf_path)
                shutil.move(pdf_path, os.path.join(target_folder, f"vivo_{pdf_name}"))
                print(f"Fatura PDF movida: {pdf_name}")
        else:
            print("Link 'Boleto (.pdf)' não encontrado no menu suspenso.")

    except Exception as e:
        print(f"Erro ao tentar baixar via menu suspenso: {type(e).__name__} - {e}")

def download_invoices_from_page(driver, popup_handler, target_folder, cnpj, login_page=None, usuario=None, senha=None, reopen_customer_fn=None):
    try:
        rows = WebDriverWait(driver, 5, 0.1).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.mve-grid-row"))
        )
    except TimeoutException:
        print("Nenhum grid de faturas encontrado, tentando menu suspenso.")
        process_invoice_menu_button(driver, popup_handler, target_folder)
        return

    def already_downloaded(invoice):
        try:
            customer = invoice.find_element(By.CSS_SELECTOR, "div[data-test-secondary-info] span").text.strip()
            due = invoice.find_element(By.CSS_SELECTOR, "div[data-test-invoice-due-date]").text.strip().replace("/", "")
            pdf_name = f"vivo_{customer}_{due}.pdf"
            return os.path.exists(os.path.join(target_folder, pdf_name))
        except Exception:
            return False

    pending = [
        r for r in rows
        if not r.find_elements(By.CSS_SELECTOR, ".invoice-due-date-label-paid")
        and r.find_elements(By.XPATH, ".//button[contains(., 'Baixar agora')]")
        and not already_downloaded(r)
    ]
    if not pending:
        print("Nenhuma fatura pendente ou já baixada")
        return

    popup_handler.close_known_popups()  

    for i, invoice in enumerate(pending, 1):
        print(f"Fatura {i}/{len(pending)}")
        attempts = 0
        while attempts < 3:
            try:
                if login_page and usuario and senha:
                    session_active = ensure_logged_in(driver, login_page, usuario, senha, reopen_customer_fn, cnpj)
                    if session_active:
                        print("Sessão renovada. Continuando downloads...")
                        time.sleep(1)

                        rows = driver.find_elements(By.CSS_SELECTOR, "div.mve-grid-row")
                        pending = [
                            r for r in rows
                            if not r.find_elements(By.CSS_SELECTOR, ".invoice-due-date-label-paid")
                            and r.find_elements(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                            and not already_downloaded(r)
                        ]
                        if i-1 < len(pending):
                            invoice = pending[i-1]
                        else:
                            print("Todas as faturas já baixadas após relogin")
                            break

                before_files = set(os.listdir(TEMP_DOWNLOAD_FOLDER))  
                btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                driver.execute_script("arguments[0].click();", btn)

                try:
                    zip_btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Todas em boleto (.zip)')]")
                    driver.execute_script("arguments[0].click();", zip_btn)
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
                            pdf_path = os.path.join(TEMP_DOWNLOAD_FOLDER, f)
                            wait_for_download_complete(pdf_path)
                            shutil.move(pdf_path, os.path.join(target_folder, f"vivo_{customer}_{due}.pdf"))
                    break

                except NoSuchElementException:
                    pdf_btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Boleto (.pdf)')]")
                    driver.execute_script("arguments[0].click();", pdf_btn)
                    pdf_name = wait_for_new_file(TEMP_DOWNLOAD_FOLDER, before_files, extension=".pdf")
                    if not pdf_name:
                        break

                    pdf_path = os.path.join(TEMP_DOWNLOAD_FOLDER, pdf_name)
                    wait_for_download_complete(pdf_path)

                    customer = invoice.find_element(By.CSS_SELECTOR, "div[data-test-secondary-info] span").text.strip()
                    due = invoice.find_element(By.CSS_SELECTOR, "div[data-test-invoice-due-date]").text.strip().replace("/", "")
                    shutil.move(pdf_path, os.path.join(target_folder, f"vivo_{customer}_{due}.pdf"))
                    break

            except (ElementClickInterceptedException, StaleElementReferenceException):
                print("Click bloqueado ou elemento obsoleto, tentando novamente...")
                time.sleep(0.1)
                attempts += 1
            except Exception as e:
                print("Erro inesperado ao baixar fatura:", type(e).__name__, e)
                break

def download_all_paginated_invoices(driver, popup_handler, base_folder, cnpj, login_page=None, usuario=None, senha=None, reopen_customer_fn=None):
    target_folder = os.path.join(base_folder, "Vivo", cnpj.replace(".", "").replace("/", "-"))
    os.makedirs(target_folder, exist_ok=True)
    os.makedirs(TEMP_DOWNLOAD_FOLDER, exist_ok=True)

    try:
        WebDriverWait(driver, 3, 0.1).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[data-test-dont-have-account-message-wireline]")
        ))
        driver.find_element(By.CSS_SELECTOR, "button[data-test-redirect-dashboard-button]").click()
        print("Nenhuma fatura disponível")
        return
    except TimeoutException:
        pass

    first = ""
    try:
        first = WebDriverWait(driver, 4, 0.1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span"))
        ).text.strip()
    except Exception:
        pass

    page = 1
    while True:
        print(f"Page {page}")

        if login_page and usuario and senha:
            ensure_logged_in(driver, login_page, usuario, senha, reopen_customer_fn, cnpj)

        download_invoices_from_page(driver, popup_handler, target_folder, cnpj, login_page, usuario, senha, reopen_customer_fn)

        try:
            btn = WebDriverWait(driver, 3, 0.1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.button--pagination-next > button"))
            )
            if not btn.is_enabled():
                break
            driver.execute_script("arguments[0].click();", btn)

            WebDriverWait(driver, 5, 0.1).until(
                lambda d: d.find_element(By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span").text.strip() != first
            )
            first = driver.find_element(By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span").text.strip()
            page += 1
        except Exception:
            break
