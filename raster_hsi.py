from raster import *


class HSIRaster(Raster):
    def __init__(self, file_name, hsi_curve, band=1, raster_array=None, geo_info=False):
        """
        A GeoTiff Raster dataset (wrapped osgeo.gdal. Dataset)
        :param file_name: STR of a GeoTiff file name including directory (must end on ".tif")
        :param hsi_curve: nested list of [[par-values], [HSI-values]], where
                    [par-values] (e.g., velocity values) and
                    [HSI-values] must have the same length.
        :param band: INT of the band number to use
        """
        Raster.__init__(self, file_name=file_name, band=band, raster_array=raster_array, geo_info=geo_info)
        self.make_hsi(hsi_curve)

    def make_hsi(self, hsi_curve):
        """
        Turn array into hsi-value array based on a step function of a hsi curve that is used
            for linear interpolation of hsi values from parameter values.
        :return: Raster
        """
        par_values = hsi_curve[0]
        hsi_values = hsi_curve[1]
        try:
            with np.nditer(self.array, flags=["external_loop"], op_flags=["readwrite"]) as it:
                for x in it:
                    x[...] = interpolate_from_list(par_values, hsi_values, x)
        except AttributeError:
            print("WARNING: np.array is one-dimensional.")
        return self._make_raster("hsi")
