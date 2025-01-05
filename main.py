import duckdb
from pathlib import Path
import logging
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)-10s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

def main():
    with open('app_config.toml', 'rb') as config_file:
            config = tomllib.load(config_file)

    # Clean-up old files
    if config['cleanup_old_files']:
        logger.info('Deleting old files...')
        Path('duplicates.csv').unlink(missing_ok=True)
        Path('monarch upload.csv').unlink(missing_ok=True)
        Path('unmatched transactions.csv').unlink(missing_ok=True)

    # Use lookup.csv to add Merchant and Category
    # Name and order columns to match CSV format needed by Monarch Money
    lookup_query = '''
        select
            dest."Transaction Date" as Date
            , coalesce(lkup.Merchant, dest.Description) as Merchant
            , lkup.Category
            , $account_name as Account
            , dest.Description as "Original Statement"
            , 'Reference #: ' || dest."Ref#" as Notes
            , dest.Amount * -1 as Amount
            , null as Tags
        from
            read_csv($source_csv_path) as dest
        left join
            read_csv("lookup.csv") as lkup
            on dest.Description ilike lkup.Pattern
    '''

    # Check for duplicates in the results
    # If duplicates are found, the process will fail and the patterns will need to be updated to be more specific
    duplicate_query = '''
        select *
        from results
        qualify count(*) over (partition by Notes) > 1
        order by Notes
    '''

    # This query identifies results without a category
    unmatched_query = '''
        select
            "Original Statement"
            , Merchant
            , count(*) as Transaction_Count
        from
            results
        where
            Category is null
        group by
            all
        order by
            "Original Statement"
    '''

    params = {
        'account_name': config['account_name'],
        'source_csv_path': config['source_csv_path']
    }

    logger.info('Generating "results" dataset')
    results = duckdb.sql(lookup_query, params=params)
    logger.info(f'> Results dataset contains {results.shape[0]} record(s)')

    logger.info('Generating "duplicates" dataset')
    duplicates = duckdb.sql(duplicate_query)
    logger.info(f'> Duplicates dataset contains {duplicates.shape[0]} record(s)')

    if duplicates.shape[0] > 0:
        logger.error('Duplicates found, outputting "duplicates.csv" for review')
        duplicates.write_csv('duplicates.csv')
        raise Exception('Pattern matching has created duplicates. See duplicates.csv for details.')

    if config['output_unmatched_records']:
        logger.info('Generating "unmatched_records" dataset')
        unmatched_records = duckdb.sql(unmatched_query)
        logger.info(f'> Unmatched Records dataset contains {unmatched_records.shape[0]} record(s)')

        if unmatched_records.shape[0] > 0:
            unmatched_records.write_csv('unmatched transactions.csv')
            if config['allow_unmatched_records']:
                logger.warning('Unmatched merchants found, outputting "unmatched transactions.csv" for review')
                unmatched_records.write_csv('unmatched transactions.csv')
            else:
                logger.error('Unmatched Merchants are not allowed, outputting "unmatched transactions.csv" for review')
                raise Exception('Unmatched Merchants found. See "unmatched transactions.csv" for details.')

    logger.info('Writing results to "monarch upload.csv"')
    results.write_csv('monarch upload.csv')

    logger.info('Process complete')

if __name__ == '__main__':
    main()