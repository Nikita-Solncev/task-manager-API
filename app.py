from flask import Flask, request, jsonify, session

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_migrate import Migrate

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import JWTManager

import datetime
from dotenv import dotenv_values

from validators.validators import jwt_token_required


config = dotenv_values(".env")
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config["SQLALCHEMY_DATABASE_URI"]
app.secret_key = config["SECRET_KEY"]
app.config["JWT_SECRET_KEY"] = config["JWT_SECRET_KEY"]

jwt = JWTManager(app)


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
    """
    Creates new user in the system
    Request: {
        "username": username
        "password": password    #the password is stored encrypted
    }
    """
    req = request.get_json()

    select_query = db.select(User.name)
    result = db.session.execute(select_query)
    users = result.scalars().all()

    username = req.get("username")
    password = req.get("password")

    if username in users:
        return jsonify({"message": "This username is already used"}), 401
    
    access_token = create_access_token(identity=username)
    user = User(
        name=username,
        password=password,
        token=access_token
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "username": username,
        "password": password,
        "token": access_token,
        "message": "User registered"
        }), 200


@app.route("/projects", methods=["POST"])
@jwt_token_required
def create_project():
    """
    Creating new project
    Request: {
        "token": token,
        "project_name": project_name
    }
    """
    req = request.get_json()
    name = req.get("project_name")
    token = req.get("token")
    
    user = User.query.filter_by(token=token).first()
      
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
    #TODO Make another connecting system, like invites 
    ...
    # if 'logged_in' in session and session['logged_in']:
    #     req = request.get_json()
        
    #     username = session["username"]
    #     password = session["password"]
        
    #     #СОМНИТЕЛЬНО‼
    #     user = User.query.filter_by(name=username, password=password).first()
        
    #     project_name = req.get("project_name")
    #     project = Project.query.filter_by(name = project_name).first()
        
        
    #     if project:
    #         is_already_in_this_project = ProjectRole.query.filter_by(userId = user.id, projectId = project.id).first()
    #         if not is_already_in_this_project:
    #             con = ProjectRole(userId = user.id, projectId = project.id, role="participant")

    #             db.session.add(con)
    #             db.session.commit()
                
    #             return jsonify({"message": f"Connected to project {project.name}"}), 200
            
    #         else:
    #             return jsonify({"message": "You are already connected to this project"})
        
    #     else:
    #         return jsonify({"message": "project does not exist"}), 401

    # else:
    #     return jsonify({"message": "You must log in"}), 401
    
    
@app.route("/projects/<int:project_id>/tasks", methods=["POST"])
@jwt_token_required
def create_task(project_id):
    """
    Creates new task in project
    Request: {
        "token": token
        "task_name": task name
        "task_description": task description
    }
    """  
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        project = ProjectRole.query.filter_by(userId=user.id, projectId = project_id).first() 
        name = req.get("task_name")
        description = req.get("description")
        
        task = Task(name = name, description = description, creation_date = datetime.date.today() ,statusId = 1, projectId = project_id)

        db.session.add(task)
        db.session.commit()
        
        return jsonify({"message": "task succesfully created",
                        "task": {"id": task.id, "name": task.name, "description": task.description, "creation date": task.creation_date, "status id": task.statusId, "project id": task.projectId}}), 200
    else:
        return jsonify({"message": "Invalid token"}), 401

#GET REQUESTS
@app.route("/projects", methods=["GET"])
@jwt_token_required
def all_projects():
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        projects = ProjectRole.query.filter_by(userId = user.id)
        projects_dict = {}
        for project in projects:
            del project.__dict__['_sa_instance_state']
            del project.__dict__["projectId"]
            projects_dict[project.id] = project.__dict__

        return jsonify(projects_dict), 200
    else:
        return jsonify({"message": "Invalid token"}), 401


@app.route("/projects/<int:project_id>")
@jwt_token_required
def project_by_id(project_id):
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        project = ProjectRole.query.filter_by(userId = user.id, projectId = project_id).first()
        all_project_members = ProjectRole.query.filter_by(projectId = project_id).all()  
        del project.__dict__['_sa_instance_state']
        del project.__dict__["id"]
        project.__dict__["members_id"] = [all_project_members[i].userId for i in range(len(all_project_members))]
    
        return project.__dict__, 200
    else:
        return jsonify({"message": "Invalid token"}), 401


@app.route("/projects/<int:project_id>/tasks", methods=["GET"])
@jwt_token_required
def all_tasks_in_project(project_id):
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        if ProjectRole.query.filter_by(userId=user.id, projectId = project_id).first():
            tasks = Task.query.filter_by(projectId = project_id).all()  
            tasks_dict = {}
            for task in tasks:
                del task.__dict__['_sa_instance_state']
                tasks_dict[task.id] = task.__dict__
                
            return jsonify(tasks_dict), 200
        else: 
            return jsonify({"message": "Such project does not exist"}), 400

    
    else:   
        return jsonify({"message": "Invalid token"}), 401


@app.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["GET"])
@jwt_token_required
def task_by_id(project_id, task_id):
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        if ProjectRole.query.filter_by(userId=user.id, projectId = project_id).first():
            task = Task.query.filter_by(projectId = project_id, id = task_id).first()
            if task:
                del task.__dict__['_sa_instance_state']
                
                return task.__dict__
            else: 
                return jsonify({"message": "Such task does not exist"}), 400
        else: 
            return jsonify({"message": "Such project does not exist"}), 400
        
    else:   
        return jsonify({"message": "Invalid token"}), 401


#PUT REQUESTS
@app.route("/projects/<int:project_id>", methods=["PUT"])
@jwt_token_required
def update_project_data(project_id):
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        user_role = ProjectRole.query.filter_by(userId = user.id, projectId = project_id).first()
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
            return jsonify({"message": "You don't participate in this project or you are not Owner of this project"}), 403
    else:   
        return jsonify({"message": "Invalid token"}, 401)
    
    
@app.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["PUT"])
@jwt_token_required
def update_task_data(project_id, task_id):
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        user_role = ProjectRole.query.filter_by(userId = user.id, projectId = project_id).first()
        if user_role:
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
        else:
            return jsonify({"message": "Project does not exist or you do not participate in this project"}), 400
    else:   
        return jsonify({"message": "Invalid token"}, 401)

#DELETE REQUESTS
@app.route("/projects/<int:project_id>", methods=["DELETE"])
@jwt_token_required
def leave_project(project_id): 
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        user_role = ProjectRole.query.filter_by(userId = user.id, projectId = project_id).first()
        if user_role and user_role.role == "owner":
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
            return jsonify({"message": "You don't participate in this project or you are not Owner of this project"}), 403
    else:   
        return jsonify({"message": "Invalid token"}, 401)
    

@app.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["DELETE"])
@jwt_token_required
def delete_task(project_id, task_id):
    req = request.get_json()
    user = User.query.filter_by(token=req.get("token")).first()
    if user: #if token is valid
        user_role = ProjectRole.query.filter_by(userId = session["user_id"], projectId = project_id).first()
        if user_role:
            task = Task.query.filter_by(id = task_id, projectId = project_id).first()
            if task:
                db.session.delete(task)
                db.session.commit()
                return jsonify({"message": "Task has been deleted"}), 200
            else:
                return jsonify({"message": "Task doesn't exist"}), 401
        else:
            return jsonify({"message": "Project does not exist or you do not participate in this project"}), 400
    else:   
        return jsonify({"message": "Invalid token"}, 401)
        

if __name__ == "__main__":
    app.run(debug=True, port=5000)