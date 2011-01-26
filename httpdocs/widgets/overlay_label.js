/* 
 * Simple wrapper for labels
 */
OverlayLabel = function(
  id,     // unique id for the node from the database
  paper,  // the raphael paper this node is drawn to
  x,      // the x coordinate in pixel coordinates
  y,      // y coordinates 
  text
  )  
{ 
  // the database treenode id
  this.id = id;
  this.paper = paper;
  
  // local screen coordinates relative to the div
  // pixel coordinates
  this.x = x;
  this.y = y;
  this.text = text;
  
  var c
  
  // create a raphael circle object
  c = this.paper.g.blob(this.x, this.y, this.text);
        
  this.remove = function() {
    c.remove();
  }
}