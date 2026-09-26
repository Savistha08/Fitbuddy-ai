from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db():
    from .models import User
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user(db, user_id):
    from .models import User
    return db.query(User).filter(User.user_id == user_id).first()


def get_all_users(db):
    from .models import User
    return db.query(User).order_by(User.created_at.desc()).all()


def save_user(
    db,
    user_id,
    name,
    age,
    weight_kg,
    goal,
    intensity,
):
    from .models import User

    user = User(
        user_id=user_id,
        name=name,
        age=age,
        weight_kg=weight_kg,
        goal=goal,
        intensity=intensity,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def save_plan(
    db,
    user,
    original_plan,
    nutrition_tip
):
    user.original_plan = original_plan
    user.updated_plan = original_plan
    user.nutrition_tip = nutrition_tip

    db.commit()
    db.refresh(user)

    return user


def update_plan(db, user, updated_plan, feedback, nutrition_tip=None):
    user.updated_plan = updated_plan
    user.latest_feedback = feedback

    if nutrition_tip is not None:
        user.nutrition_tip = nutrition_tip

    db.commit()
    db.refresh(user)

    return user
