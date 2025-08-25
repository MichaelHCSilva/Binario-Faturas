# sessionManager.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

_primeiro_login = True

def ensure_logged_in(driver, login_page, usuario, senha):

    global _primeiro_login
    try:
        if "login" in driver.current_url or "auth" in driver.current_url:
            if _primeiro_login:
                print("Realizando login inicial...")
                _primeiro_login = False
            else:
                print("Sessão expirada! Refazendo login (detecção por URL)...")

            login_page.perform_login(usuario, senha)
            time.sleep(3)
            return True

        try:
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "login-input"))
            )
            if _primeiro_login:
                print("🔑 Realizando login inicial...")
                _primeiro_login = False
            else:
                print("⚠️ Sessão expirada! Refazendo login (detecção por elemento)...")

            login_page.perform_login(usuario, senha)
            time.sleep(3)
            return True
        except:
            pass

    except Exception as e:
        print(f"Erro ao checar/refazer login: {e}")

    return False
