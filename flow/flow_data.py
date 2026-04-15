# flow/flow_data.py

FLOW = {
    # -----------------------------
    # START / ELIGIBILITY
    # -----------------------------
    "start": {
        "type": "question",
        "title": "Eligibility Checker 1",
        "text": "Did you have the right to work in the UK confirmed?",
        "options": [
            {"label": "Yes", "next": "eligibility_2"},
            {"label": "No", "next": "overseas_candidate_statement"},
        ],
    },

    "eligibility_2": {
        "type": "question",
        "title": "Eligibility Checker 2",
        "text": "Did you study for your school and further education qualifications in the UK?",
        "options": [
            {"label": "Yes", "next": "domestic_eligibility_1"},
            {"label": "No", "next": "overseas_eligibility_3"},
        ],
    },

    "overseas_candidate_statement": {
        "type": "statement",
        "title": "Overseas Candidate Statement",
        "text": (
            "Candidates applying for Teacher Training with GLF Teacher Training must have the right "
            "to work in the UK confirmed BEFORE they apply for our course. We are afraid we cannot "
            "continue with your application until this is confirmed.\n\n"
            "Please note that we do not sponsor Tier 4 or Tier 2 visas.\n\n"
            "From 01/01/21, the new points-based immigration system will apply to trainee teachers "
            "from overseas, including EU, other EEA, and Swiss nationals.\n\n"
            "Following the UK's departure from the EU, it has also been confirmed that most EU, "
            "other EEA and Swiss nationals will not be eligible for support from Student Finance "
            "for courses starting from September 2021.\n\n"
            "For more information, contact DfE for overseas candidates and book a 1:1 support meeting:\n"
            "https://getintoteaching.education.gov.uk/\n\n"
            "We wish you well as you take your next steps into teacher training."
        ),
        "options": [
            {"label": "Start over", "next": "start"},
        ],
    },

    # -----------------------------
    # OVERSEAS PATH
    # -----------------------------
    "overseas_eligibility_3": {
        "type": "question",
        "title": "Overseas Eligibility Checker 3",
        "text": (
            "Do you have a recognised statement of comparability from ENIC/NARIC to show that you have "
            "at least a grade C or 4 in Maths and English for both Primary and Secondary teacher training routes, "
            "and a Grade C/4 in Science for those candidates who want to teach on a Primary route?"
        ),
        "options": [
            {"label": "Yes", "next": "overseas_eligibility_4"},
            {"label": "No, I do not have a comparability statement yet", "next": "overseas_3_no_statement"},
            {"label": "No, I have a comparability statement but it does not show the required GCSE equivalence", "next": "overseas_3_not_enough"},
        ],
    },

    "overseas_3_no_statement": {
        "type": "statement",
        "title": "Next steps: ENIC Statement of Comparability",
        "text": (
            "Suggested next step:\n"
            "• Contact ENIC with evidence of your overseas high school qualifications to gain a Statement of Comparability "
            "(a certificate that shows how international qualifications compare to the UK education system).\n\n"
            "Please return to GLF Teacher Training once you have this, showing you have the equivalent of:\n"
            "• Grade C/4 in English and Maths (Primary & Secondary routes)\n"
            "• Grade C/4 in Science (Primary route only)\n\n"
            "There is a cost for this service which you will need to fund.\n"
            "ENIC link: https://www.enic.org.uk/individuals/statement-of-comparability"
        ),
        "options": [
            {"label": "Continue", "next": "overseas_eligibility_4"},
            {"label": "Start over", "next": "start"},
        ],
    },

    "overseas_3_not_enough": {
        "type": "statement",
        "title": "Next steps: Equivalency Tests (Overseas)",
        "text": (
            "Suggested next step:\n"
            "• Apply for and pass an equivalency test in English and Maths (Primary & Secondary routes) and Science "
            "(Primary route only), or all three where required.\n\n"
            "GLF Teacher Training will accept equivalency tests from recognised providers taken within the last 3 years, "
            "but you will need to provide an original certificate.\n\n"
            "The DfE states that qualifications in key and functional skills at level 2 are not equivalent to GCSEs "
            "in terms of content.\n\n"
            "Recommended providers:\n"
            "• Equivalency Testing: https://www.equivalencytesting.com/\n"
            "• A Star Equivalency: https://astarequivalency.co.uk/\n"
            "• Birmingham City University: https://www.bcu.ac.uk/education-and-social-work/initial-teacher-training/gcse-equivalency-test/gcse-equivalency-tests-non-bcu-applicants\n\n"
            "If you need more support, you can email your ENIC comparability statement to our GLF ITT admin team for checking:\n"
            "info@glftt.org\n\n"
            "You may also find our weekly online information events helpful:\n"
            "https://www.glftt.org/19/events"
        ),
        "options": [
            {"label": "Continue", "next": "overseas_eligibility_4"},
            {"label": "Start over", "next": "start"},
        ],
    },

    "overseas_eligibility_4": {
        "type": "question",
        "title": "Overseas Eligibility Checker 4",
        "text": (
            "Do you have a recognised statement of comparability from ENIC/NARIC to show that you have an undergraduate degree "
            "equivalent to a UK bachelor’s degree with honours? Your comparability statement should show that your overseas degree "
            "is comparable to a degree at a 2:2 or higher.\n\n"
            "To meet the eligibility criteria, you need a first degree (comprising at least 300 HE credits of which at least 60 must "
            "be at level 6 of the QCF)."
        ),
        "options": [
            {"label": "Yes", "next": "overseas_eligibility_5"},
            {"label": "No, I do not have a comparability statement (degree-level) yet", "next": "overseas_4_no_statement"},
            {"label": "No, I have a comparability statement but it does not show a degree equivalent to 2:2+ honours", "next": "overseas_4_not_enough"},
        ],
    },

    "overseas_4_no_statement": {
        "type": "statement",
        "title": "Next steps: ENIC Degree Comparability",
        "text": (
            "Suggested next step:\n"
            "• Contact ENIC with evidence of your overseas degree-level qualifications to gain a Statement of Comparability.\n\n"
            "Please return to GLF Teacher Training once you have this, showing that you have an undergraduate degree equivalent to a UK "
            "bachelor’s degree with honours (comparable to a degree at a 2:2 or higher).\n\n"
            "ENIC link: https://www.enic.org.uk/individuals/statement-of-comparability"
        ),
        "options": [
            {"label": "Continue", "next": "overseas_eligibility_5"},
            {"label": "Start over", "next": "start"},
        ],
    },

    "overseas_4_not_enough": {
        "type": "statement",
        "title": "Next steps: Degree options (Overseas)",
        "text": (
            "Suggested next step:\n"
            "• If you are unsure, send your comparability statement to our GLF ITT admin team for checking and further support:\n"
            "info@glftt.org\n\n"
            "You may then consider one of the following options:\n\n"
            "1) If your degree is equivalent to a foundation degree (Level 5), you may be able to do a ‘top up’ one-year course to gain a "
            "BA Honours degree:\n"
            "https://educationforyou.co.uk/articles/37\n\n"
            "2) If your degree is not equivalent to a BA Honours or a Foundation degree:\n"
            "Explore degree-based routes into teaching through a Teacher Degree Apprenticeship, or work as a Teaching Assistant while completing "
            "a BA Honours Degree via distance learning:\n"
            "https://www.glftt.org/16/routes-into-teaching\n\n"
            "3) Study a UK-based degree from scratch (Education Studies or a specific Secondary subject). UCAS lists all undergraduate courses:\n"
            "https://www.ucas.com\n\n"
            "University guides you may find useful as a starting point:\n"
            "• Complete University Guide: https://www.thecompleteuniversityguide.co.uk/courses/search/undergraduate/education\n"
            "• Uni Compare: https://universitycompare.com/courses/degrees/undergraduate/education-studies\n"
            "• Educations.com: https://www.educations.com/\n\n"
            "For more support with the right option for you, contact:\n"
            "info@glftt.org"
        ),
        "options": [
            {"label": "Finish", "next": "closing_statement_1"},
            {"label": "Start over", "next": "start"},
        ],
    },

    "overseas_eligibility_5": {
        "type": "question",
        "title": "Overseas Eligibility Check 5",
        "text": (
            "It appears from the answers you have provided that you have:\n"
            "• the right to work in the UK\n"
            "• a statement of comparability from ENIC to show you have the equivalent of Grade C/4 in English and Maths, and Grade C/4 in Science "
            "(for primary candidates only)\n"
            "• an equivalent to a BA Honours Degree\n\n"
            "Would you like to continue learning more about the teacher training routes available to you?"
        ),
        "options": [
            {"label": "Yes", "next": "routes_into_teaching_1"},
            {"label": "No", "next": "closing_statement_2"},
        ],
    },

    # -----------------------------
    # DOMESTIC PATH
    # -----------------------------
    "domestic_eligibility_1": {
        "type": "question",
        "title": "Domestic Candidates Eligibility Checker 1",
        "text": (
            "Do you have at least a grade C or 4 in Maths and English for both Primary and Secondary teacher training routes, "
            "and a Grade C/4 in Science for those candidates who want to teach on a Primary route?"
        ),
        "options": [
            {"label": "Yes", "next": "domestic_eligibility_2"},
            {"label": "No (missing GCSEs / equivalents)", "next": "domestic_1_no_gcse"},
        ],
    },

    "domestic_1_no_gcse": {
        "type": "statement",
        "title": "Next steps: Equivalency Tests (Domestic)",
        "text": (
            "Suggested next step:\n"
            "• Apply for and pass an equivalency test in English and Maths (Primary & Secondary routes) and Science (Primary route only), "
            "or all three where required.\n\n"
            "GLF Teacher Training will accept equivalency tests from recognised providers taken within the last 3 years, but you will need to "
            "provide an original certificate.\n\n"
            "The DfE states that qualifications in key and functional skills at level 2 are not equivalent to GCSEs in terms of content.\n\n"
            "Recommended providers:\n"
            "• Equivalency Testing: https://www.equivalencytesting.com/\n"
            "• A Star Equivalency: https://astarequivalency.co.uk/\n"
            "• Birmingham City University: https://www.bcu.ac.uk/education-and-social-work/initial-teacher-training/gcse-equivalency-test/gcse-equivalency-tests-non-bcu-applicants\n\n"
            "These equivalency tests will need to be funded by the candidate."
        ),
        "options": [
            {"label": "Continue", "next": "domestic_eligibility_2"},
            {"label": "Start over", "next": "start"},
        ],
    },

    "domestic_eligibility_2": {
        "type": "question",
        "title": "Domestic Eligibility Checker 2",
        "text": (
            "Do you have an undergraduate bachelor’s degree with honours - 2:2 or above?\n\n"
            "To meet the eligibility criteria, you need a first degree (comprising at least 300 HE credits of which at least 60 must be at level 6 of the QCF)."
        ),
        "options": [
            {"label": "Yes", "next": "routes_into_teaching_1"},
            {"label": "No (not sure / not 2:2+ honours)", "next": "domestic_2_no_degree"},
        ],
    },

    "domestic_2_no_degree": {
        "type": "statement",
        "title": "Next steps: Degree options (Domestic)",
        "text": (
            "Suggested next step:\n"
            "• If you are not sure, send your Degree certificate to our GLF ITT admin team for checking and further support:\n"
            "info@glftt.org\n\n"
            "You may then consider one of the following options:\n\n"
            "1) If your degree is not BA Honours level but is a foundation degree (Level 5), you may be able to do a ‘top up’ one-year course to gain a "
            "BA Honours degree:\n"
            "https://educationforyou.co.uk/articles/37\n\n"
            "2) If your degree is not a BA Honours or a Foundation degree:\n"
            "Explore degree-based routes into teaching through a Teacher Degree Apprenticeship, or work as a Teaching Assistant while completing a BA Honours "
            "Degree via distance learning:\n"
            "https://www.glftt.org/16/routes-into-teaching\n\n"
            "3) Study a UK-based degree from scratch (Education Studies or a specific Secondary subject). UCAS lists all undergraduate degree courses:\n"
            "https://www.ucas.com\n\n"
            "University guides you may find useful as a starting point:\n"
            "• Complete University Guide: https://www.thecompleteuniversityguide.co.uk/courses/search/undergraduate/education\n"
            "• Uni Compare: https://universitycompare.com/courses/degrees/undergraduate/education-studies\n"
            "• Educations.com: https://www.educations.com/"
        ),
        "options": [
            {"label": "Finish", "next": "closing_statement_3"},
            {"label": "Start over", "next": "start"},
        ],
    },

    # -----------------------------
    # ROUTES INTO TEACHING
    # -----------------------------
    "routes_into_teaching_1": {
        "type": "question",
        "title": "Routes into Teaching 1",
        "text": "Do you want to train while earning a salary?",
        "options": [
            {"label": "Yes", "next": "routes_into_teaching_salary_info"},
            {"label": "No", "next": "routes_into_teaching_fee_info"},
        ],
    },

    "routes_into_teaching_salary_info": {
        "type": "statement",
        "title": "Routes into Teaching",
        "text": (
            "GLF Teacher Training has three employment-based routes into teaching. "
            "All these routes have specific eligibility requirements regarding school experience and require a school willing to support/employ you on these routes."
        ),
        "options": [
            {"label": "Continue", "next": "employment_routes_1"},
            {"label": "Back", "next": "routes_into_teaching_1"},
        ],
    },

    "routes_into_teaching_fee_info": {
        "type": "statement",
        "title": "Routes into Teaching",
        "text": (
            "GLF Teacher Training offers a fee-funded route into teaching that does not require a school employment-based contract "
            "and allows trainees to take on teaching classes in manageable milestones."
        ),
        "options": [
            {"label": "Continue", "next": "fee_paying_route"},
            {"label": "Back", "next": "routes_into_teaching_1"},
        ],
    },

    "employment_routes_1": {
        "type": "question",
        "title": "Employment-Based Routes 1",
        "text": "Do you have classroom experience?",
        "options": [
            {"label": "Yes", "next": "employment_routes_2"},
            {"label": "No", "next": "employment_routes_no_experience"},
        ],
    },

    "employment_routes_no_experience": {
        "type": "statement",
        "title": "Employment-Based Routes",
        "text": (
            "It is unlikely that schools will pay a salary and potentially training fees for candidates with no school experience. "
            "You would be more suited to our fee-paying route."
        ),
        "options": [
            {"label": "Continue", "next": "fee_paying_route"},
            {"label": "Back", "next": "employment_routes_1"},
        ],
    },

    "employment_routes_2": {
        "type": "statement",
        "title": "Employment-Based Routes 2",
        "text": (
            "We have outlined the details and eligibility for each of GLF’s employment-based routes below.\n\n"
            "Salaried Route\n"
            "Salaried routes are for qualifying candidates with at least a year of school experience. This means candidates will not have to pay tuition fees "
            "and will receive a salary while training to become qualified teachers. Candidates will become an unqualified teacher employed by a school for the "
            "duration of the training programme. This route offers a QTS paid by the schools and gives a PGCE option at an additional cost to the candidate. "
            "The University of Brighton accredits the PGCE, with learning that is integral to the course and supported by the candidate's course tutor. "
            "Candidates will be expected to have some of their own classes independently from day one, with some time out of school for training. These courses "
            "are in high demand and very competitive, so it’s essential to apply as soon as possible if you’re eligible. Candidates will need a school willing to "
            "employ them, pay their salary and pay their training fees to the training provider. The length of this course is approximately 10 months.\n\n"
            "Postgraduate Teacher Apprenticeship Route\n"
            "Postgraduate Teacher Apprenticeships in Primary and a range of Secondary Subjects (for qualifying candidates). This route pays candidates' training fees "
            "via the organisation's apprenticeship training levy pot, and the candidate receives a salary while training. Candidates will be Apprentice employees in "
            "a school for the duration of their apprenticeship. This route offers a QTS paid by the Trust and gives a PGCE option at an additional cost to the candidate. "
            "The University of Brighton accredits the PGCE, with learning that is integral to the course and supported by a course tutor. Candidates may be expected to "
            "have some of their own classes independently from day one, with 20% of their time out of school for training. Candidates will need a school willing to employ "
            "them, pay their salary, and have GLF, as a Trust, pay their training fees. To access the DFE training levy, candidates must have a British Passport and have "
            "been in the country for three years. The length of this course is approximately 10 months.\n\n"
            "Assessment Only Route\n"
            "This route is for qualifying candidates with significant school experience. Candidates can only take the assessment route if they already meet the standards for "
            "qualified teacher status (QTS), and they do not need any further training or time to get the required evidence to pass QTS. Candidates must be ready to meet the "
            "Teachers’ Standards. Candidates must currently be teaching in a school, have worked in two or more school settings and across two age phases to meet the ITT entry criteria.\n\n"
            "Candidates must show they can meet the Teachers’ Standards across two age phases, encompassing a range of assessments and teaching and learning approaches. "
            "Candidates’ experience in assessment, teaching, and planning must take into account both physical and developmental ages.\n\n"
            "Candidates must demonstrate they have sufficient and appropriate experience in their chosen age phases and should undertake a second school experience for at least 6 weeks "
            "in a mainstream setting to support their evidence for the Teachers’ Standards.\n\n"
            "Candidates should teach a minimum of 50% and a maximum of 80% of an experienced teacher’s timetable for the duration of the assessment period.\n\n"
            "Applicants must have the opportunity to work with adults other than teachers and pupils across the ability range within the school, and in the school's pastoral setting. "
            "Secondary applicants’ timetables are expected to have 80% of their teaching commitment to their specialist subject.\n\n"
            "Candidates will undergo a series of assessments and provide a portfolio, and this programme takes up to 12 weeks. All candidates taking the assessment-only route will require "
            "an initial meeting to ensure they qualify and will need the employing school's support.\n\n"
            "The cost of the Assessment Only Assessment programme will need to be paid by the candidate or employing school."
        ),
        "options": [
            {"label": "Continue", "next": "subject_phase_1"},
            {"label": "Back to Routes", "next": "routes_into_teaching_1"},
        ],
    },

    "fee_paying_route": {
        "type": "statement",
        "title": "Fee-paying Routes into Teaching",
        "text": (
            "Fee-paying routes: Some teacher training courses are fee-funded. This means candidates must pay tuition fees and will not earn a salary while they train.\n\n"
            "There are ways to fund training to support candidates, such as tuition fees and maintenance loans. Find out more about student and maintenance loans:\n"
            "https://getintoteaching.education.gov.uk/landing/how-to-fund-your-teacher-training\n\n"
            "Secondary candidates may also be eligible for a Department for Education tax-free bursary or scholarship (depending on the subject). Details of subject bursaries and scholarships can be found here:\n"
            "https://getintoteaching.education.gov.uk/landing/how-to-fund-your-teacher-training\n\n"
            "For fee-funded routes, the bursary is paid directly to the candidate; for employment-based routes, it is paid to the employing school to offset salary costs.\n\n"
            "This route comes with a QTS and PGCE option. The University of Brighton accredits the PGCE, with learning that is integral to your course and supported by your course tutors. "
            "The length of this course is approximately 10 months.\n\n"
            "Trainees on this route will be supernumerary and will support class teachers, taking on more responsibility for class teaching when the candidate is ready and in line with expected "
            "teaching milestones per term."
        ),
        "options": [
            {"label": "Continue", "next": "subject_phase_1"},
            {"label": "Back to Routes", "next": "routes_into_teaching_1"},
        ],
    },

    # -----------------------------
    # SUBJECT & PHASE
    # -----------------------------
    "subject_phase_1": {
        "type": "question",
        "title": "Subject & Phase 1",
        "text": "Do you want to teach Primary or Secondary?",
        "options": [
            {"label": "Primary", "next": "subject_phase_2"},
            {"label": "Secondary", "next": "subject_phase_3"},
        ],
    },

    "subject_phase_2": {
        "type": "question",
        "title": "Subject & Phase 2",
        "text": "Do you want to teach Primary at ages 3–7 or 7–11?",
        "options": [
            {"label": "Primary ages 3–7", "next": "flexibility"},
            {"label": "Primary ages 7–11", "next": "flexibility"},
        ],
    },

    "subject_phase_3": {
        "type": "question",
        "title": "Subject & Phase 3",
        "text": (
            "Do you want to teach in Secondary Shortage Subjects or other Secondary subjects?\n\n"
            "Shortage Subjects are those with a bursary attached. For 26–27, this is Biology, Chemistry, Computing, Design and Technology, Geography, Languages, "
            "Maths and Physics. Bursary amounts can be found here:\n"
            "https://getintoteaching.education.gov.uk/landing/how-to-fund-your-teacher-training\n\n"
            "For fee-funded routes, the bursary is paid directly to the candidate; for employment-based routes, it is paid to the employing school to offset salary costs.\n\n"
            "Non-Shortage Secondary Subjects are any other subjects and do not come with any bursary. Candidates can still apply for a Student and Maintenance loan to cover training costs."
        ),
        "options": [
            {"label": "Secondary Shortage Subjects", "next": "flexibility"},
            {"label": "Secondary Non-Shortage Subjects", "next": "flexibility"},
        ],
    },

    # -----------------------------
    # FLEXIBILITY
    # -----------------------------
    "flexibility": {
        "type": "question",
        "title": "Flexibility",
        "text": "Do you wish to train flexibly on GLF’s flexible training route?",
        "options": [
            {"label": "Yes", "next": "flexible_training_route"},
            {"label": "No", "next": "training_locations"},
        ],
    },

    "flexible_training_route": {
        "type": "statement",
        "title": "Flexible Training Route",
        "text": (
            "Flexible training routes: GLF Teacher Training offer this route in Secondary shortage subjects, in a range of subjects. "
            "We also offer this for some eligible candidates in Primary and non-shortage Secondary subjects.\n\n"
            "This is a flexible way for postgraduate candidates to train to teach. This training route allows candidates to train over five terms, supporting them in managing "
            "work/life balance, continuing other work/studies, or building towards a part-time teaching career.\n\n"
            "This route is available only as a QTS option."
        ),
        "options": [
            {"label": "Continue", "next": "training_locations"},
            {"label": "Back", "next": "flexibility"},
        ],
    },

    # -----------------------------
    # TRAINING LOCATIONS & NEXT STEPS
    # -----------------------------
    "training_locations": {
        "type": "question",
        "title": "Training Locations",
        "text": (
            "We offer placement schools across the southeast from Surrey, Croydon, Oxfordshire, Reading, West Sussex, Wokingham and Hampshire to meet candidates' needs. "
            "You will spend 80% of your time at your placement school and 20% training at one of our training venues, learning from our experts.\n\n"
            "Would you prefer our Oxford/Reading training venue or our Banstead in Surrey venue?"
        ),
        "options": [
            {"label": "Oxford/Reading", "next": "next_steps_1"},
            {"label": "Banstead, Surrey", "next": "next_steps_1"},
        ],
    },

    "next_steps_1": {
        "type": "question",
        "title": "Next Steps 1",
        "text": (
            "We offer the chance for candidates to visit one of our GLF Teacher Training Schools for a School Experience visit. "
            "This can help you decide on the subject/phase that is right for you and help you meet the teachers and children you would be working with.\n\n"
            "Would you like us to set this up for you?"
        ),
        "options": [
            {"label": "I would like to attend a School Experience Visit", "next": "next_steps_2"},
            {"label": "Not at this stage, but I would like to be sent more information", "next": "next_steps_3"},
        ],
    },

    "next_steps_2": {
        "type": "statement",
        "title": "Next Steps 2",
        "text": (
            "Please complete our enquiry form, noting in question 14 where you would like school experience.\n\n"
            "Alternatively, contact us and we can set this up for you:\n"
            "info@glftt.org"
        ),
        "options": [
            {"label": "Continue", "next": "next_steps_3"},
        ],
    },

    "next_steps_3": {
        "type": "question",
        "title": "Next Steps 3",
        "text": (
            "We offer a range of engagement events to promote what GLF Teacher Training has to offer, including a weekly online Coffee and Chat "
            "and regional face-to-face recruitment events in our schools.\n\n"
            "Would you like to attend?"
        ),
        "options": [
            {"label": "I would like to attend an event", "next": "events"},
            {"label": "I do not want to attend an event, but I would like to be sent more information", "next": "contact_us"},
        ],
    },

    "events": {
        "type": "statement",
        "title": "GLF Teacher Training Events",
        "text": (
            "Please visit our events page and sign up for one of our events:\n"
            "https://www.glftt.org/19/events"
        ),
        "options": [
            {"label": "Finish", "next": "closing_statement_4"},
            {"label": "Back", "next": "next_steps_3"},
        ],
    },

    "contact_us": {
        "type": "statement",
        "title": "Contact GLF Teacher Training",
        "text": (
            "Contact us at GLF Teacher Training for us to send you more information.\n\n"
            "Please email us at: info@glftt.org"
        ),
        "options": [
            {"label": "Finish", "next": "closing_statement_4"},
            {"label": "Back", "next": "next_steps_3"},
        ],
    },

    # -----------------------------
    # CLOSING STATEMENTS
    # -----------------------------
    "closing_statement_1": {
        "type": "statement",
        "title": "Closing Statement 1",
        "text": (
            "Thanks for your interest in teacher training with GLF Teacher Training, and we wish you luck with your next steps. "
            "We look forward to hearing from you once you have the necessary documentation/qualifications.\n\n"
            "Once you have your degree, please come back to GLF Teacher Training, and we can support you with the next steps to gain QTS.\n\n"
            "Contact us for support:\n"
            "info@glftt.org"
        ),
        "options": [
            {"label": "Start over", "next": "start"},
        ],
    },

    "closing_statement_2": {
        "type": "statement",
        "title": "Closing Statement 2",
        "text": (
            "Thanks for your interest in teacher training with GLF Teacher Training. We look forward to hearing from you once you are ready to learn more "
            "or apply for a teacher training route.\n\n"
            "You may find coming to one of our weekly online information events useful to find out more:\n"
            "https://www.glftt.org/19/events\n\n"
            "You can also contact us on our enquiry form to find out more:\n"
            "https://forms.office.com/pages/responsepage.aspx?id=A0fOQITwQUy0ICoaMUBRJ6y1g0Xjm71LjaZx0sst-dFUQTZQUFhXU1ZFWUk5TVhXV05BQUNXV0c0QiQlQCN0PWcu&route=shorturl"
        ),
        "options": [
            {"label": "Start over", "next": "start"},
        ],
    },

    "closing_statement_3": {
        "type": "statement",
        "title": "Closing Statement 3",
        "text": (
            "Thanks for your interest in teacher training with GLF Teacher Training, and we wish you luck with your next steps. "
            "We look forward to hearing from you once you have the necessary documentation/qualifications.\n\n"
            "Once you have your degree, please come back to GLF Teacher Training, and we would be happy to support you to gain QTS at this point."
        ),
        "options": [
            {"label": "Start over", "next": "start"},
        ],
    },

    "closing_statement_4": {
        "type": "statement",
        "title": "Closing Statement 4",
        "text": (
            "Thanks for your interest in teacher training with GLF Teacher Training. GLF Schools, as a Trust, is passionate about training the next generation "
            "of teachers for our schools.\n\n"
            "Please visit GLF’s Teacher Training Website:\n"
            "https://www.glftt.org\n\n"
            "Or fill in our enquiry form and we will be in touch:\n"
            "https://forms.office.com/pages/responsepage.aspx?id=A0fOQITwQUy0ICoaMUBRJ6y1g0Xjm71LjaZx0sst-dFUQTZQUFhXU1ZFWUk5TVhXV05BQUNXV0c0QiQlQCN0PWcu&route=shorturl\n\n"
            "GLF Teacher Training has a lot to offer:\n"
            "• Whether you are considering joining as a graduate straight from university, moving into teaching from a school support role, or changing careers, "
            "there is a training route at GLF for you.\n"
            "• Teaching is a rewarding career like no other. Although it can be challenging at times, you always know that each day you go to work, you make a difference.\n"
            "• No two days are the same; you are guaranteed to work as part of a team with whom you can laugh and learn.\n"
            "• You can make a difference to the lives of young people as you see them learn, grow, and flourish.\n"
            "• If you are passionate about your subject or phase of education, put this to work and inspire the next generation.\n"
            "• Teaching is a career with financial support to train, a competitive starting salary, progression opportunities, and a generous pension.\n"
            "• There are flexible training routes and part-time teaching options available. Term-time contracts can support candidates in managing work and family life.\n"
            "• Training to teach within one of GLF Trust Schools offers excellent career progression opportunities.\n"
            "• Your continued professional development matters to us. We will support you throughout your teacher training, your first teaching position as an early career teacher, and beyond.\n\n"
            "We look forward to hearing from you.\n\n"
            "Every Teacher Shapes a Life."
        ),
        "options": [
            {"label": "Start over", "next": "start"},
        ],
    },
}
