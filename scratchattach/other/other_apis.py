"""Other Scratch API-related functions"""

import json

from ..utils import commons
from ..utils.exceptions import BadRequest, InvalidLanguage, InvalidTTSGender
from ..utils.requests import Requests as requests
from ..utils.enums import Languages, Language, TTSVoices, TTSVoice


# --- Front page ---

def get_news(*, limit=10, offset=0):
    return commons.api_iterative("https://api.scratch.mit.edu/news", limit=limit, offset=offset)


def featured_data():
    return requests.get("https://api.scratch.mit.edu/proxy/featured").json()


def featured_projects():
    return featured_data()["community_featured_projects"]


def featured_studios():
    return featured_data()["community_featured_studios"]


def top_loved():
    return featured_data()["community_most_loved_projects"]


def top_remixed():
    return featured_data()["community_most_remixed_projects"]


def newest_projects():
    return featured_data()["community_newest_projects"]


def curated_projects():
    return featured_data()["curator_top_projects"]


def design_studio_projects():
    return featured_data()["scratch_design_studio"]


# --- Statistics ---

def total_site_stats():
    data = requests.get("https://scratch.mit.edu/statistics/data/daily/").json()
    data.pop("_TS")
    return data


def monthly_site_traffic():
    data = requests.get("https://scratch.mit.edu/statistics/data/monthly-ga/").json()
    data.pop("_TS")
    return data


def country_counts():
    return requests.get("https://scratch.mit.edu/statistics/data/monthly/").json()["country_distribution"]


def age_distribution():
    data = requests.get("https://scratch.mit.edu/statistics/data/monthly/").json()["age_distribution_data"][0]["values"]
    return_data = {}
    for value in data:
        return_data[value["x"]] = value["y"]
    return return_data


def monthly_comment_activity():
    return requests.get("https://scratch.mit.edu/statistics/data/monthly/").json()["comment_data"]


def monthly_project_shares():
    return requests.get("https://scratch.mit.edu/statistics/data/monthly/").json()["project_data"]


def monthly_active_users():
    return requests.get("https://scratch.mit.edu/statistics/data/monthly/").json()["active_user_data"]


def monthly_activity_trends():
    return requests.get("https://scratch.mit.edu/statistics/data/monthly/").json()["activity_data"]


# --- CSRF Token Generation API ---

def get_csrf_token():
    """
    Generates a scratchcsrftoken using Scratch's API.

    Returns:
        str: The generated scratchcsrftoken
    """
    return requests.get(
        "https://scratch.mit.edu/csrf_token/"
    ).headers["set-cookie"].split(";")[3][len(" Path=/, scratchcsrftoken="):]


# --- Various other api.scratch.mit.edu API endpoints ---

def get_health():
    return requests.get("https://api.scratch.mit.edu/health").json()


def get_total_project_count() -> int:
    return requests.get("https://api.scratch.mit.edu/projects/count/all").json()["count"]


def check_username(username):
    return requests.get(f"https://api.scratch.mit.edu/accounts/checkusername/{username}").json()["msg"]


def check_password(password):
    return requests.post("https://api.scratch.mit.edu/accounts/checkpassword/", json={"password": password}).json()[
        "msg"]


# --- April fools endpoints ---

def aprilfools_get_counter() -> int:
    return requests.get("https://api.scratch.mit.edu/surprise").json()["surprise"]


def aprilfools_increment_counter() -> int:
    return requests.post("https://api.scratch.mit.edu/surprise").json()["surprise"]


# --- Resources ---
def get_resource_urls():
    return requests.get("https://resources.scratch.mit.edu/localized-urls.json").json()


# --- Misc ---
# I'm not sure what to label this as
def scratch_team_members() -> dict:
    # Unfortunately, the only place to find this is a js file, not a json file, which is annoying
    text = requests.get("https://scratch.mit.edu/js/credits.bundle.js").text
    text = "[{\"userName\"" + text.split("JSON.parse('[{\"userName\"")[1]
    text = text.split("\"}]')")[0] + "\"}]"

    return json.loads(text)


def translate(language: str | Languages, text: str = "hello"):
    if isinstance(language, str):
        lang = Languages.find_by_attrs(language.lower(), ["code", "tts_locale", "name"], str.lower)
    elif isinstance(language, Languages):
        lang = language.value
    else:
        lang = language

    if not isinstance(lang, Language):
        raise InvalidLanguage(f"{language} is not a language")

    if lang.code is None:
        raise InvalidLanguage(f"{lang} is not a valid translate language")

    response_json = requests.get(
        f"https://translate-service.scratch.mit.edu/translate?language={lang.code}&text={text}").json()

    if "result" in response_json:
        return response_json["result"]
    else:
        raise BadRequest(f"Language '{language}' does not seem to be valid.\nResponse: {response_json}")


def text2speech(text: str = "hello", voice_name: str = "female", language: str = "en-US"):
    """
    Sends a request to Scratch's TTS synthesis service.
    Returns:
        - The TTS audio (mp3) as bytes
        - The playback rate (e.g. for giant it would be 0.84)
    """
    if isinstance(voice_name, str):
        voice = TTSVoices.find_by_attrs(voice_name.lower(), ["name", "gender"], str.lower)
    elif isinstance(voice_name, TTSVoices):
        voice = voice_name.value
    else:
        voice = voice_name

    if not isinstance(voice, TTSVoice):
        raise InvalidTTSGender(f"TTS Gender {voice_name} is not supported.")

    # If it's kitten, make sure to change everything to just meows
    if voice.name == "kitten":
        text = ''
        for word in text.split(' '):
            if word.strip() != '':
                text += "meow "

    if isinstance(language, str):
        lang = Languages.find_by_attrs(language.lower(), ["code", "tts_locale", "name"], str.lower)
    elif isinstance(language, Languages):
        lang = language.value
    else:
        lang = language

    if not isinstance(lang, Language):
        raise InvalidLanguage(f"Language '{language}' is not a language")

    if lang.tts_locale is None:
        raise InvalidLanguage(f"Language '{language}' is not a valid TTS language")

    response = requests.get(f"https://synthesis-service.scratch.mit.edu/synth"
                            f"?locale={lang.tts_locale}&gender={voice.gender}&text={text}")
    return response.content, voice.playback_rate
