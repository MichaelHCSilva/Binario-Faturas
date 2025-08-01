from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
import time
import os
import re

def baixar_todas_faturas_paginadas(driver, pasta_download_base, cnpj_atual):
    pagina = 1
    
    cnpj_formatado = cnpj_atual.replace('.', '').replace('/', '-')
    pasta_destino_final = os.path.join(pasta_download_base, "Vivo", cnpj_formatado)
    os.makedirs(pasta_destino_final, exist_ok=True)
    
    try:
        primeiro_item_texto_antes = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span"))
        ).text.strip()
    except Exception as e:
        primeiro_item_texto_antes = ""
        print(f"⚠️ Não foi possível capturar o texto do primeiro item na primeira página: {e}")

    while True:
        print(f"\n📄 Página {pagina} - Iniciando...")
        baixar_faturas_com_intervalo_amplo(driver, pasta_download_base, pasta_destino_final)

        try:
            proximo_botao = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.button--pagination-next > button"))
            )

            if not proximo_botao.is_enabled():
                print("🚩 Última página atingida.")
                break

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", proximo_botao)
            time.sleep(1) # Espera maior para a rolagem
            
            try:
                proximo_botao.click()
            except Exception:
                driver.execute_script("arguments[0].click();", proximo_botao)

            print("⏳ Aguardando a nova página de faturas carregar...")
            WebDriverWait(driver, 20).until(
                lambda d: d.find_element(By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span").text.strip() != primeiro_item_texto_antes
            )
            
            primeiro_item_texto_antes = driver.find_element(By.CSS_SELECTOR, "div.mve-grid-row:first-of-type div[data-test-secondary-info] span").text.strip()

            pagina += 1
            time.sleep(2) # Aumentado o tempo de espera entre as páginas

        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
            print(f"⚠️ Erro ao ir para a próxima página ou carregar faturas: {e}")
            break


def baixar_faturas_com_intervalo_amplo(driver, pasta_download_temporaria, pasta_destino_final, tempo_espera=30): # Aumentado o tempo de espera padrão
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.mve-grid-row"))
        )
        todas_linhas = driver.find_elements(By.CSS_SELECTOR, "div.mve-grid-row")
        faturas = [linha for linha in todas_linhas if "Baixar agora" in linha.text]

        print(f"🔍 {len(faturas)} fatura(s) encontrada(s).")

        for idx, fatura in enumerate(faturas, start=1):
            print(f"\n📌 Processando fatura {idx} de {len(faturas)}...")

            try:
                codigo_cliente_elem = fatura.find_element(By.CSS_SELECTOR, "div[data-test-secondary-info] span")
                codigo_cliente = codigo_cliente_elem.text.strip()
                
                data_fatura_elem = fatura.find_element(By.CSS_SELECTOR, "div[data-test-invoice-due-date]")
                data_fatura_texto = data_fatura_elem.text.strip()
                data_formatada = data_fatura_texto.replace("/", "")
                
                novo_nome = f"vivo_{codigo_cliente}_{data_formatada}.pdf"

                botao_dropdown = fatura.find_element(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_dropdown)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(botao_dropdown))
                
                try:
                    botao_dropdown.click()
                except:
                    driver.execute_script("arguments[0].click();", botao_dropdown)

                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu.show"))
                )

                botoes = fatura.find_elements(By.CSS_SELECTOR, "button.dropdown-item.dropdown-button__option")
                boleto_baixado = False

                for botao in botoes:
                    if "Boleto" in botao.text:
                        arquivos_antes = arquivos_na_pasta(pasta_download_temporaria)
                        
                        try:
                            # Remove arquivos temporários antes de iniciar o download
                            for f in os.listdir(pasta_download_temporaria):
                                if f.endswith(".crdownload"):
                                    os.remove(os.path.join(pasta_download_temporaria, f))
                                    print(f"⚠️ Arquivo temporário obsoleto removido: {f}")
                        except Exception as e_limpeza:
                            print(f"❌ Erro ao limpar arquivos temporários: {e_limpeza}")
                        
                        try:
                            botao.click()
                            time.sleep(5) # Aumentado o tempo de espera para o download iniciar
                        except:
                            driver.execute_script("arguments[0].click();", botao)
                            time.sleep(5) # Aumentado o tempo de espera

                        print("✅ Download clicado. Aguardando arquivo...")
                        
                        nome_arquivo_antigo = esperar_novo_arquivo(pasta_download_temporaria, arquivos_antes, tempo_espera)
                        
                        if nome_arquivo_antigo:
                            caminho_antigo = os.path.join(pasta_download_temporaria, nome_arquivo_antigo)
                            
                            esperar_download_completo(caminho_antigo, tempo_max=30)
                            
                            caminho_novo = os.path.join(pasta_destino_final, novo_nome)
                            
                            try:
                                os.rename(caminho_antigo, caminho_novo)
                                print(f"📥 Arquivo movido e renomeado para: {caminho_novo}")
                            except Exception as e_rename:
                                print(f"❌ Erro ao renomear arquivo '{nome_arquivo_antigo}': {e_rename}")
                                print(f"⚠️ O arquivo pode estar em uso ou o nome já existe.")
                        else:
                            print("⏱️ Timeout ao aguardar download.")
                            
                        boleto_baixado = True
                        break

                if not boleto_baixado:
                    print("❌ Botão 'Boleto (.pdf)' não encontrado.")

            except Exception as e_fatura:
                print(f"⚠️ Erro ao tentar baixar a fatura {idx}: {e_fatura}")
                if "invalid session id" in str(e_fatura):
                    print("❌ Sessão do navegador perdida. O script será encerrado.")
                    raise e_fatura
                
    except Exception as e_geral:
        print(f"⚠️ Erro geral ao processar faturas: {e_geral}")


def arquivos_na_pasta(caminho):
    try:
        return set(os.listdir(caminho))
    except Exception:
        return set()


def esperar_novo_arquivo(pasta, arquivos_antes, tempo_max=30): # Aumentado o tempo máximo de espera
    print(f"⏳ Esperando por novo arquivo... (max {tempo_max}s)")
    tempo_inicio = time.time()
    while time.time() - tempo_inicio < tempo_max:
        arquivos_atual = arquivos_na_pasta(pasta)
        novos = arquivos_atual - arquivos_antes
        novos_pdfs = [f for f in novos if f.endswith(".pdf") and not f.endswith(".crdownload")]

        if novos_pdfs:
            print(f"✅ Novo arquivo '{novos_pdfs[0]}' detectado.")
            return novos_pdfs[0]
        time.sleep(1)
        print("...")

    return None

def esperar_download_completo(caminho_arquivo, tempo_max):
    """Espera até que o arquivo de download termine de ser escrito no disco."""
    tempo_inicio = time.time()
    while time.time() - tempo_inicio < tempo_max:
        if not caminho_arquivo.endswith(".crdownload"):
            return True
        time.sleep(1)
    return False