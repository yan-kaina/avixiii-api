import graphene
from graphene_django.debug import DjangoDebug
from store.schema import Query as StoreQuery
from store.schema import Mutation as StoreMutation

class Query(StoreQuery, graphene.ObjectType):
    # This adds the python `debug` field to your GraphQL API
    debug = graphene.Field(DjangoDebug, name='_debug')

class Mutation(StoreMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
