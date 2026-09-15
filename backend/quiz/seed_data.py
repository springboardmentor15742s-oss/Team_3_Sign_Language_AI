"""
Seed data for the Quiz / Knowledge-Check module (roadmap: "Quiz
generation" + "Skill evaluation" under the Assessment & Certification
Module).

These are knowledge questions about ASL vocabulary, grammar, and Deaf
culture — complementary to, not a replacement for, the live
gesture-practice assessment engine elsewhere in the app. All questions
below are original wording covering well-established, general facts about
ASL and Deaf culture (not copied from any quiz, textbook, or website).

Five questions per LEARNING_LEVELS tier, roughly increasing in depth.
"""

SEED_QUESTIONS = [
    # ---------------- Beginner ----------------
    {
        "level": "Beginner",
        "topic": "ASL Basics",
        "question_text": 'What does the abbreviation "ASL" stand for?',
        "option_a": "American Sign Language",
        "option_b": "Advanced Signing Level",
        "option_c": "Auditory Speech Language",
        "option_d": "American Spelling Lexicon",
        "correct_option": "a",
        "explanation": "ASL stands for American Sign Language, a complete, natural language used primarily by Deaf communities in the US and parts of Canada.",
    },
    {
        "level": "Beginner",
        "topic": "Fingerspelling",
        "question_text": "Fingerspelling is most commonly used for which of these?",
        "option_a": "Spelling out proper names or words with no dedicated sign",
        "option_b": "Replacing sentence grammar entirely",
        "option_c": "Counting past 100",
        "option_d": "Signing song lyrics only",
        "correct_option": "a",
        "explanation": "Fingerspelling uses the manual alphabet to spell out names, places, or specialized terms that don't have an established ASL sign.",
    },
    {
        "level": "Beginner",
        "topic": "Sign Parameters",
        "question_text": "Which of the following is one of the core parameters that make up a sign?",
        "option_a": "Handshape",
        "option_b": "Volume",
        "option_c": "Pitch",
        "option_d": "Font size",
        "correct_option": "a",
        "explanation": "Signs are built from parameters including handshape, location, movement, and palm orientation — volume and pitch are spoken-language concepts that don't apply to signs.",
    },
    {
        "level": "Beginner",
        "topic": "ASL Basics",
        "question_text": "In ASL, where is the sign for most family-member terms (like MOTHER and FATHER) typically made?",
        "option_a": "Near the face/head",
        "option_b": "Near the knee",
        "option_c": "Behind the back",
        "option_d": "On the opposite shoulder only",
        "correct_option": "a",
        "explanation": "Many family signs are made near the face — for example, male family signs are often near the forehead and female family signs nearer the chin, as a general pattern.",
    },
    {
        "level": "Beginner",
        "topic": "ASL Basics",
        "question_text": "Which of these is NOT one of the four learner levels used on this platform?",
        "option_a": "Professional",
        "option_b": "Beginner",
        "option_c": "Novice-Plus",
        "option_d": "Advanced",
        "correct_option": "c",
        "explanation": "This platform's learner levels are Beginner, Intermediate, Advanced, and Professional.",
    },
    # ---------------- Intermediate ----------------
    {
        "level": "Intermediate",
        "topic": "Grammar",
        "question_text": "What term describes the facial expressions and head/body movements that carry grammatical meaning in ASL?",
        "option_a": "Non-manual markers",
        "option_b": "Manual overlays",
        "option_c": "Verbal cues",
        "option_d": "Tonal inflection",
        "correct_option": "a",
        "explanation": "Non-manual markers (facial expression, eyebrow position, head tilt, mouth morphemes) are a required grammatical part of ASL, not just emotional expression.",
    },
    {
        "level": "Intermediate",
        "topic": "Deaf Culture",
        "question_text": 'In Deaf culture, what does capitalized "Deaf" typically refer to, as opposed to lowercase "deaf"?',
        "option_a": "Cultural and linguistic identity/community membership",
        "option_b": "A more severe degree of hearing loss",
        "option_c": "A person who has never used a hearing aid",
        "option_d": "There is no meaningful difference",
        "correct_option": "a",
        "explanation": 'Capital-D "Deaf" is commonly used to refer to cultural identity and community/language membership, while lowercase "deaf" typically refers to the audiological condition.',
    },
    {
        "level": "Intermediate",
        "topic": "Grammar",
        "question_text": "ASL sentence structure is often described as following which organizing principle?",
        "option_a": "Topic-comment ordering",
        "option_b": "Strict Subject-Verb-Object only, with no exceptions",
        "option_c": "Reverse alphabetical word order",
        "option_d": "Random word order with no grammar",
        "correct_option": "a",
        "explanation": 'ASL frequently uses topic-comment structure ("that movie, I liked") alongside spatial grammar, rather than being locked to English-style Subject-Verb-Object order.',
    },
    {
        "level": "Intermediate",
        "topic": "Deaf Culture",
        "question_text": "Which US institution is historically significant as the world's only university designed specifically for Deaf and hard-of-hearing students?",
        "option_a": "Gallaudet University",
        "option_b": "Lifeprint College",
        "option_c": "Stokoe Institute",
        "option_d": "National ASL Academy",
        "correct_option": "a",
        "explanation": "Gallaudet University, in Washington, D.C., is widely recognized as the world's premier university built specifically around Deaf and hard-of-hearing education.",
    },
    {
        "level": "Intermediate",
        "topic": "Etiquette",
        "question_text": "When communicating with a Deaf person through a sign language interpreter, general etiquette is to:",
        "option_a": "Speak/sign directly to the Deaf person, not the interpreter",
        "option_b": "Speak only to the interpreter and avoid eye contact with the Deaf person",
        "option_c": "Speak louder than usual",
        "option_d": "Avoid facial expressions entirely",
        "correct_option": "a",
        "explanation": "The interpreter facilitates communication, but conversational attention and eye contact should stay directed at the Deaf person you're actually talking with.",
    },
    # ---------------- Advanced ----------------
    {
        "level": "Advanced",
        "topic": "Linguistics",
        "question_text": "In ASL, a handshape used to represent a category of object (e.g. vehicles, flat objects) to show movement, size, or shape is called a:",
        "option_a": "Classifier",
        "option_b": "Modifier sign",
        "option_c": "Root gesture",
        "option_d": "Depiction suffix",
        "correct_option": "a",
        "explanation": "Classifiers are handshapes that stand in for categories of nouns, letting a signer show how something moved, its size, or its shape spatially.",
    },
    {
        "level": "Advanced",
        "topic": "Linguistics",
        "question_text": "Which linguist is widely credited with pioneering research in the 1960s that established ASL as a full, rule-governed language rather than a simplified gestural code?",
        "option_a": "William Stokoe",
        "option_b": "Noam Chomsky",
        "option_c": "Ferdinand de Saussure",
        "option_d": "Helen Keller",
        "correct_option": "a",
        "explanation": "William Stokoe's linguistic research at Gallaudet, published starting in 1960, was foundational in establishing ASL's status as a genuine, independently-structured language.",
    },
    {
        "level": "Advanced",
        "topic": "Grammar",
        "question_text": "What is 'signing space' used for in fluent ASL discourse?",
        "option_a": "Assigning locations to referents so pronouns and verbs can point back to them spatially",
        "option_b": "Deciding how loudly to sign",
        "option_c": "Marking punctuation at the end of a sentence",
        "option_d": "Indicating which hand is dominant only",
        "correct_option": "a",
        "explanation": "Signers set up referents ('placing' people/things) at specific points in the space around them, then use directional verbs and pointing to refer back to them grammatically.",
    },
    {
        "level": "Advanced",
        "topic": "Sociolinguistics",
        "question_text": "What is meant by 'code-switching' for a bilingual ASL/English signer?",
        "option_a": "Shifting between ASL and a more English-influenced signing style depending on the audience/context",
        "option_b": "Switching which hand is dominant mid-sentence",
        "option_c": "Alternating between fingerspelling and gesture only",
        "option_d": "A technical term for a typing error",
        "correct_option": "a",
        "explanation": "Like spoken bilinguals, ASL/English bilingual signers often shift their register — e.g. between ASL and more English-ordered signing (like Signed Exact English or PSE) — based on who they're communicating with.",
    },
    {
        "level": "Advanced",
        "topic": "Linguistics",
        "question_text": "Facial grammar in ASL can change the meaning of a sentence from a statement to a question. Which of these is an example?",
        "option_a": "Raised eyebrows typically mark a yes/no question",
        "option_b": "Closed eyes always mark the past tense",
        "option_c": "A smile always negates the sentence",
        "option_d": "Facial expression has no grammatical effect in ASL",
        "correct_option": "a",
        "explanation": "Non-manual grammar is required, not optional, in ASL — for example, raised eyebrows are a standard marker for yes/no questions, while furrowed brows commonly mark wh- questions.",
    },
    # ---------------- Professional ----------------
    {
        "level": "Professional",
        "topic": "Workplace Accessibility",
        "question_text": "Under the Americans with Disabilities Act (ADA), a US employer is generally expected to provide which kind of support for a Deaf employee, when needed and reasonable?",
        "option_a": "Reasonable accommodations, such as a sign language interpreter or visual alert systems",
        "option_b": "No accommodations are required by law",
        "option_c": "Only accommodations the employee pays for themselves",
        "option_d": "Accommodations only during the employee's first week",
        "correct_option": "a",
        "explanation": "The ADA generally requires covered employers to provide reasonable accommodations — interpreters, visual/text alerting systems, and similar — for qualified employees who are Deaf or hard of hearing.",
    },
    {
        "level": "Professional",
        "topic": "Workplace Accessibility",
        "question_text": "What does CART (as used in accessibility/workplace settings) refer to?",
        "option_a": "Communication Access Realtime Translation — live speech-to-text captioning",
        "option_b": "A certification exam for ASL interpreters",
        "option_c": "A wheeled device used to transport interpreting equipment",
        "option_d": "A coding standard for accessibility websites",
        "correct_option": "a",
        "explanation": "CART (Communication Access Realtime Translation) provides real-time, verbatim speech-to-text captioning, commonly used in meetings, classrooms, and events.",
    },
    {
        "level": "Professional",
        "topic": "Workplace Accessibility",
        "question_text": "What does Video Relay Service (VRS) allow a Deaf person to do?",
        "option_a": "Make phone calls to hearing people through a video interpreter",
        "option_b": "Stream ASL classes for free",
        "option_c": "Automatically translate sign language into subtitles on TV",
        "option_d": "Record ASL videos for later upload only",
        "correct_option": "a",
        "explanation": "VRS connects a Deaf caller (signing on video) with a hearing party (on a standard phone call) through a live sign language interpreter, enabling real-time phone conversations.",
    },
    {
        "level": "Professional",
        "topic": "Workplace Etiquette",
        "question_text": "Before scheduling an important meeting with a Deaf colleague, a good first professional step is to:",
        "option_a": "Ask about their preferred communication accommodation in advance",
        "option_b": "Assume they will lip-read and skip any accommodation planning",
        "option_c": "Send a memo in Braille regardless of their needs",
        "option_d": "Cancel the meeting and communicate only by email going forward",
        "correct_option": "a",
        "explanation": "Communication needs vary a lot between individuals — asking in advance (interpreter, captioning, written notes, etc.) is both respectful and far more effective than guessing.",
    },
    {
        "level": "Professional",
        "topic": "Certification Preparation",
        "question_text": "Which combination best reflects how this platform recommends preparing for a Professional-level certification?",
        "option_a": "Consistent gesture practice, strong accuracy across many signs, and broad vocabulary/topic coverage",
        "option_b": "A single lucky high-accuracy attempt on one sign",
        "option_c": "Watching course videos without ever practicing gestures",
        "option_d": "Certification is granted automatically after registration",
        "correct_option": "a",
        "explanation": "Certification eligibility (see certification/rules.py) is based on sustained accuracy and breadth of practiced signs — not a single attempt or passive video-watching alone.",
    },
]


def seed_quiz_questions_if_empty():
    """Idempotent — only inserts if quiz_questions is currently empty, so
    it's safe to call on every app startup without duplicating data."""
    from database import db

    if db.count_quiz_questions() > 0:
        return
    for q in SEED_QUESTIONS:
        db.create_quiz_question(
            level=q["level"],
            topic=q["topic"],
            question_text=q["question_text"],
            option_a=q["option_a"],
            option_b=q["option_b"],
            option_c=q["option_c"],
            option_d=q["option_d"],
            correct_option=q["correct_option"],
            explanation=q["explanation"],
        )
