import pandas as pd
import os

def split_excel_to_csv():
    print("Starting Excel to CSV conversion...")
    
    excel_path = "data/raw_data.xlsx"
    
    # Check if the file actually exists before trying to open it
    if not os.path.exists(excel_path):
        print(f"Error: Could not find {excel_path}. Please check the data folder.")
        return

    try:
        # sheet_name=None tells Pandas to read EVERY sheet in the file
        # It returns a dictionary: {'SheetName1': DataFrame, 'SheetName2': DataFrame}
        all_sheets = pd.read_excel(excel_path, sheet_name=None)
        
        for sheet_name, df in all_sheets.items():
            
            clean_name = sheet_name.lower().strip()
            csv_filename = f"data/{clean_name}.csv"
            
            df.to_csv(csv_filename, index=False)
            print(f"✅ Successfully converted sheet '{sheet_name}' -> '{csv_filename}'")
            
        print("All sheets converted successfully! You can now run the PySpark ETL.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    split_excel_to_csv()