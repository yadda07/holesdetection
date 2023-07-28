import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon

def has_holes(geom):
    # Retourne True si la géométrie a des trous, False autrement
    if geom is None:
        return False
    if isinstance(geom, Polygon):
        return len(geom.interiors) > 0
    elif isinstance(geom, MultiPolygon):
        return any(len(poly.interiors) > 0 for poly in geom.geoms)
    return False

if __name__ == "__main__":
    # Lecture du Shapefile
    print('Reading Shapefile...')
    gdf = gpd.read_file('C:/Users/u200179/OneDrive - XP Fibre/Workstation/PROJECT/ZAPM T223/ZAPM_XP-FIBRE_2023T2/ZAPM_XP-FIBRE.shp')

    # Sélection des géométries avec des trous
    print('Selecting geometries with holes...')
    gdf_holes = gdf[gdf.geometry.apply(has_holes)]

    # Enregistrement dans un nouveau Shapefile
    print('Saving to new shapefile...')
    gdf_holes.to_file('C:/Users/u200179/OneDrive - XP Fibre/Workstation/PROJECT/ZAPM T223/ZAPM_XP-FIBRE_2023T2/ZAPM_XP-FIBRE_with_holes.shp')
    print('Done.')
