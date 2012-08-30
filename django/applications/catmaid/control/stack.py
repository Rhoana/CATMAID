from django.shortcuts import get_object_or_404

from catmaid.models import *
from catmaid.control.authentication import *
from catmaid.control.common import *
from catmaid.transaction import *

def get_stack_info(project_id=None, stack_id=None, user=None):
    """ Returns a dictionary with relevant information for stacks.
    Depending on the tile_source_type, get information from database
    or from tile server directly
    """
    p = get_object_or_404(Project, pk=project_id)
    s = get_object_or_404(Stack, pk=stack_id)
    ps_all = ProjectStack.objects.filter(project=project_id, stack=stack_id)
    if len(ps_all) != 1:
        return {'error': 'Multiple project - stack associations, but should only be one.'}
    ps=ps_all[0]
    pu = ProjectUser.objects.filter(project=project_id, user=user.id).count()

    # https://github.com/acardona/CATMAID/wiki/Convention-for-Stack-Image-Sources
    if int(s.tile_source_type) == 2:
        # request appropriate stack metadata from tile source
        url=s.image_base.rstrip('/').lstrip('http://')
        # Important: Do not use localhost, but 127.0.0.1 instead
        # to prevent an namespace lookup error (gaierror)
        # Important2: Do not put http:// in front!
        conn = httplib.HTTPConnection(url)
        conn.request('GET', '/metadata')
        response = conn.getresponse()
        # read JSON response according to metadata convention
        # Tornado reponse is escaped JSON string
        read_response = response.read()
        # convert it back to dictionary str->dict
        return json.loads(read_response)
    else:
        broken_slices_qs = BrokenSlice.objects.filter(stack=stack_id)
        broken_slices = {}
        for ele in broken_slices_qs:
            broken_slices[ele.index] = 1
        overlays = []
        overlays_qs = Overlay.objects.filter(stack=stack_id)
        for ele in overlays_qs:
            overlays.append( {
                'id': ele.id,
                'title': ele.title,
                'image_base': ele.image_base,
                'default_opacity': ele.default_opacity,
                } )
        result={
            'sid': int(s.id),
            'pid': int(p.id),
            'ptitle': p.title,
            'stitle': s.title,
            'image_base': s.image_base,
            'num_zoom_levels': int(s.num_zoom_levels),
            'file_extension': s.file_extension,
            'editable': int(pu>0),
            'translation': {
                'x': ps.translation.x,
                'y': ps.translation.y,
                'z': ps.translation.z
            },
            'resolution': {
                'x': float(s.resolution.x),
                'y': float(s.resolution.y),
                'z': float(s.resolution.z)
            },
            'dimension': {
                'x': int(s.dimension.x),
                'y': int(s.dimension.y),
                'z': int(s.dimension.z)
            },
            'tile_height': int(s.tile_height),
            'tile_width': int(s.tile_width),
            'tile_source_type': int(s.tile_source_type),
            'metadata' : s.metadata,
            'broken_slices': broken_slices,
            'trakem2_project': int(s.trakem2_project),
            'overlay': overlays
        }

    return result

@catmaid_login_required
def stack_info(request, project_id=None, stack_id=None, logged_in_user=None):
    result=get_stack_info(project_id, stack_id, logged_in_user)
    return HttpResponse(json.dumps(result, sort_keys=True, indent=4), mimetype="text/json")

@catmaid_login_required
def stack_models(request, project_id=None, stack_id=None, logged_in_user=None):
    """ Retrieve Mesh models for a stack
    """
    d={}
    filename=os.path.join(settings.HDF5_STORAGE_PATH, '%s_%s.hdf' %(project_id, stack_id) )
    if not os.path.exists(filename):
        return HttpResponse(json.dumps(d), mimetype="text/json")
    with closing(h5py.File(filename, 'r')) as hfile:
        meshnames=hfile['meshes'].keys()
        for name in meshnames:
            vertlist=hfile['meshes'][name]['vertices'].value.tolist()
            facelist= hfile['meshes'][name]['faces'].value.tolist()
            d[str(name)] = {
                'metadata': {
                    'colors': 0,
                    'faces': 2,
                    'formatVersion': 3,
                    'generatedBy': 'NeuroHDF',
                    'materials': 0,
                    'morphTargets': 0,
                    'normals': 0,
                    'uvs': 0,
                    'vertices': 4},
                'morphTargets': [],
                'normals': [],
                'scale': 1.0,
                'uvs': [[]],
                'vertices': vertlist,
                'faces': facelist,
                'materials': [],
                'colors': []
            }
    return HttpResponse(json.dumps(d), mimetype="text/json")
