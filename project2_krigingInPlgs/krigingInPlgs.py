# -*- coding: utf-8 -*-
import arcpy, os

arcpy.env.overwriteOutput = True
# create a temp dir to save the data in progressing
def _CreateTempDir(tempPath):
    # make sure the path is valid
    if not os.path.exists(tempPath):
        os.makedirs(tempPath)
    tempDir = os.path.join(tempPath, "tempDir")
    os.makedirs(tempDir)
    return tempDir


# run kriging for the pnts in each plg
def Main(inPntFea, inPlgFea, outPath, outKrigingName):
    arcpy.env.workspace = os.path.split(inPntFea)[0]
    # create a feature layer
    pntLayer = arcpy.MakeFeatureLayer_management(inPntFea)
    plgLayer = arcpy.MakeFeatureLayer_management(inPlgFea)

    # get total feature count in plg data
    plgFeatureNum = int(arcpy.GetCount_management(plgLayer)[0])
    print(plgFeatureNum)
    print(type(plgFeatureNum))

    # statistic the min value
    resTab = arcpy.Statistics_analysis(inPntFea, os.path.join(outPath, "temp"), [["NEAR_DIST", "MIN"]], ["wyid"])

    # select data with the plg id
    with arcpy.da.SearchCursor(inPlgFea, ["SHAPE@", "wyid"]) as cursor:
        for row in cursor:
            # get the plg extent
            plgXMin = row[0].extent.XMin
            plgXMax = row[0].extent.XMax
            plgYMin = row[0].extent.YMin
            plgYMax = row[0].extent.YMax
            print row[1]

            with arcpy.da.SearchCursor(resTab, ["wyid", "MIN_NEAR_DIST"]) as tabCur:
                for tabRow in tabCur:
                    if row[1] == tabRow[0]:
                        valueMin = tabRow[1]

            # get the Min value group by wyid


            # set gp process environment, kriging can not use this
            # arcpy.env.extent = arcpy.Extent(plgXMin, plgXMax, plgYMin, plgYMax)

            # select pnt data with the field 'wyid' of plg
            selectedPnt = arcpy.SelectLayerByAttribute_management(pntLayer, "NEW_SELECTION", '"wyid" = {}'.format(row[1]))
            # print selectedPnt
            print '"wyid" = {}'.format(row[1])

            resRas = os.path.join(outPath, outKrigingName + str(row[1]) + ".tif")

            # run the kriging gp
            resKrig = arcpy.sa.Kriging(selectedPnt, "NEAR_DIST", arcpy.sa.KrigingModelOrdinary(), "", arcpy.sa.RadiusVariable(9))
            # arcpy.Kriging_3d(pntLayer, "NEAR_DIST", resRas, "CIRCULAR", "", "Variable 9")
            # arcpy.Kriging_3d(inPntFea, "NEAR_DIST", resRas, "CIRCULAR", "1.9555535", "Variable 9")

            # rasterCalculate calculate the
            # arcpy.sa.Con()
            # resKrig = arcpy.RasterCalculator(valueMin/resKrig)
            resKrig = valueMin/resKrig
            # save the kriging result
            resKrig.save(os.path.join(outPath, resRas))

            # arcpy.Idw_3d(selectedPnt, "NEAR_DIST", resRas)

            # clear the env
            arcpy.ClearEnvironment("extent")



# input data
inPntFea = "E:/工作任务/任务七_噪声分析平面/progress/pntInBld_wyid.shp"
inPlgFea = "E:/工作任务/任务六_倾斜摄影做视线分析/转平面数据/甘肃中医药平面.shp"
outPath = "E:/工作任务/任务七_噪声分析平面/pyRes"
outKrigingName = "克里金插值"
# outKrigingName = "IDW"

# decode area
codeType = "utf-8"
inPntFea = inPntFea.decode(codeType)
inPlgFea = inPlgFea.decode(codeType)
outPath = outPath.decode(codeType)
outKrigingName = outKrigingName.decode(codeType)

# run the script
Main(inPntFea, inPlgFea, outPath, outKrigingName)