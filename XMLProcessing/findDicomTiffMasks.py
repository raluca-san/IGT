# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 10:18:00 2017

The XML file : \\cochlea.artorg.unibe.ch\IGT\Projects\LIVER\_Clinical_Data\Laparoscopic_Liver_Surgery\Bern\Pat_BP_0010922318_2015-10-13_14-27-30\Technical Report\MeVis Data\datasets\BP.xml
contains tumors tags <Tumor> </Tumour> where the filename is located

The segmented tumor can be found in the MeVis DICOM file “BP_0010922318_0001021.dcm”.

@author: Raluca Sandu
"""

import os
import time
import argparse
import pandas as pd
import untangle as ut



srvPath = '\\\\cochlea.artorg.unibe.ch\IGT\Projects\LIVER\_Clinical_Data\Laparoscopic_Liver_Surgery'
print('searching in ', srvPath)
foundData = []

for dirname, dirnames, filenames in os.walk(srvPath):
    if dirname.find('datasets') == -1:
        continue
    # find the datasets folder
    for filename in filenames:
        # find the xml file ": PatientIntials.xml"
        idxPat = dirname.upper().lower().find('pat_') + 4
        idxPatEnd = dirname.find('_', idxPat)
        patientInitials = dirname[idxPat:idxPatEnd]
        clinic = dirname[len(srvPath)+1:dirname.find('\\', len(srvPath)+2)]

        file, fileExtension = os.path.splitext(filename)

        if fileExtension.lower().endswith('.xml') and patientInitials == file:
            roiData = []
            xmlFilePathName = os.path.join(dirname, filename)
            xmlFilePathName_norm = os.path.normpath(xmlFilePathName)
             # open XML filename and extract the path of the tumor segmentation map
            try:
                obj = ut.parse(xmlFilePathName_norm)
                data = obj.HEPAVISION_INFO.IMAGEDATA
                k = 0
                for imagedata in data:
                    rois = imagedata.ROI
                    for roi in rois:
                        try:
                            result = roi.RESULT
                            # save the obj id and filepaths to be able to retrieve the source img on which the segmentation was based on
                            roiData.append({
                                    'objID': roi.OBJ_ID.cdata,
                                    'FilePathSourceImg' : roi.FILENAME.cdata[2:],
                                    'ImageType' : roi.cdata
                            })
                            for re in result:
                                if 'Tumor' in re.cdata:
                                    k+=1
                                   
                                    # remove the "./" in front of the filename
                                    filenameTumor = re.FILENAME.cdata[2:]
                                    # the DICOM contains only the metadata
                                    filepathTumorDICOM = os.path.join(dirname,filenameTumor)
                                    # the TIFF contains the binary image mask
                                    filepathTumorTiff = os.path.join(dirname, filenameTumor[:-4]+'.tif')
                                    # save the obj id
                                    basedon_ROI_OBJID = re.BASED_ON.cdata

                        except Exception:
                            print('')
                    if k>1:  print('Tumors found:',str(k))
                    # iterate through the list of dict ROIs to find segmentation source based on OBJ_ID
                    filepathSourceImg, ImageType = next((item["FilePathSourceImg"], item["ImageType"])for item in roiData if item["objID"] == basedon_ROI_OBJID)
                    
                    foundData.append({
                                    'PatientID' : obj.HEPAVISION_INFO.PATIENT.PID.cdata,
                                    'PatientIn': patientInitials,
                                    'Clinic' : clinic,
                                    'PathXML' : xmlFilePathName,
                                    'PathDicomTumor': filepathTumorDICOM,
                                    'PathTiffTumor': filepathTumorTiff,
                                    'PathDicomSource':  os.path.join(dirname, filepathSourceImg),
                                    'ImageType' : ImageType
                                    
                                })
            except Exception:
                print('XML file structure problem:',xmlFilePathName)

#%%

df = pd.DataFrame(foundData)  # convert list of dicts to pandas dataframe
timestr = time.strftime("%Y%m%d-%H%M%S")
filename = '3DMevisSegmentationMasks_' + timestr + '.xlsx'
writer = pd.ExcelWriter(filename)
df.to_excel(writer,sheet_name='MevisFilepaths', index=False)