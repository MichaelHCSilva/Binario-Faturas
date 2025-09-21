import os
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils.vivo_file_utils import wait_for_download_file, move_file
from services.invoice_service import FaturaService

logger = logging.getLogger(__name__)

def process_invoice_menu_button(driver, popup_manager, download_dir, target_folder, skip_existing=True):
    try:
        menu_btn = WebDriverWait(driver, 8, 0.2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-open-dropdown-button='true']"))
        )
        driver.execute_script("arguments[0].click();", menu_btn)

        dropdown = WebDriverWait(driver, 8, 0.2).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu"))
        )

        before_files = set(os.listdir(download_dir))
        links = dropdown.find_elements(By.CSS_SELECTOR, "a")
        boleto_link = next((a for a in links if "Boleto (.pdf)" in a.text), None)

        if boleto_link:
            driver.execute_script("arguments[0].click();", boleto_link)
            pdf_name = wait_for_download_file(download_dir, before_files, extension=".pdf")
            if pdf_name:
                pdf_path = os.path.join(download_dir, pdf_name)
                final_path = move_file(pdf_path, target_folder, f"vivo_{pdf_name}", overwrite=False)
                if final_path:
                    FaturaService(target_folder).processar_fatura_pdf(final_path)

    except TimeoutException:
        logger.info("Menu suspenso não encontrado, nenhuma fatura via menu disponível.")
    except Exception:
        logger.exception("Erro inesperado ao processar menu de faturas")
