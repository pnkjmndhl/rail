# this script gets the subset of the original excel file thats present in the network and plots it on transfers.shp

from rail import *
import arcpy

arcpy.env.overwriteOutput = True
arcpy.env.workspace = r'C:/GIS/'

intermediate_csv = "intermediate/transfers.csv"

# new data frames from files
transfer = pandas.ExcelFile(transfer_xl_file).parse("BASE")
all_aar_csv_df = pandas.read_csv(all_aar_csv)


def get_network_railroad_aar_dict():
    dummy = []
    for row in arcpy.SearchCursor(link_shp):
        dummy.append(
            [row.getValue("RR1"), row.getValue("RR2"), row.getValue("RR3"), row.getValue("RR4"), row.getValue("RR5")])
    flat_list = list(set([x for sublist in dummy for x in sublist]))
    flat_list.remove(0)
    new_dict = {x: list(all_aar_csv_df[all_aar_csv_df.ABBR == str(x)]['AARCode'].values) for x in flat_list}
    reverse_dict = {value: key for key in new_dict for value in new_dict[key]}
    return reverse_dict


my_aar_dict = get_network_railroad_aar_dict()

# add new columns with the RR#
transfer['JRR1NO'] = transfer.JRR1.map(my_aar_dict)
transfer['JRR2NO'] = transfer.JRR2.map(my_aar_dict)
transfer = transfer.dropna()  # remove the transfers not found in allaarCode (these are transfers that we dont need)

dummy = []
# for reading existing flags
for row in arcpy.SearchCursor(transfer_shp_snapped):
    dummy.append([row.getValue("SPLC6"), row.getValue("JRR1"), row.getValue("JRR2"), row.getValue("flag")])

dummy_df = pandas.DataFrame(dummy)
dummy_df.columns = ['SPL_', 'JRR1_', 'JRR2_', 'flag']
dummy_df = dummy_df[dummy_df['flag'] != 0]  # keep only the records that have flags

transfer = pandas.concat([transfer, dummy_df], axis=1)
transfer = transfer.drop(['SPL_', 'JRR1_', 'JRR2_'], axis=1)

transfer = transfer.fillna(0)  # if not found in the old network file, its marked 0:(good nodes)

transfer['nearNID'] = ""
transfer['nearNDist'] = ""

transfer.to_csv(intermediate_csv)  # also write the contents to a csv file
arcpy.DeleteFeatures_management(transfer_xl_shp)

arcpy.TableToTable_conversion(intermediate_csv, "intermediate", "transfers.dbf")
arcpy.MakeXYEventLayer_management("intermediate/transfers.dbf", "LONNBR", "LATNBR", 'dummy',
                                  arcpy.SpatialReference(4326))
arcpy.CopyFeatures_management("dummy", transfer_xl_shp)
