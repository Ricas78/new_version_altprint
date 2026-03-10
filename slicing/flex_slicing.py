

from Altprint.flex_c_test_multigap import FlexProcess, FlexPrint


process = FlexProcess(settings_file="slicing/parameters/flex_parameters.yml")
part = FlexPrint(process)


part.slice()
part.make_layers()
part.export_gcode("slicing/gcode/sliced_geometry.gcode")
