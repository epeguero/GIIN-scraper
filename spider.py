import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import dispatcher

import smtplib, ssl, platform
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import json

from enum import Enum

class GIINSpider(scrapy.Spider):
    name = 'toscrape-xpath'
    start_urls = ['https://jobs.thegiin.org/']

    def parse(self, response):
        # We finish when we fail to find any recent jobs in a page
        finished = True

        for job in response.css('.block-link'):
            posted = job.css('.posted::text').get()

            # filter out "featured jobs" side column
            if posted != None:
                posted_words = posted.split()

                # parse posted date, assuming 
                # the following format:
                # "New" | "Posted {x} days ago"
                days_ago = 0 if posted_words[0] == "New" else int(posted_words[1])

                block_link_src = job.css('.block-link-src')

                if days_ago <= 7:
                    finished = False
                    yield {
                        'title': block_link_src.xpath('.//text()').get(),
                        'org': job.css('.organization').xpath('.//text()').get(),
                        'link': self.start_urls[0] + block_link_src.attrib['href'],
                        'days_ago': days_ago
                        }

        # Next page comes after the 'active' one
        pagination = response.css('.pagination')
        curr_page_num = int(pagination.css('.active::text').get())
        next_url_query = pagination.css('*::attr(href)').re(r'\?page=' + str(curr_page_num + 1))
        if not finished and next_url_query != []:
            next_url = next_url_query[0]
            yield response.follow(self.start_urls[0] + next_url, self.parse)


# Collect Spider Results
def spider_results():
    results = []

    def crawler_results(signal, sender, item, response, spider):
        results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_passed)

    process = CrawlerProcess(get_project_settings())
    process.crawl(GIINSpider)
    process.start()  # the script will block here until the crawling is finished
    return results


# Email the results
def send_gmail(fromaddr, toaddr, msg, password):
    server = smtplib.SMTP_SSL('smtp.gmail.com')
    server.login(fromaddr, password)
    server.sendmail(fromaddr, toaddr, msg)
    server.quit()

class Mode(Enum):
    SendToLocalSMTP = 0,
    SendToDevGmail = 1,
    SendToListGmail = 2


# Format job
def generate_msg_html(jobs):
    def html_elem(e, s):
        return "<{}>{}</{}>".format(e, s, e)

    top_level_html="<html><body>{}\n{}</body></html>"

    def job_to_html(j):
        title = "Job Title: {}".format(j["title"])
        org = "Host Organization: {}".format(j["org"])
        age = "Posted {} days ago.".format(j["days_ago"])
        listed_job_details = [title, org, age]
        listed_job_details_html = map(lambda s: html_elem("span", s), listed_job_details)
        job_html=html_elem("li", '\n'.join(listed_job_details_html))
        return job_html

    intro = "Check out these new job opportunities posted within the last week:"
    jobs_html = map(job_to_html, jobs)
    msg = top_level_html.format(html_elem("p", intro), '\n'.join(jobs_html))
    return msg


mode = Mode.SendToDevGmail
fromaddr = 'test_sender@gmail.com'
password = 'pemsalyebgndeaip'

mailing_list = ['test_target@example.org']

if __name__ == '__main__':
    # Scrape GIIN for job info
    print('Crawling GIIN for job listings')
    jobs = spider_results()
    print(f'found {len(jobs)} new job listings')

    # Compose message based on listings
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'GIIN Job Alert: New Job Posts Available!'
    msg['From'] = fromaddr
    msg.attach(MIMEText(generate_msg_html(jobs), 'html'))

    # Send message to mailing list
    server = smtplib.SMTP('localhost', 1025) if mode == Mode.SendToLocalSMTP else smtplib.SMTP_SSL('smtp.gmail.com')
    if mode == Mode.SendToListGmail:
        for toaddr in mailing_list:
            print(f'sending email from {fromaddr} to {toaddr}...')
            msg['To'] = toaddr
            send_gmail(fromaddr, toaddr, msg.as_string(), password)

    elif mode == Mode.SendToDevGmail:
        print(f'sending email to dev at {fromaddr}...')
        msg['To'] = fromaddr
        send_gmail(fromaddr, fromaddr, msg.as_string(), password)

    elif mode == Mode.SendToLocalSMTP:
        print(f'sending email to local SMPT server...')
        msg['To'] = fromaddr
        server = smtplib.SMTP('localhost', 1025)
        server.sendmail(fromaddr, fromaddr, msg.as_string())
        server.quit()
