from flask import Flask, request, jsonify, session

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_migrate import Migrate

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
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    
    tasks = relationship("Task", back_populates="project")
    
    
class ProjectRole(db.Model):
    __tablename__ = "projectRole"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"))
    # projectName: Mapped[str] = mapped_column(String(150), ForeignKey("project.name"), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    
    project_id = relationship("Project", foreign_keys=[projectId])
    # project_name = relationship("Project", foreign_keys=[projectName])
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
        return jsonify({"message": "This username is already used"}), 401

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
        return jsonify({"message": "Logged in successfuly"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401
    

@app.route("/projects", methods=["POST"])
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
        return jsonify({"message": "project already exists"})
    
    project = Project(name = name)
    db.session.add(project)
    db.session.flush()

    projectRole = ProjectRole(userId = user.id, projectId = project.id, role = "owner" )
    
    db.session.add(projectRole)
    db.session.commit()
    
    return jsonify({"message": "Project created",
                    "project": {"name": project.name, "id": project.id}}), 200


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
                con = ProjectRole(userId = user.id, projectId = project.id, role="participant")

                db.session.add(con)
                db.session.commit()
                
                return jsonify({"message": f"Connected to project {project.name}"}), 200
            
            else:
                return jsonify({"message": "You are already connected to this project"})
        
        else:
            return jsonify({"message": "project does not exist"}), 401

    else:
        return jsonify({"message": "You must log in"}), 401
    
    
@app.route("/projects/<int:project_id>/tasks", methods=["POST"])
def create_task(project_id):
        project = ProjectRole.query.filter_by(userId = session["user_id"], projectId = project_id).first()
        print(project)
        
        req = request.get_json()
        
        name = req.get("task_name")
        description = req.get("description")
        
        task = Task(name = name, description = description, creation_date = datetime.date.today() ,statusId = 1, projectId = project_id)

        db.session.add(task)
        db.session.commit()
        
        return jsonify({"message": "task succesfully created",
                        "task": {"id": task.id, "name": task.name, "description": task.description, "creation date": task.creation_date, "status id": task.statusId, "project id": task.projectId}}), 200


#GET REQUESTS
@app.route("/projects", methods=["GET"])
def all_projects():
    projects = ProjectRole.query.filter_by(userId = session["user_id"])
    projects_dict = {}
    for project in projects:
        del project.__dict__['_sa_instance_state']
        del project.__dict__["projectId"]
        projects_dict[project.id] = project.__dict__
    
    return jsonify(projects_dict)


@app.route("/projects/<int:project_id>")
def project_by_id(project_id):
    project = ProjectRole.query.filter_by(userId = session["user_id"], id = project_id).first()
    del project.__dict__['_sa_instance_state']
    del project.__dict__["projectId"]
    
    return project.__dict__


@app.route("/projects/<int:project_id>/tasks", methods=["GET"])
def all_tasks_in_project(project_id):
    tasks = Task.query.filter_by(projectId = project_id).all()  
    tasks_dict = {}
    for task in tasks:
        del task.__dict__['_sa_instance_state']
        tasks_dict[task.id] = task.__dict__
        
    return jsonify(tasks_dict)


@app.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["GET"])
def task_by_id(project_id, task_id):
    task = Task.query.filter_by(projectId = project_id, id = task_id).first()
    del task.__dict__['_sa_instance_state']
    
    return task.__dict__


#PUT REQUESTS
@app.route("/projects/<int:project_id>", methods=["PUT"])
def update_project_data(project_id):
    user_role = ProjectRole.query.filter_by(userId = session["user_id"], projectId = project_id).first()
    if user_role and user_role.role == "owner":
        if request.data:
            project = Project.query.filter_by(id = project_id).first()    
            if project:
                req = request.get_json()
                updated_name = req.get("name")
                old_name = project.name
                project.name = updated_name if updated_name else project.name
                db.session.add(project)
                db.session.commit()
                return jsonify({"message": f"Project name was succesfully updated from '{old_name}' to '{project.name}'"}), 200
                
            else:
                return jsonify({"message": "Project does not exist or you have no access to it"}), 400
                
        else:
            return jsonify({"message": "Your json request is empty"}), 415
    else:
        return jsonify({"message": "Only owner can change data about project"}), 403
    
    
@app.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["PUT"])
def update_task_data(project_id, task_id):
    if request.data:
        task = Task.query.filter_by(id = task_id, projectId = project_id).first()    
        if task:
            req = request.get_json()
            updated_name = req.get("name")
            updated_description = req.get("description")
            updated_status = req.get("status")
            
            task.name = updated_name if updated_name else task.name
            task.description = updated_description if updated_description else task.description
            task.statusId = updated_status if updated_status else task.statusId
            db.session.add(task)
            db.session.commit()
            return jsonify({"message": f"Task data was succesfully updated"}), 200
            
        else:
            return jsonify({"message": "Task does not exist or you have no access to it"}), 400
        
    else:
        return jsonify({"message": "Your json request is empty"}), 415 


#DELETE REQUESTS
@app.route("/projects/<int:project_id>", methods=["DELETE"])
def leave_project(project_id):
    if 'logged_in' in session and session['logged_in']:  
        req = request.get_json()
        
        username = session["username"]
        password = session["password"]
        
        user = User.query.filter_by(name=username, password=password).first()
        project = Project.query.filter_by(id = project_id).first()
        
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
    

@app.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(project_id, task_id):
    task = Task.query.filter_by(id = task_id, projectId = project_id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task has been deleted"}), 200
    else:
        return jsonify({"message": "Task doesn't exist"}), 401
    

if __name__ == "__main__":
    app.run(debug=True, port=5000)