# Identify plagiarism from the web -- Plagiarism-Checker/other tool (Simon)
# Input: list of literal input, untokenized
# write to text file using function, and then input that into copy leaks
# IMPORTANT: This is the NLP PART!
# calculate some threshold for top index, generate parenthetical from source?
# output: list of dicts with error type, text to fix, and suggested fix(tokenized)
# #Copyleaks API key
# Make ..env fil, .gitignore, .env, so that the ..env file isn't pushed and then:
# api key in   ..env file as API_KEY
# Add ..env file to .gitignore, commit and do not

# input, don't assume it starts sentence or ends with period, could be a lot of text, need to
# run line by line. Could split by period.
# consider using regex to account for MORE cases for text splitting
import time
from dataclasses import dataclass
#For Loading API Key
import os
from dotenv import load_dotenv
import requests
import tempfile
import json as js


global COPYLEAKS_API_KEY
global EMAIL
global WEBHOOK_API_KEY
global WEBHOOK_URL_ID

if "COPYLEAKS_API_KEY" not in os.environ or "EMAIL" not in os.environ or "WEBHOOK_URL_ID" not in os.environ or "WEBHOOK_API_KEY" not in os.environ:
    # Load environment variables from .env file
    load_dotenv()

    # Get API_KEY from environment variables
    COPYLEAKS_API_KEY = os.environ.get("API_KEY", "MISSING API KEY")
    EMAIL = os.environ.get("EMAIL", "MISSING EMAIL")
    WEBHOOK_API_KEY = os.environ.get("WEBHOOK_API_KEY", "MISSING WEBHOOK API")
    WEBHOOK_URL_ID = os.environ.get("WEBHOOK_URL_ID", "MISSING WEBHOOK URL")

@dataclass
class plagiarism_check_output:
    typeOfError: str
    textToFix: str
    suggestedFix: str
    url: str

    def to_dict(self):  # Make sure to define a to_dict method
        return {
            "typeOfError": self.typeOfError,
            "textToFix": self.textToFix,
            "suggestedFix": self.suggestedFix,
            "url": self.url
        }

def copyleaks_login():
    # if "API_KEY" not in os.environ or "EMAIL" not in os.environ:
    #     # Load environment variables from .env file
    #     load_dotenv()
    #
    #     # Get API_KEY from environment variables
    #     API_KEY = os.environ.get("API_KEY", "MISSING API KEY")
    #     EMAIL = os.environ.get("EMAIL", "MISSING EMAIL")

    url = "https://id.copyleaks.com/v3/account/login/api"
    payload = {
        "key": COPYLEAKS_API_KEY,
        "email": EMAIL
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get("access_token")


def copyleaks_submit_file(input: str, login_key:str) -> tuple[str, dataclass()]:
    # May want to sort results of request?
    # if "WEBHOOK_URL" not in os.environ:
    #     load_dotenv()
    #     WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "MISSING WEBHOOK URL")
    scanID = ""
    with tempfile.NamedTemporaryFile(mode='r+', suffix='.txt') as temp_file:
        temp_file.write(input)
        filename = os.path.basename(temp_file.name)
        scanID = filename
        url = "https://api.copyleaks.com/v3/scans/submit/file/"+filename
        payload = {
            "base64": "SGVsbG8gd29ybGQh",
            "filename": filename,
            # Sandbox turned to true to save credits: remove later!
            "properties": {"webhooks": {"status": "https://webhook.site/"+WEBHOOK_URL_ID + "/webhook/{STATUS}/" + filename},
                           "sandbox": True,
                           "expiration": 2,
                           # "pdf": {
                           #     "create": True,
                           #     "title": filename
                           # },
                           # Adjust 1-3, 1= fastest and 3= slowest, most thorough
                           "sensitivityLevel": 3}
        }
        headers = {
            "Authorization": "Bearer " + login_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.put(url, json=payload, headers=headers)
        return scanID, response

def webhook_fetch_latest_data():
    url = "https://webhook.site/token/"+WEBHOOK_URL_ID+"/requests?sorting=newest"

    headers = {"api-key": WEBHOOK_API_KEY,
               "Content-Type": "application/json",
               "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    return response

def plagiarism_check(full_input: str, login_key: str) -> list[dict]:
    inputs = full_input.split(".")
    errors = [{}] * len(inputs)
    print(len(inputs))
    for i in range(len(inputs)):
        copyleaks_submit_file(inputs[i], login_key)

    threshold = 49 # for comparison with aggregated Score
    json = webhook_fetch_latest_data().json().get("data")
    print(len(json))
    for i in range(len(inputs)):
        singlejson = json[i]
        results = singlejson["content"]
        results = results[results.find("\"score\":{\""):]
        scores = js.loads(results[results.find("{\"identicalWords"):results.find(",\"internet")])
        aggregatedScore = scores["aggregatedScore"]
        if aggregatedScore > threshold:
            internet = js.loads(results[results.find("{\"url"):results.find("],\"database")])
            url = internet["url"]
            suggestedFix = None
            try:
                author = internet["metadata"]["author"]
                # author is in metadata in internet, so is publication date
                publishDate = internet["metadata"]["publishDate"]
                suggestedFix = "(" + author + ", " + publishDate + ")"
            except KeyError:
                pass
            # replace 0 with some index from loop
            error = plagiarism_check_output(typeOfError="Plagiarized text from Web",
                                            textToFix=inputs[i],
                                            suggestedFix=suggestedFix,
                                            url=url).to_dict()
            errors[i] = error

    return [error for error in errors if error is not None]


if __name__ == "__main__":
    if "API_KEY" not in os.environ or "EMAIL" not in os.environ:
        # Load environment variables from .env file
        load_dotenv()
    COPYLEAKS_API_KEY = os.environ.get("COPYLEAKS_API_KEY", "MISSING API KEY")
    EMAIL = os.environ.get("EMAIL", "MISSING EMAIL")
    WEBHOOK_URL_ID = os.environ.get("WEBHOOK_URL_ID", "MISSING WEBHOOK URL")
    # print(COPYLEAKS_API_KEY, EMAIL)
    access_token = copyleaks_login()
    print(access_token)
    test2 = "our ultimate goal is to create and foster. increased participation in the sport of badminton nationwide"
    # resp = copyleaks_submit_file(test2, access_token)
    # print(resp[1].status_code)
    # print(resp[1].headers.get("id"))
    test = plagiarism_check(test2, access_token)
    print(test)