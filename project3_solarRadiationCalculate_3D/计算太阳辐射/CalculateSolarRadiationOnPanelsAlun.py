import arcpy
import os
import sys


class LicenseError3D(Exception):
    pass


class LicenseErrorSpatial(Exception):
    pass


class NoUnits(Exception):
    pass


class NotSupported(Exception):
    pass





def getNameFromFeatureClass(feature_class):
    descFC = arcpy.Describe(feature_class)
    return descFC.name


# Get Workspace from Building feature class location
def getWorkSpaceFromFeatureClass(feature_class, get_gdb):
    dirname = os.path.dirname(arcpy.Describe(feature_class).catalogPath)
    desc = arcpy.Describe(dirname)

    if hasattr(desc, "datasetType") and desc.datasetType == 'FeatureDataset':
        dirname = os.path.dirname(dirname)

    if get_gdb == "yes":
        return dirname
    else:                   # directory where gdb lives
        return os.path.dirname(dirname)


def createIntGDB(path, name):
    intGDB = os.path.join(path, name)
    if not arcpy.Exists(intGDB):
        arcpy.CreateFileGDB_management(path, name, "CURRENT")
        return intGDB
    else:
        return intGDB


# Field Exists Definition Module
def FieldExist(featureclass, fieldname):
    fieldList = arcpy.ListFields(featureclass, fieldname)
    fieldCount = len(fieldList)
    if fieldCount == 1:
        return True
    else:
        return False


# Define DeleteAdd Fields
def DeleteAddField(featureclass, field, fieldtype):
    try:
        if FieldExist(featureclass, field):
            arcpy.DeleteField_management(featureclass, field)

        arcpy.AddField_management(featureclass, field, fieldtype)

    except arcpy.ExecuteWarning:
        print((arcpy.GetMessages(1)))
        arcpy.AddWarning(arcpy.GetMessages(1))

    except arcpy.ExecuteError:
        print((arcpy.GetMessages(2)))
        arcpy.AddError(arcpy.GetMessages(2))

    # Return any other type of error
    except:
        # By default any other errors will be caught here
        #
        e = sys.exc_info()[1]
        print((e.args[0]))
        arcpy.AddError(e.args[0])

def CalculateTotalRadiation(Input1FeaturesLayer, OutPutFeaturesLayer):
    # variables
    spatial_ref = arcpy.Describe(Input1FeaturesLayer).spatialReference
    # 获取坐标系的平面单位
    units = spatial_ref.linearUnitName

    aprx = arcpy.mp.ArcGISProject("CURRENT")
    homeDirectory = aprx.homeFolder

    if os.path.exists(homeDirectory + "\\p20"):      # it is a package
        homeDirectory = homeDirectory + "\\p20"

    arcpy.AddMessage("Project Home Directory is: " + homeDirectory)

    # Create and set workspace location in same directory as input feature class gdb
    workspacePath = getWorkSpaceFromFeatureClass(Input1FeaturesLayer, "no")
    scratch_ws = createIntGDB(workspacePath, "Intermediate.gdb")

    arcpy.env.workspace = scratch_ws

    # make new feature class based on possible selection
    if arcpy.Exists(OutPutFeaturesLayer):
        arcpy.Delete_management(OutPutFeaturesLayer)

    arcpy.CopyFeatures_management(Input1FeaturesLayer, OutPutFeaturesLayer)

    # select panels
    arcpy.AddMessage("Calculating total solar radiation for selected panels...")

    radiation_panel_field = "radiation_panel_kWhday"
    radiation_field = "radiation_value_kWhm2day"
    shape_area_field = "SHAPE@AREA"
    total_radiation_field = "total_radiation_kWhday"

    DeleteAddField(OutPutFeaturesLayer, radiation_panel_field, "DOUBLE")

    if "Foot" in units:
        conversion_factor = 10.76391
    else:
        if "Meter" in units:
            conversion_factor = 1
        else:
            raise NoUnits

    # step through all points
    with arcpy.da.UpdateCursor(OutPutFeaturesLayer, [shape_area_field, radiation_field, radiation_panel_field]) as u_cursor:
        for u_row in u_cursor:
            u_row[2] = (u_row[0] / conversion_factor) * float(u_row[1])

            # Update the cursor
            u_cursor.updateRow(u_row)

    DeleteAddField(OutPutFeaturesLayer, total_radiation_field, "DOUBLE")

    # calculate area
    arr = arcpy.da.FeatureClassToNumPyArray(OutPutFeaturesLayer, (radiation_panel_field))
    sum = arr[radiation_panel_field].sum()

    arcpy.CalculateField_management(OutPutFeaturesLayer, total_radiation_field, sum, "PYTHON_9.3")

    arcpy.AddMessage("Total potential solar radiation for selected panels: " + str(sum) + " kWh/day.")



# Get Attributes from User
Input1FeaturesLayer = arcpy.GetParameter(0)
OutPutFeaturesLayer = arcpy.GetParameter(1)

CalculateTotalRadiation(Input1FeaturesLayer, OutPutFeaturesLayer)