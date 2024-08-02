import os
import requests
from flask import Flask, redirect, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = 'http://localhost:5000/callback'

auth_url = 'https://stepik.org/oauth2/authorize/'
token_url = 'https://stepik.org/oauth2/token/'


# def get_course_units(headers, course_id):
#     units_url = f'https://stepik.org/api/units?course={course_id}'
#     response = requests.get(units_url, headers=headers)
#
#     if response.status_code != 200:
#         raise Exception(f"Ошибка при запросе модулей курса: {response.status_code}, {response.text}")
#
#     return response.json().get('units')


def get_user_info(headers):
    user_info_url = 'https://stepik.org/api/stepics/1'
    response = requests.get(user_info_url, headers=headers)

    if response.status_code != 200:
        return f"Ошибка при запросе информации о пользователе: {response.status_code}, {response.text}"

    return response.json().get('users')[0]


def get_user_created_courses(headers, user_id):
    courses_url = f'https://stepik.org/api/courses?teacher={user_id}'
    response = requests.get(courses_url, headers=headers)

    if response.status_code != 200:
        return f"Ошибка при запросе курсов: {response.status_code}, {response.text}"

    return response.json().get('courses')


def get_course_info(headers, course_id):
    course_url = f'https://stepik.org/api/courses/{course_id}'
    response = requests.get(course_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Ошибка при запросе информации о курсе: {response.status_code}, {response.text}")

    return response.json().get('courses')[0]


def get_module_info(headers, module_id):
    section_url = f'https://stepik.org/api/sections/{module_id}'
    response = requests.get(section_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Ошибка при запросе информации о модуле: {response.status_code}, {response.text}")

    return response.json().get('sections')[0]


def get_unit_info(headers, unit_id):
    unit_url = f'https://stepik.org/api/units/{unit_id}'
    response = requests.get(unit_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Ошибка при запросе блока: {response.status_code}, {response.text}")

    return response.json().get('units')[0]


def get_lesson_info(headers, lesson_id):
    lesson_url = f'https://stepik.org/api/lessons/{lesson_id}'
    response = requests.get(lesson_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Ошибка при запросе урока: {response.status_code}, {response.text}")

    return response.json().get('lessons')[0]


def get_step_info(headers, step_id):
    step_url = f'https://stepik.org/api/steps/{step_id}'
    response = requests.get(step_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Ошибка при запросе шага: {response.status_code}, {response.text}")

    return response.json().get('steps')[0]


def get_step_sources(headers, step_id):
    step_sources_url = f'https://stepik.org/api/step-sources/{step_id}'
    response = requests.get(step_sources_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Ошибка при запросе ресурсов шага: {response.status_code}, {response.text}")

    return response.json().get('step-sources')[0]


def print_step_sources(sources):
    step_type = sources['block']['name']
    text = ''
    if step_type == 'text':
        text += f"{tab}{tab}{tab}{sources['block']['text']}:{line_feed}\n"
    elif step_type == 'choice':
        text += f"{tab}{tab}{tab}Вопрос:{sources['block']['text']}:{line_feed}\n"
        text += f"{tab}{tab}{tab}Варианты ответа:{line_feed}\n"
        options = sources['block']['source']['options']
        for i, option in enumerate(options):
            text += f"{i + 1}. {option['text']} : {option['is_correct']}{line_feed}"
    return text


line_feed = '<br>'
tab = '&emsp;'


def print_course_structure(headers, course_id):
    course = get_course_info(headers, course_id)
    course_structure = f"Курс: {course['title']} {line_feed} Описание: {course['description']} {line_feed}"

    course_structure += f"Модули: {line_feed}"
    modules = course['sections']
    for module_id in modules:
        module = get_module_info(headers, module_id)
        course_structure += f"{tab}{module['title']}:{line_feed}"

        units = module['units']
        for unit_id in units:
            unit = get_unit_info(headers, unit_id)
            lesson_id = unit['lesson']
            lesson = get_lesson_info(headers, lesson_id)
            course_structure += f"{tab}{tab}{lesson['title']}:{line_feed}\n"

            for step_id in lesson['steps']:
                step_sources = get_step_sources(headers, step_id)
                course_structure += print_step_sources(step_sources)

    return course_structure


def get_auth_code():
    code = request.args.get('code')
    if not code:
        raise Exception("Ошибка: Не удалось получить код авторизации.")

    return code


def get_auth_token(data):
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise Exception(f"Ошибка при запросе токена: {response.status_code}, {response.text}")

    token = response.json().get('access_token')
    if not token:
        raise Exception("Ошибка: Не удалось получить токен.")

    return token


@app.route('/')
def index():
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'read'
    }
    auth_redirect_url = f"{auth_url}?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=read"
    return redirect(auth_redirect_url)


@app.route('/callback')
def callback():

    code = get_auth_code()
    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri
    }
    token = get_auth_token(data)

    course_id = 210328
    headers = {
        'Authorization': f'Bearer {token}'
    }

    course_structure = print_course_structure(headers, course_id)

    return course_structure


if __name__ == '__main__':
    app.run(debug=True)
