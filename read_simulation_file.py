import pandas as pd
from converters import make_franchises_to_names

def get_file_data(seasonid, sort_by):
    converter = make_franchises_to_names()
    str_converter = {f"{str(key)}.0": value for key, value in converter.items()}
    file_path = f'simulations/{seasonid}_simulations.csv'

    # Read the CSV data into a DataFrame
    df = pd.read_csv(file_path)
    print(f"{len(df)} simulations found for {seasonid}")

    # Define a helper function to calculate percentages
    def calculate_percentage(df, threshold):
        return (df.apply(lambda col: (col > threshold).sum()) / len(df) * 100).round(2)

    # Calculate the desired metrics
    metrics = {
        'makePlayoffs': calculate_percentage(df, 0),
        'makeSecondRound': calculate_percentage(df, 1),
        'makeConferenceFinal': calculate_percentage(df, 2),
        'makeCupFinal': calculate_percentage(df, 3),
        'stanleyCupChampion': calculate_percentage(df, 4)
    }

    # Concatenate DataFrames along columns axis
    final_df = pd.concat(metrics, axis=1)
    final_df = final_df.sort_values(by=sort_by, ascending=False)

    # Convert percentages to string format with '%' sign
    final_df = final_df.astype(str) + '%'
    final_df = final_df.reset_index().rename(columns={'index': 'franchiseId'})
    final_df['franchiseId'] = final_df['franchiseId'].map(str_converter)

    print(final_df)
    return final_df

def main():
    get_file_data(20242025, 'makePlayoffs')

if __name__ == '__main__':
    main()
