"""Seed content: construct library, question bank and career knowledge base.

Derived from PRD sections 10 (Student Intelligence Engine), 11
(Recommendation System) and 13 (Career Knowledge System).
"""

# Construct library (MVP) grouped by domain. Order matters for display.
CONSTRUCTS = {
    "Cognitive": ["analytical_thinking", "problem_solving", "numerical_reasoning"],
    "Interests": ["technology", "business", "healthcare", "arts"],
    "Personality": ["conscientiousness", "openness", "extraversion"],
    "Values": ["income", "security", "helping_others"],
    "Work Preferences": ["leadership", "teamwork", "entrepreneurship"],
}

CONSTRUCT_LABELS = {
    "analytical_thinking": "Analytical Thinking",
    "problem_solving": "Problem Solving",
    "numerical_reasoning": "Numerical Reasoning",
    "technology": "Technology Interest",
    "business": "Business Interest",
    "healthcare": "Healthcare Interest",
    "arts": "Arts & Creativity",
    "conscientiousness": "Conscientiousness",
    "openness": "Openness",
    "extraversion": "Extraversion",
    "income": "Income Orientation",
    "security": "Security Orientation",
    "helping_others": "Helping Others",
    "leadership": "Leadership",
    "teamwork": "Teamwork",
    "entrepreneurship": "Entrepreneurship",
}

# Question bank. Two Likert items per construct (some reverse-scored).
# value scale: 1 (Strongly disagree) .. 5 (Strongly agree)
QUESTIONS = [
    # Cognitive — analytical_thinking
    ("Q-AT-1", "I enjoy breaking complex problems into smaller parts to understand them.", "analytical_thinking", "Cognitive", False),
    ("Q-AT-2", "I prefer to act on gut feeling rather than carefully analysing a situation.", "analytical_thinking", "Cognitive", True),
    # problem_solving
    ("Q-PS-1", "I keep trying different approaches until I solve a difficult problem.", "problem_solving", "Cognitive", False),
    ("Q-PS-2", "I get stuck and give up quickly when a problem has no obvious solution.", "problem_solving", "Cognitive", True),
    # numerical_reasoning
    ("Q-NR-1", "I am comfortable working with numbers, data and statistics.", "numerical_reasoning", "Cognitive", False),
    ("Q-NR-2", "Mathematical or quantitative tasks make me anxious.", "numerical_reasoning", "Cognitive", True),
    # Interests — technology
    ("Q-TE-1", "I like understanding how computers, software or gadgets work.", "technology", "Interests", False),
    ("Q-TE-2", "I enjoy building, coding or tinkering with technology.", "technology", "Interests", False),
    # business
    ("Q-BU-1", "I am interested in how companies make money and grow.", "business", "Interests", False),
    ("Q-BU-2", "I enjoy negotiating, selling or persuading others.", "business", "Interests", False),
    # healthcare
    ("Q-HC-1", "I am drawn to caring for people's health and well-being.", "healthcare", "Interests", False),
    ("Q-HC-2", "I find biology and the human body fascinating.", "healthcare", "Interests", False),
    # arts
    ("Q-AR-1", "I enjoy creative activities like design, writing, music or art.", "arts", "Interests", False),
    ("Q-AR-2", "I often come up with original or imaginative ideas.", "arts", "Interests", False),
    # Personality — conscientiousness
    ("Q-CO-1", "I plan my work carefully and meet deadlines.", "conscientiousness", "Personality", False),
    ("Q-CO-2", "I often leave tasks unfinished or get disorganised.", "conscientiousness", "Personality", True),
    # openness
    ("Q-OP-1", "I enjoy exploring new ideas and unfamiliar experiences.", "openness", "Personality", False),
    ("Q-OP-2", "I prefer routine and dislike change.", "openness", "Personality", True),
    # extraversion
    ("Q-EX-1", "I feel energised when interacting with lots of people.", "extraversion", "Personality", False),
    ("Q-EX-2", "I prefer working quietly on my own rather than in groups.", "extraversion", "Personality", True),
    # Values — income
    ("Q-IN-1", "A high salary is very important to me when choosing a career.", "income", "Values", False),
    ("Q-IN-2", "I would happily take meaningful work even if it paid less.", "income", "Values", True),
    # security
    ("Q-SE-1", "Job stability and security matter a lot to me.", "security", "Values", False),
    ("Q-SE-2", "I am comfortable with uncertainty and risk in my career.", "security", "Values", True),
    # helping_others
    ("Q-HO-1", "I want my work to make a positive difference in people's lives.", "helping_others", "Values", False),
    ("Q-HO-2", "Helping others is one of my main motivations.", "helping_others", "Values", False),
    # Work Preferences — leadership
    ("Q-LE-1", "I like taking charge and leading a team toward a goal.", "leadership", "Work Preferences", False),
    ("Q-LE-2", "I would rather follow than be responsible for leading others.", "leadership", "Work Preferences", True),
    # teamwork
    ("Q-TW-1", "I do my best work collaborating closely with others.", "teamwork", "Work Preferences", False),
    ("Q-TW-2", "I enjoy contributing to a shared team result.", "teamwork", "Work Preferences", False),
    # entrepreneurship
    ("Q-EN-1", "I dream of starting my own venture or business one day.", "entrepreneurship", "Work Preferences", False),
    ("Q-EN-2", "I am willing to take risks to pursue a new opportunity.", "entrepreneurship", "Work Preferences", False),
]

# Career knowledge base. profile_weights = ideal student feature vector (0..1)
# the matching engine compares the student's vector against.
CAREERS = [
    {
        "slug": "data-scientist", "name": "Data Scientist", "category": "Technology",
        "description": "Data scientists analyse large datasets to uncover patterns and build predictive models that help organisations make decisions.",
        "responsibilities": ["Clean and explore data", "Build and evaluate machine-learning models", "Communicate insights to stakeholders"],
        "skills": ["Statistics", "Python/R", "Machine learning", "Data visualisation", "Critical thinking"],
        "subjects": ["Mathematics", "Computer Science", "Statistics"],
        "education_pathway": "Bachelor's in Computer Science, Statistics, or Mathematics, often followed by specialised data-science training.",
        "work_environment": "Office / Remote", "salary_range": "High", "outlook": "Excellent — growing rapidly",
        "related": ["software-engineer", "ai-researcher", "business-analyst"],
        "profile_weights": {"analytical_thinking": 0.95, "problem_solving": 0.9, "numerical_reasoning": 0.95,
                             "technology": 0.85, "openness": 0.7, "conscientiousness": 0.7},
    },
    {
        "slug": "software-engineer", "name": "Software Engineer", "category": "Technology",
        "description": "Software engineers design, build and maintain the applications and systems that power modern life.",
        "responsibilities": ["Write and review code", "Design software systems", "Debug and test applications"],
        "skills": ["Programming", "Problem solving", "System design", "Collaboration"],
        "subjects": ["Computer Science", "Mathematics"],
        "education_pathway": "Bachelor's in Computer Science or Software Engineering; bootcamps and self-study are also viable.",
        "work_environment": "Office / Remote", "salary_range": "High", "outlook": "Excellent",
        "related": ["data-scientist", "product-manager", "ai-researcher"],
        "profile_weights": {"analytical_thinking": 0.85, "problem_solving": 0.95, "technology": 0.95,
                             "numerical_reasoning": 0.7, "teamwork": 0.6, "openness": 0.65},
    },
    {
        "slug": "ai-researcher", "name": "AI / Machine Learning Researcher", "category": "Science",
        "description": "AI researchers push the boundaries of what machines can learn, developing new algorithms and models.",
        "responsibilities": ["Read and write research papers", "Design experiments", "Prototype novel models"],
        "skills": ["Advanced mathematics", "Deep learning", "Research methodology", "Programming"],
        "subjects": ["Mathematics", "Computer Science", "Physics"],
        "education_pathway": "Bachelor's then Master's/PhD in Computer Science, Machine Learning or related fields.",
        "work_environment": "Lab / University / Office", "salary_range": "High", "outlook": "Excellent",
        "related": ["data-scientist", "software-engineer"],
        "profile_weights": {"analytical_thinking": 0.95, "numerical_reasoning": 0.95, "problem_solving": 0.9,
                             "technology": 0.85, "openness": 0.85},
    },
    {
        "slug": "doctor", "name": "Medical Doctor", "category": "Healthcare",
        "description": "Doctors diagnose and treat illness, caring for patients' physical and mental health.",
        "responsibilities": ["Diagnose conditions", "Treat patients", "Communicate with patients and families"],
        "skills": ["Biology knowledge", "Empathy", "Decision making", "Communication"],
        "subjects": ["Biology", "Chemistry", "Physics"],
        "education_pathway": "Medical degree (MBBS/MD) followed by internship and specialisation.",
        "work_environment": "Hospital / Clinic", "salary_range": "High", "outlook": "Strong — stable demand",
        "related": ["nurse", "psychologist", "pharmacist"],
        "profile_weights": {"healthcare": 0.95, "helping_others": 0.9, "conscientiousness": 0.9,
                             "analytical_thinking": 0.75, "security": 0.6},
    },
    {
        "slug": "nurse", "name": "Registered Nurse", "category": "Healthcare",
        "description": "Nurses provide hands-on patient care, support treatment plans and are the backbone of healthcare teams.",
        "responsibilities": ["Monitor patients", "Administer care and medication", "Support doctors and families"],
        "skills": ["Patient care", "Empathy", "Teamwork", "Attention to detail"],
        "subjects": ["Biology", "Chemistry"],
        "education_pathway": "Diploma or Bachelor's in Nursing followed by registration.",
        "work_environment": "Hospital / Clinic", "salary_range": "Medium", "outlook": "Strong",
        "related": ["doctor", "psychologist"],
        "profile_weights": {"healthcare": 0.9, "helping_others": 0.95, "teamwork": 0.8,
                             "conscientiousness": 0.8, "security": 0.6},
    },
    {
        "slug": "psychologist", "name": "Psychologist", "category": "Healthcare",
        "description": "Psychologists study behaviour and the mind, helping people improve their mental well-being.",
        "responsibilities": ["Assess clients", "Provide therapy or counselling", "Conduct behavioural research"],
        "skills": ["Empathy", "Active listening", "Research", "Communication"],
        "subjects": ["Psychology", "Biology"],
        "education_pathway": "Bachelor's then Master's/Doctorate in Psychology with supervised practice.",
        "work_environment": "Clinic / Private practice", "salary_range": "Medium", "outlook": "Strong",
        "related": ["doctor", "nurse", "teacher"],
        "profile_weights": {"helping_others": 0.95, "healthcare": 0.6, "openness": 0.75,
                             "analytical_thinking": 0.7, "extraversion": 0.6},
    },
    {
        "slug": "entrepreneur", "name": "Entrepreneur / Founder", "category": "Business",
        "description": "Entrepreneurs identify opportunities and build businesses, taking on risk to create new value.",
        "responsibilities": ["Spot market opportunities", "Build and lead teams", "Raise funding and grow ventures"],
        "skills": ["Risk taking", "Leadership", "Selling", "Resilience"],
        "subjects": ["Business Studies", "Economics", "Mathematics"],
        "education_pathway": "No fixed path — business degrees help, but experience and initiative matter most.",
        "work_environment": "Dynamic / Varied", "salary_range": "Variable", "outlook": "High potential, high risk",
        "related": ["product-manager", "business-analyst", "marketing-manager"],
        "profile_weights": {"entrepreneurship": 0.98, "leadership": 0.85, "business": 0.85,
                             "openness": 0.75, "income": 0.7, "security": 0.2},
    },
    {
        "slug": "business-analyst", "name": "Business Analyst", "category": "Business",
        "description": "Business analysts bridge data and decisions, helping organisations work smarter and more profitably.",
        "responsibilities": ["Analyse business processes", "Interpret data", "Recommend improvements"],
        "skills": ["Analytical thinking", "Communication", "Data literacy", "Domain knowledge"],
        "subjects": ["Economics", "Mathematics", "Business Studies"],
        "education_pathway": "Bachelor's in Business, Economics, or related analytical fields.",
        "work_environment": "Office", "salary_range": "Medium-High", "outlook": "Strong",
        "related": ["data-scientist", "product-manager", "entrepreneur"],
        "profile_weights": {"analytical_thinking": 0.85, "business": 0.85, "numerical_reasoning": 0.75,
                             "teamwork": 0.65, "conscientiousness": 0.7},
    },
    {
        "slug": "product-manager", "name": "Product Manager", "category": "Business",
        "description": "Product managers decide what to build and why, coordinating design, engineering and business.",
        "responsibilities": ["Define product strategy", "Prioritise features", "Coordinate cross-functional teams"],
        "skills": ["Leadership", "Communication", "Analytical thinking", "Empathy for users"],
        "subjects": ["Business Studies", "Computer Science", "Economics"],
        "education_pathway": "Varied — business or technical degrees plus product experience.",
        "work_environment": "Office / Remote", "salary_range": "High", "outlook": "Strong",
        "related": ["software-engineer", "business-analyst", "entrepreneur"],
        "profile_weights": {"leadership": 0.85, "business": 0.8, "technology": 0.6,
                             "extraversion": 0.65, "analytical_thinking": 0.7, "teamwork": 0.7},
    },
    {
        "slug": "marketing-manager", "name": "Marketing Manager", "category": "Business",
        "description": "Marketing managers shape how products reach and resonate with audiences.",
        "responsibilities": ["Plan campaigns", "Understand customers", "Manage brand and growth"],
        "skills": ["Creativity", "Communication", "Data analysis", "Persuasion"],
        "subjects": ["Business Studies", "Economics", "English"],
        "education_pathway": "Bachelor's in Marketing, Business or Communications.",
        "work_environment": "Office", "salary_range": "Medium-High", "outlook": "Stable",
        "related": ["entrepreneur", "product-manager"],
        "profile_weights": {"business": 0.85, "arts": 0.6, "extraversion": 0.75,
                             "openness": 0.7, "leadership": 0.6},
    },
    {
        "slug": "graphic-designer", "name": "Graphic / UX Designer", "category": "Arts & Design",
        "description": "Designers craft visuals and experiences that are both beautiful and usable.",
        "responsibilities": ["Design interfaces and graphics", "Prototype ideas", "Collaborate with teams"],
        "skills": ["Creativity", "Visual design", "Empathy", "Tools (Figma, etc.)"],
        "subjects": ["Art", "Computer Science", "Design"],
        "education_pathway": "Diploma or Bachelor's in Design, plus a strong portfolio.",
        "work_environment": "Studio / Remote", "salary_range": "Medium", "outlook": "Strong",
        "related": ["product-manager", "software-engineer", "marketing-manager"],
        "profile_weights": {"arts": 0.95, "openness": 0.85, "technology": 0.55,
                             "teamwork": 0.6, "conscientiousness": 0.6},
    },
    {
        "slug": "teacher", "name": "Teacher / Educator", "category": "Education",
        "description": "Teachers shape the next generation, helping students learn and grow.",
        "responsibilities": ["Plan and deliver lessons", "Mentor students", "Assess progress"],
        "skills": ["Communication", "Patience", "Subject expertise", "Empathy"],
        "subjects": ["Any subject specialism", "Education"],
        "education_pathway": "Bachelor's in the subject plus a teaching qualification.",
        "work_environment": "School / College", "salary_range": "Medium", "outlook": "Stable",
        "related": ["psychologist", "nurse"],
        "profile_weights": {"helping_others": 0.9, "extraversion": 0.65, "conscientiousness": 0.75,
                             "openness": 0.6, "security": 0.6},
    },
    {
        "slug": "civil-engineer", "name": "Civil Engineer", "category": "Engineering",
        "description": "Civil engineers design and build the infrastructure of society — roads, bridges and buildings.",
        "responsibilities": ["Design structures", "Manage construction projects", "Ensure safety standards"],
        "skills": ["Mathematics", "Problem solving", "Project management", "Attention to detail"],
        "subjects": ["Mathematics", "Physics"],
        "education_pathway": "Bachelor's in Civil Engineering followed by professional licensing.",
        "work_environment": "Office / Site", "salary_range": "Medium-High", "outlook": "Stable",
        "related": ["software-engineer", "business-analyst"],
        "profile_weights": {"numerical_reasoning": 0.85, "problem_solving": 0.85, "analytical_thinking": 0.8,
                             "conscientiousness": 0.8, "security": 0.6},
    },
    {
        "slug": "accountant", "name": "Accountant / Financial Analyst", "category": "Finance",
        "description": "Accountants and financial analysts manage and interpret the numbers that keep organisations healthy.",
        "responsibilities": ["Prepare financial reports", "Analyse budgets", "Ensure compliance"],
        "skills": ["Numerical reasoning", "Attention to detail", "Integrity", "Analysis"],
        "subjects": ["Mathematics", "Economics", "Accounting"],
        "education_pathway": "Bachelor's in Accounting or Finance plus professional certification.",
        "work_environment": "Office", "salary_range": "Medium-High", "outlook": "Stable",
        "related": ["business-analyst", "entrepreneur"],
        "profile_weights": {"numerical_reasoning": 0.95, "conscientiousness": 0.9, "analytical_thinking": 0.8,
                             "security": 0.75, "income": 0.6},
    },
]
