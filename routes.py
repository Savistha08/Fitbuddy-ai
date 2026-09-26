import json
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from .ai.gemini_flash_generator import (
    generate_nutrition_tip_with_flash,
)

from .ai.gemini_generator import (
    generate_workout_gemini,
)

from .ai.updated_plan import (
    update_workout_plan,
)

from .config import settings

from .database import (
    get_all_users,
    get_db,
    get_user,
    save_plan,
    save_user,
    update_plan,
)

from .schemas import (
    FeedbackRequest,
    PlanResponse,
    UserInput,
    WorkoutPlan,
)


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


def _plan_text(plan) -> str:

    return json.dumps(
        plan.model_dump(),
        indent=2,
        ensure_ascii=False
    )


def _require_admin(
    request: Request
) -> bool:

    return (
        request.session.get(
            "admin_authenticated"
        )
        is True
    )


@router.get(
    "/",
    response_class=HTMLResponse
)
def home(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",

        context={
            "title": settings.app_name
        },
    )


@router.post(
    "/generate-workout",
    response_class=HTMLResponse
)
async def generate_workout_form(

    request: Request,

    name: Annotated[
        str,
        Form()
    ],

    user_id: Annotated[
        str,
        Form()
    ],

    age: Annotated[
        int,
        Form()
    ],

    weight_kg: Annotated[
        float,
        Form()
    ],

    goal: Annotated[
        str,
        Form()
    ],

    intensity: Annotated[
        str,
        Form()
    ],

    db: Session = Depends(get_db),
):

    try:

        user_input = UserInput(
            name=name,
            user_id=user_id,
            age=age,
            weight_kg=weight_kg,
            goal=goal,
            intensity=intensity,
        )

    except Exception as exc:

        return templates.TemplateResponse(

            request=request,

            name="index.html",

            context={
                "title": settings.app_name,
                "error": str(exc),
            },

            status_code=422,
        )

    plan, demo_plan = await generate_workout_gemini(
        user_input
    )

    tip, demo_tip = await generate_nutrition_tip_with_flash(
        user_input
    )


    user = save_user(

        db,

        user_id=user_input.user_id,
        name=user_input.name,
        age=user_input.age,
        weight_kg=user_input.weight_kg,
        goal=user_input.goal,
        intensity=user_input.intensity,
    )

    save_plan(

        db,
        user,

        original_plan=_plan_text(plan),

        nutrition_tip=json.dumps(
            tip.model_dump(),
            ensure_ascii=False
        ),
    )

    return templates.TemplateResponse(

        request=request,

        name="result.html",

        context={

            "title": settings.app_name,

            "user": user,

            "plan": plan,

            "nutrition_tip": tip,

            "demo_mode": (
                demo_plan or demo_tip
            ),

            "message": None,
        },
    )


@router.post(
    "/submit-feedback",
    response_class=HTMLResponse
)
async def submit_feedback_form(

    request: Request,

    user_id: Annotated[
        str,
        Form()
    ],

    feedback: Annotated[
        str,
        Form()
    ],

    db: Session = Depends(get_db),
):

    try:

        request_data = FeedbackRequest(
            user_id=user_id,
            feedback=feedback
        )

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    db_user = get_user(
        db,
        request_data.user_id
    )

    if db_user is None:

        raise HTTPException(
            status_code=404,
            detail="User ID not found."
        )

    user_input = UserInput(

        name=db_user.name,

        user_id=db_user.user_id,

        age=db_user.age,

        weight_kg=db_user.weight_kg,

        goal=db_user.goal,

        intensity=db_user.intensity,
    )

    current_plan = WorkoutPlan.model_validate_json(
        db_user.updated_plan or db_user.original_plan
    )

    updated_plan, demo_plan = await update_workout_plan(
        user_input,
        current_plan,
        request_data.feedback,
    )

    tip, demo_tip = await generate_nutrition_tip_with_flash(
        user_input
    )

    update_plan(

        db,
        db_user,

        updated_plan=_plan_text(
            updated_plan
        ),

        feedback=request_data.feedback,

        nutrition_tip=json.dumps(
            tip.model_dump(),
            ensure_ascii=False
        ),
    )

    return templates.TemplateResponse(

        request=request,

        name="result.html",

        context={

            "title": settings.app_name,

            "user": db_user,

            "plan": updated_plan,

            "nutrition_tip": tip,

            "demo_mode": (
                demo_plan or demo_tip
            ),

            "message": (
                "Your plan was updated "
                "using your feedback."
            ),
        },
    )


@router.get(
    "/view-all-users",
    response_class=HTMLResponse
)
def view_all_users(

    request: Request,

    db: Session = Depends(get_db)
):

    if not _require_admin(request):

        return RedirectResponse(
            "/admin/login",
            status_code=status.HTTP_303_SEE_OTHER
        )

    users = get_all_users(db)

    return templates.TemplateResponse(

        request=request,

        name="all_users.html",

        context={
            "title": "Admin Dashboard",
            "users": users
        },
    )


@router.get(
    "/admin/login",
    response_class=HTMLResponse
)
def admin_login_page(
    request: Request
):

    return templates.TemplateResponse(

        request=request,

        name="admin_login.html",

        context={
            "title": "Admin Login",
            "error": None
        },
    )


@router.post(
    "/admin/login",
    response_class=HTMLResponse
)
def admin_login(

    request: Request,

    token: Annotated[
        str,
        Form()
    ],
):

    if token != settings.admin_token:

        return templates.TemplateResponse(

            request=request,

            name="admin_login.html",

            context={
                "title": "Admin Login",
                "error": "Invalid admin token."
            },

            status_code=401,
        )

    request.session[
        "admin_authenticated"
    ] = True

    return RedirectResponse(
        "/view-all-users",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/admin/logout")
def admin_logout(
    request: Request
):

    request.session.clear()

    return RedirectResponse(
        "/admin/login",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post(
    "/api/generate-workout",
    response_model=PlanResponse
)
async def api_generate_workout(

    user_input: UserInput,

    db: Session = Depends(get_db),
):

    plan, demo_plan = (
        await generate_workout_gemini(
            user_input
        )
    )

    tip, demo_tip = (
        await generate_nutrition_tip_with_flash(
            user_input
        )
    )

    user = save_user(

        db,

        user_id=user_input.user_id,
        name=user_input.name,
        age=user_input.age,
        weight_kg=user_input.weight_kg,
        goal=user_input.goal,
        intensity=user_input.intensity,
    )

    save_plan(

        db,
        user,

        original_plan=_plan_text(plan),

        nutrition_tip=json.dumps(
            tip.model_dump(),
            ensure_ascii=False
        ),
    )

    return PlanResponse(

        user_id=user.user_id,

        name=user.name,

        goal=user.goal,

        intensity=user.intensity,

        workout_plan=plan,

        nutrition_tip=tip,

        demo_mode=(
            demo_plan or demo_tip
        ),
    )


@router.post(
    "/api/submit-feedback",
    response_model=PlanResponse
)
async def api_submit_feedback(

    request_data: FeedbackRequest,

    db: Session = Depends(get_db),
):

    db_user = get_user(
        db,
        request_data.user_id
    )

    if db_user is None:

        raise HTTPException(
            status_code=404,
            detail="User ID not found."
        )

    user_input = UserInput(

        name=db_user.name,

        user_id=db_user.user_id,

        age=db_user.age,

        weight_kg=db_user.weight_kg,

        goal=db_user.goal,

        intensity=db_user.intensity,
    )

    current_plan = WorkoutPlan.model_validate_json(
        db_user.updated_plan or db_user.original_plan
    )

    updated_plan, demo_plan = (
        await update_workout_plan(

            user_input,

            current_plan,

            request_data.feedback,
        )
    )

    tip, demo_tip = (
        await generate_nutrition_tip_with_flash(
            user_input
        )
    )

    update_plan(

        db,
        db_user,

        updated_plan=_plan_text(
            updated_plan
        ),

        feedback=request_data.feedback,

        nutrition_tip=json.dumps(
            tip.model_dump(),
            ensure_ascii=False
        ),
    )

    return PlanResponse(

        user_id=db_user.user_id,

        name=db_user.name,

        goal=db_user.goal,

        intensity=db_user.intensity,

        workout_plan=updated_plan,

        nutrition_tip=tip,

        demo_mode=(
            demo_plan or demo_tip
        ),
    )


@router.get("/api/users")
def api_users(

    request: Request,

    db: Session = Depends(get_db)
):

    expected = settings.admin_token

    supplied = request.headers.get(
        "X-Admin-Token"
    )

    if (
        not expected
        or supplied != expected
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid admin token."
        )

    return [

        {
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "weight_kg": user.weight_kg,
            "goal": user.goal,
            "intensity": user.intensity,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "has_updated_plan": bool(
                user.updated_plan
            ),
        }

        for user
        in get_all_users(db)
    ]