""" 
Estimates a linear warp field, the target is a file passed as parameter.

Output is placed in VGG directory structure as used by Supreme library:
http://mentat.za.net/supreme

"""

import scipy.ndimage as nd
import scipy.misc as misc
import numpy as np

from register.models import model
from register.metrics import metric
from register.samplers import sampler

from register.visualize import plot
from register import register

from matplotlib import pyplot
from os.path import basename

import osgeo.gdal as gdal
import sys


print "Loading images..."
dsImage = gdal.Open(sys.argv[1])
dsTemplate = gdal.Open(sys.argv[2])
image = dsImage.GetRasterBand(1).ReadAsArray().astype(np.double)
template = dsTemplate.GetRasterBand(1).ReadAsArray().astype(np.double)

# Form the affine registration instance.
print "Setting up affine registration..."
affine = register.Register(
    model.CubicSpline,
    metric.Residual,
    sampler.CubicConvolution
    )

# Coerce the image data into RegisterData.
print "Loading images into RegisterData objects..."
image = register.RegisterData(image)
template = register.RegisterData(template)

# Register.
print "Registering..."
p, warp, img, error = affine.register(
    image,
    template,
    alpha=0.000001,
    #plotCB=plot.gridPlot,
    verbose=True
    )

#print "Close dialog to exit..."
#plot.show()

pyplot.imsave('png/%s.png' % basename(sys.argv[1])[5:8], image.data, cmap='gray', format='png') 
pyplot.imsave('png/%s.png' % basename(sys.argv[2])[5:8], template.data, cmap='gray', format='png') 

filenum = int(basename(sys.argv[1])[5:8])
Hfile = open('H/%03d.%03d.H' % (filenum-1, filenum), 'w')
Hfile.write('%f %f %f\n%f %f %f\n0.0 0.0 1.0\n' % (p[0]+1.0, p[2], p[4], p[1], p[3]+1.0, p[5]))
Hfile.close()

p = affine.model(image.coords).identity
warp = affine.model(image.coords).warp(p)
resampledImage = affine.sampler(template.coords).f(image.data, warp).reshape(image.data.shape)
p = affine.model(template.coords).identity
warp = affine.model(template.coords).warp(p)
resampledTemplate = affine.sampler(template.coords).f(template.data, warp).reshape(template.data.shape)

print "Before: ", int(np.abs(metric.Residual().error(resampledImage, resampledTemplate)).sum())
print "After: ", int(np.abs(metric.Residual().error(resampledImage, img)).sum())

pyplot.figure()
pyplot.axis('image')
pyplot.subplot(1,2,1)
pyplot.imshow(np.abs(resampledImage-resampledTemplate).astype(np.uint8), cmap='gray')
pyplot.subplot(1,2,2)
pyplot.imshow(np.abs(resampledImage-img).astype(np.uint8), cmap='gray')
pyplot.show()
pyplot.close()

print "Done."