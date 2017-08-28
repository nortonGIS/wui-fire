import ctypes
import arcpy as a

dll = ctypes.cdll.LoadLibrary("C:\\Temp\\FlamMapF.dll")
fm = getattr(dll, "?Run@@YAHPBD000NN000HHN@Z")
fm.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_double]
fm.restype = ctypes.c_int

Landscape = a.GetParameterAsText(0)
FuelMoist = a.GetParameterAsText(1)
OutputFile = a.GetParameterAsText(2)
FuelModel = "-1"
Windspeed = 20.0	# mph
WindDir = 0.0		# Direction angle in degrees
Weather = "-1"
WindFileName = "-1"
DateFileName = "-1"
FoliarMoist = 100	# 50%
CalcMeth = 0		# 0 = Finney 1998, 1 = Scott & Reinhardt 2001
Res = -1.0

e = fm(Landscape, FuelMoist, OutputFile, FuelModel, Windspeed, WindDir, Weather, WindFileName, DateFileName, FoliarMoist, CalcMeth, Res)
if e > 0:
 a.AddError("Problem with parameter {0}".format(e))


