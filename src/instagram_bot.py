"""
File:           instagram_bot.py
Author:         Dibyaranjan Sathua
Created on:     10/04/21, 3:06 pm
"""
from typing import Optional, Dict
from pathlib import Path
import time
import random
import logging
import yaml
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from src.exceptions import InstagramBotExceptions


class InstagramBot:
    """ Class responsible to increase instagram followers """
    URL = "https://www.instagram.com"

    def __init__(self, driver: Path, config_file: Path):
        self._driver = driver
        self._config_file = config_file
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--window-size=1920,1080")
        self.driver: Optional[webdriver.Chrome] = None
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self._config: Optional[Dict] = None
        self.load_config()
        self.stats = dict()

    def __del__(self):
        if self.driver is not None:
            self.driver.close()

    def load_config(self):
        """ Load config file """
        if not self._config_file.is_file():
            self.logger.error(f"Config file {self._config_file} doesn't exist.")
            raise InstagramBotExceptions()
        with open(self._config_file, mode="r") as fh_:
            self._config = yaml.full_load(fh_)

    def init_driver_and_signin(self):
        """ Initialize a driver and sign in"""
        self.logger.info(f"Initializing web driver")
        self.driver = webdriver.Chrome(self._driver, options=self.options)
        self.logger.info(f"Sending request to {self.URL}")
        self.driver.get(self.URL)
        time.sleep(10)
        self.signin()

    def signin(self):
        """ Signin to instagram """
        self.logger.info("Signing in to instagram")
        username = self.driver.find_element_by_name("username")
        username.send_keys(self._config["Cred"]["Username"])
        password = self.driver.find_element_by_name("password")
        password.send_keys(self._config["Cred"]["Password"])
        # Get the login button by text
        buttons = self.driver.find_elements_by_css_selector("button > div")
        login_btn = next((btn for btn in buttons if btn.text == "Log In"), None)
        if login_btn is None:
            self.logger.error(f"Unable to locate login button.")
            raise InstagramBotExceptions()
        login_btn.click()
        time.sleep(5)
        self.logger.info(f"Signin completed")

    def save_login_info_page(self):
        """ Save login info pop up. Click on Save """
        # Get all div texts
        divs = self.driver.find_elements_by_css_selector("div")
        texts = [div.text for div in divs]
        if "Save Your Login Info?" in texts:
            self.logger.info(f"Bot in Save Your Login Info? page")
            try:
                save_btn = self.driver.find_element_by_xpath('//button[text()="Save Info"]')
                save_btn.click()
            except NoSuchElementException:
                self.logger.error(f"Unable to locate Save button on 'Save Your Login Info?' page")
            time.sleep(5)

    def turn_on_notification_page(self):
        """ Handle notification pop up. Click on Not Now """
        # Get all h2 texts
        h2_elements = self.driver.find_elements_by_css_selector("h2")
        texts = [h2.text for h2 in h2_elements]
        if "Turn on Notifications" in texts:
            self.logger.info(f"Bot in Turn on Notifications page")
            try:
                not_now_btn = self.driver.find_element_by_xpath('//button[text()="Not Now"]')
                not_now_btn.click()
            except NoSuchElementException:
                self.logger.error("Unable to locate Not Now button on 'Turn on Notifications' page")
            time.sleep(5)

    def crawl(self):
        """ crawl each hashtag url and follow poster and put comments """
        self.init_driver_and_signin()
        self.save_login_info_page()
        self.turn_on_notification_page()
        # sleep for sometime before processing the tags
        while True:
            time.sleep(random.randint(15, 20))
            self.process_hashtags()
            time.sleep(random.randint(15, 20))
            self.process_discover_page()

    def process_hashtags(self):
        """ Processing of hashtags """
        hashtag_baseurl = f"{self.URL}/explore/tags"
        max_image = self._config["MaxImagePerHashTag"]
        for tag in self._config["HashTags"]:
            if tag not in self.stats:
                self.stats[tag] = {
                    "username": [],
                    "likes": 0,
                    "comments": 0
                }
            url = f"{hashtag_baseurl}/{tag}/"
            self.logger.info(f"Sending request to {url}")
            self.driver.get(url)
            time.sleep(10)
            # click on the first thumbnail
            first_thumbnail = self.driver.find_element_by_css_selector("div.eLAPa > div._9AhH0")
            first_thumbnail.click()
            time.sleep(random.randint(5, 10))
            for _ in range(max_image):
                try:
                    self.processing_image(tag)
                except Exception as err:
                    self.logger.error(f"Error processing image. {err}")
                # Click the next button
                self.driver.find_element_by_link_text("Next").click()
                time.sleep(random.randint(14, 20))
            # Print stats
            self.print_stats()
            # sleep before processing next hashtag
            time.sleep(random.randint(22, 30))

    def process_discover_page(self):
        """ Processing posts on discover page """
        url = f"{self.URL}/explore"
        max_image = self._config["MaxImagePerDiscoverPage"]
        self.logger.info(f"Sending request to {url}")
        self.driver.get(url)
        time.sleep(10)
        first_thumbnail = self.driver.find_element_by_css_selector("div.eLAPa > div._9AhH0")
        first_thumbnail.click()
        time.sleep(random.randint(5, 10))
        tag = "discover-page"
        if tag not in self.stats:
            self.stats[tag] = {
                    "username": [],
                    "likes": 0,
                    "comments": 0
                }
        for _ in range(max_image):
            try:
                self.processing_image(tag)
            except Exception as err:
                self.logger.error(f"Error processing image. {err}")
            # Click the next button
            self.driver.find_element_by_link_text("Next").click()
            time.sleep(random.randint(14, 20))
        # print stats
        self.print_stats()

    def processing_image(self, tag: str):
        """ Follow the user, like the picture and comment an emoji U+1F4A1 (bulb) """
        user_following_flag = False     # Indicate if we are following the user
        user_like_flag = False          # Indicate if we have liked the post
        username = self.driver.find_element_by_css_selector("div.e1e1d > span > a").text
        follow_btn = self.driver.find_element_by_css_selector("div.bY2yH > button")
        if follow_btn.text == "Follow":
            self.logger.info(f"Started Following a new user {username}")
            follow_btn.click()
            time.sleep(random.randint(10, 16))
            self.stats[tag]["username"].append(username)
        else:
            user_following_flag = True
            self.logger.info(f"Already following user {username}")

        # Get all action buttons
        action_btns = self.driver.find_elements_by_css_selector(
            "section.ltpMr._96JFA.t6Mad div.QBdPU"
        )
        for btn in action_btns:
            svg = btn.find_element_by_css_selector("svg")
            value = svg.get_attribute("aria-label")
            # Don't unlike it if it was liked previously
            if value == "Like":
                self.logger.info(f"Liking the image")
                btn.click()
                time.sleep(random.randint(18, 24))
                self.stats[tag]["likes"] += 1
            elif value == "Unlike":
                user_like_flag = True
                self.logger.info(f"Image was already liked")
            elif value == "Comment":
                # Don't comment if we are already following the user and already liked the post
                if user_following_flag and user_like_flag:
                    self.logger.info(f"Skipping comment as the user has already been followed and "
                                     f"the post was already liked")
                else:
                    self.logger.info(f"Commenting on the post")
                    btn.click()
                    time.sleep(5)
                    # Send comment
                    comment_box = self.driver.find_element_by_css_selector("form textarea")
                    comment = random.choice(self._config["Comments"])
                    comment_box.send_keys(comment)
                    time.sleep(random.randint(6, 10))
                    comment_box.send_keys(Keys.ENTER)
                    time.sleep(random.randint(12, 18))
                    self.stats[tag]["comments"] += 1

    def print_stats(self):
        """ Print the stats """
        print(f"=========================== STATS ================================")
        for tag, stats in self.stats.items():
            print(f"{tag}")
            for key, value in stats.items():
                print(f"\t\t{key}: {value}")
        print(f"=========================== END ================================")
