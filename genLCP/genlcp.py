import ctypes
import arcpy as a

dll = ctypes.cdll.LoadLibrary("C:\\Temp\\GenLCPv2.dll")
fm = getattr(dll, "?Gen@@YAHPBD000000@Z")
fm.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
fm.restype = ctypes.c_int

Res = a.GetParameterAsText(0)
Elev = a.GetParameterAsText(1)
Slope = a.GetParameterAsText(2)
Aspect = a.GetParameterAsText(3)
Fuel = a.GetParameterAsText(4)
Canopy = a.GetParameterAsText(5)

e = fm(Res, Elev, Slope, Aspect, Fuel, Canopy, "")
if e > 0:
 a.AddError("Error {0}".format(e))
