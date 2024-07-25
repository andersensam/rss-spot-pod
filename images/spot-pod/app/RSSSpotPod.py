 #  ________   ___   __    ______   ______   ______    ______   ______   ___   __    ______   ________   ___ __ __     
 # /_______/\ /__/\ /__/\ /_____/\ /_____/\ /_____/\  /_____/\ /_____/\ /__/\ /__/\ /_____/\ /_______/\ /__//_//_/\    
 # \::: _  \ \\::\_\\  \ \\:::_ \ \\::::_\/_\:::_ \ \ \::::_\/_\::::_\/_\::\_\\  \ \\::::_\/_\::: _  \ \\::\| \| \ \   
 #  \::(_)  \ \\:. `-\  \ \\:\ \ \ \\:\/___/\\:(_) ) )_\:\/___/\\:\/___/\\:. `-\  \ \\:\/___/\\::(_)  \ \\:.      \ \  
 #   \:: __  \ \\:. _    \ \\:\ \ \ \\::___\/_\: __ `\ \\_::._\:\\::___\/_\:. _    \ \\_::._\:\\:: __  \ \\:.\-/\  \ \ 
 #    \:.\ \  \ \\. \`-\  \ \\:\/.:| |\:\____/\\ \ `\ \ \ /____\:\\:\____/\\. \`-\  \ \ /____\:\\:.\ \  \ \\. \  \  \ \
 #     \__\/\__\/ \__\/ \__\/ \____/_/ \_____\/ \_\/ \_\/ \_____\/ \_____\/ \__\/ \__\/ \_____\/ \__\/\__\/ \__\/ \__\/    
 #                                                                                                               
 # Project: RSS Parser on GKE Autopilot Spot Pod Demo
 # @author : Samuel Andersen and KC Ayyagari
 # @version: 2024-05-31
 #
 # General Notes:
 #
 # TODO: Continue adding functionality 
 #

import os
import sys
import json
import requests
import feedparser
import google.auth
import google.auth.transport.requests
from bs4 import BeautifulSoup
from time import mktime
from datetime import datetime
from google.cloud import bigquery
from google.cloud import pubsub_v1

# Setup the default credentials and project Id
DEFAULT_CRED, GCP_PROJECT_ID = google.auth.default()
TARGET_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

# Get the name of the BigQuery table we want to write to
BQ_TABLE = os.environ['BQ_TABLE']

# Get the Pub/Sub topic we'll listen to messages on
PUBSUB_TOPIC = os.environ['PUBSUB_TOPIC']
PUBSUB_SUBSCRIBER = os.environ['PUBSUB_SUBSCRIBER']

## Have an Exception class used for handling BigQuery errors
class BQException(Exception):
    pass

## Function to take a document summary and upload to BigQuery
#  @param json_summary Summary of the document in JSON format
def write_summary_bq(json_summary):

    # Initialize the BigQuery client
    client = bigquery.Client()

    errors = client.insert_rows_json(BQ_TABLE, [json_summary])

    if errors == []:
        print(f'DEBUG: Successfully inserted summarized document {json_summary["url"]}', file=sys.stderr)
    else:
        print("DEBUG: Encountered errors while inserting rows: {}".format(errors), file=sys.stderr)
        raise BQException('Unable to insert summary into BQ table')
    
## Function to check if a row exists within a BigQuery Table. Returns a boolean
#  @param url URL of the article we're checking for in BQ
def check_article_bq(url):

    client = bigquery.Client()

    query = """
    SELECT
        COUNT(*)
    FROM
        `{}`
    WHERE
        url LIKE @url;
    """.format(BQ_TABLE)

    # Ensure that the document_id is properly processed
    job_config = bigquery.QueryJobConfig(
        query_parameters = [
            bigquery.ScalarQueryParameter('url', 'STRING', url)
        ])

    # Execute the query and wait for results
    res = client.query_and_wait(query = query, job_config = job_config)

    # Scan the result, knowing that only one column is returned, containing the COUNT(*)
    for row in res:
        # If COUNT(*) > 0, the record already exists in the dataset
        if (row[0] > 0):
            return True
        
    # If we get no response, or if it's simply 0, return False
    return False

## Function to extract article data from a website
#  Returns a dictionary with the information specified in 'result'
#  @param url URL we want to pull information from
def extract_article_data(url):

    # Try fetching the URL
    response = requests.get(url)

    # Check for errors and raise an exception if we run into one
    response.raise_for_status()

    # Setup the content parser
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the title
    title_tag = soup.find('h1') or soup.find('title')

    # Extract the body of the article
    article_body = soup.find('article') or soup.find('div', class_ = 'content')

    if article_body:

        # Remove unwanted elements like ads or sidebars
        for unwanted in article_body.find_all('div', {'class': 'sidebar'}):
            unwanted.decompose()

    # Grab other relevant metadata
    author_tag = soup.find('span', class_ = 'author') or soup.find('meta', {'name': 'author'})

    # Prepare for the multiple date representations there may be
    published_date = None
    date_tag = soup.find('time') or soup.find('meta', {'name': 'pubdate'})

    # Check if we can extract the datetime
    if date_tag and date_tag.get('datetime'):
        published_date = date_tag['datetime']

    # If we can only extract the text
    elif date_tag:
        published_date = date_tag.text.strip()

    result = {
        'url': url,
        'title': title_tag.text.strip() if title_tag else None,
        'text': article_body.get_text(separator = ' ', strip = True),
        'author': author_tag.text.strip() if author_tag else None,
        'published_date': published_date
    }

    return result

## Process a RSS feed and extract the articles from it
#  @param feed_url The URL of the feed we want to process
def process_rss_feed(feed_url):

    # Initialize the parser and fetch the URL
    feed = feedparser.parse(feed_url)

    if feed.bozo:

        print(f'ERR: Error parsing RSS feed: {feed.bozo_exception}', file=sys.stderr)
        return
    
    # Process each entry in the feed
    for entry in feed.entries:

        # Grab the article URL
        article_url = entry.link

        # Check if the article has already been processed
        if check_article_bq(article_url):
            continue

        article_data = None

        # Extract the article data per the function above
        try:
            article_data = extract_article_data(article_url)
        except:

            print(f"ERR: Error extracting article with URL {article_url}. Ignoring...", file=sys.stderr)
            continue

        try:
            # Grab the title from the RSS feed itself if it wasn't already found
            if not article_data['title']:

                # See if the RSS parser could find a title
                if ('title' in entry):
                    article_data['title'] = entry.title 

                # Set a blank, default otherwise 
                else:
                    article_data['title'] = "Title Not Found"

            # Do the same for author
            if not article_data['author']:

                if ('author' in entry):
                    article_data['author'] = entry.author 
                else:
                    article_data['author'] = "Author Not Found"

            # Same thing for the published date
            if not article_data['published_date']:

                if ('published_parsed' in entry):
                    dt_publish = datetime.fromtimestamp(mktime(entry.published_parsed))
                    article_data['published_date'] = dt_publish.strftime('%Y-%m-%d')
                else:
                    article_data['published_date'] = "Published Date Not Found"
        except:

            print(f"ERR: Error extracting additional fields from RSS feed for article {article_url}. Ignoring...", file=sys.stderr)

        article_data['origin_name'] = feed.feed.title
        article_data['rss_feed'] = feed.feed.link
        
        # Write the article summary to BQ
        write_summary_bq(article_data)
        print(article_data, file=sys.stderr)

## Process a Pub/Sub message and grab the URL in its attributes 
#  @param message Message to be referenced 
def process_message(message):

    # Get the name of the file to process
    target_url = message.attributes['url']

    # Process the RSS feed at this URL
    process_rss_feed(target_url)
    
    # ACK the message and get off the queue
    message.ack()

## Create a streaming pull subscription to the Pub/Sub topic
def streaming_pull_subscription():

    # Initialize the Pub/Sub client
    subscriber = pubsub_v1.SubscriberClient()

    # Define the subscription path
    subscription_path = subscriber.subscription_path(GCP_PROJECT_ID, PUBSUB_SUBSCRIBER)

    def callback(message):

        try:
            # Process the message
            process_message(message)

        except BQException:
            print(f'WARN: Error writing summary to BigQuery. Adding the message back to the queue.', file=sys.stderr)
            message.nack()

    # Setup the streaming client
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    # Wait for KeyboardInterrupt and then exit
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()