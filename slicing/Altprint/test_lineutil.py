# The split function is used to split geometries (such as LineStrings) at specified points. Splits a geometry by another geometry and returns a collection of geometries
from shapely.ops import split
# A LineString is a geometry type composed of one or more line segments (raster zig-zag). Unlike a LinearRing, a LineString is not closed. A MultiLineString is a collection of one or more LineStrings (defined by a list of coordinate pairs (x, y) that define the vertices of the line). These classes represent geometric objects in 2D space
from shapely.geometry import LineString, MultiLineString


def line_flex_region(path):

    x, y = path.xy  # Extract the x and y coordinates from the path
    # Define points A and B as the start and end points of the path
    A = (x[0], y[0])
    B = (x[-1], y[-1])
    # return flex_path as LineString
    flex_path = LineString([A, B])
    return flex_path


# quebra varios segmentos que estão dentro de um ou mais pontos em comum(spliter) em uma outra geometria
# This function takes two arguments: lines (a list of LineStrings) and spliter (a LineString or other geometry)
def split_lines(lines, spliter):
    final = []  # create a list
    for line in lines:  # Iterate through each LineString in lines
        # Use the "split" function to split the LineString at the intersection points with "spliter"
        splited = split(line, spliter)
        for i in list(splited.geoms):
            if type(i) == LineString:  # If a geometry is a LineString
                # Add the resulting geometries (either LineStrings or other types) to the final list
                final.append(i)
            # If a geometry is not a LineString, print “not linestring” (this is a debugging step)
            else:
                print("not linestring")
    return final  # Return the list of split geometries

# quebra uma unica região, que contém todos segmentos dentro dela, em outras regiões (separar as regiões normal, flexivel e de recuperação)


# This function takes two arguments: lines (a MultiLineString) and regions (a list of (list of LineStrings))
def split_by_regions(lines, regions):
    # create a list of geometries extracted from the MultiLineString (lines)
    final = list(lines.geoms)
    # For each region in "regions", call the function "split_lines" on the list of geometries "final"  and split the geometrys at specified region
    for i in range(len(regions)):
        for region in regions[i]:
            # Update final with the newly split geometries
            final = split_lines(final, region)
    # Return a MultiLineString composed of the final split geometries
    return MultiLineString(final)
