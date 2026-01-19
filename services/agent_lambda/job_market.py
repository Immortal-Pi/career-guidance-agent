from apify_client import ApifyClient
import os 
from dotenv import load_dotenv

load_dotenv()
# Initialize the ApifyClient with your API token
client = ApifyClient(os.getenv('APIFY_API'))

# Prepare the Actor input
run_input = {
    "scrapeJobs.searchUrl": "https://www.indeed.com/jobs?q=sales&l=New+York%2C+NY&vjk=b28e7b80d0399215",
    "scrapeJobs.scrapeCompany": False,
    "count": 10,
    "outputSchema": "raw",
    "skipSimilarJobs": True,
    "findContacts": False,
    "findContacts.contactCompassToken": "",
    "findContacts.position": [
        "founder",
        "director",
    ],
}

# Run the Actor and wait for it to finish
run = client.actor("ecy4Yh6oyD3hzsARO").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)