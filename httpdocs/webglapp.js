
function WebGLViewer(divID) {

  self = this;

  this.divID = divID;
  this.divID_jQuery = '#' + divID;

  this.divWidth = $(this.divID_jQuery).width();
  this.divHeight = $(this.divID_jQuery).height();

  this.neurons = [];

  var camera, scene, renderer, grid_lines, scale, controls;
  var mouseX = 0, mouseY = 0;
  var project_id = project.id;
  var stack_id = project.focusedStack.id;

  /* transform coordinates from CATMAID coordinate system
     to WebGL coordinate system: x->x, y->y+dy, z->-z
    */
  var transform_coordinates = function ( point ) {
    return [point[0],-point[1]+dimension.y*resolution.y,-point[2] ];
  }

  // ---

  var resolution = project.focusedStack.resolution;
      dimension = project.focusedStack.dimension;
      translation = project.focusedStack.translation;

  // ---


  var connectivity_types = new Array('neurite', 'presynaptic_to', 'postsynaptic_to');

  init();
  animate();
  debugaxes();
  draw_grid();
  
  /*
  jQuery.ajax({
    url: "dj/"+project_id+"/stack/" + stack_id + "/info",
    type: "GET",
    dataType: "json",
    success: function (data) {

      resolution = data.stack_scale;
      dimension = data.stack_dimension;
      translation = data.stack_translation;

      var x_middle = (dimension.x*resolution.x)/2.0 + translation.x,
          y_middle = (dimension.y*resolution.y)/2.0 + translation.y,
          z_middle = (dimension.z*resolution.z)/2.0 + translation.z;

      scale = 50./dimension.x;

      var coord = transform_coordinates([x_middle, y_middle, z_middle]);

      create_stackboundingbox(
              coord[0]*scale,
              coord[1]*scale,
              coord[2]*scale,
              dimension.x*resolution.x*scale,
              dimension.y*resolution.y*scale,
              dimension.z*resolution.z*scale
      );

      self.updateActiveNode( 30, 0, 0);
    }
  });*/

  function init() {
    container = document.getElementById(self.divID);
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera( 75, self.divWidth / self.divHeight, 1, 3000 );
    // TODO: lookAt does not work
    camera.lookAt( new THREE.Vector3(0.0,0.0,400.0) );
    controls = new THREE.TrackballControls( camera );
    controls.rotateSpeed = 1.0;
    controls.zoomSpeed = 1.2;
    controls.panSpeed = 0.8;
    controls.noZoom = false;
    controls.noPan = false;
    controls.staticMoving = true;
    controls.dynamicDampingFactor = 0.3;
    
    renderer = new THREE.WebGLRenderer();
    //renderer = new THREE.CanvasRenderer();
    renderer.setSize( self.divWidth, self.divHeight );
    container.appendChild( renderer.domElement );
    container.addEventListener( 'mousemove', onDocumentMouseMove, false );

    // 
    var x_middle = (dimension.x*resolution.x)/2.0 + translation.x,
        y_middle = (dimension.y*resolution.y)/2.0 + translation.y,
        z_middle = (dimension.z*resolution.z)/2.0 + translation.z;

    scale = 50./dimension.x;

    var coord = transform_coordinates([x_middle, y_middle, z_middle]);

    create_stackboundingbox(
            coord[0]*scale,
            coord[1]*scale,
            coord[2]*scale,
            dimension.x*resolution.x*scale,
            dimension.y*resolution.y*scale,
            dimension.z*resolution.z*scale
    );

  }

  var Skeleton = function( skeleton_data )
  {
    this.translate = function( dx, dy, dz )
    {
      for ( var i=0; i<connectivity_types.length; ++i ) {
        if( dx ) {
          this.actor[connectivity_types[i]].translateX( dx );
        }
        if( dy ) {
          this.actor[connectivity_types[i]].translateY( dy );
        }
        if( dz ) {
          this.actor[connectivity_types[i]].translateZ( dz );
        }
      }
    }

    this.updateCompositeActor = function()
    {
      for ( var i=0; i<connectivity_types.length; ++i ) {
        this.actor[connectivity_types[i]] = new THREE.Line( this.geometry[connectivity_types[i]],
            this.line_material[connectivity_types[i]], THREE.LinePieces );
      }
    }

    this.removeActorFromScene = function()
    {
      for ( var i=0; i<connectivity_types.length; ++i ) {
        scene.removeObject( this.actor[connectivity_types[i]] );
      }
    }

    this.addCompositeActorToScene = function()
    {
      for ( var i=0; i<connectivity_types.length; ++i ) {
        scene.add( this.actor[connectivity_types[i]] );
      }
    }

    var type, from_vector, to_vector;

    this.line_material = new Object();
    this.geometry = new Object();
    this.actor = new Object();

    this.geometry[connectivity_types[0]] = new THREE.Geometry();
    this.geometry[connectivity_types[1]] = new THREE.Geometry();
    this.geometry[connectivity_types[2]] = new THREE.Geometry();

    this.line_material[connectivity_types[0]] = new THREE.LineBasicMaterial( { color: 0xffff00, opacity: 1.0, linewidth: 3 } );
    this.line_material[connectivity_types[1]] = new THREE.LineBasicMaterial( { color: 0xff0000, opacity: 1.0, linewidth: 6 } )
    this.line_material[connectivity_types[2]] = new THREE.LineBasicMaterial( { color: 0x0000ff, opacity: 1.0, linewidth: 6 } )

    this.original_vertices = skeleton_data.vertices;
    this.original_connectivity = skeleton_data.connectivity;
    this.id = skeleton_data.id;
    this.baseName = skeleton_data.baseName;

    for (var fromkey in this.original_connectivity) {
      var to = this.original_connectivity[fromkey];
      for (var tokey in to) {
        
        type = connectivity_types[connectivity_types.indexOf(this.original_connectivity[fromkey][tokey]['type'])];
        var fv=transform_coordinates([
                 this.original_vertices[fromkey]['x'],
                 this.original_vertices[fromkey]['y'],
                 this.original_vertices[fromkey]['z']
            ]);
        from_vector = new THREE.Vector3(fv[0], fv[1], fv[2] );

        // transform
        from_vector.multiplyScalar( scale );

        this.geometry[type].vertices.push( new THREE.Vertex( from_vector ) );

        var tv=transform_coordinates([
                 this.original_vertices[tokey]['x'],
                 this.original_vertices[tokey]['y'],
                 this.original_vertices[tokey]['z']
            ]);
        to_vector = new THREE.Vector3(tv[0], tv[1], tv[2] );

        // transform
        // to_vector.add( translate_x, translate_y, translate_z );
        to_vector.multiplyScalar( scale );

        this.geometry[type].vertices.push( new THREE.Vertex( to_vector ) );
      }
    }

    this.updateCompositeActor();

  }

  // array of skeletons
  var skeletons = new Object();

  // active node geometry
  var active_node;

  this.createActiveNode = function( x, y, z)
  {
    sphere = new THREE.SphereGeometry( 50, 32, 32, 1 );
    active_node = new THREE.Mesh( sphere, new THREE.MeshBasicMaterial( { color: 0xffaa00 } ) );
    active_node.scale.set( 0.05, 0.05, 0.05 );
    active_node.position.set( x,y,z );
    scene.add( active_node );
  }

  this.removeActiveNode = function() {
    if(active_node) {
      scene.removeObject( active_node );
      active_node = null;
    }
  }

  this.updateActiveNode = function( x, y, z )
  {
    if(!active_node) {
      this.createActiveNode( 0, 0, 0 );
    }
    var co = transform_coordinates( [
      translation.x + ((x) / project.focusedStack.scale) * resolution.x,
      translation.y + ((y) / project.focusedStack.scale) * resolution.y,
      translation.z + z * resolution.z]
    );
    active_node.position.set( co[0]*scale, co[1]*scale, co[2]*scale );
  }

  // add skeleton to scene
  this.addSkeleton = function( skeleton_id, skeleton_data )
  {
    if( skeletons.hasOwnProperty(skeleton_id) ){
      alert("This skeleton (ID: "+skeleton_id+") has already been added to the viewer");
      return;
    } else {
      skeleton_data['id'] = skeleton_id;
      skeletons[skeleton_id] = new Skeleton( skeleton_data );
      self.addToSkeletonList( skeletons[skeleton_id] );
      skeletons[skeleton_id].addCompositeActorToScene();
      return true;
    }
  }

  // remove skeleton from scence
  this.removeSkeleton = function( skeleton_id )
  {
    if( !skeletons.hasOwnProperty(skeleton_id) ){
        alert("Skeleton "+skeleton_id+" does not exist. Cannot remove it!");
        return;
    } else {
        skeletons[skeleton_id].removeActorFromScene();
        delete skeletons[skeleton_id];
        return true;
    }
  }

  function create_stackboundingbox(x, y, z, dx, dy, dz)
  {
    console.log('bouding box', x, y, z, dx, dy, dz);
    var gg = new THREE.CubeGeometry( dx, dy, dz );
    var mm = new THREE.MeshBasicMaterial( { color: 0xff0000, wireframe: true } );
    var mesh = new THREE.Mesh( gg, mm );
    mesh.position.set(x, y, z);
    scene.add( mesh );
    // update camera
    camera.position.x = dx;
    camera.position.y = dy;
  }

  function debugaxes() {
    var object = new THREE.Axes();
    object.position.set( -1, -1, 0 );
    object.scale.x = object.scale.y = object.scale.z = 0.1;
    scene.add( object );
  }

  function draw_grid() {
    // Grid
    var line_material = new THREE.LineBasicMaterial( { color: 0xffffff, opacity: 0.2 } ),
      geometry = new THREE.Geometry(),
      floor = 0, step = 25;
    for ( var i = 0; i <= 40; i ++ ) {
      geometry.vertices.push( new THREE.Vertex( new THREE.Vector3( - 500, floor, i * step - 500 ) ) );
      geometry.vertices.push( new THREE.Vertex( new THREE.Vector3(   500, floor, i * step - 500 ) ) );
      geometry.vertices.push( new THREE.Vertex( new THREE.Vector3( i * step - 500, floor, -500 ) ) );
      geometry.vertices.push( new THREE.Vertex( new THREE.Vector3( i * step - 500, floor,  500 ) ) );

    }
    grid_lines = new THREE.Line( geometry, line_material, THREE.LinePieces );
    scene.add( grid_lines );
  }

  function animate() {
    requestAnimationFrame( animate );
    render();
  }

  function onDocumentMouseMove(event) {
    mouseX = ( event.clientX - self.divWidth );
    mouseY = ( event.clientY - self.divHeight );
  }

  function render() {
    controls.update();
    /*camera.position.x += ( mouseX - camera.position.x ) * .05;
    camera.position.y += ( -mouseY - camera.position.y ) * .05;
    camera.lookAt( scene.position );*/
    renderer.clear();
    renderer.render( scene, camera );
  }


  this.addToSkeletonList = function ( skeleton ) {
    var newElement = $('<li/>'),
        linkElement, enclosingObject = this;
    newElement.attr('id', '3d-object-' + skeleton.baseName );
    newElement.text(skeleton.baseName + ' ');
    linkElement = $('<a/>');
    linkElement.attr('href', '#');
    linkElement.text("(remove)");
    enclosingObject = this;
    linkElement.click(function (e) {
      self.removeSkeleton( skeleton.id );
      newElement.remove();
    });
    newElement.append(linkElement);
    $('#view-3d-webgl-object-list').append(newElement);
  };

  this.addFromCATMAID = function (projectID, skeletonID, neuronName) {
    if( skeletonID !== undefined )
    {
        jQuery.ajax({
          //url: "../../model/export.skeleton.json.php",
          url: "dj/"+projectID+"/skeleton/" + skeletonID + "/json",
          type: "GET",
          dataType: "json",
          success: function (skeleton_data) {
            skeleton_data['baseName'] = neuronName;
            self.addSkeleton( parseInt(skeletonID), skeleton_data );
          }
        });
    }
  };

  this.toString = function () {
    return "WebGL Viewer(" + this.divID + ")";
  };

}

function nameFromCATMAIDInfo(info) {
  return info.skeleton_name + ' [' + info.neuron_name + ']';
}

function addNeuronFromCATMAID(divID, info) {

  var divID_jQuery = '#' + divID;

  if (!$(divID_jQuery).data('viewer')) {
    $(divID_jQuery).data('viewer', new WebGLViewer(divID));
  }

  $(divID_jQuery).data('viewer').addFromCATMAID(info.project_id, info.skeleton_id, nameFromCATMAIDInfo(info));
}

function createWebGLViewerFromCATMAID(divID) {

  var divID_jQuery = '#' + divID;

  if (!$(divID_jQuery).data('viewer')) {
    $(divID_jQuery).data('viewer', new WebGLViewer(divID));
  }
}

function update3DWebGLViewATN() {
  // FIXME: need physical coordinates! create new backend code to retrieve
  var atn = SkeletonAnnotations.getActiveNodePosition();

  var divID = 'viewer-3d-webgl-canvas';
  var divID_jQuery = '#' + divID;

  if (!$(divID_jQuery).data('viewer')) {
    $(divID_jQuery).data('viewer', new WebGLViewer(divID));
  }

  if (!atn) {
    alert("You must have an active node selected to add its skeleton to the 3D WebGL View.");
    $(divID_jQuery).data('viewer').removeActiveNode();
    return;
  }

  $(divID_jQuery).data('viewer').updateActiveNode( atn.x, atn.y, atn.z );
  
}

function addTo3DWebGLView() {
  var atn_id = SkeletonAnnotations.getActiveNodeId();
  if (!atn_id) {
    alert("You must have an active node selected to add its skeleton to the 3D WebGL View.");
    return;
  }
  if (SkeletonAnnotations.getActiveNodeType() != "treenode") {
    alert("You can only add skeletons to the 3D WebGL View at the moment - please select a node of a skeleton.");
    return;
  }
  requestQueue.register('model/treenode.info.php', 'POST', {
    pid: project.id,
    tnid: atn_id
  }, function (status, text, xml) {
    if (status == 200) {
      var e = eval("(" + text + ")");
      if (e.error) {
        alert(e.error);
      } else {
        e['project_id'] = project.id;
        addNeuronFromCATMAID('viewer-3d-webgl-canvas', e);
      }
    } else {
      alert("Bad status code " + status + " mapping treenode ID to skeleton and neuron");
    }
    return true;
  });
}