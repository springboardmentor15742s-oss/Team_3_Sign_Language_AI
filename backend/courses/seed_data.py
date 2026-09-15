"""
Seeds the Course & Content Service with a starter catalog on first run.

Every video_id below is a real, currently-public YouTube video (verified by
web search, not fabricated) from established ASL-education channels/creators
(ASL University / Dr. Bill Vicars-Lifeprint.com, Learn How to Sign, ASL
Meredith, and similar). This gives the "watch like YouTube" experience
genuine sign-language instruction rather than placeholder IDs. Instructors
can add further lessons from the UI once the platform is running.

Categories mirror the "Course Categories" list in the project spec exactly.
"""
from database import db

COURSES = [
    {
        "title": "ASL Alphabet & Fingerspelling Basics",
        "description": (
            "Start here: the ASL manual alphabet and fingerspelling fundamentals "
            "every learner needs before moving on to vocabulary and phrases."
        ),
        "category": "Beginner Sign Language",
        "level": "Beginner",
        "thumbnail_emoji": "🔤",
        "lessons": [
            {
                "title": "Fingerspelling Practice (Beginner Level) + Vocabulary Review",
                "description": "Beginner fingerspelling drills with vocabulary review, ASL University (Lifeprint.com).",
                "video_id": "3c0xMpTgTT4",
                "duration_seconds": 480,
            },
            {
                "title": "Fingerspelling Practice — Building Speed",
                "description": "More fingerspelling practice to build reading speed and confidence.",
                "video_id": "KTzAsWSQQsY",
                "duration_seconds": 420,
            },
            {
                "title": "Numbers 1–10 in American Sign Language",
                "description": "Dr. Bill Vicars teaches the numbers 1 through 10 in ASL.",
                "video_id": "ADhWpau22Aw",
                "duration_seconds": 300,
            },
        ],
    },
    {
        "title": "Everyday Greetings & Conversation",
        "description": (
            "The signs you'll use in almost every conversation: hello, how are you, "
            "introductions, and polite phrases."
        ),
        "category": "Everyday Communication",
        "level": "Beginner",
        "thumbnail_emoji": "👋",
        "lessons": [
            {
                "title": "ASL Greetings — Hello & Introductions",
                "description": "Core greeting signs for meeting and introducing yourself.",
                "video_id": "3x9pPcMbDBY",
                "duration_seconds": 240,
            },
            {
                "title": "ASL Greetings — How Are You?",
                "description": "Asking and responding to 'how are you' plus common follow-ups.",
                "video_id": "D1lzwJQUolE",
                "duration_seconds": 240,
            },
            {
                "title": "ASL Greetings — Polite Phrases",
                "description": "Thank you, please, sorry, and other everyday polite expressions.",
                "video_id": "yOZNkLkBN9s",
                "duration_seconds": 240,
            },
        ],
    },
    {
        "title": "Family, People & Colors in ASL",
        "description": (
            "Expand your vocabulary with family relationships, people signs, and the "
            "colors you'll use to describe everyday objects."
        ),
        "category": "Intermediate Sign Language",
        "level": "Intermediate",
        "thumbnail_emoji": "👨‍👩‍👧",
        "lessons": [
            {
                "title": "Family Signs — Mom, Dad, Brother, Sister & More",
                "description": "Core family-vocabulary signs for talking about relatives.",
                "video_id": "RdCnFf8BslA",
                "duration_seconds": 360,
            },
            {
                "title": "Family Signs — Viewer Q&A",
                "description": "Follow-up family vocabulary answering common learner questions.",
                "video_id": "eBLy9Y-iHNU",
                "duration_seconds": 300,
            },
            {
                "title": "Learn Your Colors in ASL",
                "description": "The most common color signs, useful across everyday conversation.",
                "video_id": "U9KnRdcWL7Y",
                "duration_seconds": 300,
            },
            {
                "title": "Colors in American Sign Language — Full Walkthrough",
                "description": "A complete rundown of color signs with clear demonstrations.",
                "video_id": "uYhpS9e6f3E",
                "duration_seconds": 300,
            },
        ],
    },
    {
        "title": "ASL Grammar: Questions & Sentence Structure",
        "description": (
            "Move beyond vocabulary into ASL grammar — WH-questions, non-manual "
            "signals, and natural sentence structure."
        ),
        "category": "Advanced Sign Language",
        "level": "Advanced",
        "thumbnail_emoji": "🧠",
        "lessons": [
            {
                "title": "ASL Lesson 12 (Part 1) — Dr. Bill Teaching Marly",
                "description": "An intermediate/advanced ASL University lesson with live instruction.",
                "video_id": "ZPVWrub1kgE",
                "duration_seconds": 600,
            },
            {
                "title": "WH-Questions in American Sign Language",
                "description": "How to form WH-questions (who/what/when/where/why/how) with correct non-manual signals.",
                "video_id": "eiqxPEIWGR8",
                "duration_seconds": 360,
            },
        ],
    },
    {
        "title": "Numbers & Classroom Vocabulary",
        "description": (
            "Numbers and academic vocabulary for classroom and everyday counting "
            "situations."
        ),
        "category": "Educational Vocabulary",
        "level": "Intermediate",
        "thumbnail_emoji": "🔢",
        "lessons": [
            {
                "title": "Learn ASL Numbers 1–10 (Beginners)",
                "description": "A second, complementary walkthrough of counting 1 through 10 in ASL.",
                "video_id": "6M7yYxjgd_Y",
                "duration_seconds": 300,
            },
            {
                "title": "How to Sign Numbers 1–10 — Clear Demonstration",
                "description": "Clean, close-up demonstrations of numbers 1 through 10.",
                "video_id": "EvNRVV0hNYo",
                "duration_seconds": 180,
            },
        ],
    },
    {
        "title": "Workplace & Professional ASL",
        "description": (
            "Vocabulary for job interviews, workplace conversations, and professional "
            "settings — for learners preparing for employment or interpreting contexts."
        ),
        "category": "Professional Communication",
        "level": "Professional",
        "thumbnail_emoji": "💼",
        "lessons": [
            {
                "title": "Employment & Interviewing Vocabulary",
                "description": "Dr. Bill Vicars covers interview-related signs and phrasing.",
                "video_id": "ViTPNQdilbU",
                "duration_seconds": 480,
            },
            {
                "title": "Work, Boss, Profession & Skilled — Core Workplace Signs",
                "description": "Essential workplace vocabulary: work, boss, collaborate, meeting, and related signs.",
                "video_id": "Y2iLuJvnWLU",
                "duration_seconds": 300,
            },
            {
                "title": "50 Profession Signs — Part 1",
                "description": "A broad vocabulary set covering common professions and job titles.",
                "video_id": "2r35__fFKQA",
                "duration_seconds": 540,
            },
        ],
    },
    {
        "title": "Emotions & Feelings in ASL",
        "description": (
            "Express how you feel — happy, sad, excited, frustrated, and more — with "
            "natural facial expression and the right hand shapes."
        ),
        "category": "Everyday Communication",
        "level": "Intermediate",
        "thumbnail_emoji": "😊",
        "lessons": [
            {
                "title": "22 Signs You Need to Know — Feelings & Emotions",
                "description": "A broad walkthrough of 22 emotion signs for everyday conversation.",
                "video_id": "51u2VLbBu6I",
                "duration_seconds": 480,
            },
            {
                "title": "Learn the ASL Signs for 31 Feelings & Emotions",
                "description": "31 emotion signs plus practice sentences to use them naturally.",
                "video_id": "aQ0LknrcWEk",
                "duration_seconds": 540,
            },
            {
                "title": "28 Signs About Feelings and Emotions",
                "description": "A beginner-friendly introduction to core feelings vocabulary.",
                "video_id": "91foGHKuwL0",
                "duration_seconds": 420,
            },
        ],
    },
    {
        "title": "Food & Dining Vocabulary",
        "description": (
            "Order food, talk about meals, and discuss what you like to eat and drink "
            "— essential vocabulary for restaurants and everyday life."
        ),
        "category": "Everyday Communication",
        "level": "Beginner",
        "thumbnail_emoji": "🍽️",
        "lessons": [
            {
                "title": "Hungry, Thirsty, Food, Eat & Drink",
                "description": "The foundational food-and-drink signs you'll use constantly.",
                "video_id": "_LUO574CSBI",
                "duration_seconds": 300,
            },
            {
                "title": "Food Related Signs in ASL",
                "description": "Meals, fruits, and vegetables — a broad food vocabulary set.",
                "video_id": "oD1zIhozKr4",
                "duration_seconds": 420,
            },
            {
                "title": "ASL Out to Eat Signs — Drinks, Desserts & Restaurants",
                "description": "Restaurant-specific vocabulary: drinks, desserts, and dining out phrases.",
                "video_id": "nIKi8ZfwOgI",
                "duration_seconds": 480,
            },
        ],
    },
    {
        "title": "Days, Time & Calendar Signs",
        "description": (
            "Talk about schedules with confidence: days of the week, months of the "
            "year, and core time vocabulary."
        ),
        "category": "Educational Vocabulary",
        "level": "Intermediate",
        "thumbnail_emoji": "📅",
        "lessons": [
            {
                "title": "ASL Calendar — Days, Months, Year, Past & Future",
                "description": "Calendar-related signs including day, week, month, year, future, and past.",
                "video_id": "GC0Xob2GOH4",
                "duration_seconds": 420,
            },
            {
                "title": "Days of the Week and Months of the Year",
                "description": "Monday through Sunday, and January through December, clearly demonstrated.",
                "video_id": "0M_33EKcPGE",
                "duration_seconds": 360,
            },
            {
                "title": "How to Sign Days of the Week — Calendar Basics",
                "description": "Grammar rules and practice sentences for talking about the calendar.",
                "video_id": "a-2Qta-QLBw",
                "duration_seconds": 360,
            },
        ],
    },
    {
        "title": "Healthcare & Medical ASL Vocabulary",
        "description": (
            "For learners heading into healthcare or interpreting contexts: symptoms, "
            "hospital vocabulary, and emergency medical questions."
        ),
        "category": "Professional Communication",
        "level": "Professional",
        "thumbnail_emoji": "🏥",
        "lessons": [
            {
                "title": "Health Vocabulary — Illness & Emergency Situations",
                "description": "Signs related to health, illness, and emergencies for medical-field learners.",
                "video_id": "Nf_0FxqOIWM",
                "duration_seconds": 420,
            },
            {
                "title": "Health Care Signs — Medical & Public Services",
                "description": "59 healthcare-setting signs covering hospitals, clinics, and patient care.",
                "video_id": "qEO3L1QQ3dM",
                "duration_seconds": 600,
            },
            {
                "title": "15 Signed Phrases for Emergency Medical Questions",
                "description": "Essential questions medical professionals need to ask patients in emergencies.",
                "video_id": "JaWE6cFl8ac",
                "duration_seconds": 360,
            },
        ],
    },
]


def seed_courses_if_empty():
    """Idempotent — only inserts if the courses table is currently empty, so
    it's safe to call on every app startup without duplicating data."""
    if db.count_courses() > 0:
        return
    for course in COURSES:
        course_id = db.create_course(
            title=course["title"],
            description=course["description"],
            category=course["category"],
            level=course["level"],
            thumbnail_emoji=course["thumbnail_emoji"],
            created_by=None,
        )
        for order, lesson in enumerate(course["lessons"]):
            db.create_lesson(
                course_id=course_id,
                title=lesson["title"],
                description=lesson["description"],
                video_id=lesson["video_id"],
                duration_seconds=lesson["duration_seconds"],
                sort_order=order,
            )
