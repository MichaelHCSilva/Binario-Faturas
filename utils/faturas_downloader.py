# utils/faturas_downloader.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import os
import shutil
import zipfile
import re
from datetime import datetime

# Define a pasta de download temporário
PASTA_DOWNLOAD_TEMP = os.path.join(os.path.expanduser("~"), "OneDrive", "Documentos", "Binario-Faturas", "faturas_temp")

def fechar_popups_genericos(driver, tempo_max=5):
    """Tenta fechar diferentes tipos de pop-ups que podem interceptar cliques."""
    try:
        # Tenta fechar o pop-up de feedback da Qualtrics (QSI)
        fechar_qsi_btn = WebDriverWait(driver, tempo_max).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qsi-creative-button-type='close']"))
        )
        fechar_qsi_btn.click()
        print("✅ Pop-up de feedback (QSI) detectado e fechado.")
        time.sleep(1)
        return True
    except TimeoutException:
        pass

    try:
        # Tenta fechar o pop-up de aviso de download
        fechar_aviso_btn = WebDriverWait(driver, tempo_max).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-dialog-button='cancelar-download']"))
        )
        fechar_aviso_btn.click()
        print("✅ Pop-up de aviso de download detectado e fechado.")
        time.sleep(1)
        return True
    except TimeoutException:
        pass
    
    return False

def arquivos_na_pasta(caminho):
    """Retorna um conjunto de nomes de arquivos em uma pasta."""
    try:
        return set(os.listdir(caminho))
    except FileNotFoundError:
        return set()

def esperar_novo_arquivo(pasta, arquivos_antes, tempo_max=90, extensao=".pdf"):
    """Espera por um novo arquivo na pasta por um tempo máximo."""
    print(f"⏳ Esperando por novo arquivo... (max {tempo_max}s)")
    tempo_inicio = time.time()
    while time.time() - tempo_inicio < tempo_max:
        arquivos_atual = arquivos_na_pasta(pasta)
        novos_arquivos = arquivos_atual - arquivos_antes
        
        arquivos_encontrados = [f for f in novos_arquivos if f.endswith(extensao) and not f.endswith(".crdownload")]

        if arquivos_encontrados:
            print(f"✅ Novo arquivo '{arquivos_encontrados[0]}' detectado.")
            return arquivos_encontrados[0]
        
        time.sleep(2)
        
    print(f"⏱️ Timeout ao aguardar download de arquivo com a extensão '{extensao}'.")
    return None

def esperar_download_completo(caminho_arquivo, tempo_max=60):
    """Espera até que o arquivo termine de ser escrito no disco."""
    tempo_inicio = time.time()
    while time.time() - tempo_inicio < tempo_max:
        if not caminho_arquivo.endswith(".crdownload"):
            return True
        time.sleep(1)
    return False

def baixar_faturas_da_pagina(driver, pasta_destino_final, cnpj_atual):
    """Processa e baixa as faturas visíveis na página atual, pulando as pagas."""
    try:
        # Espera que as linhas de fatura sejam carregadas
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.mve-grid-row"))
        )
        todas_linhas = driver.find_elements(By.CSS_SELECTOR, "div.mve-grid-row")
        
        faturas_pendentes = []
        for linha in todas_linhas:
            try:
                # Se a fatura tiver o status 'Paga', nós a ignoramos.
                linha.find_element(By.CSS_SELECTOR, ".invoice-due-date-label-paid")
                print("⚠️ Fatura paga detectada. Pulando para a próxima.")
                continue
            except NoSuchElementException:
                pass
            
            try:
                linha.find_element(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                faturas_pendentes.append(linha)
            except NoSuchElementException:
                continue

        print(f"🔍 {len(faturas_pendentes)} fatura(s) pendente(s) a baixar nesta página.")

        if len(faturas_pendentes) == 0:
            print("✅ Não há faturas pendentes nesta página. Nada para baixar.")
            return

        for idx, fatura in enumerate(faturas_pendentes, start=1):
            print(f"\n📌 Processando fatura {idx} de {len(faturas_pendentes)}...")
            
            max_tentativas = 3
            tentativa_atual = 0
            while tentativa_atual < max_tentativas:
                try:
                    fechar_popups_genericos(driver)
                    
                    botao_dropdown = fatura.find_element(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_dropdown)
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(botao_dropdown)).click()
                    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu.show")))
                    
                    # Lógica para decidir entre PDF e ZIP
                    try:
                        # Tenta encontrar a opção de download de múltiplas faturas (ZIP)
                        botao_boleto_zip = fatura.find_element(By.XPATH, ".//button[contains(., 'Todas em boleto (.zip)')]")
                        arquivos_antes = arquivos_na_pasta(PASTA_DOWNLOAD_TEMP)
                        botao_boleto_zip.click()
                        print("✅ Download de Todas em boleto (.zip) clicado. Aguardando arquivo...")
                        
                        nome_arquivo_zip = esperar_novo_arquivo(PASTA_DOWNLOAD_TEMP, arquivos_antes, extensao=".zip")

                        if nome_arquivo_zip:
                            caminho_arquivo_zip = os.path.join(PASTA_DOWNLOAD_TEMP, nome_arquivo_zip)
                            esperar_download_completo(caminho_arquivo_zip)
                            
                            print(f"📦 Extraindo arquivos de '{nome_arquivo_zip}'...")
                            with zipfile.ZipFile(caminho_arquivo_zip, 'r') as zip_ref:
                                zip_ref.extractall(PASTA_DOWNLOAD_TEMP)
                            
                            os.remove(caminho_arquivo_zip)
                            print("✅ Arquivo .zip extraído e removido.")

                            # Captura o código do cliente e a data da fatura da linha da tabela
                            try:
                                codigo_cliente = fatura.find_element(By.CSS_SELECTOR, "div[data-test-secondary-info] span").text.strip()
                                data_fatura_texto = fatura.find_element(By.CSS_SELECTOR, "div[data-test-invoice-due-date]").text.strip()
                                data_formatada = data_fatura_texto.replace("/", "")
                                print(f"📝 Dados da fatura na página: Código do cliente '{codigo_cliente}', Data de vencimento '{data_formatada}'.")
                            except NoSuchElementException:
                                print("⚠️ Não foi possível capturar o código do cliente ou a data da fatura da página.")
                                codigo_cliente = None
                                data_formatada = datetime.now().strftime("%Y%m%d") # Usa a data de hoje como fallback

                            for nome_pdf in os.listdir(PASTA_DOWNLOAD_TEMP):
                                if nome_pdf.endswith(".pdf"):
                                    caminho_antigo_pdf = os.path.join(PASTA_DOWNLOAD_TEMP, nome_pdf)
                                    
                                    # Tenta renomear com os dados da página primeiro
                                    if codigo_cliente and data_formatada:
                                        novo_nome_pdf = f"vivo_{codigo_cliente}_{data_formatada}.pdf"
                                        print(f"✅ Renomeando arquivo extraído para: {novo_nome_pdf}")
                                    else:
                                        # Se os dados da página não estiverem disponíveis, tenta extrair do nome do arquivo
                                        match = re.search(r'gvtinv_(\d+)\.pdf$', nome_pdf)
                                        if match:
                                            codigo_cliente_zip = match.group(1)
                                            data_hoje = datetime.now().strftime("%Y%m%d")
                                            novo_nome_pdf = f"vivo_{codigo_cliente_zip}_{data_hoje}.pdf"
                                            print(f"✅ Renomeando arquivo extraído para: {novo_nome_pdf} (dados do nome do arquivo)")
                                        else:
                                            print(f"⚠️ Não foi possível extrair dados de '{nome_pdf}' para renomear. Movendo sem renomear.")
                                            shutil.move(caminho_antigo_pdf, os.path.join(pasta_destino_final, nome_pdf))
                                            continue # Pula para o próximo arquivo do loop

                                    caminho_novo_pdf = os.path.join(pasta_destino_final, novo_nome_pdf)
                                    
                                    try:
                                        shutil.move(caminho_antigo_pdf, caminho_novo_pdf)
                                        print(f"📥 Arquivo movido e renomeado para: {caminho_novo_pdf}")
                                    except Exception as e_rename:
                                        print(f"❌ Erro ao mover/renomear arquivo '{nome_pdf}': {e_rename}")
                        else:
                            print("❌ Falha no download ou timeout do arquivo .zip. Pulando para a próxima fatura.")
                    
                    except NoSuchElementException:
                        # Se o botão de ZIP não existe, tenta o de PDF individual
                        try:
                            botao_boleto_pdf = fatura.find_element(By.XPATH, ".//button[contains(., 'Boleto (.pdf)')]")
                            arquivos_antes = arquivos_na_pasta(PASTA_DOWNLOAD_TEMP)
                            botao_boleto_pdf.click()
                            print("✅ Download de Boleto (.pdf) clicado. Aguardando arquivo...")
                            
                            time.sleep(5)

                            nome_arquivo_antigo = esperar_novo_arquivo(PASTA_DOWNLOAD_TEMP, arquivos_antes, extensao=".pdf")
                            
                            if nome_arquivo_antigo:
                                caminho_antigo = os.path.join(PASTA_DOWNLOAD_TEMP, nome_arquivo_antigo)
                                esperar_download_completo(caminho_antigo)
                                
                                codigo_cliente = fatura.find_element(By.CSS_SELECTOR, "div[data-test-secondary-info] span").text.strip()
                                data_fatura_texto = fatura.find_element(By.CSS_SELECTOR, "div[data-test-invoice-due-date]").text.strip()
                                data_formatada = data_fatura_texto.replace("/", "")
                                novo_nome = f"vivo_{codigo_cliente}_{data_formatada}.pdf"
                                
                                caminho_novo = os.path.join(pasta_destino_final, novo_nome)
                                
                                try:
                                    shutil.move(caminho_antigo, caminho_novo)
                                    print(f"📥 Arquivo movido e renomeado para: {caminho_novo}")
                                except Exception as e_rename:
                                    print(f"❌ Erro ao mover/renomear arquivo '{nome_arquivo_antigo}': {e_rename}")
                            else:
                                print("❌ Falha no download ou timeout. Pulando para a próxima fatura.")

                        except NoSuchElementException:
                            print("⚠️ As opções 'Boleto (.pdf)' e 'Todas em boleto (.zip)' não estão disponíveis para esta fatura. Pulando.")
                    
                    break
                
                except ElementClickInterceptedException as e:
                    print(f"❌ O clique foi interceptado por um pop-up. Tentando fechar e retentar (tentativa {tentativa_atual + 1}/{max_tentativas}): {e}")
                    fechar_popups_genericos(driver, tempo_max=2)
                    tentativa_atual += 1
                except (TimeoutException, StaleElementReferenceException) as e:
                    print(f"⚠️ Erro ao tentar processar a fatura {idx}: {e}")
                    break
                except Exception as e:
                    print(f"❌ Erro ao tentar clicar no botão de download: {e}. Pulando para a próxima fatura.")
                    break
            
    except Exception as e_geral:
        print(f"⚠️ Erro geral ao processar as faturas da página: {e_geral}")

def baixar_todas_faturas_paginadas(driver, pasta_download_base, cnpj_atual):
    """Navega por todas as páginas de faturas e baixa os arquivos."""
    pagina = 1
    
    cnpj_formatado = cnpj_atual.replace('.', '').replace('/', '-')
    pasta_destino_final = os.path.join(pasta_download_base, "Vivo", cnpj_formatado)
    os.makedirs(pasta_destino_final, exist_ok=True)
    os.makedirs(PASTA_DOWNLOAD_TEMP, exist_ok=True)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-dont-have-account-message-wireline]"))
        )
        print(f"✅ Não há faturas para o CNPJ {cnpj_atual}. Clicando em 'Ok, entendi' e pulando.")
        botao_entendi = driver.find_element(By.CSS_SELECTOR, "button[data-test-redirect-dashboard-button]")
        driver.execute_script("arguments[0].click();", botao_entendi)
        time.sleep(3)
        return
    except TimeoutException:
        print("✅ A mensagem 'Não há contas' não foi encontrada. Prosseguindo com a busca por faturas.")
        pass

    try:
        primeiro_item_texto_antes = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span"))
        ).text.strip()
    except Exception:
        print("⚠️ Não foi possível capturar o texto do primeiro item. A página pode estar vazia ou lenta.")
        primeiro_item_texto_antes = "vazio"

    while True:
        print(f"\n📄 Página {pagina} - Iniciando...")
        baixar_faturas_da_pagina(driver, pasta_destino_final, cnpj_atual)

        try:
            fechar_popups_genericos(driver)

            proximo_botao = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.button--pagination-next > button"))
            )

            if not proximo_botao.is_enabled():
                print("🚩 Última página atingida.")
                break
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", proximo_botao)
            
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(proximo_botao)).click()

            print("⏳ Aguardando a nova página de faturas carregar...")
            WebDriverWait(driver, 30).until(
                lambda d: d.find_element(By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span").text.strip() != primeiro_item_texto_antes
            )
            
            primeiro_item_texto_antes = driver.find_element(By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span").text.strip()
            pagina += 1
            time.sleep(2)

        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
            print(f"⚠️ Erro ao ir para a próxima página ou carregar faturas: {e}")
            break