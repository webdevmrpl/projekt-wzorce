import traceback
from fastapi import FastAPI, Request, Response
from app.routers.task import router as task_router
from app.routers.users import router as user_router
from app.settings import security

app = FastAPI()
app.include_router(task_router)
app.include_router(user_router)
security.handle_errors(app)


# @app.exception_handler(Exception)
# async def custom_exception_handler(request: Request, exc: Exception):
#     return Response(
#         status_code=500,
#         content={
#             "message": "An error occurred.",
#             "details": repr(exc),
#             "trace": traceback.format_exc(),
#         },
#     )
