import gitlab_private_token
import requests

GITLAB_PROJECTS_URL = "https://gitlab.textdata.org/api/v4/projects"
GITLAB_FILES_URL = "https://gitlab.textdata.org/api/v4/projects/{0}/repository/files/{1}"
GITLAB_COMMITS_URL = "https://gitlab.textdata.org/api/v4/projects/{0}/repository/commits"

def create_new_project(project_name):
    print("Creating GitLab project with name ", project_name)
    payload = { "private_token": gitlab_private_token.GITLAB_PRIVATE_TOKEN, "name": project_name }
    resp = requests.post(GITLAB_PROJECTS_URL, data=payload)

    if resp.status_code != 201:
        print('Error creating gitlab project. Error code: ', resp.status_code)
    
    return resp.status_code

def get_new_project_id(project_name):
    payload = { "private_token": gitlab_private_token.GITLAB_PRIVATE_TOKEN, "search": project_name, "order_by": "created_at" }
    resp = requests.get(GITLAB_PROJECTS_URL, data=payload)

    if resp.status_code != 200:
        print('Error getting gitlab project id. Error code: ', resp.status_code)
        return None

    # results are returned in order of most recently created, thus we always want the first project.
    # this is cautionary in case there are multiple projects with the same name.
    return resp.json()[0]["id"]

def commit_evaluation_files(project_id, commit_files, files_contents):
    for i in range(len(commit_files)):
        commit_response = commit_file(project_id, commit_files[i], files_contents[i])
        if commit_response != 201:
            return None

    return commit_response

def commit_file(project_id, file_name, file_contents, commit_message="Init project", branch="master"):
    payload = {
        "private_token": gitlab_private_token.GITLAB_PRIVATE_TOKEN,
        "branch": branch,
        "commit_message": commit_message,
        "content": file_contents
    }
    resp = requests.post(GITLAB_FILES_URL.format(project_id, file_name), data=payload)

    if resp.status_code != 201:
        print('Error commiting file: ', file_name)

    return resp.status_code
