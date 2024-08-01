# import json
# import os

# import src._iam.adapters.user_repository as user_repo
# import src._iam.domain.entities as entities
# import src._iam.domain.value_objects as value_objects
# import src._receipt_tracking.adapters.name_search as name_search
# import src._receipt_tracking.adapters.product_encode_json as product_encode_json  # noqa
# import src._receipt_tracking.adapters.repositories.products_repository as product_repo
# import src._receipt_tracking.domain.value_objects as r_t_value_objects
# from sqlalchemy import select, text
# from sqlalchemy.orm import Session
# from src.config.app_config import app_settings
# from src.db.base import Database

# # TACO_PATH = f"/home/jap/projects/vlep-io/app/backend/app/src/db/TACO.json"  # noqa
# # PRIVATE_PATH = f"/home/jap/projects/vlep-io/app/backend/app/src/db/PRIVATE.json"  # noqa
# TACO_PATH = f"/home/{os.getenv('USER_NAME') or 'vlep'}/backend/{os.getenv('MODULE_NAME') or 'app'}/src/INIT_TACO.json"  # noqa
# PRIVATE_PATH = f"/home/{os.getenv('USER_NAME') or 'vlep'}/backend/{os.getenv('MODULE_NAME') or 'app'}/src/INIT_PRIVATE.json"  # noqa


# def init_db(session: Session) -> None:
#     session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
#     session.execute(text("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch"))

#     user = user_repo.UserSqlModel.metadata.tables["iam.users"]
#     stmt = select(user).filter_by(email=app_settings.first_admin_email)
#     user = session.execute(stmt).first()
#     if not user:
#         hashed_pass = entities.User.get_password_hash(
#             app_settings.first_admin_password.get_secret_value()
#         )
#         user = entities.User.create_user(
#             email=app_settings.first_admin_email,
#             hashed_password=hashed_pass,
#             role=value_objects.Role(value_objects.RoleName.Administrator),
#             full_name=value_objects.FullName(
#                 first_name="Joaquim", last_name="Alves Pinto"
#             ),
#         )
#         user.confirm_user()
#         users_repo = user_repo.UserRepo(session=session)
#         users_repo.add(aggregate_root=user)

#     products = list(session.execute(text("SELECT * FROM receipt_tracking.products")))
#     if not products:
#         with open(TACO_PATH) as f:
#             raw = f.read()
#             taco_list_of_dict = json.loads(raw)

#         for item in taco_list_of_dict:
#             item["description"] = name_search.preprocess_str(item["description"])
#         else:
#             taco = product_encode_json.ArgEncodeTACO(taco_list_of_dict)

#         taco_args = taco.kwargs

#         with open(PRIVATE_PATH) as f:
#             raw = f.read()
#             ind_dict = json.loads(raw)

#         ind = product_encode_json.ArgEncodePrivate(ind_dict)
#         ind_args = ind.kwargs

#         all_args = taco_args + ind_args
#         products_repo = product_repo.ProductRepo(session=session)

#         for item in all_args:
#             product = r_t_value_objects.Product.add_product(**item)
#             products_repo.add(product)

#     session.commit()


# if __name__ == "__main__":
#     db = Database(app_settings.sqlalchemy_db_uri)
#     session = db.session_factory()
#     init_db(session=session)
