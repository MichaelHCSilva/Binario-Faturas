from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def baixar_todas_faturas_paginadas(driver, pasta_download="/mnt/c/Users/compu/Downloads"):
    pagina = 1

    while True:
        print(f"\n📄 Página {pagina} - Iniciando...\n")
        baixar_faturas_com_intervalo_amplo(driver, pasta_download)

        try:
            proximo_botao = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.button--pagination-next > button"))
            )

            if not proximo_botao.is_enabled():
                print("🚩 Última página atingida.")
                break

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", proximo_botao)
            time.sleep(0.5)

            try:
                proximo_botao.click()
            except Exception:
                driver.execute_script("arguments[0].click();", proximo_botao)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.mve-grid-row"))
            )

            pagina += 1
            time.sleep(1.0)

        except Exception as e:
            print(f"⚠️ Erro ao ir para a próxima página: {e}")
            break


def baixar_faturas_com_intervalo_amplo(driver, pasta_download="/mnt/c/Users/compu/Downloads", tempo_espera=20):
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
                botao_dropdown = fatura.find_element(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_dropdown)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(., 'Baixar agora')]")))
                
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
                        arquivos_antes = arquivos_na_pasta(pasta_download)
                        try:
                            botao.click()
                        except:
                            driver.execute_script("arguments[0].click();", botao)

                        print("✅ Download clicado.")
                        boleto_baixado = True
                        esperar_novo_arquivo(pasta_download, arquivos_antes, tempo_espera)
                        break

                if not boleto_baixado:
                    print("❌ Botão 'Boleto (.pdf)' não encontrado.")

            except Exception as e_fatura:
                print(f"⚠️ Erro ao tentar baixar a fatura {idx}: {e_fatura}")

    except Exception as e_geral:
        print(f"⚠️ Erro geral ao processar faturas: {e_geral}")


def arquivos_na_pasta(caminho):
    try:
        return set(os.listdir(caminho))
    except Exception:
        return set()


def esperar_novo_arquivo(pasta, arquivos_antes, tempo_max=20):
    for _ in range(int(tempo_max * 2)):
        arquivos_atual = arquivos_na_pasta(pasta)
        novos = arquivos_atual - arquivos_antes
        novos_pdfs = [f for f in novos if f.endswith(".pdf")]

        if novos_pdfs:
            print(f"📥 Arquivo detectado: {novos_pdfs[0]}")
            return
        time.sleep(0.5)

    print("⏱️ Timeout ao aguardar download.")