# claro_pending_invoices_page
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import locale

logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

class FaturasPendentesPage:
    def __init__(self, driver, timeout=30):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def _obter_mes_ano_atual_e_anterior(self) -> Tuple[Tuple[str,int], Tuple[str,int]]:
        hoje = datetime.today()
        mes_atual, ano_atual = hoje.strftime('%B').lower(), hoje.year
        mes_anterior_data = hoje.replace(day=1) - timedelta(days=1)
        mes_anterior, ano_anterior = mes_anterior_data.strftime('%B').lower(), mes_anterior_data.year
        return (mes_atual, ano_atual), (mes_anterior, ano_anterior)

    def _normalizar_texto(self, texto: str) -> str:
        return texto.strip().lower()

    def _clicar_aba_mes(self, mes, ano) -> bool:
        xpath_aba = f"//li[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{mes}') and contains(., '{ano}')]"
        try:
            aba = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_aba)))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", aba)
            self.driver.execute_script("arguments[0].click();", aba)
            return True
        except TimeoutException:
            return False

    def _buscar_faturas_pendentes(self, mes, ano) -> List:
        try: 
            self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "invoice-list-item")))
        except TimeoutException: 
            return []
        
        faturas_pendentes = []
        mes_ano_str = f"{mes} {ano}".lower()
        
        for f in self.driver.find_elements(By.CLASS_NAME, "invoice-list-item"):
            try:
                titulo = self._normalizar_texto(f.find_element(By.CLASS_NAME, "invoice-list-item__content-infos-text--title").text)
                status_texto = self._normalizar_texto(f.find_element(By.CLASS_NAME, "status-tag").text)
                
                if mes_ano_str in titulo and (status_texto == 'aguardando' or status_texto == 'vencida'): 
                    faturas_pendentes.append(f)
            except Exception: 
                continue
        
        return faturas_pendentes

    def selecionar_e_baixar_fatura(self) -> Optional[str]:
        (mes_atual, ano_atual), (mes_anterior, ano_anterior) = self._obter_mes_ano_atual_e_anterior()
        for mes, ano in [(mes_atual, ano_atual), (mes_anterior, ano_anterior)]:
            if self._clicar_aba_mes(mes, ano):
                faturas = self._buscar_faturas_pendentes(mes, ano)
                if faturas:
                    f = faturas[0]
                    try:
                        botao = f.find_element(By.XPATH, ".//a[contains(text(), 'Selecionar')]")
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", botao)
                        self.wait.until(EC.element_to_be_clickable(botao)).click()
                        download_link = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="download-invoice"]')))
                        nome_arquivo = download_link.get_attribute("download")
                        self.driver.execute_script("arguments[0].click();", download_link)
                        return nome_arquivo
                    except Exception: 
                        continue
        return None
