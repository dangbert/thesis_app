import re
import json
from pydantic import BaseModel, conint, Field
from typing import Annotated

SMART = ["specific", "measurable", "action-oriented", "relevant", "time-bound"]

SMART_RUBRIC = """
A SMART learning goal must be Specific, Measurable, Action-oriented, Relevant, and Time-bound as described further below:
Specific: Concrete and unambiguous definition of the goal: is it clear what you want to achieve?
Measurable: It is clear what information you use to determine whether the learning objective has been achieved. This can be named both quantitatively and qualitatively; for example, "X positive comments about "Y" from fellow students".
Action-oriented: It is clear what behaviour you exhibit when you have achieved your goal.
Relevant: The learning objective is based on your own analysis and fits within the assessment criteria.
Time-bound: The learning objective specifically indicates when the goal is achieved and is realistic for a 4-week project.

Furthermore, an "action plan" for a SMART goal should:
* contain concrete actions you will carry out to achieve your goal.
* Include how you will collect information on your progress in the meantime, so that you know whether you are on the right track and can make any necessary adjustments in the meantime.
* Be clear and follow logically from the formulated learning objective  .
* Be achievable within the stipulated time.
* Allow for interim evaluation and adjustment.
""".strip()


# NOTE: don't use this one as its own fstring
SMART_EXAMPLE = """
{
    "smart": "Make eye contact with the audience during my video pitch and literature presentation to better engage the viewer with my story. In the video pitch, I do this by looking closely into the camera most of the time and in the literature presentation by alternately looking at the different people in the audience, both my fellow students and teachers.",
    "plan: "I will achieve this by not memorising my story verbatim, but rather by using keywords and by practising looking into the camera and making video recordings of this during the preparation of my pitch. I also practise my literature presentation dry where my group mates sit on opposite sides of the room. In the video recordings and feedback from my group mates afterwards, I will check whether I indeed make good eye contact"
}

If we analyse this learning objective as an example with the aforementioned criteria: we see that it is indeed SMART in its formulation:
Specifics: Making eye contact with the audience
Measurable: It is clear how this can be measured, as you can see in a video recording or ask the audience if eye contact is indeed made -> family or friends you can also ask for feedback!
Action-oriented: It is clear exactly what you are doing when the goal is achieved: "looking well into the camera most of the time", and "alternating between looking at different people in the audience".
Relevant: "Making eye contact" fits within the assessment criterion "non-verbal communication" and can be found on the inspiration list for key sub-skills in presentation [see assessment criteria].
Time-bound: "during my video pitch and literature presentation"

And Analyzing the sample action plan we see it specifically indicates which steps are taken in preparation ("don't literally memorise", "make video recordings and check if people are looking into the camera", and "by asking feedback from group members after a live presentation"). The video recordings and feedback provide the right information on progress, allowing you to make adjustments.
""".strip()

PROMPT_SYNTHETIC_SMART = """
You're a student taking a course where you're tasked with writing a SMART goal defining your personal learning objective for the course.
{SMART_RUBRIC}

Your response should contain a SMART goal written from your perspective as a student, as well as an appropriate action plan, formatted like the example response below (simple json object contaiing plain text data with no markdown formatting).
{SMART_EXAMPLE}

In your case the goal you're writing should focus on a skill such as '{skill}' (for example {skill_description}) and may write your goal/plan using a tone of voice such as '{tone}'.
{extra}
Now respond only with a SMART goal written from your perspective as a student as well as an appropriate action plan in json format like the example. You do not have to adhere to the particular wording structure using in the example, just the json format.
""".strip()

# List of sub-skills for presenting to inspire you in setting your personal learning goal:
SKILLS = {
    "clarity in communication": "ability to explain complex concepts and ideas in a simple and understandable way, but also to use effective signal and reference words to involve the audience in the story",
    "structure of the presentation": "ability to structure a presentation logically and coherently, with a clear introduction, middle and conclusion, and to make clear connections between different parts.",
    "language use": "ability to use precise, clear and professional language, including the appropriate use of scientific terminology. Spaces between sentences are not filled with distracting filler words, but rather used strategically to get the message across to the audience.",
    "time management and speaking pace": "ability to use an appropriate pace of speech that is comfortable for the audience to follow and that fits the story within time without missing important points.",
    "pitch and intonation": "using different pitches and intonation to make the presentation more engaging and understandable. Intonations can also be used to place emphasis on a specific part of a sentence to better guide the audience through the story.",
    "voice volume": "ability to use the voice in such a way that everyone can hear the presentation clearly.",
    "non-verbal communication": "eye contact: the ability to make contact with the audience and involve them in the story by consciously looking at them (e.g. looking into the camera) and distributing attention evenly across the audience",
    "facial expression": "ability to use facial expressions to give an accessible presentation (e.g., friendly smile) and to emphasize what is being said (e.g., by using facial expressions).",
    # TODO: "[see also the knowledge clip about hand gestures and body language]":
    "hand gestures": "ability to use hand gestures that support and thereby reinforce the spoken message. Consider, for example, counting with the hands when 3 main points are mentioned, or emphasizing the 'one' versus the 'other' side of the matter, etc. !.",
}

TONES = [
    "formal",
    "professional",
    "authoritative",
    "serious",
    "assertive",
    "respectful",
    "informal",
    "humorous",
    "optimistic",
    "inspirational",
    "motivating",
    "conversational",
    "sarcastic",
    "cynical",
    "playful",
    "sympathetic",
    "empathetic",
    "sincere",
    "objective",
    "subjective",
    "critical",
    "analytical",
    "persuasive",
    "descriptive",
]

# ~50 words related to education, learning, and goals
EDUCATION_WORDS = [
    "education",
    "learning",
    "goals",
    "knowledge",
    "understanding",
    "study",
    "teaching",
    "training",
    "development",
    "curriculum",
    "pedagogy",
    "literacy",
    "numeracy",
    "skill",
    "mastery",
    "achievement",
    "progress",
    "advancement",
    "enlightenment",
    "discipline",
    "research",
    "theory",
    "practice",
    "application",
    "analysis",
    "comprehension",
    "retention",
    "recall",
    "insight",
    "innovation",
    "creativity",
    "critical",
    "thinking",
    "problem-solving",
    "communication",
    "collaboration",
    "motivation",
    "inspiration",
    "aspiration",
    "success",
    "effort",
    "perseverance",
    "dedication",
    "discipline",
    "focus",
    "guidance",
    "feedback",
    "evaluation",
    "improvement",
]

### peer reviewing:
FEEDBACK_PRINCIPLES = """
Your feedback must adhere to the following principles:
* Feedback shall be geared to providing information about progress and achievement, not towards providing a summative grade or pass/fail assessment.
* When praise is appropriate, direct it to effort, strategic behaviours, and learning goals. Avoid praising ability or intelligence.
* Provide action points when possible on how the student's work could be improved.
* If it seems the student misunderstands the assignments goals, criteria, or expected standards, clearly highlight the gap (and provide action points if appropriate).
""".strip()

PROMPT_SMART_FEEDBACK = """
You are a peer reviewer, tasked with giving a student feedback about an assignment.
{FEEDBACK_PRINCIPLES}

The rubric for the assignment follows (delimited by =====):
=====
{SMART_RUBRIC}
=====

An example of a SMART goal and action plan follows:
=====
{SMART_EXAMPLE}
=====

Now the student's draft follows:
=====
{student_draft}
=====

Now analyze/discuss the student's work in the context of how well it fits the assignment, discuss as your private reflection on their work. Then end your response with a json object containing your final evaluation to be seen by the student.
For scores, use a scale from 1 to 10 inclusive, where 1 is the worst and 10 is the best (null is an unacceptable score), and for "feedback" be sure to adhere to the aforementioned feedback principles (don't discuss the score in the feedback as its private).
The json object MUST use double quotes for keys/values and should conform to this json schema:
{json_schema}
"""


# prompt format:
# * feedback principles
# * specific format of response (e.g. chain of thought followed by json)
# * assignment specific info + rubric (+ possibly exemplars)
# * student's draft


class SMARTResponse(BaseModel):
    smart: str
    plan: str


class FeedbackAttr(BaseModel):
    score: Annotated[int, conint(ge=1, le=10)] = Field(
        default=None, title="Score in the range [1,10] inclusive.", ge=1, le=10
    )
    feedback: str


class SMARTFeedback(BaseModel):
    specific: FeedbackAttr
    measurable: FeedbackAttr
    action_oriented: FeedbackAttr
    relevant: FeedbackAttr
    time_bound: FeedbackAttr
    overall_feedback: str


def parseSMARTFeedback(response: str, retry: bool = False):
    """
    Attempt to find the JSON substring in the response and parse it into a SMARTFeedback object.
    Raises jsonDecodeError or ValidationError on failure.
    """
    json_str = re.search(r"{.*}", response, re.DOTALL).group()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        if not retry or "Expecting property name enclosed in double quotes" not in str(
            e
        ):
            raise e
        # hacky fix for single quotes (better to avoid this in the first place)
        tmp = response.replace("'", '"')
        return parseSMARTFeedback(tmp, retry=False)

    feedback = SMARTFeedback(**data)
    return feedback
