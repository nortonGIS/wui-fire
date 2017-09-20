#-------------------------------------------------------------------------------
# Name:        AllReturns_lasdtoheight
# Purpose:     All_returns.lasd --> Height Raster
#
# Author:      Matthew
#
# Created:     23/05/2017
# Copyright:   (c) Matthew 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True

# Set scratch workspace and environment settings
scriptpath = sys.path[0]
ToolData = os.path.dirname(scriptpath)
toolpath = os.path.dirname(ToolData)
scratchfolder = os.path.join(ToolData,"Scratch")
scratchws = env.scratchWorkspace
scratchgdb = os.path.join(scratchfolder, "Scratch.gdb")
if not env.scratchWorkspace:
  scratchws = scratchgdb

# Set Paths
outputs_path = os.path.join(toolpath, "Outputs")
inputs_path = os.path.join(toolpath, "Inputs")
LAS_path = os.path.join(inputs_path, "LAS")
lasdpath = os.path.join(inputs_path, "Pendleton.lasd")     # Replace LAS, create lasd manually
# naippath = os.path.join(inputs_path,"Altamont_Test_NAIP_unprocessed.tif")
##arcpy.env.snapRaster = naip
##extentpath = os.path.join(inputs_path, "altamont_sp.shp")
##
##arcpy.env.extent = arcpy.Describe(extentpath).extent

# Create FP.lasd
FP_lasdpath = os.path.join(inputs_path, "FP.lasd")
arcpy.MakeLasDatasetLayer_management(lasdpath,FP_lasdpath,[0,1,3,4,5,6,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],"","","","","")
arcpy.AddMessage("FP.lasd created in inputs.")

# Create LP.lasd
LP_lasdpath = os.path.join(inputs_path, "LP.lasd")
arcpy.MakeLasDatasetLayer_management(lasdpath,LP_lasdpath,[1,2,8,10,21,22],"","","","","")
arcpy.AddMessage("LP.lasd created in inputs.")

# ---------------Set extent properties---------------------------
# naipdesc = arcpy.Describe(naippath)
# bndXmin = naipdesc.extent.XMin
# naipclip = os.path.join(outputs_path,"Concord_Test_NAIP.tif")
# outputextent = str(naipdesc.extent.XMin)+" "+str(naipdesc.extent.XMax)+" "+str(naipdesc.extent.YMin)+" "+str(naipdesc.extent.YMax)
# arcpy.Clip_management(naippath, outputextent, naipclip,"","","","")
#
# Create Boundary
# ZeroValueRast = Int(naipclip)*0
# bndrast = os.path.join(scratchfolder,"bndrast.tif")
# ZeroValueRast.save(bndrast)
# bnd = os.path.join(outputs_path,"bnd.shp")
# arcpy.RasterToPolygon_conversion(Raster(bndrast),bnd,"NO_SIMPLIFY","")
# arcpy.AddMessage("bnd.shp created in Outputs folder.")

# -------------Create DEM, DSM, Heights--------------------------
#
# cell_size = str(arcpy.GetRasterProperties_management(naipclip,"CELLSIZEX",""))
cell_size = 3.0316211
#
# Create DEM
DEMpath = os.path.join(outputs_path,"DEM.tif")
arcpy.LasDatasetToRaster_conversion(LP_lasdpath, DEMpath, "ELEVATION", "BINNING AVERAGE NATURAL_NEIGHBOR", "FLOAT", "CELLSIZE", cell_size, "1")
arcpy.AddMessage("DEM.tif created in Outputs folder.")
#
# Create DSM
TempDSMpath = os.path.join(scratchfolder,"TempDSM.tif")
DSMpath = os.path.join(outputs_path,"DSM.tif")
arcpy.LasDatasetToRaster_conversion(FP_lasdpath, TempDSMpath, "ELEVATION", "BINNING MAXIMUM SIMPLE", "FLOAT", "CELLSIZE", cell_size, "1")
DSM = Con(IsNull(Float(TempDSMpath)),Float(DEMpath),Float(TempDSMpath))
DSM.save(DSMpath)
arcpy.AddMessage("DSM.tif created in Outputs folder.")
#
# Create Heights
no_clip_heights = os.path.join(scratchfolder,"no_clip_heights.tif")
hts_interm1 = os.path.join(scratchfolder,"hts_interm1.tif")
hts_interm2 = os.path.join(scratchfolder,"hts_interm2.tif")
heights = Float(DSMpath)-Float(DEMpath)
heights = Con(IsNull(Float(heights)), 0, Float(heights))
heights = Con(Float(heights) < 0, 0, Float(heights))
heights = SetNull(Float(heights),Float(heights),"VALUE > 350")                                          # Minimum "Cloud" heights defined here.  NOTE UNITS
if int(arcpy.GetRasterProperties_management(heights,"ANYNODATA").getOutput(0)):
    arcpy.AddMessage("Interpolating under clouds/birds.")
    heights.save(hts_interm1)
    heights.save(hts_interm2)
    del heights
    cloudrast = os.path.join(scratchgdb,"cloudrast")
    arcpy.gp.Reclassify_sa(hts_interm1, "VALUE", "-10000 10000 NODATA;NODATA 1", cloudrast, "DATA")
    cloudpts = os.path.join(scratchgdb,"cloudpts")
    arcpy.RasterToPoint_conversion(cloudrast,cloudpts,"VALUE")
    cloudpts_buf30 = os.path.join(scratchgdb,"cloudptsbuf30")
    arcpy.Buffer_analysis(cloudpts, cloudpts_buf30, "30 Feet", "FULL", "ROUND", "ALL", "", "PLANAR")
    nocloudmask = ExtractByMask(hts_interm2,cloudpts_buf30)
    interppts = os.path.join(scratchgdb,"interppts")
    arcpy.RasterToPoint_conversion(nocloudmask, interppts,"")
    NNinterp = os.path.join(scratchgdb,"NNinterp")
    arcpy.gp.NaturalNeighbor_sa(interppts, "grid_code", NNinterp, hts_interm2)
    arcpy.MosaicToNewRaster_management(hts_interm2+";"+NNinterp,scratchfolder,"no_clip_heights.tif", "", "32_BIT_FLOAT", "", "1", "FIRST", "FIRST")
else:
    heights.save(no_clip_heights)

out_height = os.path.join(outputs_path,"heights.tif")
heights.save(out_height)

## Clipping Geometry (remove 0-value NoData values)
#int_dem = Int(Float(DEMpath))
#int_dem_path = os.path.join(scratchfolder,"int_dem.tif")
#int_dem.save(int_dem_path)

#out_height = os.path.join(outputs_path,"heights.tif")
#arcpy.Clip_management(no_clip_heights,"",out_height,int_dem_path,"NoData","ClippingGeometry","")
#arcpy.AddMessage("heights.tif created in Outputs folder.")

