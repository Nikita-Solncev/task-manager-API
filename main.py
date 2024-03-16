from flask import Flask, request, jsonify, session

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_migrate import Migrate

import json
import datetime
from dotenv import dotenv_values


config = dotenv_values(".env")
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config["SQLALCHEMY_DATABASE_URI"]
app.secret_key = config["SECRET_KEY"]


#database ↓↓↓

class Base(DeclarativeBase):
    ...
    
db = SQLAlchemy(model_class=Base)
migrate = Migrate(app, db)
db.init_app(app)


class Project(db.Model):
    __tablename__ = "project"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    
    roles = relationship("ProjectRole", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    
    
class ProjectRole(db.Model):
    __tablename__ = "projectRole"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"))
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    
    project = relationship("Project", back_populates="roles")
    user = relationship("User", back_populates="roles")
    

class User(db.Model):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(75), nullable=False)
    
    roles = relationship("ProjectRole", back_populates="user")
    


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


#api ↓↓↓

#POST REQUESTS
@app.route("/register", methods=["POST"])
def register():
    req = request.get_json()

    select_query = db.select(User.name)
    result = db.session.execute(select_query)
    users = result.scalars().all()

    username = req.get("username")
    password = req.get("password")
    email = req.get("email")

    if username in users:
        return "User already exists"

    user = User(
        name=username,
        password=password,
        email=email
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered"}), 200


@app.route("/login", methods=["POST"])
def login():
    req = request.get_json()
    username = req.get("username")
    password = req.get("password")
    

    user = User.query.filter_by(name=username, password=password).first()

    if user:
        session['logged_in'] = True
        session['username'] = user.name
        session['password'] = user.password
        session['user_id'] = user.id
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401
    

@app.route("/create_project", methods=["POST"])
def create_project():
    req = request.get_json()
    name = req.get("project_name")
    
    username = session["username"]
    password = session["password"]
    user = User.query.filter_by(name=username, password=password).first()
    
    select_query = db.select(Project.name)
    result = db.session.execute(select_query)
    projects = result.scalars().all()
    if name in projects:
        return "project already exists"
    
    project = Project(name = name)
    db.session.add(project)
    db.session.flush()

    projectRole = ProjectRole(userId = user.id, projectId = project.id, role = "owner" )
    
    db.session.add(projectRole)
    db.session.commit()

    return jsonify({"message": "Project created"}), 200


@app.route("/connect_to_project", methods=["POST"])
def connect_to_project():
    if 'logged_in' in session and session['logged_in']:
        req = request.get_json()
        
        username = session["username"]
        password = session["password"]
        
        #СОМНИТЕЛЬНО‼
        user = User.query.filter_by(name=username, password=password).first()
        
        project_name = req.get("project_name")
        project = Project.query.filter_by(name = project_name).first()
        
        
        if project:
            is_already_in_this_project = ProjectRole.query.filter_by(userId = user.id, projectId = project.id).first()
            if not is_already_in_this_project:
                
                session["is_connected_to_project"] = True
                session["project_id"] = project.id
                
                
                con = ProjectRole(userId = user.id, projectId = project.id, role="participant")

                db.session.add(con)
                db.session.commit()
                

                return jsonify({"message": "Connected to project"}), 200
            
            else:
                #TODO: ПОФИКСИТЬ 
                session["is_connected_to_project"] = True
                session["project_id"] = project.id
                return jsonify({"message": "You are already connected to this project"}), 200
        
        else:
            return jsonify({"message": "project does not exist"}), 401

    else:
        return jsonify({"message": "You must log in"}), 401
    
    
@app.route("/create_task", methods=["POST"])
def create_task():
    if "is_connected_to_project" in session and session["is_connected_to_project"]:
        req = request.get_json()
        
        name = req.get("name")
        description = req.get("description")
        status_id = req.get("status_id")
        project_id = session["project_id"]
        
        task = Task(name = name, description = description, creation_date = datetime.date.today() ,statusId = status_id, projectId = project_id)

        db.session.add(task)
        db.session.commit()
        
        return jsonify({"message": "task succesfully created"})
    else:
        print(session)
        return jsonify({"message": "You must be connected to project"}), 401


#GET REQUESTS
@app.route("/project", methods=["GET"])
def all_projects():
    projects = ProjectRole.query.filter_by(userId = session["user_id"])
    projects_dict = {}
    for project in projects:
        del project.__dict__['_sa_instance_state']
        projects_dict[project.id] = project.__dict__
    
    return jsonify(projects_dict)


@app.route("/project/<int:project_id>")
def project_by_id(project_id):
    project = ProjectRole.query.filter_by(userId = session["user_id"], projectId = project_id).first()
    del project.__dict__['_sa_instance_state']
    
    return project.__dict__


@app.route("/task", methods=["GET"])
def all_tasks():
    tasks = Task.query.filter_by(projectId = session["project_id"]).all()  
    tasks_dict = {}
    for task in tasks:
        del task.__dict__['_sa_instance_state']
        tasks_dict[task.id] = task.__dict__
        
    return jsonify(tasks_dict)


@app.route("/task/<int:task_id>")
def task_by_id(task_id):
    task = Task.query.filter_by(projectId = session["project_id"], id = task_id).first()
    del task.__dict__['_sa_instance_state']
    
    return task.__dict__

       
#DELETE REQUESTS
@app.route("/leave_project", methods=["DELETE", "POST"])
def leave_project():
    if 'logged_in' in session and session['logged_in']:  
        req = request.get_json()
        
        username = session["username"]
        password = session["password"]
        
        
        user = User.query.filter_by(name=username, password=password).first()
        
        project_name = req.get("project_name")
        project = Project.query.filter_by(name = project_name).first()
        
        is_already_in_this_project = ProjectRole.query.filter_by(userId = user.id, projectId = project.id).first()
        if is_already_in_this_project:
            projectRole = ProjectRole.query.filter_by(projectId=project.id, userId=user.id).first()
            db.session.delete(projectRole)
            db.session.commit()
            return jsonify({"message": "You left the project"}), 200
        else:
            return jsonify({"message": "You cannot leave a project that you are not a member of"}), 401
    
    else:
        return jsonify({"message": "You must log in"}), 401


@app.route("/delete_task", methods=["DELETE", "POST"])
def delete_task():
    req = request.get_json()
    task_id = req.get("task_id")
    
    task = Task.query.filter_by(id = task_id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task has been deleted"}), 200
    else:
        return jsonify({"message": "Task doesn't exist"}), 401
    
    

if __name__ == "__main__":
    app.run(debug=True, port=5000)
