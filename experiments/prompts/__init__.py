import config
from prompts.parsing import *  # noqa

# import english prompts as default which this file can override
from prompts.english import *  # noqa

logger = config.get_logger(__name__)

PROMPT_SYNTHETIC_SMART = """
You're a student taking a course where you're tasked with writing a SMART goal defining your personal learning objective for the course.
{SMART_RUBRIC}

Your response should contain a SMART goal written from your perspective as a student, as well as an appropriate action plan, formatted like the example response below (simple json object containing plain text data with no markdown formatting).
{SMART_EXAMPLE}

In your case the goal you're writing should focus on a skill such as '{skill}' (for example {skill_description}) and you shall write your goal/plan using a tone of voice such as '{tone}'.
{extra}
Now respond only with a SMART goal written from your perspective as a student as well as an appropriate action plan in json format like the example. You do not have to adhere to the particular wording structure used in the example, just the json format. However, your SMART goald and plan should be written in the {language} language.
""".strip()

EDUCATION_WORDS = [
    "onderwijs",
    "leren",
    "doelen",
    "kennis",
    "begrip",
    "studie",
    "onderwijzen",
    "opleiding",
    "ontwikkeling",
    "curriculum",
    "pedagogie",
    "geletterdheid",
    "rekenvaardigheid",
    "vaardigheid",
    "beheersing",
    "prestatie",
    "vooruitgang",
    "vooruitgang",
    "verlichting",
    "discipline",
    "onderzoek",
    "theorie",
    "praktijk",
    "toepassing",
    "analyse",
    "begrip",
    "retentie",
    "herinneren",
    "inzicht",
    "innovatie",
    "creativiteit",
    "kritisch",
    "denken",
    "problemen oplossen",
    "communicatie",
    "samenwerking",
    "motivatie",
    "inspiratie",
    "aspiratie",
    "succes",
    "inspanning",
    "doorzettingsvermogen",
    "toewijding",
    "discipline",
    "focus",
    "begeleiding",
    "feedback",
    "evaluatie",
    "verbetering",
]
