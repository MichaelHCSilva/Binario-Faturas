import os
import time
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils.popup_manager import PopupManager
from utils.session_manager_vivo import ensure_logged_in
from pages.vivo.vivo_logging import logger, log_stats
from pages.vivo.vivo_invoice_page import download_invoices_from_page
from utils.json_failure_logger import JsonFailureLogger

def download_all_paginated_invoices(driver, popup_manager, download_dir, base_folder, cnpj,
                                    login_page=None, usuario=None, senha=None,
                                    reopen_customer_fn=None, skip_existing=True):
    global log_stats
    log_stats["total"] = 0
    log_stats["sucesso"] = 0
    log_stats["falha"] = 0
    log_stats["falhas"].clear()

    target_folder = os.path.join(base_folder, "Vivo", cnpj.replace(".", "").replace("/", "-"))
    os.makedirs(target_folder, exist_ok=True)

    failure_logger = JsonFailureLogger()

    page = 1
    first = ""

    attempts = 0
    while attempts < 2:
        try:
            first = WebDriverWait(driver, 15, 0.3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span")
                )
            ).text.strip()
            break
        except TimeoutException:
            attempts += 1
            if attempts == 1:
                logger.info("Nenhuma fatura visível, tentando refresh...")
                driver.refresh()
                time.sleep(1)
            elif attempts == 2 and reopen_customer_fn:
                logger.info("Nenhuma fatura visível, reabrindo cliente...")
                try:
                    reopen_customer_fn(driver, cnpj)
                    time.sleep(1)
                except Exception:
                    logger.exception("Erro ao reabrir cliente")
            else:
                dados_falha = {
                    "cliente": cnpj,
                    "pagina": page,
                    "posicao": None,
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "erro": "Nenhuma fatura disponível nesta conta"
                }
                failure_logger.registrar_falha_vivo(dados_falha)
                logger.info("Nenhuma fatura disponível nesta conta.")
                return

    while True:
        if login_page and usuario and senha:
            ensure_logged_in(driver, login_page, usuario, senha)

        download_invoices_from_page(driver, popup_manager, download_dir, target_folder, cnpj,
                                    login_page, usuario, senha, reopen_customer_fn, skip_existing,
                                    page_number=page)

        try:
            next_btn = WebDriverWait(driver, 8, 0.2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.button--pagination-next > button"))
            )
            if not next_btn.is_enabled():
                break
            driver.execute_script("arguments[0].click();", next_btn)

            WebDriverWait(driver, 15, 0.3).until(
                lambda d: d.find_element(
                    By.CSS_SELECTOR,
                    "div.mve-grid-row:first-of-type div[data-test-secondary-info] span"
                ).text.strip() != first
            )
            first = driver.find_element(
                By.CSS_SELECTOR,
                "div.mve-grid-row:first-of-type div[data-test-secondary-info] span"
            ).text.strip()
            page += 1
        except TimeoutException:
            break
        except Exception as e:
            dados_falha = {
                "cliente": cnpj,
                "pagina": page,
                "posicao": None,
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "erro": f"Erro ao navegar para a próxima página: {str(e)}"
            }
            failure_logger.registrar_falha_vivo(dados_falha)
            logger.exception("Erro ao navegar para a próxima página")
            break

    logger.info(f"Download concluído: {log_stats['total']} faturas processadas, "
                f"{log_stats['sucesso']} inseridas com sucesso, {log_stats['falha']} falhas\n")

    if log_stats["falha"] > 0:
        logger.info("Resumo das falhas:")
        for falha in log_stats["falhas"]:
            logger.info(falha)
            failure_logger.registrar_falha(falha)
