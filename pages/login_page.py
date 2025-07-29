import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginPage:
    URL = "https://mve.vivo.com.br/oauth?logout=true"

    # Constants for element selectors
    USERNAME_INPUT = (By.ID, "login-input")
    CONTINUE_BUTTON = (By.CSS_SELECTOR, "button[data-test-access-button]")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password'][name='password']")
    SUBMIT_BUTTON = (By.XPATH, "//button[@type='submit' and @data-test-access-button]")

    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open_login_page(self):
        """Open the login page"""
        self.driver.get(self.URL)
        time.sleep(2)

    def enter_username(self, username):
        """Fill in the username (CPF)"""
        username_field = self.wait.until(EC.presence_of_element_located(self.USERNAME_INPUT))
        username_field.clear()
        username_field.send_keys(username)
        time.sleep(1)

    def click_continue(self):
        """Click the continue button after entering username"""
        continue_btn = self.wait.until(EC.element_to_be_clickable(self.CONTINUE_BUTTON))
        continue_btn.click()
        time.sleep(2)

    def enter_password(self, password):
        """Fill in the password"""
        password_field = self.wait.until(EC.element_to_be_clickable(self.PASSWORD_INPUT))
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1.5)

    def click_login(self):
        """Click the final login/submit button"""
        login_btn = self.wait.until(EC.element_to_be_clickable(self.SUBMIT_BUTTON))
        login_btn.click()
        time.sleep(3)

    def perform_login(self, username, password):
        """Full login process"""
        self.enter_username(username)
        self.click_continue()
        self.enter_password(password)
        self.click_login()
