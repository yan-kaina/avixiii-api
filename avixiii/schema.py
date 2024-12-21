import graphene
from graphene_django.debug import DjangoDebug

class Query(graphene.ObjectType):
    # This adds the python `debug` field to your GraphQL API
    debug = graphene.Field(DjangoDebug, name='_debug')

schema = graphene.Schema(query=Query)
