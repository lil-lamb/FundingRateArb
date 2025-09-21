# First, we import the 'requests' library to talk to the internet
# and 'pandas' to easily handle and save data.
import requests
import pandas as pd
# from IPython.utils.text import date_format

# This is the CoinMarketCap Fear & Greed API endpoint.
# It's where we will request our data from.
url = "https://api.alternative.me/fng/"

# The API requires an authentication key (like a password) in the request headers.
# You must replace "YOUR_KEY_HERE" with your own CoinMarketCap API key.
headers = {
    # "X-CMC_PRO_API_KEY": "b325e69c-4b14-4027-87e9-15dbec745d0e"
}

# 'params' is where we define extra options for our request.
# Here, 'limit' means "how many results do we want?" (30 days in this case).
params = {
    "limit": 0
}

# Send the GET request to the API with our URL, headers, and parameters.
# The '.json()' method converts the API\'s response from raw text into a Python dictionary.
response = requests.get(url, headers=headers, params=params).json()

# The data we want is stored inside the 'data' key of the JSON.
# We convert it into a Pandas DataFrame so we can easily work with it like a table.
df = pd.DataFrame(response['data'])

# The 'timestamp' column is originally just a string.
# We convert it into an actual datetime object so Excel will read it as a date.
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

# Save the DataFrame into an Excel file on your computer.
# 'index=False' means "don’t save the row numbers."
df.to_excel("fear_greed_data.xlsx", index=False)

# Let us know that everything worked and where the file is saved.
print("Saved to fear_greed_data.xlsx")
