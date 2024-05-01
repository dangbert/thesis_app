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
Now respond only with a SMART goal written from your perspective as a student as well as an appropriate action plan in json format like the example. You do not have to adhere to the particular wording structure used in the example, just the json format. However, your SMART goal and plan should be written in the {language} language.
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

# get raw feedback as text (no scores requested)
PROMPT_SMART_FEEDBACK_TEXT_ONLY = """
You are a peer reviewer, tasked with giving a student feedback about an assignment.
Your feedback must adhere to the following principles:
{FEEDBACK_PRINCIPLES}

The rubric for the assignment follows (delimited by =====):
=====
{SMART_RUBRIC}
=====

An example of a SMART goal and action plan follows:
smart goal:
"Make eye contact with the audience during my video pitch and literature presentation to better engage the viewer with my story. In the video pitch, I do this by looking closely into the camera most of the time and in the literature presentation by alternately looking at the different people in the audience, both my fellow students and teachers."

action plan:
"I will achieve this by not memorising my story verbatim, but rather by using keywords and by practising looking into the camera and making video recordings of this during the preparation of my pitch. I also practise my literature presentation dry where my group mates sit on opposite sides of the room. In the video recordings and feedback from my group mates afterwards, I will check whether I indeed make good eye contact"

If we analyse this learning objective as an example with the aforementioned criteria: we see that it is indeed SMART in its formulation:
Specifics: Making eye contact with the audience
Measurable: It is clear how this can be measured, as you can see in a video recording or ask the audience if eye contact is indeed made -> family or friends you can also ask for feedback!
Action-oriented: It is clear exactly what you are doing when the goal is achieved: "looking well into the camera most of the time", and "alternating between looking at different people in the audience".
Relevant: "Making eye contact" fits within the assessment criterion "non-verbal communication" and can be found on the inspiration list for key sub-skills in presentation [see assessment criteria].
Time-bound: "during my video pitch and literature presentation"

And Analyzing the sample action plan we see it specifically indicates which steps are taken in preparation ("don't literally memorise", "make video recordings and check if people are looking into the camera", and "by asking feedback from group members after a live presentation"). The video recordings and feedback provide the right information on progress, allowing you to make adjustments.
=====

Now provide feedback (written in {language}) and adhering to the feedback principles on the following assignment:

smart goal:
{learning_goal}

action plan:
{action_plan}
""".strip()
