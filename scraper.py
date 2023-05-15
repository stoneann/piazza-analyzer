from concurrent.futures import process
import json
import csv
import requests
from piazza_api import Piazza
from utils import preprocess_content, parse_time, folders, csv_delimiter
from enum import StrEnum
import time
import click

class Scraper:

    class APIUrls(StrEnum):
        LOGIC_URL = 'https://piazza.com/logic/api'

    def validate_response(self, response):
        """Validates an API response to ensure request was successful."""
        content = response.json()
        if (response.status_code != 200 or content["result"] is None 
            or content["result"] != "OK"):
            print(f'ERROR: {content["error"]}')
            exit(1)
    
    def __init__(self, username, password, courseid, filter_folder = ""):
        """Initalizes all self variables."""
        self.piazza = Piazza()
        self.user = username
        self.password = password
        self.nid = courseid
        self.session = requests.Session()
        self.filter_folder = filter_folder
        # TODO: how to get these to automatically update?
        self.get_feed_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0',
            'Accept': 'application/json, text/plain, */*' ,
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://piazza.com/class/' + self.nid ,
            'Content-Type': 'application/json' ,
            'CSRF-Token': '2kpkGWfWvqEYnonGEUlZGP3T', 
            'Origin': 'https://piazza.com' ,
            'Connection': 'keep-alive' ,
            'Sec-Fetch-Dest': 'empty' ,
            'Sec-Fetch-Mode': 'cors' ,
            'Sec-Fetch-Site': 'same-origin' ,
            'TE': 'trailers'
        }

        self.get_one_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0' ,
            'Accept': 'application/json, text/javascript, */*; q=0.01' ,
            'Accept-Language': 'en-US,en;q=0.5' ,
            'Accept-Encoding': 'gzip, deflate, br' ,
            'Referer': 'https://piazza.com/class/' + self.nid ,
            'Content-Type': 'application/json; charset=utf-8' ,
            'CSRF-Token': '2kpkGWfWvqEYnonGEUlZGP3T' ,
            'X-Requested-With': 'XMLHttpRequest' ,
            'Origin': 'https://piazza.com' ,
            'Connection': 'keep-alive' ,
            'Sec-Fetch-Dest': 'empty' ,
            'Sec-Fetch-Mode': 'cors' ,
            'Sec-Fetch-Site': 'same-origin' 
        }

    def user_login(self):
        """Log in user using the variables assigned username and password."""
        login_data = {
            "method": "user.login",
            "params": {"email": self.user,
                       "pass": self.password}
        }

        response = self.session.post(
            self.APIUrls.LOGIC_URL,
            data=json.dumps(login_data)
        )
        self.validate_response(response)

        cookies = ""
        for c in response.cookies:
            temp = c.name + "=" + c.value + "; "
            cookies += temp
        self.get_feed_headers['Cookie'] = cookies

        return response

    def get_feed(self, feed_offset, feed_limit):
        """Get the most recent feed that takes in 3 params:
            offset : starting post
            limit : number of posts to get
        """

        payload= {
            'method': 'network.get_my_feed'
        }

        data_raw={
            "method":"network.get_my_feed",
            "params":{
                "nid": self.nid,
                "offset":feed_offset,
                "limit":feed_limit
            }}
        
        response = self.session.post(
            self.APIUrls.LOGIC_URL,
            headers=self.get_feed_headers,
            params=payload,
            data=json.dumps(data_raw)
        )
        self.validate_response(response)

        return response.json()

    def get_feed_by_folder(self):
        """Get the most recent feed from a specific folder."""
        payload= {
            'method': 'network.filter_feed'
        }

        data_raw={
            "method":"network.filter_feed",
            "params":{
                "nid":self.nid,
                "folder":1,
                "filter_folder":self.filter_folder
            }}

        response = self.session.post(
            self.APIUrls.LOGIC_URL,
            headers=self.get_feed_headers,
            params=payload,
            data=json.dumps(data_raw)
        )
        self.validate_response(response)

        return response.json()

    def process_feed(self, content):
        """Processes every element in the feed."""
        f = dict() 

        for folder in folders:
            f[folder] = list()
        
        for post in content['result']['feed']:
            self.get_one(post['id'], f)

        return f

    def get_one(self, cid, folders):
        """Processes one post in the feed."""
        post = None
        while (post == None):        
            data_raw={
                "method" : "content.get",
                "params" : {
                    "cid" : cid, #"l2q8bs0vpdqte",
                    "nid" : self.nid,
                }}

            response = self.session.post(
                self.APIUrls.LOGIC_URL,
                headers=self.get_one_headers,
                params={
                    "method" : "content.get"
                },
                json=data_raw
            )
            self.validate_response(response)

            post = response.json()['result']
            if post is not None:
                fields = {}
                fields['post_id'] = cid
                fields['subject'] = post["history"][0]["subject"]
                fields['content'] = preprocess_content( post["history"][0]["content"])
                fields['unique_views'] = post["unique_views"]
                fields['good_question'] = len(post["tag_good_arr"])
                fields['visibility'] = post['status']
                followups = 0
                for child in post["children"]:
                    if child["type"] == "i_answer":
                        fields['i_answer'] = preprocess_content(child["history"][0]["content"])
                    elif child["type"] == "s_answer":
                        fields['i_answer'] = preprocess_content(child["history"][0]["content"])
                    else:
                        followups = followups + 1
                fields['num_followups'] = followups
                # Add the fields to the correct folder
                folder = 0
                if len(post["folders"]) > 0:
                    folder = post["folders"][0]
                if folder in folders:
                    folders[post["folders"][0]].append(fields)
            else:
                time.sleep(0.075) 
                # TODO -- analyze the best time for this
                # at 0.075 it took 77 minutes for the entire dataset

    def writeCSV(self, data, write_folder):
        """Writes the gathered data to a CSV."""
        for piazza_folder in folders:
            with open(f'map_posts/{write_folder}/{piazza_folder}.csv', 'w') as csvfile:
                fieldnames = ['post_id', 'subject', 'content', 'unique_views', 'good_question', 'visibility', 'i_answer', 's_answer', 'num_followups']
                filewriter = csv.DictWriter(csvfile, delimiter=csv_delimiter, fieldnames=fieldnames)
                filewriter.writeheader()
                for row in data[piazza_folder]:
                    filewriter.writerow(row)
        

@click.command()
@click.option("--username", "-u", "username", type=click.STRING,
              required=True, help="Piazza username.")
@click.option("--password", "-p", "password", type=click.STRING,
              required=True, help="Piazza password.")
@click.option("--nid", "-n", "nid", type=click.STRING,
              required=True, help="Piazza course id. Found in the username when loading class piazza.")
@click.option("--filter_folder", "-f", "filter_folder", type=click.STRING,
              help="Folder to filter on when getting posts.")
@click.option("--write_folder_name", "-wf", type=click.STRING, 
              required=True, help="Name of the folder data will be written into. Data will already be written into separate CSVs based on piazza folder.")
@click.option("--feed_amount", "-fa", type=click.INT,
              help="Number of posts to process. If all posts in a class, this value should be >= total number posts in course.")
@click.option("--feed_offset", "-fo", type=click.INT,
              help="Number of posts to skip before getting feed. Example: if you don't want the most recent 20 posts this field would be 20.")
def main(username, password, nid, filter_folder, write_folder_name, 
         feed_amount=10000, feed_offset=0):
    # TODO: Implement functionality for filter_folders
    s = Scraper(username, password, nid, filter_folder)
    s.user_login()
    t0 = time.time()
    content = s.get_feed(feed_offset, feed_amount)
    data = s.process_feed(content)
    s.writeCSV(data, write_folder_name)
    total = time.time() - t0
    print(f'Total process time is {total} seconds')


if __name__ == "__main__":
    main()
