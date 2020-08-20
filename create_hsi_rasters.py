from fun import *
from raster_hsi import HSIRaster, Raster
from time import perf_counter


def combine_hsi_rasters(raster_list, method="geometric_mean"):
    """
    Combine HSI rasters into combined Habitat Suitability Index (cHSI) Rasters
    :param raster_list: list of HSIRasters (HSI)
    :param method: string (default="geometric_mean", alt="product)
    :return HSIRaster: contains float pixel values
    """
    pass


def get_hsi_curve(json_file, life_stage, parameters):
    """
    Retrieve HSI curves from fish json file for a specific life stage and a set of parameters
    :param fish_json: string (directory and name of json file containing HSI curves)
    :param life_stage: string (fish life stage, either "fry", "spawning", "juvenile", or "adult")
    :param parameters: list (may contain "velocity", "depth", and/or "grain_size")
    :return curve_data: dictionary of life stage specific HSI curves as pd.DataFrame for requested parameters;
                        for example: curve_data["velocity"]["HSI"]
    """
    pass


def get_hsi_raster(tif_dir, hsi_curve):
    """
    Calculate and return Habitat Suitability Index Rasters
    :param tif_dir: string of directory and name of  a tif file with parameter values (e.g., depth in m)
    :param hsi_curve: nested list of [[par-values], [HSI-values]], where
                            [par-values] (e.g., velocity values) and
                            [HSI-values] must have the same length.
    :return hsi_raster: Raster with HSI values
    """
    pass


def main():
    pass    


if __name__ == '__main__':
    # define global variables for the main() function
    parameters = ["velocity", "depth"]
    life_stage = "juvenile"  # either "fry", "juvenile", "adult", or "spawning"
    fish_file = os.path.abspath("") + "\\habitat\\trout.json"
    tifs = {"velocity": os.path.abspath("") + "\\basement\\flow_velocity.tif",
            "depth": os.path.abspath("") + "\\basement\\water_depth.tif"}
    hsi_output_dir = os.path.abspath("") + "\\habitat\\"

    # run code and evaluate performance
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print("Time elapsed: " + str(t1 - t0))
