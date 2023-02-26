import argparse
import datetime
import glob
import json
from logging import Logger
import os
import re
import subprocess
import sys
import google.cloud.logging


# function to process a line
def process_line(line, unique_words, logger):
    # there is a one record per line in the jsonl file
    # so we can just read the line as json
    # and add the word to the set
    # log debug with logger
    logger.debug(f"line: {line}")
    # if BOOKWORD not present, skip the line
    if "BOOKWORD" not in json.loads(line):
        print(line)
        return
    word = json.loads(line)["BOOKWORD"]
    unique_words.add(word)


# function to process file line by line using as little memory as possible
def process_file(file, unique_words, args):
    # if the file is in the gcp bucket
    # download it to the local tmp directory
    # create a downloads directory if it doesn't exist
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    if args.bucket:
        bucket_file_name = f"gs://{args.bucket}/{file}"
        subprocess.check_output(
            f"gsutil cp {bucket_file_name} downloads/{file}", shell=True
        )
        file = f"downloads/{file}"

    # open the file
    with open(file, "r") as f:
        # read the first line
        line = f.readline()
        # while the line is not empty
        while line:
            # process the line
            process_line(line, unique_words, logger)
            # read the next line
            line = f.readline()


def get_jsonl_files(jsonl_dir, bucket=None):
    if bucket:
        # get the list of jsonl files from the gcp bucket
        # save only the file name
        jsonl_files = [
            f"gs://{bucket}/{f.split('/')[-1]}"
            for f in subprocess.check_output(
                f"gsutil ls gs://{bucket}/*.jsonl", shell=True
            )
            .decode("utf-8")
            .split()
        ]

        # remove bucket from the file name
        jsonl_files = [f.replace(f"gs://{bucket}/", "") for f in jsonl_files]

        # regex to match epoch timestamped files
        # e.g. 1600000000.jsonl
        epoc_regex = r"\d{10}.jsonl"

        # remove filest that are not output.jsonl or matches regexp {epoc}.jsonl
        jsonl_files = [
            f for f in jsonl_files if f == "output.jsonl" or re.match(epoc_regex, f)
        ]

    else:
        # get the list of jsonl files from the local directory
        jsonl_files = glob.glob(f"{jsonl_dir}/*.jsonl")
    return jsonl_files


if __name__ == "__main__":
    # setup logging for gcp
    # https://cloud.google.com/logging/docs/setup/python
    # Imports the Cloud Logging client library

    # Instantiates a client
    client = google.cloud.logging.Client()

    # Retrieves a Cloud Logging handler based on the environment
    # you're running in and integrates the handler with the
    # Python logging module. By default this captures all logs
    # at INFO level and higher
    client.setup_logging()

    # get the jsonl files from bucket or local directory
    # take it from the command line
    # or default to the local directory
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl_dir", default="feeds")
    parser.add_argument("--bucket", required=False)
    args = parser.parse_args()

    # create a logger
    logger = Logger("word_count")

    # log that the script started

    logger.info("Word count script started")

    # get the list of jsonl files
    jsonl_files = get_jsonl_files(args.jsonl_dir, args.bucket)

    # log all the files to be processed
    # with a logger
    logger.debug(f"jsonl_files: {jsonl_files}")

    # check that feed_directory/output.jsonl exists in the list
    # if not, exit
    # if it does, remove it from the list
    #
    for file in jsonl_files:
        if file.endswith("output.jsonl"):
            jsonl_files.remove(file)
            break
    else:
        logger.error("output.jsonl not found")
        sys.exit(1)

    unique_words = set()

    # create a dictionary to store the number of unique words
    #  per date
    #  key: date
    #  value: number of unique words
    date_unique_words = {}

    # first process "output.jsonl"
    # then process the rest of the files
    process_file("output.jsonl", unique_words, args)

    # put number output.jsonl to metrics dated as Feb 1, 2023
    # with a logger
    # date for Feb 1, 2023
    # 2023-02-01T00:00:00Z
    output_jsonl_date = "2023-02-01T00:00:00Z"

    # add the number of unique words to the dictionary
    date_unique_words[output_jsonl_date] = len(unique_words)

    # report the number of unique words
    # with a logger
    logger.info(
        f"Number of unique words in inital state at {output_jsonl_date}: {len(unique_words)}"
    )
    # also print it to stdout
    print(
        f"Number of unique words in inital state at {output_jsonl_date}: {len(unique_words)}"
    )

    for file in jsonl_files:
        process_file(file, unique_words, args)
        # report the number of unique words after each file
        # with a logger

        # get metrics date from the file name
        # e.g. 1600000000.jsonl
        # by picking up digits before the first dot
        file_date = re.findall(r"\d+", file)[0]
        # convert to date
        file_timestamp = datetime.datetime.fromtimestamp(int(file_date)).isoformat()

        # add the number of unique words to the dictionary
        date_unique_words[file_timestamp] = len(unique_words)

        # report the number of unique words
        # with a logger
        logger.info(
            f"Number of unique words after {file} at {file_timestamp}: {len(unique_words)}"
        )
        # also print it to stdout
        print(
            f"Number of unique words after {file} at {file_timestamp}: {len(unique_words)}"
        )

    # write the dictionary to a json file
    with open("feeds/metrics.json", "w") as f:
        json.dump(date_unique_words, f)

    # if the bucket is specified
    # upload the metrics.json file to the bucket
    if args.bucket:
        subprocess.check_output(
            f"gsutil cp feeds/metrics.json gs://{args.bucket}/", shell=True
        )

    # log that the script finished
    logger.info("Word count script finished")
