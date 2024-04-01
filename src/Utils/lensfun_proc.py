import lensfunpy

cam_maker = 'DJI'
cam_model = 'Air 2S'
lens_maker = 'DJI'
lens_model = ''


db = lensfunpy.Database()
cam = db.find_cameras(cam_maker, cam_model, True)[0]
lens = db.find_lenses(cam, lens_maker, lens_model, True)[0]

print(cam)
# Camera(Maker: NIKON CORPORATION; Model: NIKON D3S; Variant: ;
#        Mount: Nikon F AF; Crop Factor: 1.0; Score: 0)

print(lens)
# Lens(Maker: Nikon; Model: Nikkor 28mm f/2.8D AF; Type: RECTILINEAR;
#      Focal: 28.0-28.0; Aperture: 2.79999995232-2.79999995232;
#      Crop factor: 1.0; Score: 110)