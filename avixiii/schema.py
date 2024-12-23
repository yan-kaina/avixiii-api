import graphene
from graphene_django.debug import DjangoDebug
from authentication.schema import Query as AuthQuery, Mutation as AuthMutation
from store.schema import Query as StoreQuery, Mutation as StoreMutation

class Query(AuthQuery, StoreQuery, graphene.ObjectType):
    # This adds the python `debug` field to your GraphQL API
    debug = graphene.Field(DjangoDebug, name='_debug')

class Mutation(AuthMutation, StoreMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
