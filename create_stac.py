import pystac
import rasterio
import os
from shapely.geometry import Polygon, mapping
from glob import glob
from datetime import datetime
from pystac.extensions.eo import Band, EOExtension

#create empty catalog
catalog = pystac.Catalog(id='test-catalog', description='Tutorial catalog.')
print(list(catalog.get_children()))
print(list(catalog.get_items()))

#define_folder
folder_path = r"E:\Tellman_Lab\THP_project\CSDA_S2\CSDA_S2_stacked_with_label\bolivia"
#get bounding box
def get_bbox_and_footprint(raster_uri):
    with rasterio.open(raster_uri) as ds:
        bounds = ds.bounds
        bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
        footprint = Polygon([
            [bounds.left, bounds.bottom],
            [bounds.left, bounds.top],
            [bounds.right, bounds.top],
            [bounds.right, bounds.bottom]
        ])
        
        return (bbox, mapping(footprint))
    
FloodPlanet_bands = [Band.create(name='Band 1', description='Blue: 0.49um', common_name='Blue'),
                     Band.create(name='Band 2', description='Green: 0.56um', common_name='Green'),
                     Band.create(name='Band 3', description='Red: 0.665um', common_name='Red'),
                     Band.create(name='Band 4', description='Red Edge 1: 0.705um', common_name='Red Edge 1'),
                     Band.create(name='Band 5', description='Red Edge 2: 0.74um', common_name='Red Edge 2'),
                     Band.create(name='Band 6', description='Red Edge 3: 0.783um', common_name='Red Edge 3'),
                     Band.create(name='Band 7', description='NIR: 0.842um', common_name='NIR'),
                     Band.create(name='Band 8', description='Red Edge 4: 0.865um', common_name='Red Edge 4'),
                     Band.create(name='Band 9', description='SWIR 1: 1.61um', common_name='SWIR 1'),
                     Band.create(name='Band 10', description='SWIR 2: 2.19um', common_name='SWIR 2'),
                     Band.create(name='Band 11', description='Label Band', common_name='Label Band'),
                     ]

img_list = glob(folder_path + "//*.tif")
print(img_list)
for img in img_list:
    bbox, footprint = get_bbox_and_footprint(img)
    item_id = img.split('\\')[-1]
    # print(item_id)
    item = pystac.Item(id=item_id,
                 geometry=footprint,
                 bbox=bbox,
                 datetime=datetime.utcnow(),
                 properties={})
    eo = EOExtension.ext(item, add_if_missing=True)
    eo.apply(bands=FloodPlanet_bands)
    item.common_metadata.instruments = "Sentinal-2"
    item.common_metadata.gsd = 10
    
    assert item.get_parent() is None
    catalog.add_item(item)
    item.add_asset(key='image', asset = pystac.Asset(href=img, media_type=pystac.MediaType.GEOTIFF))
    # eo_on_asset = EOExtension.ext(item.assets["image"])
    # eo_on_asset.apply(FloodPlanet_bands)
    
    catalog.normalize_hrefs(os.path.join(folder_path, 'stac'))
    catalog.make_all_asset_hrefs_relative()
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    # with open(item.self_href) as f:
    #     print(f.read())


    
    
# catalog.describe()   
#