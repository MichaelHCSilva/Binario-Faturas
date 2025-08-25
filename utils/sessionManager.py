import time

def ensure_logged_in(driver, login_page, usuario, senha):
    """Verifica se a sessão expirou e refaz login se necessário."""
    try:
        if "login-input" in driver.page_source or "Acessar com" in driver.page_source:
            print("⚠️ Sessão expirada! Refazendo login...")
            login_page.perform_login(usuario, senha)
            time.sleep(3)
            return True
    except Exception:
        pass
    return False
