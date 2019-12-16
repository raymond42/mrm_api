import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType

from api.question.models import Question as QuestionModel
from utilities.validations import (
    validate_empty_fields,
    validate_date_time_range,
    validate_question_type
)
from utilities.utility import update_entity_fields
from helpers.auth.authentication import Auth
from helpers.auth.error_handler import SaveContextManager
from helpers.pagination.paginate import Paginate, validate_page
from helpers.questions_filter.questions_filter import (
    filter_questions_by_date_range
)
from api.bugsnag_error import return_error


class Question(SQLAlchemyObjectType):
    """
        Autogenerated return type of questions
    """
    class Meta:
        model = QuestionModel

    question_response_count = graphene.Int()

    def resolve_question_response_count(self, info):
        return self.question_response_count


class CreateQuestion(graphene.Mutation):
    """
        Creates a Question. Takes the required arguments (question title,\
             question type, question, start date and end date)
    """
    class Arguments:
        question_title = graphene.String(required=True)
        question_type = graphene.String(required=True)
        question = graphene.String(required=True)
        start_date = graphene.DateTime(required=True)
        end_date = graphene.DateTime(required=True)
        check_options = graphene.List(graphene.String, required=False)
    question = graphene.Field(Question)

    @Auth.user_roles('Admin', 'Super Admin')
    def mutate(self, info, **kwargs):
        validate_empty_fields(**kwargs)
        validate_question_type(**kwargs)
        validate_date_time_range(**kwargs)
        question_type = kwargs['question_type']
        fields = kwargs
        if question_type == "check" and not kwargs.get('check_options'):
            return_error.report_errors_bugsnag_and_graphQL(
                "No check options supplied for question type check"
            )
        if question_type != "check":
            fields['check_options'] = None
        payload = {
            'model': QuestionModel, 'field': 'question',
            'value':  kwargs['question']
        }
        question = QuestionModel(**fields)
        with SaveContextManager(question, 'Question', payload):
            return CreateQuestion(question=question)


class PaginatedQuestions(Paginate):
    """
        Paginates the returned questions with the number of pages,\
            the total number of questions if it has next or previous page\
                the current page and the questions field
    """
    questions = graphene.List(Question)

    def resolve_questions(self, info):
        page = self.page
        per_page = self.per_page
        query = Question.get_query(info)
        active_questions = query.filter(QuestionModel.state == "active")
        if not page:
            return active_questions.all()
        page = validate_page(page)
        self.query_total = active_questions.count()
        result = active_questions.limit(per_page).offset(page * per_page)
        if result.count() == 0:
            return_error.report_errors_bugsnag_and_graphQL("No questions found")
        return result


class UpdateQuestion(graphene.Mutation):
    """
       Updates a Question. Takes the required argument (question id,)
        and optional arguments(question title, question type, question,
             start date, end date and is active for checking if the
                 question is active or not)
    """
    class Arguments:
        question_id = graphene.Int(required=True)
        question_title = graphene.String()
        question_type = graphene.String()
        question = graphene.String()
        start_date = graphene.DateTime()
        end_date = graphene.DateTime()
        is_active = graphene.Boolean()

    question = graphene.Field(Question)

    @Auth.user_roles('Admin', 'Super Admin')
    def mutate(self, info, question_id, **kwargs):
        validate_empty_fields(**kwargs)
        validate_question_type(**kwargs)
        query_question = Question.get_query(info)
        active_questions = query_question.filter(
            QuestionModel.state == "active")
        exact_question = active_questions.filter(
            QuestionModel.id == question_id).first()
        if not exact_question:
            return_error.report_errors_bugsnag_and_graphQL("Question not found")
        validate_date_time_range(**kwargs)
        update_entity_fields(exact_question, **kwargs)
        exact_question.save()
        return UpdateQuestion(question=exact_question)


class DeleteQuestion(graphene.Mutation):
    """
        Deletes a question taking a required argument which is the question id\
            and state which checks if the question is active, archived or\
                 deleted
    """
    class Arguments:
        question_id = graphene.Int(required=True)
        state = graphene.String()

    question = graphene.Field(Question)

    @Auth.user_roles('Admin', 'Super Admin')
    def mutate(self, info, question_id):
        query_question = Question.get_query(info)
        active_questions = query_question.filter(
            QuestionModel.state == "active")
        exact_question = active_questions.filter(
            QuestionModel.id == question_id).first()
        if not exact_question:
            return_error.report_errors_bugsnag_and_graphQL("Question not found")
        update_entity_fields(exact_question, state="archived")
        exact_question.save()
        return DeleteQuestion(question=exact_question)


class UpdateQuestionViews(graphene.Mutation):
    """
        Updates the question view taking a required argument which increments\
             the total views of questions.
    """
    class Arguments:
        increment_total_views = graphene.Boolean(required=True)

    questions = graphene.List(Question)

    def mutate(self, info, **kwargs):
        query = Question.get_query(info)
        questions = query.all()
        new_total_views = 0
        for question in questions:
            if kwargs['increment_total_views'] and not question.total_views:
                new_total_views = 1
            if kwargs['increment_total_views'] and question.total_views:
                new_total_views = question.total_views + 1
            update_entity_fields(question, total_views=new_total_views)
            question.save()
        return UpdateQuestionViews(questions=questions)


class Query(graphene.ObjectType):
    """
        Query to return the questions
    """
    questions = graphene.Field(
        PaginatedQuestions,
        page=graphene.Int(),
        per_page=graphene.Int(),
        description="Returns a list of paginated questions. Accepts arguments \
            \n- page: which is a particular page which is returned \
                \n- per_page: the number of questions displayed \
                within a particular page"
    )
    question = graphene.Field(
        lambda: Question,
        id=graphene.Int(),
        description="Returns a specific question\
            \n- id: Unique identifier of a question")
    all_questions = graphene.List(
        Question,
        start_date=graphene.String(),
        end_date=graphene.String(),
        description="Returns a list of all questions")

    def resolve_all_questions(self, info, start_date=None, end_date=None):
        # get all questions
        query = Question.get_query(info)
        questions = query.filter(QuestionModel.state == "active").all()
        questions_by_range = filter_questions_by_date_range(
            questions,
            start_date, end_date
        )
        return questions_by_range

    def resolve_questions(self, info, **kwargs):
        response = PaginatedQuestions(**kwargs)
        return response

    def resolve_question(self, info, id):
        # Query to get a question
        query = Question.get_query(info)
        active_questions = query.filter(QuestionModel.state == "active")
        response = active_questions.filter(QuestionModel.id == id).first()
        if not response:
            return_error.report_errors_bugsnag_and_graphQL(
                'Question does not exist')
        return response


class Mutation(graphene.ObjectType):
    create_question = CreateQuestion.Field(
        description="Creates a new question with the arguments below[required]\
            \n- question_title: The title field of the question[required]\
            \n- question_type: The field containing the type of question\
            [required]\n- question: The question body field[required]\
            \n- start_date:Start date when the question is created[required]\
            \n- end_date: The final date set for the question[required]")
    delete_question = DeleteQuestion.Field(
        description="Mutation to delete a specific question and takes arguments[required]\
            \n- question_id: Unique identifier of the question\
            \n- state: Check if the question is active, archived or deleted")
    update_question = UpdateQuestion.Field(
        description="Updates a question and takes the arguments below\
            \n- question_id: Unique identifier of the question[required]\
            \n- question_title: The title field of the question\
            \n- question_type: The field containing the type of question\
            \n- question: The question body field\
            \n- start_date:The start date when the question is created\
            \n- end_date: The final date set for the question\
            \n- is_active: The boolean body field checking if the\
                 question is active")
    update_question_views = UpdateQuestionViews.Field(
        description="Mutation to update the number of users that have viewed the questions\
            \n- increment_total_views: Boolean field for total views \
            incrementation")
