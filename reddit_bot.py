#!/usr/bin/env python3
"""
BITSAT Reddit Bot - No_Attendance_Bot
A sassy, dark humor bot for r/bitsatards that provides BITSAT cutoff data
with unhinged commentary and motivational roasting.
"""

import praw
import random
import time
import logging
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BITSATBot:
    def __init__(self):
        """Initialize the BITSAT Reddit Bot"""
        self.reddit = None
        self.subreddit = None
        self.processed_comments = set()
        
        # Dynamic response components for generating unique responses
        self.dark_starters = [
            "Arre yaar", "Bhai dekh", "Suno", "Arey", "Oye", "Beta", "Dost", "Yaar", "Bro", "Listen up"
        ]

        self.motivational_dark = [
            "life's roasting you slowly", "universe ka twisted sense of humor", "reality's slapping you awake",
            "harsh truth delivery service", "bitter pill pharmacy", "wake up call from hell", "plot twist from satan",
            "character assassination arc", "villain backstory unlocked", "trauma bonding with destiny",
            "existential crisis speedrun", "mental breakdown any% category", "suffering simulator level 100"
        ]

        self.hinglish_vibes = [
            "matlab", "basically", "obviously", "clearly", "apparently", "technically",
            "realistically", "honestly", "frankly", "seriously", "literally", "actually", "bro"
        ]

        self.cool_endings = [
            "but you're built different", "time to become the villain", "embrace your dark era",
            "plot armor loading...", "main character syndrome activated", "sigma grindset unlocked",
            "no cap fr fr", "periodt bestie", "that's the brutal tea", "it is what it is king",
            "we move like psychopaths", "different breed of chaos", "built for destruction",
            "menace to society vibes", "unhinged energy only"
        ]

        self.dark_wisdom = [
            "pain is just life's way of saying hello", "suffering is character development on steroids",
            "every L is just practice for the final boss fight", "failure is success wearing a disguise",
            "rock bottom has excellent wifi", "storms are just nature's therapy sessions",
            "diamonds are coal that handled pressure like a psychopath", "scars are just life's autographs",
            "trauma is just spicy character development", "depression is just your brain's dark mode"
        ]
        
        # Keywords that trigger supportive responses
        self.stress_keywords = [
            'stressed', 'anxiety', 'worried', 'scared', 'nervous', 'pressure',
            'overwhelmed', 'tired', 'exhausted', 'burnout', 'depressed',
            'giving up', 'quit', 'hopeless', 'can\'t do it'
        ]
        
        # Keywords that trigger study-related responses
        self.study_keywords = [
            'study', 'prep', 'preparation', 'mock', 'test', 'score', 'marks',
            'physics', 'chemistry', 'maths', 'english', 'logical', 'reasoning',
            'practice', 'revision', 'syllabus', 'books', 'coaching'
        ]
        
        # AI trigger commands
        self.ai_triggers = ['!ai', '!bot', '!help']
    
    def authenticate(self):
        """Authenticate with Reddit API using environment variables"""
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                username=os.getenv('REDDIT_USERNAME'),
                password=os.getenv('REDDIT_PASSWORD'),
                user_agent=f'BITSATBot/1.0 by {os.getenv("REDDIT_USERNAME")}'
            )
            
            # Test authentication
            logger.info(f"Authenticated as: {self.reddit.user.me()}")
            self.subreddit = self.reddit.subreddit('bitsatards')  # Now working in bitsatards
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _is_active_hours(self) -> bool:
        """Check if bot should be active (9 AM to 1 AM IST)"""
        # Get current time in IST (Indian Standard Time)
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        current_hour = now_ist.hour
        current_time = now_ist.strftime("%H:%M IST")

        # Active from 9 AM (09:00) to 1 AM (01:00) next day IST
        # Active hours: 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0
        # Inactive hours: 1, 2, 3, 4, 5, 6, 7, 8 (1 AM to 9 AM IST)
        if 1 <= current_hour <= 8:
            logger.debug(f"Inactive hours detected: {current_time} (hour {current_hour})")
            return False  # Inactive from 1 AM to 8:59 AM IST

        logger.debug(f"Active hours: {current_time} (hour {current_hour})")
        return True  # Active from 9 AM to 12:59 AM IST

    def should_respond(self, comment) -> bool:
        """Determine if the bot should respond to a comment"""
        # Check if bot should be active during these hours
        if not self._is_active_hours():
            return False

        # Don't respond to own comments
        if comment.author and comment.author.name == self.reddit.user.me().name:
            return False

        # Don't respond to already processed comments
        if comment.id in self.processed_comments:
            return False

        # Don't respond to deleted/removed comments
        if comment.author is None:
            return False

        # Don't respond to bots (AutoModerator, other bots)
        if comment.author:
            author_name = comment.author.name.lower()
            bot_names = [
                'automoderator', 'automod', 'moderator', 'bot', '_bot', 'reddit',
                'snapshillbot', 'totesmessenger', 'remindmebot', 'wikisummarizerbot'
            ]
            if any(bot_name in author_name for bot_name in bot_names):
                return False

        comment_text = comment.body.strip()

        # Clean formatting to detect commands properly
        clean_text = self._clean_text_formatting(comment_text)

        # Always respond to comments starting with "!" (these are cutoff commands)
        if clean_text.startswith('!') or comment_text.startswith('!'):
            return True

        # Only respond to VERY SPECIFIC cutoff queries (not general comments)
        if self._is_specific_cutoff_query(comment.body):
            return True

        # Check for admission queries (can I get, will I qualify, etc.)
        if self._is_admission_query(comment.body):
            return True

        return False
    
    def generate_response(self, comment) -> str:
        """Generate intelligent response based on comment analysis"""
        comment_text = comment.body.strip()
        author_name = comment.author.name if comment.author else "anonymous"

        # Handle ! commands first (these are always cutoff related)
        if comment_text.startswith('!'):
            return self._generate_cutoff_response(author_name, comment_text)

        # Check if this is an admission query
        if self._is_admission_query(comment_text):
            return self._generate_admission_response(author_name, comment_text)

        # Check if this is a specific cutoff query in natural language
        if self._is_specific_cutoff_query(comment_text):
            return self._generate_cutoff_response(author_name, comment_text)

        # This shouldn't happen with current logic, but just in case
        return self._create_unique_response(author_name, comment_text, [])

    def _clean_text_formatting(self, text):
        """Remove Reddit formatting and normalize text"""
        import re

        # Remove Reddit markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold **text**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic *text*
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code `text`
        text = re.sub(r'```(.*?)```', r'\1', text, flags=re.DOTALL)  # Code blocks
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough ~~text~~
        text = re.sub(r'\^(.*?)\^', r'\1', text)      # Superscript ^text^
        text = re.sub(r'_(.*?)_', r'\1', text)        # Underline _text_

        # Remove special characters and punctuation
        text = re.sub(r'[^\w\s]', ' ', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _is_specific_cutoff_query(self, comment_text):
        """Intelligently detect cutoff queries by analyzing word combinations"""
        # Clean formatting first
        clean_text = self._clean_text_formatting(comment_text)
        text_lower = clean_text.lower().strip()

        # Break into words for analysis
        words = text_lower.split()

        # Remove common stop words
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'bruh', 'bro', 'yaar', 'man'}
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 1]

        # Cutoff-related terms
        cutoff_terms = {
            'cutoff', 'cutoffs', 'cut-off', 'cut-offs', 'minimum', 'required', 'needed',
            'admission', 'qualifying', 'entrance', 'score', 'scores', 'marks', 'points'
        }

        # Campus terms
        campus_terms = {
            'pilani', 'goa', 'hyderabad', 'hyd', 'bits', 'campus', 'campuses'
        }

        # Branch terms (including new abbreviations and case variations)
        branch_terms = {
            'cse', 'computer', 'science', 'cs', 'ece', 'electronics', 'communication',
            'eee', 'electrical', 'mechanical', 'mech', 'chemical', 'chem', 'civil',
            'manufacturing', 'manuf', 'mathematics', 'math', 'maths', 'computing',
            'biology', 'bio', 'biological', 'physics', 'phy', 'chemistry', 'economics',
            'eco', 'pharmacy', 'pharm', 'instrumentation', 'instru',
            # New abbreviations
            'mnc', 'eni',
            # Case variations for all terms
            'CSE', 'COMPUTER', 'SCIENCE', 'CS', 'ECE', 'ELECTRONICS', 'COMMUNICATION',
            'EEE', 'ELECTRICAL', 'MECHANICAL', 'MECH', 'CHEMICAL', 'CHEM', 'CIVIL',
            'MANUFACTURING', 'MANUF', 'MATHEMATICS', 'MATH', 'MATHS', 'COMPUTING',
            'BIOLOGY', 'BIO', 'BIOLOGICAL', 'PHYSICS', 'PHY', 'CHEMISTRY', 'ECONOMICS',
            'ECO', 'PHARMACY', 'PHARM', 'INSTRUMENTATION', 'INSTRU', 'MNC', 'ENI',
            # Title case variations
            'Cse', 'Computer', 'Science', 'Cs', 'Ece', 'Electronics', 'Communication',
            'Eee', 'Electrical', 'Mechanical', 'Mech', 'Chemical', 'Chem', 'Civil',
            'Manufacturing', 'Manuf', 'Mathematics', 'Math', 'Maths', 'Computing',
            'Biology', 'Bio', 'Biological', 'Physics', 'Phy', 'Chemistry', 'Economics',
            'Eco', 'Pharmacy', 'Pharm', 'Instrumentation', 'Instru', 'Mnc', 'Eni'
        }

        # Question indicators (more flexible)
        question_words = {
            'what', 'how', 'tell', 'show', 'give', 'share', 'know', 'kya', 'kitne',
            'batao', 'bata', 'chahiye', 'need', 'want', 'looking', 'find', 'can', 'will',
            'get', 'admission', 'qualify', 'eligible', 'chance', 'possible'
        }

        # Check for word combinations
        has_cutoff_term = any(word in cutoff_terms for word in meaningful_words)
        has_campus = any(word in campus_terms for word in meaningful_words)
        has_branch = any(word in branch_terms for word in meaningful_words)
        has_question = any(word in question_words for word in meaningful_words)

        # Advanced pattern matching for natural language
        patterns = [
            # Direct cutoff mentions with campus/branch
            has_cutoff_term and (has_campus or has_branch),

            # Campus + Branch combination (like "Goa ECE cutoff")
            has_campus and has_branch and len(meaningful_words) <= 5,

            # Question + campus/branch + cutoff context (but not general questions)
            has_question and (has_campus or has_branch) and (has_cutoff_term or any(word in {'score', 'marks', 'needed', 'require', 'admission', 'minimum'} for word in meaningful_words)),

            # Campus + Branch + any cutoff-related context (even without explicit "cutoff" word)
            has_campus and has_branch and any(word in {'score', 'marks', 'needed', 'require', 'admission', 'minimum'} for word in meaningful_words),

            # Short queries with campus and branch (like "Goa ECE cutoff bruh")
            has_campus and has_branch and len(words) <= 6,

            # Specific phrases that indicate cutoff queries
            any(phrase in text_lower for phrase in [
                'tell me', 'what is', 'how much', 'how many', 'kya hai', 'kitne marks', 'batao',
                'cutoff for', 'marks for', 'score for', 'needed for'
            ]) and (has_campus or has_branch) and (has_cutoff_term or any(word in {'score', 'marks', 'needed', 'require', 'admission', 'minimum'} for word in meaningful_words))
        ]

        return any(patterns)

    def _is_admission_query(self, comment_text):
        """Check if this is a 'can I get' admission query"""
        clean_text = self._clean_text_formatting(comment_text)
        text_lower = clean_text.lower().strip()

        # Admission query patterns
        admission_patterns = [
            'can i get', 'can i qualify', 'will i get', 'chances of getting',
            'eligible for', 'admission in', 'qualify for', 'get admission',
            'kya mil jayega', 'mil sakta hai', 'admission mil jayega'
        ]

        # Must contain admission pattern
        has_admission_pattern = any(pattern in text_lower for pattern in admission_patterns)

        # Must contain branch or campus terms
        branch_terms = {
            'cse', 'computer', 'science', 'cs', 'ece', 'electronics', 'communication',
            'eee', 'electrical', 'mechanical', 'mech', 'chemical', 'chem', 'civil',
            'manufacturing', 'manuf', 'mathematics', 'math', 'maths', 'computing',
            'biology', 'bio', 'biological', 'physics', 'phy', 'chemistry', 'economics',
            'eco', 'pharmacy', 'pharm', 'instrumentation', 'instru', 'mnc', 'eni',
            'msc', 'm.sc', 'pilani', 'goa', 'hyderabad', 'hyd'
        }

        words = text_lower.split()
        has_branch_or_campus = any(word in branch_terms for word in words)

        # Must contain a score (number)
        import re
        has_score = bool(re.search(r'\b\d{2,3}\b', text_lower))

        return has_admission_pattern and has_branch_or_campus and has_score

    def _create_unique_response(self, author, comment_text, meaningful_words):
        """Create a completely unique response every time"""
        import hashlib
        import time

        # Create unique seed based on comment content, author, and timestamp
        unique_seed = f"{author}{comment_text}{time.time()}"
        seed_hash = int(hashlib.md5(unique_seed.encode()).hexdigest()[:8], 16)
        random.seed(seed_hash)

        # Build response components
        starter = random.choice(self.dark_starters)
        vibe = random.choice(self.hinglish_vibes)
        motivation = random.choice(self.motivational_dark)
        ending = random.choice(self.cool_endings)
        wisdom = random.choice(self.dark_wisdom)

        # Different response patterns for variety
        patterns = [
            # Pattern 1: Direct address with dark motivation
            f"{starter} {author}, {vibe} {motivation} but remember - {wisdom}. {ending.capitalize()} 💀✨",

            # Pattern 2: Comment-specific with wisdom
            f"Yo {author}! {vibe} this is just {motivation}. Here's the thing - {wisdom}. {ending.capitalize()} 🔥",

            # Pattern 3: Hinglish mix with motivation
            f"{starter}, {vibe} life threw you this curveball? {motivation.capitalize()} hai yaar. But {wisdom} - {ending} 💪😈",

            # Pattern 4: Cool philosophical
            f"Dekh {author}, {vibe} {motivation} is happening. Real talk - {wisdom}. Time to {ending} 🎯",

            # Pattern 5: Sarcastic motivation
            f"{starter} {author}, {motivation}? {vibe} perfect timing. Remember: {wisdom}. Now {ending} 🚀💀"
        ]

        # Add comment-specific elements if available
        if meaningful_words:
            word = random.choice(meaningful_words)
            specific_patterns = [
                f"{starter} {author}, {vibe} {word} is giving you {motivation}? Plot twist: {wisdom}. {ending.capitalize()} 🎭",
                f"Yo {author}! {word} se {motivation}? {vibe} {wisdom} - {ending} 💯",
                f"{starter}, {word} and {motivation} - {vibe} classic combo. But {wisdom}, so {ending} 🔥💀"
            ]
            patterns.extend(specific_patterns)

        # Reset random seed to avoid affecting other parts
        random.seed()

        return random.choice(patterns)

    def _generate_cutoff_response(self, author, comment_text):
        """Generate intelligent cutoff response based on specific query"""
        import hashlib
        import time

        # Clean formatting from the query text
        clean_query = self._clean_text_formatting(comment_text)

        # Create unique seed for this response
        unique_seed = f"{author}{clean_query}{time.time()}"
        seed_hash = int(hashlib.md5(unique_seed.encode()).hexdigest()[:8], 16)
        random.seed(seed_hash)

        # Helper function to add case variations
        def add_case_variations(branch_dict):
            """Add all case variations for branch names"""
            new_dict = {}
            for key, value in branch_dict.items():
                # Add original
                new_dict[key] = value
                # Add uppercase
                new_dict[key.upper()] = value
                # Add title case
                new_dict[key.title()] = value
                # Add first letter uppercase
                if len(key) > 0:
                    new_dict[key[0].upper() + key[1:]] = value
            return new_dict

        # Complete cutoff data
        cutoff_data = {
            'pilani': {
                'computer science': 327, 'cse': 327, 'cs': 327, 'computer': 327,
                'electronics and communication': 314, 'ece': 314, 'electronics': 314, 'communication': 314,
                'electrical and electronics': 292, 'eee': 292, 'electrical': 292,
                'mechanical': 266, 'mech': 266, 'mechanical engineering': 266,
                'chemical': 247, 'chemical engineering': 247, 'chem': 247,
                'civil': 238, 'civil engineering': 238,
                'manufacturing': 243, 'manufacturing engineering': 243, 'manuf': 243,
                'mathematics and computing': 318, 'math and computing': 318, 'mathematics computing': 318, 'mnc': 318, 'maths': 318, 'mathematics': 318, 'mnc': 318,
                'pharmacy': 165, 'pharm': 165, 'b.pharm': 165,
                'biological sciences': 236, 'biology': 236, 'bio': 236, 'biological': 236,
                'chemistry msc': 241, 'msc chemistry': 241,
                'mathematics msc': 256, 'msc mathematics': 256, 'msc math': 256, 'msc maths': 256,
                'economics': 271, 'eco': 271, 'msc economics': 271,
                'physics': 254, 'phy': 254, 'msc physics': 254,
                'electronics and instrumentation': 282, 'instrumentation': 282, 'instru': 282, 'eni': 282
            },
            'goa': {
                'computer science': 301, 'cse': 301, 'cs': 301, 'computer': 301,
                'electronics and communication': 287, 'ece': 287, 'electronics': 287, 'communication': 287,
                'electrical and electronics': 278, 'eee': 278, 'electrical': 278,
                'mechanical': 254, 'mech': 254, 'mechanical engineering': 254,
                'chemical': 239, 'chemical engineering': 239, 'chem': 239,
                'mathematics and computing': 295, 'math and computing': 295, 'mathematics computing': 295, 'mnc': 295, 'maths': 295, 'mathematics': 295,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 236, 'msc chemistry': 236,
                'mathematics msc': 249, 'msc mathematics': 249, 'msc math': 249, 'msc maths': 249,
                'economics': 263, 'eco': 263, 'msc economics': 263,
                'physics': 243, 'phy': 243, 'msc physics': 243,
                'electronics and instrumentation': 270, 'instrumentation': 270, 'instru': 270, 'eni': 270
            },
            'hyderabad': {
                'computer science': 298, 'cse': 298, 'cs': 298, 'computer': 298,
                'electronics and communication': 284, 'ece': 284, 'electronics': 284, 'communication': 284,
                'electrical and electronics': 275, 'eee': 275, 'electrical': 275,
                'mechanical': 251, 'mech': 251, 'mechanical engineering': 251,
                'chemical': 238, 'chemical engineering': 238, 'chem': 238,
                'civil': 235, 'civil engineering': 235,
                'mathematics and computing': 293, 'math and computing': 293, 'mathematics computing': 293, 'mnc': 293, 'maths': 293, 'mathematics': 293,
                'pharmacy': 161, 'pharm': 161, 'b.pharm': 161,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 235, 'msc chemistry': 235,
                'mathematics msc': 247, 'msc mathematics': 247, 'msc math': 247, 'msc maths': 247,
                'economics': 261, 'eco': 261, 'msc economics': 261,
                'physics': 245, 'phy': 245, 'msc physics': 245,
                'electronics and instrumentation': 270, 'instrumentation': 270, 'instru': 270, 'eni': 270
            }
        }

        # Apply case variations to all campuses
        for campus in cutoff_data:
            cutoff_data[campus] = add_case_variations(cutoff_data[campus])

        # Parse the query intelligently using cleaned text
        query = clean_query.lower()
        specific_branch = None
        specific_campus = None

        # Enhanced branch detection with context understanding and detailed logging
        branch_matches = []
        for campus in cutoff_data:
            for branch in cutoff_data[campus]:
                if branch in query:
                    branch_matches.append(branch)

        # Prioritize M.Sc programs when "msc" or "m.sc" is mentioned
        if 'msc' in query or 'm.sc' in query or 'm sc' in query:
            # First check for direct MSc matches
            msc_matches = [branch for branch in branch_matches if 'msc' in branch]

            if msc_matches:
                specific_branch = max(msc_matches, key=len)
            else:
                # If no direct MSc match, try to infer from subject + msc context
                # Subject mapping for MSc programs
                subject_mappings = {
                    'mathematics': ['mathematics msc', 'msc mathematics'],
                    'math': ['mathematics msc', 'msc mathematics'],
                    'maths': ['mathematics msc', 'msc mathematics'],
                    'chemistry': ['chemistry msc', 'msc chemistry'],
                    'physics': ['physics msc', 'msc physics'],
                    'biology': ['biological sciences'],
                    'bio': ['biological sciences'],
                    'economics': ['economics', 'msc economics'],
                    'eco': ['economics', 'msc economics']  # Map eco to economics
                }

                for subject, possible_branches in subject_mappings.items():
                    if subject in query:
                        for branch in possible_branches:
                            if any(branch in cutoff_data[campus] for campus in cutoff_data):
                                specific_branch = branch
                                break

                        if specific_branch:
                            break
        else:
            # Get the longest match (most specific) for non-MSc queries
            if branch_matches:
                specific_branch = max(branch_matches, key=len)

        # Enhanced campus detection with variations
        campus_patterns = {
            'pilani': ['pilani', 'pilani campus', 'bits pilani'],
            'goa': ['goa', 'goa campus', 'bits goa', 'k k birla goa'],
            'hyderabad': ['hyderabad', 'hyd', 'hyderabad campus', 'bits hyderabad', 'bits hyd']
        }

        for campus, patterns in campus_patterns.items():
            matched_patterns = [pattern for pattern in patterns if pattern in query]
            if matched_patterns:
                specific_campus = campus
                break

        # Log query understanding in one line
        branch_str = specific_branch or 'ALL'
        campus_str = specific_campus or 'ALL'
        logger.info(f"Query: '{clean_query}' -> Branch: {branch_str}, Campus: {campus_str}")

        return self._format_cutoff_response(author, cutoff_data, specific_branch, specific_campus)

    def _generate_admission_response(self, author, clean_query):
        """Generate response for admission queries like 'can I get CSE at 300'"""
        import re

        # Extract score from query
        score_match = re.search(r'\b(\d{2,3})\b', clean_query)
        if not score_match:
            return "Bro, mention your score! How can I predict without knowing your marks? 🤔"

        user_score = int(score_match.group(1))
        query = clean_query.lower()

        logger.info(f"ADMISSION QUERY ANALYSIS: '{clean_query}'")
        logger.info(f"User score: {user_score}")

        # Load cutoff data (same as cutoff response)
        cutoff_data = self._get_cutoff_data()

        # Detect branch and campus
        specific_branch = None
        specific_campus = None

        # Branch detection with MSc priority
        if 'msc' in query or 'm.sc' in query:
            subject_mappings = {
                'mathematics': ['mathematics msc', 'msc mathematics'],
                'math': ['mathematics msc', 'msc mathematics'],
                'maths': ['mathematics msc', 'msc mathematics'],
                'chemistry': ['chemistry msc', 'msc chemistry'],
                'physics': ['physics msc', 'msc physics'],
                'biology': ['biological sciences'],
                'bio': ['biological sciences'],
                'economics': ['economics', 'msc economics'],
                'eco': ['economics', 'msc economics']
            }

            for subject, possible_branches in subject_mappings.items():
                if subject in query:
                    for branch in possible_branches:
                        if any(branch in cutoff_data[campus] for campus in cutoff_data):
                            specific_branch = branch
                            break
                    if specific_branch:
                        break
        else:
            # Regular branch detection
            branch_matches = []
            for campus in cutoff_data:
                for branch in cutoff_data[campus]:
                    if branch in query:
                        branch_matches.append(branch)

            if branch_matches:
                specific_branch = max(branch_matches, key=len)

        # Campus detection
        campus_patterns = {
            'pilani': ['pilani', 'pilani campus', 'bits pilani'],
            'goa': ['goa', 'goa campus', 'bits goa'],
            'hyderabad': ['hyderabad', 'hyd', 'hyderabad campus', 'bits hyderabad']
        }

        for campus, patterns in campus_patterns.items():
            if any(pattern in query for pattern in patterns):
                specific_campus = campus
                break

        logger.info(f"Detected branch: {specific_branch}")
        logger.info(f"Detected campus: {specific_campus}")

        return self._format_admission_response(author, user_score, cutoff_data, specific_branch, specific_campus)

    def _get_cutoff_data(self):
        """Get cutoff data (extracted from _generate_cutoff_response for reuse)"""
        # Helper function to add case variations
        def add_case_variations(branch_dict):
            new_dict = {}
            for key, value in branch_dict.items():
                new_dict[key] = value
                new_dict[key.upper()] = value
                new_dict[key.title()] = value
                if len(key) > 0:
                    new_dict[key[0].upper() + key[1:]] = value
            return new_dict

        # Complete cutoff data
        cutoff_data = {
            'pilani': {
                'computer science': 327, 'cse': 327, 'cs': 327, 'computer': 327,
                'electronics and communication': 314, 'ece': 314, 'electronics': 314, 'communication': 314,
                'electrical and electronics': 292, 'eee': 292, 'electrical': 292,
                'mechanical': 266, 'mech': 266, 'mechanical engineering': 266,
                'chemical': 247, 'chemical engineering': 247, 'chem': 247,
                'civil': 238, 'civil engineering': 238,
                'manufacturing': 243, 'manufacturing engineering': 243, 'manuf': 243,
                'mathematics and computing': 318, 'math and computing': 318, 'mathematics computing': 318, 'mnc': 318, 'maths': 318, 'mathematics': 318,
                'pharmacy': 165, 'pharm': 165, 'b.pharm': 165,
                'biological sciences': 236, 'biology': 236, 'bio': 236, 'biological': 236,
                'chemistry msc': 241, 'msc chemistry': 241,
                'mathematics msc': 256, 'msc mathematics': 256, 'msc math': 256, 'msc maths': 256,
                'economics': 271, 'eco': 271, 'msc economics': 271,
                'physics': 254, 'phy': 254, 'msc physics': 254,
                'electronics and instrumentation': 282, 'instrumentation': 282, 'instru': 282, 'eni': 282
            },
            'goa': {
                'computer science': 301, 'cse': 301, 'cs': 301, 'computer': 301,
                'electronics and communication': 287, 'ece': 287, 'electronics': 287, 'communication': 287,
                'electrical and electronics': 278, 'eee': 278, 'electrical': 278,
                'mechanical': 254, 'mech': 254, 'mechanical engineering': 254,
                'chemical': 239, 'chemical engineering': 239, 'chem': 239,
                'mathematics and computing': 295, 'math and computing': 295, 'mathematics computing': 295, 'mnc': 295, 'maths': 295, 'mathematics': 295,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 236, 'msc chemistry': 236,
                'mathematics msc': 249, 'msc mathematics': 249, 'msc math': 249, 'msc maths': 249,
                'economics': 263, 'eco': 263, 'msc economics': 263,
                'physics': 243, 'phy': 243, 'msc physics': 243,
                'electronics and instrumentation': 270, 'instrumentation': 270, 'instru': 270, 'eni': 270
            },
            'hyderabad': {
                'computer science': 298, 'cse': 298, 'cs': 298, 'computer': 298,
                'electronics and communication': 284, 'ece': 284, 'electronics': 284, 'communication': 284,
                'electrical and electronics': 275, 'eee': 275, 'electrical': 275,
                'mechanical': 251, 'mech': 251, 'mechanical engineering': 251,
                'chemical': 238, 'chemical engineering': 238, 'chem': 238,
                'civil': 235, 'civil engineering': 235,
                'mathematics and computing': 293, 'math and computing': 293, 'mathematics computing': 293, 'mnc': 293, 'maths': 293, 'mathematics': 293,
                'pharmacy': 161, 'pharm': 161, 'b.pharm': 161,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 235, 'msc chemistry': 235,
                'mathematics msc': 247, 'msc mathematics': 247, 'msc math': 247, 'msc maths': 247,
                'economics': 261, 'eco': 261, 'msc economics': 261,
                'physics': 245, 'phy': 245, 'msc physics': 245,
                'electronics and instrumentation': 270, 'instrumentation': 270, 'instru': 270, 'eni': 270
            }
        }

        # Apply case variations to all campuses
        for campus in cutoff_data:
            cutoff_data[campus] = add_case_variations(cutoff_data[campus])

        return cutoff_data

    def _format_admission_response(self, author, user_score, cutoff_data, specific_branch, specific_campus):
        """Format admission response based on user score vs cutoffs"""

        # Determine what to check
        if specific_branch and specific_campus:
            # Specific branch + campus
            required_score = cutoff_data[specific_campus].get(specific_branch, None)
            if required_score is None:
                return f"Sorry {author}, {specific_branch.upper()} is not available at {specific_campus.upper()} campus! 😅"

            campus_emoji = {'pilani': '🏛️', 'goa': '🏖️', 'hyderabad': '🏙️'}[specific_campus]

            if user_score >= required_score:
                margin = user_score - required_score
                response = f"🎉 **GOOD NEWS {author.upper()}!**\n\n"
                response += f"✅ **YES, you can get {specific_branch.upper()} at {specific_campus.upper()}!**\n\n"
                response += f"| Your Score | Required | Status | Margin |\n"
                response += f"|------------|----------|--------|--------|\n"
                response += f"| **{user_score}/390** | **{required_score}/390** | ✅ **SAFE** | +{margin} |\n\n"
                response += f"{campus_emoji} **{specific_campus.upper()} CAMPUS** - {specific_branch.upper()}\n\n"
                if margin >= 20:
                    response += "🔥 **EXCELLENT!** You're well above the cutoff! Time to celebrate! 🎊"
                elif margin >= 10:
                    response += "👍 **GOOD!** You're comfortably above the cutoff! 😊"
                else:
                    response += "⚠️ **CLOSE CALL!** You're just above the cutoff. Fingers crossed! 🤞"
            else:
                deficit = required_score - user_score
                response = f"😔 **TOUGH NEWS {author.upper()}...**\n\n"
                response += f"❌ **Sorry, {specific_branch.upper()} at {specific_campus.upper()} might be tough...**\n\n"
                response += f"| Your Score | Required | Status | Gap |\n"
                response += f"|------------|----------|--------|-----|\n"
                response += f"| **{user_score}/390** | **{required_score}/390** | ❌ **SHORT** | -{deficit} |\n\n"
                response += f"💡 **ALTERNATIVES:**\n"
                response += f"• Try other campuses for {specific_branch.upper()}\n"
                response += f"• Consider other branches at {specific_campus.upper()}\n"
                response += f"• Look into M.Sc programs (lower cutoffs)\n\n"
                response += "Don't lose hope! There are always options! 💪"

        elif specific_branch:
            # Specific branch, all campuses
            response = f"🎯 **{author.upper()}, here's your {specific_branch.upper()} admission chances:**\n\n"
            response += f"| Campus | Required | Your Score | Status |\n"
            response += f"|--------|----------|------------|--------|\n"

            campus_names = {'pilani': '🏛️ Pilani', 'goa': '🏖️ Goa', 'hyderabad': '🏙️ Hyderabad'}
            safe_campuses = []
            risky_campuses = []

            for campus in ['pilani', 'goa', 'hyderabad']:
                required = cutoff_data[campus].get(specific_branch, None)
                if required:
                    if user_score >= required:
                        status = "✅ SAFE"
                        safe_campuses.append(campus)
                    else:
                        status = f"❌ SHORT (-{required - user_score})"
                        risky_campuses.append(campus)
                    response += f"| {campus_names[campus]} | **{required}/390** | **{user_score}/390** | {status} |\n"

            response += "\n"
            if safe_campuses:
                response += f"🎉 **GOOD NEWS!** You can get {specific_branch.upper()} at: {', '.join(safe_campuses).upper()}\n"
            if risky_campuses:
                response += f"😬 **TOUGH LUCK** for: {', '.join(risky_campuses).upper()}\n"

        else:
            # General admission chances
            response = f"🎯 **{author.upper()}, here are your overall admission chances with {user_score}/390:**\n\n"
            response += "**SAFE OPTIONS:**\n"

            safe_options = []
            for campus in cutoff_data:
                for branch, required in cutoff_data[campus].items():
                    if isinstance(required, int) and user_score >= required:
                        safe_options.append(f"• {branch.upper()} at {campus.upper()}")

            if safe_options:
                response += "\n".join(safe_options[:10])  # Show top 10
                if len(safe_options) > 10:
                    response += f"\n... and {len(safe_options) - 10} more options!"
            else:
                response += "Unfortunately, very limited options with this score. Consider M.Sc programs or other colleges."

        # Add motivational ending
        motivational_endings = [
            "\n\n🌟 Remember: Your worth isn't defined by cutoffs! Keep pushing! 💪",
            "\n\n🎯 Focus on what you can control - your preparation and attitude! 🔥",
            "\n\n💡 Every rejection is a redirection to something better! Stay strong! ✨",
            "\n\n🚀 Success isn't about the college, it's about what you do there! 🌟"
        ]

        import random
        response += random.choice(motivational_endings)

        return response

    def _format_cutoff_response(self, author, cutoff_data, specific_branch, specific_campus):
        """Format the cutoff response based on query specificity"""

        # Dark and funny intros based on query type
        if specific_branch and specific_campus:
            intros = [
                f"Arre {author}, {specific_branch.upper()} at {specific_campus.upper()}? Time for some brutal honesty",
                f"Yo {author}! {specific_branch.upper()} {specific_campus.upper()} cutoff? Prepare for emotional damage",
                f"Dekh {author}, {specific_campus.upper()} {specific_branch.upper()} ka scene - reality check incoming",
                f"Bhai {author}, {specific_branch.upper()} for {specific_campus.upper()}? Here's your dose of harsh truth"
            ]
        elif specific_branch:
            intros = [
                f"Arre {author}, {specific_branch.upper()} cutoffs? Time to crush some dreams across campuses",
                f"Yo {author}! {specific_branch.upper()} ka complete destruction across all campuses",
                f"Dekh {author}, {specific_branch.upper()} cutoffs - campus wise reality slap",
                f"Bhai {author}, {specific_branch.upper()} ke liye sabhi campus ka brutal data"
            ]
        elif specific_campus:
            intros = [
                f"Arre {author}, {specific_campus.upper()} campus? Prepare for complete emotional devastation",
                f"Yo {author}! {specific_campus.upper()} campus - all branches reality check",
                f"Dekh {author}, {specific_campus.upper()} ka complete cutoff massacre",
                f"Bhai {author}, {specific_campus.upper()} campus cutoffs - full destruction mode"
            ]
        else:
            intros = [
                f"Arre {author}, complete BITSAT cutoff data? RIP your mental peace",
                f"Yo {author}! Full cutoff breakdown? Time for existential crisis",
                f"Dekh {author}, complete BITSAT cutoff apocalypse incoming",
                f"Bhai {author}, comprehensive cutoff data - prepare for trauma"
            ]

        # Campus emojis and descriptions
        campus_info = {
            'pilani': ('🏛️ **PILANI CAMPUS**', 'OG campus vibes'),
            'goa': ('🏖️ **GOA CAMPUS**', 'Beach life + studies'),
            'hyderabad': ('🏙️ **HYDERABAD CAMPUS**', 'Tech city energy')
        }

        response = random.choice(intros) + ":\n\n"

        # Specific branch query
        if specific_branch:
            if specific_campus:
                # Specific branch + campus - TABLE FORMAT
                score = cutoff_data[specific_campus].get(specific_branch, 'N/A')
                campus_emoji, campus_desc = campus_info[specific_campus]
                response += f"{campus_emoji}\n*{campus_desc}*\n\n"

                response += "| Branch | Campus | Cutoff Score |\n"
                response += "|--------|--------|-------------|\n"
                response += f"| {specific_branch.upper()} | {specific_campus.title()} | **{score}/390** |\n\n"
            else:
                # Specific branch, all campuses - TABLE FORMAT
                response += f"**{specific_branch.upper()} CUTOFFS ACROSS CAMPUSES:**\n\n"
                response += "| Campus | Cutoff Score |\n"
                response += "|--------|-------------|\n"

                campus_names = {'pilani': '🏛️ Pilani', 'goa': '🏖️ Goa', 'hyderabad': '🏙️ Hyderabad'}
                for campus in ['pilani', 'goa', 'hyderabad']:
                    score = cutoff_data[campus].get(specific_branch, 'N/A')
                    if score != 'N/A':
                        response += f"| {campus_names[campus]} | **{score}/390** |\n"
                response += "\n"

        # Specific campus query - TABLE FORMAT
        elif specific_campus:
            campus_emoji, campus_desc = campus_info[specific_campus]
            response += f"{campus_emoji}\n*{campus_desc}*\n\n"

            response += "| Branch | Cutoff Score |\n"
            response += "|--------|-------------|\n"

            # Group branches by type with proper display names
            engineering_branches = [
                ('computer science', 'CSE'),
                ('electronics and communication', 'ECE'),
                ('electrical and electronics', 'EEE'),
                ('mechanical', 'Mechanical'),
                ('chemical', 'Chemical'),
                ('civil', 'Civil'),
                ('manufacturing', 'Manufacturing'),
                ('mathematics and computing', 'Math & Computing'),
                ('electronics and instrumentation', 'Instrumentation')
            ]

            science_branches = [
                ('biological sciences', 'Biology (M.Sc)'),
                ('chemistry msc', 'Chemistry (M.Sc)'),
                ('mathematics msc', 'Mathematics (M.Sc)'),
                ('economics', 'Economics (M.Sc)'),
                ('physics', 'Physics (M.Sc)')
            ]

            pharmacy_branches = [
                ('pharmacy', 'Pharmacy')
            ]

            # Add engineering branches to table
            for branch_key, display_name in engineering_branches:
                if branch_key in cutoff_data[specific_campus]:
                    score = cutoff_data[specific_campus][branch_key]
                    response += f"| {display_name} | **{score}/390** |\n"

            # Add science branches to table
            for branch_key, display_name in science_branches:
                if branch_key in cutoff_data[specific_campus]:
                    score = cutoff_data[specific_campus][branch_key]
                    response += f"| {display_name} | **{score}/390** |\n"

            # Add pharmacy to table
            for branch_key, display_name in pharmacy_branches:
                if branch_key in cutoff_data[specific_campus]:
                    score = cutoff_data[specific_campus][branch_key]
                    response += f"| {display_name} | **{score}/390** |\n"

            response += "\n"

        # General query - show ALL branches from ALL campuses - TABLE FORMAT
        else:
            response += "**🎯 BITSAT 2024 COMPLETE CUTOFFS:**\n\n"

            # Create a comprehensive table for all campuses
            response += "| Branch | 🏛️ Pilani | 🏖️ Goa | 🏙️ Hyderabad |\n"
            response += "|--------|-----------|--------|-------------|\n"

            # All branches with proper display names
            all_branches = [
                ('computer science', 'CSE'),
                ('electronics and communication', 'ECE'),
                ('electrical and electronics', 'EEE'),
                ('mechanical', 'Mechanical'),
                ('chemical', 'Chemical'),
                ('civil', 'Civil'),
                ('manufacturing', 'Manufacturing'),
                ('mathematics and computing', 'Math & Computing'),
                ('electronics and instrumentation', 'Instrumentation'),
                ('biological sciences', 'Biology (M.Sc)'),
                ('chemistry msc', 'Chemistry (M.Sc)'),
                ('mathematics msc', 'Mathematics (M.Sc)'),
                ('economics', 'Economics (M.Sc)'),
                ('physics', 'Physics (M.Sc)'),
                ('pharmacy', 'Pharmacy')
            ]

            for branch_key, display_name in all_branches:
                pilani_score = cutoff_data['pilani'].get(branch_key, '-')
                goa_score = cutoff_data['goa'].get(branch_key, '-')
                hyd_score = cutoff_data['hyderabad'].get(branch_key, '-')

                # Only show row if at least one campus has this branch
                if pilani_score != '-' or goa_score != '-' or hyd_score != '-':
                    pilani_display = f"**{pilani_score}**" if pilani_score != '-' else '-'
                    goa_display = f"**{goa_score}**" if goa_score != '-' else '-'
                    hyd_display = f"**{hyd_score}**" if hyd_score != '-' else '-'

                    response += f"| {display_name} | {pilani_display} | {goa_display} | {hyd_display} |\n"

            response += "\n*All scores are out of 390*\n\n"

        # Dark and funny motivational endings
        endings = [
            "Numbers don't define you - but they sure love to roast you! 💀",
            "Cutoff dekh ke cry mat kar, grind kar! Tears won't get you admission 😈",
            "Every topper was once crying over cutoffs - now it's your turn! 🔥",
            "These scores are just life's way of saying 'try harder, peasant' 💪",
            "Remember: suffering today = flexing tomorrow (maybe) 😅",
            "Cutoffs are temporary, but the trauma is permanent! Stay strong 🎭",
            "These numbers are just suggestions from the universe to work harder 💯"
        ]

        response += f"\n{random.choice(endings)}\n"

        # Add sassy italic message about max marks
        sassy_messages = [
            "*Though max marks are 426, I don't think you're skilled enough to reach there, so 390 is the realistic ceiling for you* 😏",
            "*While the paper is out of 426, let's be honest - 390 is probably your upper limit anyway* 💀",
            "*Maximum possible is 426, but considering your preparation level, 390 seems more achievable* 😈",
            "*The exam goes up to 426 marks, but realistically speaking, 390 is where most mortals peak* 🎭",
            "*Just so you know, 426 is the theoretical max, but 390 is the practical reality for people like us* 😅"
        ]

        response += f"\n{random.choice(sassy_messages)}\n"
        response += f"\n📊 More detailed info: https://www.bitsadmission.com/FD/BITSAT_cutoffs.html?06012025"

        # Reset random seed
        random.seed()

        return response
    
    def process_comments(self):
        """Process new comments in the subreddit"""
        try:
            # Skip old comments, only monitor new ones
            logger.info("Starting to monitor new comments only...")
            for comment in self.subreddit.stream.comments(skip_existing=True):
                # Check time during stream (bot will exit if inactive)
                if not self._is_active_hours():
                    ist = pytz.timezone('Asia/Kolkata')
                    current_time_ist = datetime.now(ist)
                    current_time = current_time_ist.strftime("%H:%M IST")
                    current_hour = current_time_ist.hour
                    logger.info(f"🛑 STREAM SHUTDOWN: Reached inactive hours at {current_time} (hour {current_hour})")
                    logger.info("💰 Exiting comment stream to save Railway hours")
                    break

                if self.should_respond(comment):
                    response = self.generate_response(comment)

                    try:
                        comment.reply(response)
                        logger.info(f"Replied to comment {comment.id} by {comment.author.name}")
                        self.processed_comments.add(comment.id)

                        # Reduced delay for faster responses
                        time.sleep(random.uniform(5, 15))

                    except Exception as e:
                        logger.error(f"Failed to reply to comment {comment.id}: {e}")

        except Exception as e:
            logger.error(f"Error processing comments: {e}")
    
    def run(self):
        """Main bot loop with smart Railway hour management"""
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        current_hour = current_time_ist.hour
        time_str = current_time_ist.strftime("%H:%M IST")

        logger.info(f"🤖 Bot starting at {time_str} (hour {current_hour})")

        # Check if bot should be active before even starting
        if not self._is_active_hours():
            logger.info(f"⏰ Bot starting during inactive hours ({time_str}). Exiting to save Railway hours.")
            logger.info("💤 Inactive hours: 1 AM - 8:59 AM IST")
            logger.info("⏰ Active hours: 9 AM - 12:59 AM IST")
            logger.info("🔄 Bot will restart automatically during active hours")
            return

        if not self.authenticate():
            logger.error("Failed to authenticate. Please check your credentials.")
            return

        logger.info("BITSAT Bot started successfully!")
        logger.info(f"Monitoring r/{self.subreddit.display_name}")
        logger.info("Active hours: 9 AM - 1 AM (saves Railway hours during night)")

        while True:
            try:
                # Check if we should stop to save Railway hours
                if not self._is_active_hours():
                    ist = pytz.timezone('Asia/Kolkata')
                    current_time_ist = datetime.now(ist)
                    current_time = current_time_ist.strftime("%H:%M IST")
                    current_hour = current_time_ist.hour
                    logger.info(f"🛑 SHUTDOWN: Reached inactive hours at {current_time} (hour {current_hour})")
                    logger.info("💰 Stopping bot to save Railway hours during night (1 AM - 9 AM IST)")
                    logger.info("⏰ Bot will restart automatically at 9 AM IST. Good night! 😴")
                    break

                self.process_comments()
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.info("Restarting in 30 seconds...")
                time.sleep(30)
                # Try to reconnect
                try:
                    self.authenticate()
                    logger.info("Reconnected successfully")
                except:
                    logger.error("Reconnection failed, will retry...")
                    time.sleep(60)

if __name__ == "__main__":
    bot = BITSATBot()
    bot.run()
