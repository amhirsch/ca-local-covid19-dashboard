# California Local COVID-19 Dashboard

Dash dashboard to visualize the case rate of COVID-19 over time in California communities.
Data is provided by the Los Angeles Times and Los Angeles County Department of Public Health.

## Setup
### Python Environment
Clone the repository and install the pipenv environment with `$python3 -m pipenv install`.
### Acquire Data Sources
1. Navigate to the LACDPH [COVID-19 Data Dashboard](http://dashboard.publichealth.lacounty.gov/covid19_surveillance_dashboard/) and download the "14-Day Community Cases" and "7-Day Community Cases" tables into this directory.
2. Use the `fetch-latimes-place-totals.sh` Bash script to get the latest COVID-19 case totals compiled by the Los Angeles Times.

## Deploy
Run the dashboard app with `$python3 -m pipenv run python app.py`.
The live dashboard is hosted at [`localhost:8050`](http://localhost:8050).