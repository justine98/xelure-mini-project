from downloader import get_cert_loan_links_tuple
import pandas as pd
import requests
import fitz

import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("-d", "--date", help="Date to Process. format=YYmm")
argParser.add_argument("-vo", "--validation_only", action="store_true", help="Validate Existing Files")
argParser.add_argument("-sf", "--store_files", action="store_true", help="Store Files in Datalake")

cert_loan_mapping_dict = {
        'Scheduled Principal' : 'Scheduled Principal',
        'Curtailments' : 'Curtailments',
        'Prepayment' : 'Prepayments in Full',
        'Liquidation Principal' : 'Net Liquidation Proceeds',
        'Repurchase Principal' : 'Repurchased Principal',
    }

cert_columns_list = list(cert_loan_mapping_dict.values())
loan_columns_list = list(cert_loan_mapping_dict.keys())

print(cert_columns_list)
print(loan_columns_list)

if __name__=='__main__':
    args = argParser.parse_args()
    print("args=%s" % args)

    date = args.date
    if date is None:
        raise Exception("No Date Argument Passed")

    if date < "0707":
        raise Exception("No Available Enhanced Loan-Level Data from before 0707")

    if args.validation_only:
        pdf_file_path = f'datalake/cert_data/cert_data_{date}.pdf'
        cert_hold_state_pdf = fitz.open(pdf_file_path, filetype="pdf")

        csv_file_path = f'datalake/loan_data/loan_data_{date}.csv'
    else:
        pdf_file_path, csv_file_path = get_cert_loan_links_tuple(date)
        response = requests.get(pdf_file_path)
        cert_hold_state_pdf = fitz.open(stream=response.content, filetype="pdf")

    print(csv_file_path)
    raw_loan_lvl_data_df = pd.read_csv(csv_file_path)
    print(raw_loan_lvl_data_df.info)

    loan_lvl_data_df = raw_loan_lvl_data_df[loan_columns_list + ['Curtailment Adjustments', 'Principal Losses']]

    print(loan_lvl_data_df)
    loan_lvl_data_df['Curtailments'] = loan_lvl_data_df['Curtailments'] + loan_lvl_data_df['Curtailment Adjustments']
    loan_lvl_data_df.loc[:, ['Liquidation Principal']] = loan_lvl_data_df['Liquidation Principal'] - loan_lvl_data_df['Principal Losses']
    calc_principal_funds_series = loan_lvl_data_df.rename(columns=cert_loan_mapping_dict).sum().loc[cert_columns_list]
    calc_principal_funds_series['Total Principal Funds Available'] = calc_principal_funds_series.sum()
    calc_principal_funds_series = calc_principal_funds_series.round(2)

    extracted_principal_funds_dict = {} 
    for page in cert_hold_state_pdf: 
        text = page.get_text().encode("utf8")

        if "Principal Funds Available" in str(text):
            decoded_text_list = text.decode().splitlines()
            
            for cert_column in cert_columns_list:
                cert_column_idx = decoded_text_list.index(cert_column)
                value_idx = cert_column_idx + 1
                key = decoded_text_list[cert_column_idx].strip()

                print(f"Extracting {key} value")
                value = decoded_text_list[value_idx].strip()

                if "(" in value:
                    negation_flag = -1
                else:
                    negation_flag = 1

                extracted_principal_funds_dict[key] = float(value.replace('(', '').replace(')', '').replace(',','')) * negation_flag

    extracted_principal_funds_series = pd.Series(extracted_principal_funds_dict)
    extracted_principal_funds_series['Total Principal Funds Available'] = extracted_principal_funds_series.sum().round(2)

    principal_funds_comparison_df = extracted_principal_funds_series.compare(calc_principal_funds_series, keep_shape=True, keep_equal=True, result_names=('Extracted', 'Calculated'))
    principal_funds_comparison_df = principal_funds_comparison_df.astype(str)
    principal_funds_comparison_df["Comparison"] = principal_funds_comparison_df['Extracted'] == principal_funds_comparison_df['Calculated']

    print(principal_funds_comparison_df.astype(str))

    valid_columns_list = principal_funds_comparison_df.query("Comparison").index.tolist()
    invalid_columns_list = principal_funds_comparison_df.query("~Comparison").index.tolist()

    if len(invalid_columns_list) == 0:
        print("No Errors Found.")
        if args.store_files:
            print("Storing Files.")
            raw_loan_lvl_data_df.to_csv(f'datalake/loan_data/loan_data_{date}.csv')
            cert_hold_state_pdf.save(f'datalake/cert_data/cert_data_{date}.pdf')
            pd.DataFrame(extracted_principal_funds_series).transpose().to_csv(f'datalake/cert_data/summary_cert_data_{date}.csv', index=False)
        else:
            print("Not Storing Files.")
    else:
        print("Errors Found in Column(s) when calculating sum of values")
        print(invalid_columns_list)