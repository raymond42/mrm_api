import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from sqlalchemy import func
from graphql import GraphQLError

from api.room_resource.models import Resource as ResourceModel
from utilities.validations import validate_empty_fields
from utilities.utility import update_entity_fields
from helpers.auth.authentication import Auth
from helpers.auth.error_handler import SaveContextManager
from helpers.pagination.paginate import Paginate, validate_page


class Resource(SQLAlchemyObjectType):
    """
        Autogenerated return type of a room resource
    """

    class Meta:
        model = ResourceModel


class PaginatedResource(Paginate):
    """
        Returns paginated room resources
    """
    resources = graphene.List(Resource)

    def resolve_resources(self, info):
        # Function to get all room resources
        page = self.page
        per_page = self.per_page
        unique = self.unique
        query = Resource.get_query(info)
        active_resources = query.filter(ResourceModel.state == "active")
        if not page:
            if unique:
                return active_resources.distinct(ResourceModel.name).all()
            return active_resources.order_by(
                func.lower(ResourceModel.name)).all()
        page = validate_page(page)
        self.query_total = active_resources.count()
        result = active_resources.order_by(func.lower(
            ResourceModel.name)).limit(per_page).offset(page*per_page)
        if result.count() == 0:
            return GraphQLError("No more resources")
        return result


class CreateResource(graphene.Mutation):
    """
        Create a room resource
    """

    class Arguments:
        name = graphene.String(required=True)
        quantity = graphene.Int(required=True)
    resource = graphene.Field(Resource)

    @Auth.user_roles('Admin')
    def mutate(self, info, **kwargs):
        resource = ResourceModel(**kwargs)
        if kwargs.get('quantity') < 0:
            return GraphQLError("The quantity should not be less than 0")
        print()
        payload = {
            'model': ResourceModel, 'field': 'name', 'value':  kwargs['name']
            }
        with SaveContextManager(
          resource, 'Resource', payload
        ):
            return CreateResource(resource=resource)


class UpdateRoomResource(graphene.Mutation):
    """
        Update a room resource
    """
    class Arguments:
        name = graphene.String()
        resource_id = graphene.Int()
        quantity = graphene.Int()
    resource = graphene.Field(Resource)

    @Auth.user_roles('Admin')
    def mutate(self, info, resource_id, **kwargs):
        validate_empty_fields(**kwargs)
        quantity = kwargs.get('quantity')
        if quantity and quantity < 0:
            return GraphQLError("The quantity should not be less than 0")
        query = Resource.get_query(info)
        active_resources = query.filter(ResourceModel.state == "active")
        exact_resource = active_resources.filter(
            ResourceModel.id == resource_id).first()
        if not exact_resource:
            raise GraphQLError("Resource not found")

        update_entity_fields(exact_resource, **kwargs)
        exact_resource.save()
        return UpdateRoomResource(resource=exact_resource)


class DeleteResource(graphene.Mutation):
    """
        Delete a room resource
    """

    class Arguments:
        resource_id = graphene.Int(required=True)
        state = graphene.String()
    resource = graphene.Field(Resource)

    @Auth.user_roles('Admin')
    def mutate(self, info, resource_id, **kwargs):
        query_room_resource = Resource.get_query(info)
        active_resources = query_room_resource.filter(
            ResourceModel.state == "active")
        exact_room_resource = active_resources.filter(
            ResourceModel.id == resource_id).first()
        if not exact_room_resource:
            raise GraphQLError("Resource not found")

        update_entity_fields(exact_room_resource, state="archived", **kwargs)
        exact_room_resource.save()
        return DeleteResource(resource=exact_room_resource)


class Query(graphene.ObjectType):
    """
        Query to get room resources
    """

    all_resources = graphene.Field(
        PaginatedResource,
        page=graphene.Int(),
        per_page=graphene.Int(),
        unique=graphene.Boolean(),
        description="Returns a list of paginated room resources and accepts the arguments\
            \n- page: Field for page of the room response\
            \n- per_page: Field for number of responses per page\
            \n- unique: Boolean field for uniqueroom response")
    get_resources_by_room_id = graphene.List(
        lambda: Resource,
        room_id=graphene.Int(),
        description="Returns a list of room's resources. Accepts the argument\
            \n- room_id: Unique identifier of a room")

    def resolve_all_resources(self, info, **kwargs):
        # Get all resources
        resp = PaginatedResource(**kwargs)
        return resp

    def resolve_get_resources_by_room_id(self, info, room_id):
        # Get resources of a specifics room
        query = Resource.get_query(info)
        active_resources = query.filter(ResourceModel.state == "active")
        check_room = active_resources.filter(
            ResourceModel.room_id == room_id).first()
        if not check_room:
            raise GraphQLError("Room has no resource yet")

        return active_resources.filter(ResourceModel.room_id == room_id)


class Mutation(graphene.ObjectType):
    """
        Mutation to create, update and delete resources
    """

    create_resource = CreateResource.Field(
        description="Creates a new Resource having arguments\
            \n- name: The name field of the resource[required]\
            \n- room_id: The unique identifier of the room where the resource \
            is created[required]\n- quantity: The number of resources[required]"
                )
    update_room_resource = UpdateRoomResource.Field(
        description="Updates the room resources fields below\
            \n- name: The name field of the resource\
            \n- room_id: The unique identifier of the room where the resource \
            is found\n- quantity: The number of resources")
    delete_resource = DeleteResource.Field(
        description="Deletes a resource with arguments\
            \n- resource_id: Unique id identifier of the resource\
            \n- state: Check if the room response is active,\
                 archived or deleted")
