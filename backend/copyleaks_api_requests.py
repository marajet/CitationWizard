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

from dataclasses import dataclass
import os #For Loading API Key
from dotenv import load_dotenv
import requests# For CopyLeaks
import tempfile

global API_KEY
global EMAIL
global WEBHOOK_URL

if "API_KEY" not in os.environ or "EMAIL" not in os.environ or "WEBHOOK_URL" not in os.environ:
    # Load environment variables from .env file
    load_dotenv()

    # Get API_KEY from environment variables
    API_KEY = os.environ.get("API_KEY", "MISSING API KEY")
    EMAIL = os.environ.get("EMAIL", "MISSING EMAIL")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "MISSING WEBHOOK URL")

def copyleaks_login(API_KEY, EMAIL):
    # if "API_KEY" not in os.environ or "EMAIL" not in os.environ:
    #     # Load environment variables from .env file
    #     load_dotenv()
    #
    #     # Get API_KEY from environment variables
    #     API_KEY = os.environ.get("API_KEY", "MISSING API KEY")
    #     EMAIL = os.environ.get("EMAIL", "MISSING EMAIL")

    url = "https://id.copyleaks.com/v3/account/login/api"
    payload = {
        "key": API_KEY,
        "email": EMAIL
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    return requests.post(url, json=payload, headers=headers)


def copyleaks_submit_file(input: str, login_key: str) -> tuple[str, dataclass()]:
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
            "properties": {"webhooks": {"status": WEBHOOK_URL+"/webhook/{STATUS}/"+filename},
                           "sandbox": True,
                           "expiration": 2,
                           "pdf": {
                               "create": True,
                               "title": filename
                           },
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


if __name__ == "__main__":
    if "API_KEY" not in os.environ or "EMAIL" not in os.environ:
        # Load environment variables from .env file
        load_dotenv()
    API_KEY = os.environ.get("API_KEY", "MISSING API KEY")
    EMAIL = os.environ.get("EMAIL", "MISSING EMAIL")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "MISSING WEBHOOK URL")
    # print(API_KEY, EMAIL)
    # print(type(API_KEY), type(EMAIL))
    test1 = copyleaks_login(API_KEY, EMAIL)
    access_token = test1.json().get("access_token")
    # print(test1.headers)
    test2 = "our ultimate goal is to create and foster increased participation in the sport of badminton nationwide"
    resp = copyleaks_submit_file(test2, access_token)
    print(resp[1].status_code)
    print(resp[1].headers.get("id"))
    # test3 = defaultFunctionInput("our ultimate goal is to create and foster increased participation in the sport of badminton nationwide")

    ## LOGIN STATUS may need to be handled on frontend code

    # def copyLeaks_check_login_status():
    #     response = requests.get("https://id.copyleaks.com/v3/account/login/api")
    #     if response.status_code == 200:
    #         # Parse the response JSON
    #         data = response.json()
    #
    #         # Check if the user is logged in
    #         if data.get(".expires") > datetime.now():
    #             # If user is logged in, retrieve the login key/token
    #             login_key = data.get("access_token")
    #             return login_key
    #         else:
    #             return None
    #     else:
    #         # Handle request error
    #         print("Error:", response.status_code)
    #         return None

    # def copyleaks_export(scanID: str, login_key: str, webhook_url:str) -> dataclass():
    #     #Currently exportID is same as scan ID
    #     url = "https://api.copyleaks.com/v3/downloads/"+scanID+"/export/"+scanID
    #     payload = {
    #         "results": [
    #             {
    #                 "id": scanID,
    #                 "verb": "POST",
    #                 "headers": [["header-key", "header-value"]],
    #                 "endpoint": webhook_url+"/export/test/results/my-result-id"
    #             }
    #         ],
    #         "pdfReport": {
    #             "verb": "POST",
    #             "headers": [["header-key", "header-value"]],
    #             "endpoint": "https://yourserver.com/export/export-id/pdf-report"
    #         },
    #         "maxRetries": 3,
    #         "crawledVersion": {
    #             "verb": "POST",
    #             "headers": [["header-key", "header-value"]],
    #             "endpoint": "https://yourserver.com/export/test/crawled-version"
    #         },
    #         "completionWebhook": "https://yourserver.com/export/test/completed"
    #     }
    #     headers = {
    #         "Authorization": "Bearer "+login_key,
    #         "Content-Type": "application/json"
    #     }
    #
    #     response = requests.post(url, json=payload, headers=headers)
    #     return response

    # def plagiarism_check(input: defaultFunctionInput) -> plagiarismCheck_output:
    #     if "API_KEY" not in os.environ or "EMAIL" not in os.environ:
    #         # Load environment variables from .env file
    #         load_dotenv()
    #
    #         # Get API_KEY from environment variables
    #         API_KEY = os.environ.get("API_KEY", "MISSING API KEY")
    #         EMAIL = os.environ.get("EMAIL", "MISSING EMAIL")
    #     # access_token = copyLeaks_check_login_status()
    #     if access_token is None:
    #         access_token = copyleaks_login(API_KEY, EMAIL).json().get("access_token")
    #
    #     text = defaultFunctionInput.textInputLiteral
    #     textfile = copyleaks_submit_file(text)