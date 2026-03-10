import shapely as sp


def create_gaps(multipolygon: sp.MultiPolygon, num_gap: int, perc_gap: float, orientation_gap: bool):
    """
    multipolygon: objeto type <MULTIPOLYGON> do shapely que indica a região flexível
    num_gap: quantidade de gaps que será criado na região
    perc_gap: porcentagem da área dos gaps(total, somado de todos os gaps) em relação à área total da região.
    """

    #
    mask = multipolygon
    xmin, ymin, xmax, ymax = mask.bounds
# -----------------------------------------------------------------------------------------
    # Bloco de código pra região flex com sentido de prenchimento na vertical
    if orientation_gap:
        distx_total = xmax - xmin

        dist_x = (distx_total - (1-perc_gap)*distx_total)/num_gap
        util_gap = (distx_total - (num_gap*dist_x))/(num_gap+1)

        x_pointer_min = xmin + util_gap
        x_pointer_max = xmin + util_gap + dist_x

        for i in range(num_gap):

            # Generate box and append to the box_list
            box = sp.geometry.box(x_pointer_min, ymin, x_pointer_max, ymax)

            # Refresh the x_pointer
            x_pointer_min = x_pointer_min + dist_x + util_gap
            x_pointer_max = x_pointer_max + dist_x + util_gap

            mask = mask.difference(box)
# ---------------------------------------------------------------------------------

    # Bloco de código pra região flex com sentido de prenchimento na horizontal

    else:
        disty_total = ymax - ymin

        dist_y = (disty_total - (1-perc_gap)*disty_total)/num_gap
        util_gap = (disty_total - (num_gap*dist_y))/(num_gap+1)

        y_pointer_min = ymin + util_gap
        y_pointer_max = ymin + util_gap + dist_y

        for i in range(num_gap):

            # Generate box and append to the box_list
            box = sp.geometry.box(xmin, y_pointer_min, xmax, y_pointer_max)

            # Refresh the x_pointer
            y_pointer_min = y_pointer_min + dist_y + util_gap
            y_pointer_max = y_pointer_max + dist_y + util_gap

            mask = mask.difference(box)
# ---------------------------------------------------------------------------------

    # final = multipolygon.difference(mask)
    final = mask

    return final
