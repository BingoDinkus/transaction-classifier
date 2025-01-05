# transaction-classifier

## Purpose
My credit union uses multiple 3rd party services for their web solution and this prevents [Monarch Money](https://www.monarchmoney.com/) from being able to pull credit card transactions. I have to manually download transactions as a csv, and then reformat the results and add categories each transaction. To simplify this process and add consistency to merchant names and categories, I've set up a basic Python script using [DuckDB](https://duckdb.org/) to automate all but the exporting and importing steps. This script reads the downloaded transcations csv, matches it to a lookup table (stored in lookup.csv) to rename  merchats and add categories, and then spits out a csv that can be uploaded to Monarch Money.

## Setup
1. Rename `app_config.sample.toml` to `app_config.toml`
2. Edit `app_config.toml` as needed. Here's an explanation of the supported fields:
   1. `account_name`: The label you want to show for the `Account` field of the output file
   2. `source_csv_path`: The file path to the transactions csv file you downloaded
   3. `cleanup_old_files`: If true, old files created by the application will be deleted at startup. The files that will be deleted are as follows:
      * duplicates.csv
      * monarch upload.csv
      * unmatched transactions.csv
   4. `output_unmatched_records`: If true, a file named "unmatched transactions.csv" will be created, showing all the merchants that do not have a category
   5. `allow_unmatched_records`: If false, "monarch upload.csv" will be not generated when unmatched merchants are found. This requires you to handle every merchant before creating the upload file.
3. Rename `lookup.sample.csv` to `lookup.csv`
4. Edit `lookup.csv` to contain the mapping rules / patterns for how transactions are classified. Some sample entries have been provided to show how the rules should be defined.
   1. **Pattern**: The SQL [pattern](https://duckdb.org/docs/sql/functions/pattern_matching.html) each transaction is matched against
   2. **Merchant**: The merchant name to use in the output file
   3. **Category**: The category to use in the output file
5. Additional edits:
   1. You will likely need to edit `lookup_query` to use column names in your transactions file
   2. My transactions file has charges as positive amounts and payments as negative amounts. Monarch defaults to opposite of this. If your file is the same, you will either need to leave the `* -1` or change the account setting in Monarch. If your file is not the same, remove the `* -1`

## Design Choices
1. Pattern matching can create duplicates, and we do not want the same transaction appearing in the results multiple times.
   1. In most situations, it makes sense to add a priority for each pattern and limit the results to the top priority match
   2. However, for this project, I wanted a cleaner list of patterns, and decided to have the process fail if multiple patterns matched the same transaction

## About Monarch Money
I started using Monarch Money after Intuit killed off Mint. If you're interested in signing up, here's my referral code: https://www.monarchmoney.com/referral/ee628k9x4i. If you use my referral code, I'll get a $15 credit, and you'll get a 30 day free trial.