## Sources

* Los Angeles Times - [California Coronavirus Data](https://github.com/datadesk/california-coronavirus-data)
* Los Angeles County Department of Public Health - [COVID-19 Data Dashboard](http://dashboard.publichealth.lacounty.gov/covid19_surveillance_dashboard/)

## Data definitions
* **Sample period**: A 7 or 14 day window in which the cumulative count of new cases is taken.
In the case of a 14 day window, the cumulative case count is divided by two to get a one week equivalent.
* **New cases**: The raw count of new cases in a sample period.
* **Case rate**: The count of new cases in a sample period, normalized to a population of 100,000 people.
* **Reported date**: The day which a case was reported to the health department and added to the count of cases for a particular area.
This is used for the Los Angeles Times data source.
* **Episode date**: The earliest date recorded where a person first experience symptoms, a specimen was collected for testing, a laboratory receiving the specimen, or the day which a positive test was reported to the health department.
It takes several days between symptoms or testing for a positive result to be returned and reported, so this measurement has an inherit lag in reporting.
This is used for the Los Angeles County Department of Public Health data source.

GitHub: [amhirsch/ca-local-covid19-dashboard](https://github.com/amhirsch/ca-local-covid19-dashboard)