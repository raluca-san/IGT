# -*- coding: utf-8 -*-
"""
@author: Raluca Sandu
"""
import os
import pandas as pd
import argparse
from ast import literal_eval

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--input_batch_proc_paths", required=True, help="input csv file for batch processing")

    args = vars(ap.parse_args())

    if (args["input_batch_proc_paths"]) is not None:
        print("Path to CSV that has directory paths and subcapsular lesion info: ", args["input_batch_proc_paths"])

    df_download_db_all_info = pd.read_excel(args["input_batch_proc_paths"])
    frames = []  # list to store all df per lesion.

    df_download_db_all_info['Patient_Dir_Paths'].fillna("[]", inplace=True)
    df_download_db_all_info['Patient_Dir_Paths'] = df_download_db_all_info['Patient_Dir_Paths'].apply(literal_eval)

    for row in df_download_db_all_info.itertuples(index=False):
        rootdir = row.Patient_Dir_Paths[0]
        for subdir, dirs, files in os.walk(rootdir):
            for file in sorted(files):
                if file == 'tpes.xlsx':
                    # check file extension is xlsx
                    excel_input_file_per_lesion = os.path.join(subdir, file)
                    df_single_lesion = pd.read_excel(excel_input_file_per_lesion)
                    df_single_lesion.rename(columns={'LesionNr': 'Lesion_ID', 'PatientID': 'Patient_ID'}, inplace=True)
                    try:
                        patient_id = df_single_lesion.loc[0]['Patient_ID']
                        if len(patient_id) > 3:
                            df_single_lesion['Patient_ID'] = df_single_lesion['Patient_ID'].apply(
                                lambda x: x.split('-')[1])
                            patient_id = df_single_lesion.loc[0]['Patient_ID']
                        if patient_id == '01':
                            print('BAD Patient M01')
                            df_single_lesion['Patient_ID'] = 'M01'
                            df_single_lesion['Patient_ID'] = df_single_lesion['Patient_ID'].apply(
                                lambda x: x.split('-')[1])
                        # if patient_id == 'MAV-G10':
                        #     print('BAD Patient G10')
                        #     df_single_lesion['Patient_ID'] = 'G10'
                        # if patient_id == 'MAV-G11':
                        #     print('BAD Patient G11')
                        #     df_single_lesion['Patient_ID'] = 'G11'
                        # if patient_id == 'MAV-G17':
                        #     print('BAD Patient G17')
                        #     df_single_lesion['Patient_ID'] = 'G17'
                    except Exception as e:
                        print(repr(e))
                        print("Path to bad excel file:", excel_input_file_per_lesion)
                        continue
                    try:
                        df_single_lesion['Lesion_ID'] = df_single_lesion['Lesion_ID'].apply(
                                lambda x: 'MAV-' + patient_id + '-L' + str(x))
                    except Exception as e:
                        print(repr(e))
                        print("Path to bad excel file:", excel_input_file_per_lesion)
                        continue
                    frames.append(df_single_lesion)

#%%
print('no of lesions found:', len(frames))
result = pd.concat(frames, ignore_index=False)
result.drop_duplicates(subset=['Lesion_ID'], inplace=True)
result.loc[result['Patient_ID'] == 'MAV-G10', 'Patient_ID'] = 'G10'
result.loc[result['Patient_ID'] == 'MAV-G11', 'Patient_ID'] = 'G11'
result.loc[result['Patient_ID'] == 'MAV-G17', 'Patient_ID'] = 'G17'

print('No of Needles:', len(result))

df_patient = result[result['Patient_ID'] == 'MAV-G10']
filepath_excel = "TPEs_ECIO.xlsx"
writer = pd.ExcelWriter(filepath_excel)
result.to_excel(writer, sheet_name='TPEs', index=False, float_format='%.4f')
writer.save()
df_final = pd.merge(df_download_db_all_info, result, how="outer", on=['Patient_ID', 'Lesion_ID'])
# write treatment id as well. the unique key must be formed out of: [patient_id, treatment_id, lesion_id]
filepath_excel = "TPEs_MAVERRIC_ECIO.xlsx"
writer = pd.ExcelWriter(filepath_excel)
df_final.to_excel(writer, sheet_name='TPEs', index=False, float_format='%.4f')
writer.save()
