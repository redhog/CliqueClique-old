from __future__ import with_statement

import Node, AnnotationNode, SyncNode, ExprNode, SubscriptionNode, PostingNode, IntrospectionNode, Tables

class LocalNode(SyncNode.ThreadSyncNode, IntrospectionNode.IntrospectionNode, PostingNode.PostingNode):
    pass
