"""
File:           main.py
Author:         Dibyaranjan Sathua
Created on:     10/04/21, 8:13 pm
"""
from pathlib import Path
from src.instagram_bot import InstagramBot


def main():
    """ Main function """
    chromedriver = Path("__file__").absolute().parent / "webdriver" / "chromedriver"
    config_file = Path("__file__").absolute().parent / "config" / "config.yml"
    bot = InstagramBot(driver=chromedriver, config_file=config_file)
    bot.crawl()


if __name__ == "__main__":
    main()
