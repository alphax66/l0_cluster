import pandas as pd
import json

def load_and_process_data(filepath):
    # Load the JSON data
    with open(filepath, 'r') as file:
        data = json.load(file)

    # Normalize the data into a DataFrame
    df = pd.json_normalize(data['data']['get_execution']['execution_succeeded']['data'])

    # Convert 'first_day' and 'last_day' from string to datetime
    df['first_day'] = pd.to_datetime(df['first_day'])
    df['last_day'] = pd.to_datetime(df['last_day'])
    df['time'] = pd.to_datetime(df['time'])
    df['brige_date_range'] = (df['time'] - df['time'].min()).dt.days // 2
    df['time'] = df['time'].astype(str)

    # Extract year and month from 'last_day'
    df['last_year'] = df['last_day'].dt.year
    df['last_month'] = df['last_day'].dt.month

    # Define the range intervals for 'first_day' and 'tc'
    df['first_day_range'] = (df['first_day'] - df['first_day'].min()).dt.days // 10
    df['tc_range'] = df['tc'] // 10


    # Group by transaction count, first_day, source chains mask, last year, and last month
    grouped = df.groupby(['brige_date_range','first_day_range','tc_range', 'source_chains_mask', 'last_year', 'last_month'])

    # Assign a unique cluster ID to each group
    df['precise_cluster'] = grouped.ngroup()

    return df

def filter_and_export_clusters(df):
    # Remove duplicates first to ensure accurate counts
    df_unique = df.drop_duplicates(subset=['user_address'])
    # Filter clusters with more than 5 wallets
    cluster_counts = df_unique['precise_cluster'].value_counts()
    large_clusters = cluster_counts[cluster_counts > 50].index

    # Prepare the DataFrame for Excel export
    all_data = []
    for cluster_id in large_clusters:
        # Filter the dataframe for the current cluster
        cluster_data = df[df['precise_cluster'] == cluster_id]
        # Drop duplicates based on 'user_address'
        cluster_data = cluster_data.drop_duplicates(subset=['user_address'])
        # Select and rename columns
        cluster_data = cluster_data[['user_address', 'tc', 'first_day', 'last_day', 'days', 'source_chains_mask', 'input_tx_hash', 'time', 'tx_gas_limit']]
        cluster_data.columns = ['Wallet Address', 'Transaction Count', 'First Active Day', 'Last Active Day', 'Active Days', 'Source Chains Mask', 'Input tx hash', 'Bridge Tx Time', 'Tx Gas Limit']
        
        # Create a separator row with the cluster ID
        separator = pd.DataFrame({'Wallet Address': [f'Cluster {cluster_id}'], 'Transaction Count': [''], 'First Active Day': [''], 'Last Active Day': [''], 'Active Days': [''], 'Source Chains Mask': [''], 'Input tx hash': [''], 'Bridge Tx Time': [''], 'Tx Gas Limit': ['']})
        all_data.append(separator)
        all_data.append(cluster_data)

    # Concatenate all data into one DataFrame
    final_df = pd.concat(all_data, ignore_index=True)

    # Save to Excel
    final_df.to_excel('./clusters_new/fack_op_time.xlsx', index=False, engine='openpyxl')

def main():
    filepath = './json_new/fack_op_time.json'  # Update this path to your JSON file
    df = load_and_process_data(filepath)
    filter_and_export_clusters(df)

if __name__ == "__main__":
    main()
