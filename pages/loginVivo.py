from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginPage:
    URL = "https://mve.vivo.com.br/oauth?logout=true"

    USERNAME_INPUT = (By.ID, "login-input")
    CONTINUE_BUTTON = (By.CSS_SELECTOR, "button[data-test-access-button]")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password'][name='password']")
    SUBMIT_BUTTON = (By.XPATH, "//button[@type='submit' and @data-test-access-button]")

    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open_login_page(self):
        self.driver.get(self.URL)
        self.wait.until(EC.presence_of_element_located(self.USERNAME_INPUT))

    def enter_username(self, username):
        field = self.wait.until(EC.visibility_of_element_located(self.USERNAME_INPUT))
        field.clear()
        field.send_keys(username)

    def click_continue(self):
        btn = self.wait.until(EC.element_to_be_clickable(self.CONTINUE_BUTTON))
        btn.click()
        self.wait.until(EC.visibility_of_element_located(self.PASSWORD_INPUT))

    def enter_password(self, password):
        field = self.wait.until(EC.element_to_be_clickable(self.PASSWORD_INPUT))
        field.clear()
        field.send_keys(password)

    def click_login(self):
        btn = self.wait.until(EC.element_to_be_clickable(self.SUBMIT_BUTTON))
        btn.click()

    def perform_login(self, username, password):
        self.open_login_page()
        self.enter_username(username)
        self.click_continue()
        self.enter_password(password)
        self.click_login()
