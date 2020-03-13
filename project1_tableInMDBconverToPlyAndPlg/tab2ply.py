# -*- coding: utf-8 -*-
import arcpy, os, sys

arcpy.env.overwriteOutput = True

# 将gdb中的数据划分为不同的表
def DistincTable(gdb):
    tabSet = set()
    arcpy.env.workspace = gdb
    tableList = arcpy.ListTables()
    # print tableList
    for each in tableList:
        if "T810" in each:
            tabSet.add(each[:-1])
    # print tabSet
    return tabSet


# 新建字段
def _AddField(inFeaShp, fieldName, fieldType):
    try:
        arcpy.AddField_management(inFeaShp, fieldName, fieldType)
    except:
        arcpy.DeleteField_management(inFeaShp, fieldName)
        arcpy.AddField_management(inFeaShp, fieldName, fieldType)


# 复制表
def _CopyTab(inTab, outTab):
    try:
        resTab = arcpy.CopyRows_management(inTab, outTab)
    except:
        arcpy.Delete_management(inTab)
        resTab = arcpy.CopyRows_management(inTab, outTab)
    return resTab


# 创建数据库
def CreateGDB(outPath, outName):
    if not os.path.exists(os.path.join(outPath, outName + ".gdb")):
        print os.path.join(outPath, outName)
        resGDB = arcpy.CreateFileGDB_management(outPath, outName)
    else:
        resGDB = os.path.join(outPath, outName + ".gdb")
    return resGDB


# 表转线
def tab2ply(tabGDB, tabset, resGDB, conAttr=False):
    # 创建输入表是否存在空值的统计结果
    resTotal = {"notEmpty": [], "empty": []}
    arcpy.env.workspace = tabGDB
    for each in tabset:
        plyTab = each + u'1'
        pntTab = each + u'2'
        # 判断点的表是否为空
        count = int(arcpy.GetCount_management(pntTab)[0])
        print count
        # 该组表的点表非空
        if count:
            print "notEmpty"
            resTotal["notEmpty"].append(each)
            print resGDB
            # 定义输出变量
            outPlyStartTab = os.path.join(resGDB, "plyConPnt_%s_Start" % plyTab)
            outPlyStopTab = os.path.join(resGDB, "plyConPnt_%s_Stop" % plyTab)
            pntRes = os.path.join(resGDB, "pnt_%s" % plyTab)
            plyRes = os.path.join(resGDB, "ply_%s" % plyTab)
            plyResWithAttr = os.path.join(resGDB, "ply_%s_withAttr" % plyTab)
            print plyTab
            print pntTab
            # 创建表视图
            plyTabLayer = arcpy.MakeTableView_management(plyTab, "plyTabView")
            pntTabLayer = arcpy.MakeTableView_management(pntTab, "pntTabView")
            # 添加连接，挂接属性
            arcpy.AddJoin_management(plyTabLayer, u"FirPoint", pntTabLayer, u"TEXT")
            # 添加字段，保存数据并标识序号
            _AddField(plyTab, "x_pnt", "DOUBLE")
            _AddField(plyTab, "y_pnt", "DOUBLE")
            _AddField(plyTab, "h_pnt", "DOUBLE")
            _AddField(plyTab, "AAA", "SHORT")
            arcpy.CalculateField_management(plyTabLayer, "x_pnt", "!%s.X!"%pntTab, "PYTHON_9.3")
            arcpy.CalculateField_management(plyTabLayer, "y_pnt", "!%s.Y!"%pntTab, "PYTHON_9.3")
            arcpy.CalculateField_management(plyTabLayer, "h_pnt", "!%s.H!"%pntTab, "PYTHON_9.3")
            arcpy.CalculateField_management(plyTabLayer, "AAA", "1", "PYTHON_9.3")
            # 移除链接
            arcpy.RemoveJoin_management(plyTabLayer)
            # 将连接了起点的ply表复制一份，连接了ply的FirPoint和pnt的TEXT
            resTabStart = _CopyTab(plyTabLayer, outPlyStartTab)

            # 连接ply的SecPoint和pnt的TEXT
            # 添加连接，挂接属性
            arcpy.AddJoin_management(plyTabLayer, u"SecPoint", pntTabLayer, u"TEXT")
            arcpy.CalculateField_management(plyTabLayer, "x_pnt", "!%s.X!" % pntTab, "PYTHON_9.3")
            arcpy.CalculateField_management(plyTabLayer, "y_pnt", "!%s.Y!" % pntTab, "PYTHON_9.3")
            arcpy.CalculateField_management(plyTabLayer, "h_pnt", "!%s.H!" % pntTab, "PYTHON_9.3")
            arcpy.CalculateField_management(plyTabLayer, "AAA", "2", "PYTHON_9.3")
            # 移除链接
            arcpy.RemoveJoin_management(plyTabLayer)
            # 将连接了起点的ply表复制一份，连接了ply的SecPoint和pnt的TEXT
            resTabStop = _CopyTab(plyTabLayer, outPlyStopTab)
            # 将表2追加到表1
            resTab = arcpy.Append_management(resTabStop, resTabStart, "NO_TEST")
            # 创建点图层
            pntLayer = arcpy.MakeXYEventLayer_management(resTab, "x_pnt", "y_pnt", "pntLayer", "WGS 1984 Web Mercator (auxiliary sphere)")
            # 保存点数据
            arcpy.CopyFeatures_management(pntLayer, pntRes)
            # 点集转线
            resPly = arcpy.PointsToLine_management(pntRes, plyRes, "PipeID", "AAA")

            # 恢复源数据
            try:
                arcpy.DeleteField_management(plyTab, "x_pnt")
                arcpy.DeleteField_management(plyTab, "y_pnt")
                arcpy.DeleteField_management(plyTab, "h_pnt")
                arcpy.DeleteField_management(plyTab, "AAA")
            except:
                pass

            # 给线添加属性
            if conAttr:
                resPlyLayer = arcpy.MakeFeatureLayer_management(resPly, "resPlyLayer")
                resPlyLayer = arcpy.AddJoin_management(resPlyLayer, "PipeID", plyTabLayer, "PipeID")
                arcpy.CopyFeatures_management(resPlyLayer, plyResWithAttr)


        # 该组的点表为空
        else:
            print "Empty"
            resTotal["empty"].append(each)
        # sys.exit()

    print resTotal
    with open(os.path.join(os.path.split(resGDB)[0], "tableStatistic_ply.txt"), "w") as f:
        f.write(str(resTotal))

    print "finish"


# 表转plg
def tab2plg(tabGDB, tabset, resGDB):
    resTotal = {"notEmpty": [], "empty": [], "plgEnable": [], "plgAble": []}
    arcpy.env.workspace = tabGDB
    for each in tabset:
        plyTab = each + u'1'
        pntTab = each + u'2'
        plgTab = each + u'3'
        # 判断点的表是否为空
        count = int(arcpy.GetCount_management(pntTab)[0])
        print pntTab
        # 该组表的点表非空
        if count:
            print "notEmpty"
            resTotal["notEmpty"].append(each)
            print resGDB
            # 变量定义
            pntTemp = os.path.join(resGDB, "pntTemp_%s" % pntTab)
            plgRes = os.path.join(resGDB, "plg_%s" % plgTab)
            pntRes = os.path.join(resGDB, "pnt_%s" % pntTab)
            plyRes = os.path.join(resGDB, "ply_%s" % plyTab)
            plgResSpatialJoin = os.path.join(resGDB, "plg_%s_withAttr" % plgTab)
            # 添加字段
            _AddField(pntTab, "BBB", "STRING")
            _AddField(pntTab, "CCC", "STRING")
            arcpy.CalculateField_management(pntTab, "BBB", "!TEXT![:-1]", "PYTHON_9.3")
            arcpy.CalculateField_management(pntTab, "CCC", "!TEXT![-1:]", "PYTHON_9.3")
            # 创建表视图
            pntTabLayer = arcpy.MakeTableView_management(pntTab, "pntTabView")
            # 创建点图层
            pntLayer = arcpy.MakeXYEventLayer_management(pntTabLayer, "X", "Y", "pntLayer",
                                                         "WGS 1984 Web Mercator (auxiliary sphere)")
            # 删除所有最后一个值非字母的行
            arcpy.Select_analysis(pntLayer, pntTemp,
                                  "\"CCC\" = 'A' OR \"CCC\" = 'B' OR \"CCC\" = 'C' OR \"CCC\" = 'D' OR \"CCC\" = 'E'")
            # 存在可成面的点
            if int(arcpy.GetCount_management(pntTemp)[0]):
                resTotal["plgAble"].append(each)
                # 保存点数据
                arcpy.CopyFeatures_management(pntTemp, pntRes)
                # 点集转线
                resPly = arcpy.PointsToLine_management(pntRes, plyRes, "BBB", "CCC", "CLOSE")
                # 线转面
                arcpy.FeatureToPolygon_management(resPly, plgRes)
                # 添加属性
                arcpy.SpatialJoin_analysis(plgRes, pntRes, plgResSpatialJoin)

                # 恢复源数据
                try:
                    arcpy.DeleteField_management(pntTab, "BBB")
                    arcpy.DeleteField_management(pntTab, "CCC")
                except:
                    pass

            # 不存在可成面的点
            else:
                resTotal["plgEnable"].append(each)
                continue

        # 该组的点表为空
        else:
            print "Empty"
            resTotal["empty"].append(each)
        # sys.exit()

    print resTotal
    with open(os.path.join(os.path.split(resGDB)[0], "tableStatistic_plg.txt"), "w") as f:
        f.write(str(resTotal))

    print "finish"





# 输入存放表格的gdb
gdb = "E:/工作任务/任务一20200312/处理数据/process.gdb"
# 结果输出路径
outPath = "E:/工作任务/任务一20200312/处理数据/"
# 输出数据名称
outName = "resGDB"
# 是否在生成的线上添加属性
conAttr = False

# 编码转换
codeType = "utf-8"
gdb = gdb.decode(codeType)
outPath = outPath.decode(codeType)
outName = outName.decode(codeType)

# 将表分组
tabSet = DistincTable(gdb)
# 创建gdb数据库
resGDB = CreateGDB(outPath, outName)
# 表转线
tab2ply(gdb, tabSet, resGDB, conAttr)
# 表转面
# tab2plg(gdb, tabSet, resGDB, conAttr)