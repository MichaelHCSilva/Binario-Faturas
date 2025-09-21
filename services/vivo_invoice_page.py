import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)

from utils.vivo_file_utils import wait_for_download_file, move_file, extract_zip
from services.invoice_service import FaturaService
from services.vivo_logging import log_fatura
from services.vivo_menu_handler import process_invoice_menu_button

logger = logging.getLogger(__name__)

def download_invoices_from_page(driver, popup_manager, download_dir, target_folder, cnpj,
                                login_page=None, usuario=None, senha=None,
                                reopen_customer_fn=None, skip_existing=True, page_number=1):

    attempts = 0
    rows = []
    while attempts < 2:
        try:
            rows = WebDriverWait(driver, 15, 0.3).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.mve-grid-row"))
            )
            break
        except TimeoutException:
            attempts += 1
            if attempts == 1:
                logger.info(f"Página {page_number}: nenhuma fatura visível, tentando refresh...")
                driver.refresh()
                time.sleep(1)
            elif attempts == 2 and reopen_customer_fn:
                logger.info(f"Página {page_number}: reabrindo cliente...")
                try:
                    reopen_customer_fn(driver, cnpj)
                    time.sleep(1)
                except Exception:
                    logger.exception("Erro ao reabrir cliente")
            else:
                logger.info(f"Nenhuma fatura disponível na página {page_number}.")
                process_invoice_menu_button(driver, popup_manager, download_dir, target_folder, skip_existing)
                return

    popup_manager.handle_all()

    def already_downloaded(invoice):
        if not skip_existing:
            return False
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
        logger.info(f"Nenhuma fatura pendente na página {page_number}.\n")
        return

    logger.info(f"Página {page_number}")
    total_page = len(pending)

    for i, invoice in enumerate(pending, 1):
        pdf_name = "desconhecido.pdf"
        try:
            customer = invoice.find_element(By.CSS_SELECTOR, "div[data-test-secondary-info] span").text.strip()
            due = invoice.find_element(By.CSS_SELECTOR, "div[data-test-invoice-due-date]").text.strip().replace("/", "")
            pdf_name = f"vivo_{customer}_{due}.pdf"
        except Exception:
            pass

        success = False
        for attempt in range(2):
            try:
                before_files = set(os.listdir(download_dir))
                btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                driver.execute_script("arguments[0].click();", btn)

                try:
                    zip_btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Todas em boleto (.zip)')]")
                    driver.execute_script("arguments[0].click();", zip_btn)
                    zip_name = wait_for_download_file(download_dir, before_files, extension=".zip")
                    if zip_name:
                        zip_path = os.path.join(download_dir, zip_name)
                        extract_zip(zip_path, download_dir)
                        os.remove(zip_path)

                        for f in os.listdir(download_dir):
                            if f.endswith(".pdf"):
                                pdf_path = os.path.join(download_dir, f)
                                final_path = move_file(pdf_path, target_folder, pdf_name, overwrite=False)
                                if final_path:
                                    FaturaService(target_folder).processar_fatura_pdf(final_path)
                                    log_fatura(page_number, i, total_page, pdf_name, sucesso=True)
                                else:
                                    log_fatura(page_number, i, total_page, pdf_name, sucesso=False,
                                               motivo="não cadastrada no banco")
                        success = True
                        break

                except NoSuchElementException:
                    pdf_btn = invoice.find_element(By.XPATH, ".//button[contains(., 'Boleto (.pdf)')]")
                    driver.execute_script("arguments[0].click();", pdf_btn)
                    pdf_name_downloaded = wait_for_download_file(download_dir, before_files, extension=".pdf")
                    if pdf_name_downloaded:
                        pdf_path = os.path.join(download_dir, pdf_name_downloaded)
                        final_path = move_file(pdf_path, target_folder, pdf_name, overwrite=False)
                        if final_path:
                            FaturaService(target_folder).processar_fatura_pdf(final_path)
                            log_fatura(page_number, i, total_page, pdf_name, sucesso=True)
                        else:
                            log_fatura(page_number, i, total_page, pdf_name, sucesso=False,
                                       motivo="não cadastrada no banco")
                        success = True
                        break

            except (ElementClickInterceptedException, StaleElementReferenceException):
                time.sleep(0.3)
            except Exception:
                log_fatura(page_number, i, total_page, pdf_name, sucesso=False, motivo="erro inesperado")
                logger.exception("Erro inesperado ao baixar fatura")
                break

        if not success:
            log_fatura(page_number, i, total_page, pdf_name, sucesso=False, motivo="falhou após 2 tentativas")
