from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver


class ProfileTest(StaticLiveServerTestCase):
    fixtures = ['tests/test_profile_and_pdf']

    def test_profile(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        driver.get(f"{self.live_server_url}/profiles/municipality-BUF-buffalo-city/")

        self.assertEquals("Buffalo City", driver.find_element_by_css_selector(".page-heading__title").text)

        browser_logs = driver.get_log("browser")
        browser_errors = [entry for entry in browser_logs if entry['level'] == 'SEVERE']
        self.assertEquals(0, len(browser_errors), browser_errors)
