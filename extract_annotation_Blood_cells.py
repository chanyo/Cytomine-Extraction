# Cytomine Project (annotation retrieval)
# initial version : Vahid Azimi
# current modification : Young Hwan Chang (chanyo@ohsu.edu)
# BME / Computational Biology

# http://localhost-core/api/user.json : USER INFO
# http://localhost-core/api/project.json : PROJECT INFO
# http://localhost-core/api/term.json : annotation terminology


from cytomine import Cytomine
from cytomine.models import *
import numpy as np
from skimage import io
import string
from operator import sub
import os
from shapely.geometry import Point
from shapely.wkt import loads
# import matplotlib.pyplot as plt
import cv2

##########################################################################
# Cytomine connection parameters @ OHSU
# Set your public key and private key
# (these can be found by logging into Cytomine, clicking on the drop-down menu
# where your username is displayed at the top right,
# and selecting "Account". Copy and paste these keys into the script.
##########################################################################
cytomine_host = "http://localhost-core"
cytomine_public_key = "6d2dbbde-3527-4b0c-b55b-4c4c3a892ca2"
cytomine_private_key = "c14bd3fd-590c-43e2-9c44-87ef7f09b48b"




output_dir = "/Users/chanyo/Documents/Cytomine/MICE_Pancreas/"

# Connection to Cytomine Core
conn = Cytomine(cytomine_host, cytomine_public_key, cytomine_private_key, base_path='/api/', working_path='/tmp/',
                verbose=True)
# Set your user ID
id_user = "chanyo"
# Set the project ID
# : the project ID is, visit "http://localhost-core/api/project.json" and
# parse the json for the project ID of your given project.
# ex) "id":5956833,"created":"1468608291269","updated":"1469480682146","deleted":null,"name":"Breast-HE","ontology":5956825,"ontologyName":"Breast-HE"
# id_project = 5956833
# id_ontology = 5956825

# MICE Pancreas
id_project = 2182
id_ontology = 2169

# If you want to filter by image or term, uncomment the following line and in the get_annotations call
# If you want not to filter by user, comment the previous line
# id_image=XXX
id_term= 93037


# This retrieve the JSON description of existing annotations with full details (wkt, GIS information)
# If you don't need full details (e.g. only to count the number of annotations), comment showWKT,showMeta,showGIS
# to speed up the query

image_instances = ImageInstanceCollection()
image_instances.project = id_project
image_instances = conn.fetch(image_instances)
images = image_instances.data()

identity = string.maketrans("", "")

##################################################################################
# get original images crops
dump_type = 2  # 1: original image, 2: with alpha mask
zoom_level = 0  # 0 is maximum resolution

if dump_type == 1:
    annotation_get_func = Annotation.get_annotation_crop_url
elif dump_type == 2:
    annotation_get_func = Annotation.get_annotation_alpha_crop_url
else:
    annotation_get_func = Annotation.get_annotation_crop_url

for image in images:
    # if image.id == 5960353: # TEMP for annotation
    # print image.id


    annotations = conn.get_annotations(id_project=id_project,
                                       # id_user = id_user,
                                       id_image=image.id,
                                       id_term = id_term,
                                       showWKT=True, showMeta=True, showGIS=True, reviewed_only=False)

    print "Number of annotations: %d" % len(annotations.data())

    if len(annotations.data()) > 0:
        ## Creat blank image
        I_a = np.zeros((image.height, image.width), dtype=np.uint8)
        I = np.zeros((image.height, image.width), dtype=np.uint8)

        ## Iterate through annotations and append results to large image
        for a in annotations.data():
            if len(a.term) >= 1:
                if a.image == image.id:

                    if a.user == 1604 or a.user == 1617:
                        # 1630: Ge Huang
                        # 1617: Rachelle
                        # 1604: John Muschler




                        ## convert location information into a usable format
                        location = [s.translate(identity, "()POINTLYGMU").strip(" ") for s in
                                    a.location.encode("utf-8").split(', ')]
                        # location = [s.translate(identity, "()POINTLYGMU").strip(" ") for s in a.location.encode("utf-8").split(', ')]
                        location = [tuple(int(round(float(y))) for y in reversed(x.split())) for x in location]
                        location = [tuple(map(sub, (image.height, 2 * s[1]), s)) for s in location]
                        term = a.term[0]
                        user = a.user

                        ## get bounding box coordination
                        max_x = max(zip(*location)[1])
                        max_y = max(zip(*location)[0])
                        min_x = min(zip(*location)[1])
                        min_y = min(zip(*location)[0])

                        # if annotation corresponds to a region annotation
                        # THIS PART CAN BE REPLACED by dump_annotations information?

                        if term == 3185 or term == 3205 or term == 3225 or term == 3241 or term == 3255 or term == 92920 or term == 93037 or term == 108975:
                            if len(location) > 10:  # REMOVE the case Pathologist mistake
                                print a.id, max_x, max_y, min_x, min_y
                                ## build the URL and download the cropped region
                                url = []
                                img = []
                                url = 'http://localhost-core/api/imageinstance/' + str(a.image) + '/window-' + str(
                                    min_x) + '-' + str(min_y) + '-' + str(max_x - min_x) + '-' + str(
                                    max_y - min_y) + '.png?&mask=true'
                                if not os.path.exists(output_dir + 'Anno_' + str(
                                        image.originalFilename) + '/region_mask/'):
                                    os.makedirs(output_dir + 'Anno_' + str(image.originalFilename) + '/region_mask/')
                                url2 = 'http://localhost-core/api/userannotation/' + str(a.id) + '/alphamask.png'
                                img = conn.fetch_url_into_file(url,
                                                               output_dir + 'Anno_' + str(
                                                                   image.originalFilename) + '/region_mask/'
                                                               + str(a.id) + '.png')  # , is_image=True)
                                
                                img2 = conn.fetch_url_into_file(url2,
                                                               output_dir + 'Anno_' + str(
                                                                   image.originalFilename) + '/region_mask/'
                                                               + str(a.id) +'_raw'+ '.png')  # , is_image=True)
                                # read the image
                                try:
                                    im_crop2 = io.imread(output_dir
                                                        + 'Anno_' + str(image.originalFilename) + '/region_mask/' + str(
                                        a.id) + '.png', dtype=np.uint8)[:, :, 0] 
                                    im_crop = io.imread(output_dir
                                                        + 'Anno_' + str(image.originalFilename) + '/region_mask/' + str(
                                        a.id) + '_raw' + '.png',dtype=np.uint8)[:, :, 3]
                                        #a.id) + '.png', dtype=np.uint8)[:, :, 0]
                                    # im_crop = io.imread(output_dir + 'Anno_' + str(image.orginialFilename) + 
                                    #     '/crop_img/3340/71357_' + str(a.id) + '.png', dtype=np.uint8)[:,:,0]
                                    

                                except:
                                    continue   

                                ## label the region based on the ontology term
                                ## and add region to large image
                                if np.count_nonzero(im_crop) != 0:  ## to skip 'blank' images caused by Cytomine bug
                                    if term == 3185:
                                        im_crop[im_crop != 0] = 1
                                        I_a[min_y:min_y + im_crop.shape[0], min_x:min_x + im_crop.shape[1]] = im_crop
                                    elif term == 3205:
                                        im_crop[im_crop != 0] = 2
                                        # I[min_y:max_y, min_x:max_x] = im_crop
                                        I_a[min_y:min_y + im_crop.shape[0], min_x:min_x + im_crop.shape[1]] = im_crop
                                    elif term == 3225:
                                        im_crop[im_crop != 0] = 3
                                        # I[min_y:max_y, min_x:max_x] = im_crop
                                        I_a[min_y:min_y + im_crop.shape[0], min_x:min_x + im_crop.shape[1]] = im_crop
                                    elif term == 3241:
                                        im_crop[im_crop != 0] = 4
                                        # I[min_y:max_y, min_x:max_x] = im_crop
                                        I_a[min_y:min_y + im_crop.shape[0], min_x:min_x + im_crop.shape[1]] = im_crop
                                    elif term == 3255:
                                        im_crop[im_crop != 0] = 5
                                        # I[min_y:max_y, min_x:max_x] = im_crop
                                        I_a[min_y:min_y + im_crop.shape[0], min_x:min_x + im_crop.shape[1]] = im_crop
                                    elif term == 92920:
                                        im_crop[im_crop != 0] = 6
                                        # I[min_y:max_y, min_x:max_x] = im_crop
                                        I_a[min_y:min_y + im_crop.shape[0], min_x:min_x + im_crop.shape[1]] = im_crop
                                    elif term == 93037:
                                        im_crop[im_crop != 0] = 7
                                        # I[min_y:max_y, min_x:max_x] = im_crop
                                        I_a[min_y:min_y + im_crop.shape[0], min_x:min_x + im_crop.shape[1]] = im_crop
                                    elif term == 108975:
                                        im_crop[im_crop != 0] = 8
                                        # I[min_y:max_y, min_x:max_x] = im_crop
                                        I_a[min_y:min_y + im_crop.shape[0], min_x:min_x + im_crop.shape[1]] = im_crop
                                    
                                    I = I_a | I   # merge

                        ## do the same for point annotations
                        if term == 3185:  # Normal_acini
                            I[tuple(zip(*location))] = 1
                        elif term == 3205:  # Ductal_neoplasia
                            I[tuple(zip(*location))] = 2
                        elif term == 3225:  # Stroma
                            I[tuple(zip(*location))] = 3
                        elif term == 3241:  # Lymph_node
                            I[tuple(zip(*location))] = 4
                        elif term == 3255:  # Fat
                            I[tuple(zip(*location))] = 5
                        elif term == 92920:  # ADM
                            I[tuple(zip(*location))] = 6
                        elif term == 93037:  # Blood_cells
                            I[tuple(zip(*location))] = 7
                        elif term == 108975:  # islet
                            I[tuple(zip(*location))] = 8

                            #
        # https://github.com/cytomine/Cytomine-python-datamining/blob/master/cytomine-applications/classification_validation/add_and_run_job.py
        # get original images crops
        print "Downloading annotations into %s ..." % output_dir

        dump_annotations = conn.dump_annotations(annotations=annotations,
                                                 get_image_url_func=annotation_get_func,
                                                 dest_path=output_dir + 'Anno_' + str(
                                                     image.originalFilename) + '/crop_img/',
                                                 desired_zoom=zoom_level)

        # Save Image (Tile format) plt.imsave('mask_annotation.png', I, cmap="gray",dpi=1)
        y = 0
        x = 0
        # TileSize = 2500
        TileSize = 90000 #2500
        y_count = 0
        x_count = 0
        x_dim = TileSize
        y_dim = TileSize
        rem_width = image.width
        rem_height = image.height
        while x <= image.width:
            while y <= image.height:
                if (rem_width < TileSize and rem_height > TileSize) and (rem_width > 0 and rem_height > 0):
                    im_crop = I[y:y_dim, x:image.width]
                elif (rem_width > TileSize and rem_height < TileSize) and (rem_width > 0 and rem_height > 0):
                    im_crop = I[y:image.height, x:x_dim]
                elif (rem_width < TileSize and rem_height < TileSize) and (rem_width > 0 and rem_height > 0):
                    im_crop = I[y:image.height, x:image.width]
                else:
                    im_crop = I[y:y_dim, x:x_dim]
                if not os.path.exists(output_dir + 'Anno_' + str(image.originalFilename)):
                    os.makedirs(output_dir + 'Anno_' + str(image.originalFilename))
                if 'crop' not in image.originalFilename:
                    # io.imsave('/Users/chanyo/Documents/Cytomine/temp/' + str(image.id) + '/'+str(x_count)+'_'+str(y_count)+'.png', im_crop)
                    # plt.imsave(output_dir + str(image.id) + '/'+str(x_count)+'_'+str(y_count)+'.png', im_crop, cmap='gray', dpi=1)
                    cv2.imwrite(
                        output_dir + 'Anno_' + str(image.originalFilename) + '/Tile_' + str(x_count) + '_' + str(
                            y_count) + '-Annotation_Blood_cells.png', im_crop)
                else:
                    # io.imsave('/Users/chanyo/Documents/Cytomine/temp/' + str(image.id) + '/'+str(y_count)+'_'+str(x_count)+'.png', im_crop)
                    # plt.imsave(output_dir + str(image.id) + '/'+str(y_count)+'_'+str(x_count)+'.png', im_crop, cmap='gray', dpi=1)
                    cv2.imwrite(
                        output_dir + 'Anno_' + str(image.originalFilename) + '/Tile_' + str(y_count) + '_' + str(
                            x_count) + '-Annotation_Blood_cells.png', im_crop)
                y += TileSize
                y_dim += TileSize
                y_count += 1
                rem_height -= TileSize
                # print rem_width, rem_height
            y_dim = TileSize
            x += TileSize
            x_dim += TileSize
            rem_width -= TileSize
            y = 0
            y_count = 0
            x_count += 1
            rem_height = image.height

















# ##################################################################################
#        print "Ontology:"
#        ontology_terms = conn.get_terms(id_ontology=id_ontology)
#        d = dict()
#        for t in ontology_terms.data():
#            d[t.id] = t.name
#            print d[t.id]
#            print "Number of terms in ontology: %d" %len(ontology_terms.data())
#
#
#        for a in annotations.data():
#            landmark = Point(loads(a.location))
#            print "%s,%s,%d,%d" %(I.originalFilename,d[a.term[0]],landmark.x,image.height-landmark.y)
#            #print "annotation id: %d image: %d project: %d term: %s user: %d area: %d perimeter: %s wkt: %s" %(a.id,a.image,a.project,a.term,a.user,a.area,a.perimeter,a.location)
#
#







#
#    ## create blank image
#    im = np.zeros((image_h, image_w), dtype=np.uint8)
#
#    ## iterate through annotations and append results to large image
#    for a in annotations.data():
#      if len(a.term) == 1:
#        if a.image == image.id:
#          if a.user == 6048201 or a.user == 6175413 or a.user == 6090392 or a.user == 6089221:
#
#            ## convert location information into a usable format
#            location = [s.translate(identity, "()POINTLYGMU").strip(" ") for s in a.location.encode("utf-8").split(', ')]
#            location = [s.translate(identity, "()POINTLYGMU").strip(" ") for s in a.location.encode("utf-8").split(', ')]
#            location = [tuple(int(round(float(y))) for y in reversed(x.split())) for x in location]
#            location = [tuple(map(sub, (image_h, 2*s[1]), s)) for s in location]
#            term = a.term[0]
#            user = a.user
#
#            ## get bounding box coordinates
#            max_x = max(zip(*location)[1])
#            max_y = max(zip(*location)[0])
#            min_x = min(zip(*location)[1])
#            min_y = min(zip(*location)[0])
#
#            # if annotation corresponds to a region annotation
#            if term == 5983163 or term == 5983213 or term == 5983193 or term == 5983239:
#
#              ## build the URL and download the cropped region
#              url = 'http://localhost-core/api/imageinstance/'+str(a.image)+'/window-'+str(min_x)+'-'+str(min_y)+'-'+str(max_x-min_x)+'-'+str(max_y-min_y)+'.png?&mask=true'
#              if not os.path.exists('/Users/chanyo/Documents/ChangLab/Cytomine/annotation_ROIs/'+str(a.image)+'/'):
#                  os.makedirs('/Users/chanyo/Documents/ChangLab/Cytomine/annotation_images/'+str(a.image)+'/')
#              img = conn.fetch_url_into_file(url,
#                                              '/Users/chanyo/Documents/ChangLab/Cytomine/annotation_ROIs/'+str(a.image)+'/'
#                                              + str(a.id)+'.png', is_image=True)
#
#              # read the image
#              try:
#                im_crop = io.imread(
#                               '/Users/chanyo/Documents/ChangLab/Cytomine/annotation_ROIs/'
#                                + str(a.id)+'.png', dtype=np.uint8)[:,:,0]
#              except:
#                continue
#
#              ## label the region based on the ontology term
#              ## and add region to large image
#              if np.count_nonzero(im_crop) != 0: ## to skip 'blank' images caused by Cytomine bug
#                if term == 5983163:
#                  im_crop[im_crop != 0] = 1
#                  im[min_y:min_y+im_crop.shape[0], min_x:min_x+im_crop.shape[1]] = im_crop
#                elif term == 5983213:
#                  im_crop[im_crop != 0] = 2
#                  im[min_y:max_y, min_x:max_x] = im_crop
#                elif term == 5983193:
#                  im_crop[im_crop != 0] = 3
#                  im[min_y:max_y, min_x:max_x] = im_crop
#                elif term == 5983239:
#                  im_crop[im_crop != 0] = 4
#                  im[min_y:max_y, min_x:max_x] = im_crop
#
#            ## do the same for point annotations
#            if term == 5983151: # cancer cell
#              im[tuple(zip(*location))] = 1
#            elif term == 5983205: # normal cell
#              im[tuple(zip(*location))] = 2
#            elif term == 5983179: # lymphocyte
#              im[tuple(zip(*location))] = 3
#            elif term == 5983227: # stromal cell
#              im[tuple(zip(*location))] = 4


# #   split large image into tiles and save
#    y = 0
#    x = 0
#    TileSize = 2500
#    y_count = 0
#    x_count = 0
#    x_dim = TileSize
#    y_dim = TileSize
#    rem_width = image.width
#    rem_height = image.height
#    while x <= image.width:
#      while y <= image.height:
#        if (rem_width < TileSize and rem_height > TileSize) and (rem_width > 0 and rem_height > 0):
#          im_crop = im[y:y_dim, x:image.width]
#        elif (rem_width > TileSize and rem_height < TileSize) and (rem_width > 0 and rem_height > 0):
#          im_crop = im[y:image.height, x:x_dim]
#        elif (rem_width < TileSize and rem_height < TileSize) and (rem_width > 0 and rem_height > 0):
#          im_crop = im[y:image.height, x:image.width]
#        else:
#          im_crop = im[y:y_dim, x:x_dim]
#        if not os.path.exists('/Users/chanyo/Documents/ChangLab/Cytomine/Cytomine/' + str(image.id)):
#          os.makedirs('/Users/vahidazimi/Desktop/Research/young_segmentation/Cytomine/' + str(image.id))
#        if 'crop' not in image.originalFilename:
#          io.imsave('/Users/vahidazimi/Desktop/Research/young_segmentation/Cytomine/' + str(image.id) + '/'+str(x_count)+'_'+str(y_count)+'.png', im_crop)
#        else:
#          io.imsave('/Users/vahidazimi/Desktop/Research/young_segmentation/Cytomine/' + str(image.id) + '/'+str(y_count)+'_'+str(x_count)+'.png', im_crop)
#        y += length
#        y_dim += length
#        y_count += 1
#        rem_height -= TileSize
#        print rem_width, rem_height
#      y_dim = TileSize
#      x += length
#      x_dim += length
#      rem_width -= TileSize
#      y = 0
#      y_count = 0
#      x_count += 1
#      rem_height = image.height













