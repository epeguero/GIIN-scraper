# GIIN Job Scraper

This project can serve as a template for how to use (`scrapy`)[scrapy.org].
See the linked website for install instructions (probably just `pip install scrapy`)

To run only the crawler and see its output, pass the spider file to `scrapy`: `scrapy runspider spider.py`.
To run the crawler and email the results, run `spider.py` as a standalone script: `python3 spider.py`.
  * Note: to actually send email, you need to set the following parameters:
    * Set `fromaddr` to your sending email address
    * Set `mailing_list` to a list of target email addresses
  * This likely requires granting email-sending rights to your script: See (here)[https://realpython.com/python-send-email/#option-1-setting-up-a-gmail-account-for-development]

Happy Scraping!!
