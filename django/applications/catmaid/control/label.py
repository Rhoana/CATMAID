import json

from collections import defaultdict
from django.db import connection
from django.http import HttpResponse, Http404
from django.db.models import Count
from django.shortcuts import get_object_or_404

from catmaid.models import *
from catmaid.control.authentication import *
from catmaid.control.common import *


@requires_user_role([UserRole.Annotate, UserRole.Browse])
def labels_all(request, project_id=None):
    qs = ClassInstance.objects.filter(
        class_column__class_name='label',
        project=project_id)
    return HttpResponse(json.dumps(list(x.name for x in qs)), mimetype="text/plain")

@requires_user_role([UserRole.Annotate, UserRole.Browse])
def labels_for_node(request, project_id=None, ntype=None, location_id=None):
    if ntype == 'treenode':
        qs = TreenodeClassInstance.objects.filter(
            relation__relation_name='labeled_as',
            class_instance__class_column__class_name='label',
            treenode=location_id,
            project=project_id).select_related('class_instance__name')
    elif ntype == 'location' or ntype == 'connector':
        qs = ConnectorClassInstance.objects.filter(
            relation__relation_name='labeled_as',
            class_instance__class_column__class_name='label',
            connector=location_id,
            project=project_id).select_related('class_instance__name')
    else:
        raise Http404('Unknown node type: "%s"' % (ntype,))
    return HttpResponse(json.dumps(list(x.class_instance.name for x in qs)), mimetype="text/plain")

@requires_user_role([UserRole.Annotate, UserRole.Browse])
def labels_for_nodes(request, project_id=None):
    # Two POST variables, which are each an array of integers stringed together with commas as separators
    treenode_ids = request.POST['treenode_ids'].strip()
    connector_ids = request.POST['connector_ids'].strip()
    result = defaultdict(list)
    cursor = connection.cursor();

    if treenode_ids:
        # Could use treenode_ids directly as a string, but it is good to sanitize arguments
        cursor.execute('''
        SELECT treenode.id, class_instance.name
        FROM treenode, class_instance, treenode_class_instance, relation
        WHERE relation.id = treenode_class_instance.relation_id
          AND relation.relation_name = 'labeled_as'
          AND treenode_class_instance.treenode_id = treenode.id
          AND class_instance.id = treenode_class_instance.class_instance_id
          AND treenode.id IN (%s)
        ''' % ','.join(str(int(x)) for x in treenode_ids.split(','))) # convoluted to sanitize

        for row in cursor.fetchall():
            result[row[0]].append(row[1])
        # The code below:
        # 1. Is hard to read, compared to plain SQL (see above)
        # 2. Selects all possible columns, wastefully
        # 3. If appended with values(...), then returns a dictionary, wastefully
        # 4. Runs slower than the equivalent code above
        """
        qs_treenodes = TreenodeClassInstance.objects.filter(
            relation__relation_name='labeled_as',
            class_instance__class_column__class_name='label',
            treenode__id__in=(int(x) for x in treenode_ids.split(',')),
            project=project_id).select_related('treenode', 'class_instance').values('treenode_id', 'class_instance__name')
        for tci in qs_treenodes:
            result[tci['treenode_id']].append(tci['class_instance__name'])
        """

    if connector_ids:
        cursor.execute('''
        SELECT connector.id, class_instance.name
        FROM connector, class_instance, connector_class_instance, relation
        WHERE relation.id = connector_class_instance.relation_id
          AND relation.relation_name = 'labeled_as'
          AND connector_class_instance.connector_id = connector.id
          AND class_instance.id = connector_class_instance.class_instance_id
          AND connector.id IN (%s)
        ''' % ','.join(str(int(x)) for x in connector_ids.split(','))) # convoluted to sanitize
        for row in cursor.fetchall():
            result[row[0]].append(row[1])

        # See notes above for treenode_ids
        """
        qs_connectors = ConnectorClassInstance.objects.filter(
            relation__relation_name='labeled_as',
            class_instance__class_column__class_name='label',
            connector__id__in=(int(x) for x in connector_ids.split(',')),
            project=project_id).select_related('connector', 'class_instance')
        for cci in qs_connectors:
            result[cci.connector.id].append(cci.class_instance.name)
        """

    return HttpResponse(json.dumps(result), mimetype="text/plain")

@requires_user_role(UserRole.Annotate)
def label_update(request, project_id=None, location_id=None, ntype=None):
    labeled_as_relation = Relation.objects.get(project=project_id, relation_name='labeled_as')
    p = get_object_or_404(Project, pk=project_id)
    
    newTags = request.POST['tags'].split(',')
    
    # Get the existing list of tags for the tree node/connector and delete any that are not in the new list.
    if ntype == 'treenode':
        existingLabels = TreenodeClassInstance.objects.filter(
            treenode__id=location_id,
            relation=labeled_as_relation,
            class_instance__class_column__class_name='label').select_related('class_instance__name')
        TreenodeClassInstance.objects.for_user(request.user).filter(
            treenode__id=location_id,
            relation=labeled_as_relation,
            class_instance__class_column__class_name='label').exclude(class_instance__name__in=newTags).delete()
    elif ntype == 'connector' or ntype == 'location':
        existingLabels = ConnectorClassInstance.objects.filter(
            connector__id=location_id,
            relation=labeled_as_relation,
            class_instance__class_column__class_name='label').select_related('class_instance__name')
        ConnectorClassInstance.objects.for_user(request.user).filter(
            connector__id=location_id,
            relation=labeled_as_relation,
            class_instance__class_column__class_name='label').exclude(class_instance__name__in=newTags).delete()
    else:
        raise Http404('Unknown node type: "%s"' % (ntype,))

    existingNames = set(ele.class_instance.name for ele in existingLabels)

    # Add any new labels.
    label_class = Class.objects.get(project=project_id, class_name='label')
    for tag_name in newTags:
        if len(tag_name) > 0 and tag_name not in existingNames:
            # Make sure the tag instance exists.
            existing_tags = list(ClassInstance.objects.filter(
                project=p,
                name=tag_name,
                class_column=label_class))
            if len(existing_tags) < 1:
                tag = ClassInstance(
                    project=p,
                    name=tag_name,
                    user=request.user,
                    class_column=label_class)
                tag.save()
            else:
                tag = existing_tags[0]
            
            # Add the tag to the tree node/connector.
            if ntype == 'treenode':
                tci = TreenodeClassInstance(
                    user=request.user,
                    project=p,
                    relation=labeled_as_relation,
                    treenode=Treenode(id=location_id),
                    class_instance=tag)
            else:
                tci = ConnectorClassInstance(
                    user=request.user,
                    project=p,
                    relation=labeled_as_relation,
                    connector=Connector(id=location_id),
                    class_instance=tag)
            tci.save()
    return HttpResponse(json.dumps({'message': 'success'}), mimetype='text/json')
