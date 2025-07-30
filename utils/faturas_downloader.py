from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


def baixar_faturas_com_intervalo_amplo(driver, pasta_download="/mnt/c/Users/compu/Downloads", tempo_espera=15):
    print(f"\n📄 Página 1 - Iniciando download das faturas visíveis...\n")
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.mve-grid-row"))
        )
        todas_linhas = driver.find_elements(By.CSS_SELECTOR, "div.mve-grid-row")

        # Filtra apenas as faturas com botão "Baixar agora"
        faturas = [
            linha for linha in todas_linhas
            if "Baixar agora" in linha.text
        ]

        print(f"🔍 {len(faturas)} fatura(s) real(is) encontrada(s). Iniciando processamento...")

        if not faturas:
            print("❌ Nenhuma fatura real encontrada nesta página.")
            return

        for idx, fatura in enumerate(faturas, start=1):
            print(f"\n📌 Processando fatura {idx} de {len(faturas)}...")

            try:
                botao_dropdown = fatura.find_element(By.XPATH, ".//button[contains(., 'Baixar agora')]")
                driver.execute_script("arguments[0].scrollIntoView(true);", botao_dropdown)
                driver.execute_script("window.scrollBy(0, -150);")
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
                        nome_antes = arquivos_na_pasta(pasta_download)

                        try:
                            botao.click()
                        except:
                            driver.execute_script("arguments[0].click();", botao)

                        print("✅ Botão de download do boleto clicado.")
                        boleto_baixado = True

                        # Aguarda novo arquivo ser salvo
                        esperar_novo_arquivo(pasta_download, nome_antes, tempo_espera)
                        break

                if not boleto_baixado:
                    print("❌ Botão 'Boleto (.pdf)' não encontrado.")

                # Fecha dropdown se ainda estiver aberto
                driver.execute_script("document.activeElement.blur();")

                time.sleep(1)

            except Exception as e_fatura:
                print(f"⚠️ Erro ao tentar baixar a fatura {idx}: {e_fatura}")

    except Exception as e_geral:
        print(f"⚠️ Erro geral ao processar faturas: {e_geral}")


def arquivos_na_pasta(caminho):
    try:
        return set(os.listdir(caminho))
    except:
        return set()


def esperar_novo_arquivo(pasta, arquivos_antes, tempo_max=15):
    for i in range(tempo_max):
        arquivos_atual = arquivos_na_pasta(pasta)
        novos = arquivos_atual - arquivos_antes
        if novos:
            print(f"📥 Novo arquivo detectado: {list(novos)[0]}")
            return
        time.sleep(1)
    print("⏱️ Timeout ao aguardar download do arquivo.")
