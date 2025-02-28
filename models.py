from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_migrate import Migrate

import datetime


class Base(DeclarativeBase):
    ...
    
db = SQLAlchemy(model_class=Base)


class Project(db.Model):
    __tablename__ = "project"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    
    tasks = relationship("Task", back_populates="project")
    
    
class ProjectRole(db.Model):
    __tablename__ = "projectRole"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"))
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    
    project_id = relationship("Project", foreign_keys=[projectId])
    user = relationship("User", back_populates="roles")
    

class User(db.Model):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(75), nullable=False)
    token: Mapped[str] = mapped_column(String(500), nullable=False)
    
    roles = relationship("ProjectRole", back_populates="user")
    invitations = relationship("Invitation", back_populates="inviter")
    

class StatusList(db.Model):
    __tablename__ = "status_list"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    statusName: Mapped[str] = mapped_column(String(75), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    
    tasks = relationship("Task", back_populates="status")
    
    
class Task(db.Model):
    __tablename__ = "task"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    creation_date: Mapped[datetime] = mapped_column(DateTime)
    statusId: Mapped[int] = mapped_column(Integer, ForeignKey("status_list.id"))
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"))

    status = relationship("StatusList", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    
    
class Invitation(db.Model):
    __tablename__ = "invitation"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    inviter_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    
    inviter = relationship('User', back_populates="invitations")