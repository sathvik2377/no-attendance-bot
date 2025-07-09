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

    def _can_reply_to_comment(self, comment) -> bool:
        """Check if we can reply to this comment (not locked/archived)"""
        try:
            # Refresh comment to get latest status
            comment.refresh()

            # Check if comment is deleted/removed
            if comment.author is None:
                logger.debug(f"Comment {comment.id} author is None (deleted/removed)")
                return False

            # Check if comment thread is locked
            if hasattr(comment, 'locked') and comment.locked:
                logger.debug(f"Comment {comment.id} thread is locked")
                return False

            # Check if comment is archived
            if hasattr(comment, 'archived') and comment.archived:
                logger.debug(f"Comment {comment.id} is archived")
                return False

            # Check submission status
            submission = comment.submission
            if hasattr(submission, 'locked') and submission.locked:
                logger.debug(f"Submission {submission.id} is locked")
                return False

            if hasattr(submission, 'archived') and submission.archived:
                logger.debug(f"Submission {submission.id} is archived")
                return False

            return True

        except Exception as e:
            logger.debug(f"Error checking comment {comment.id} status: {e}")
            return False

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

        # Check for branch comparison queries
        if self._is_branch_comparison_query(comment.body):
            return True

        # Check for trend queries
        if self._is_trend_query(comment.body):
            return True

        # Check for suggestion queries
        if self._is_suggestion_query(comment.body):
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

        # Check if this is a branch comparison query
        if self._is_branch_comparison_query(comment_text):
            return self._generate_branch_comparison_response(author_name, comment_text)

        # Check if this is a trend query
        if self._is_trend_query(comment_text):
            return self._generate_trend_response(author_name, comment_text)

        # Check if this is a suggestion query
        if self._is_suggestion_query(comment_text):
            return self._generate_suggestion_response(author_name, comment_text)

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
            'get', 'admission', 'qualify', 'eligible', 'chance', 'possible', 'compare',
            'comparison', 'vs', 'versus', 'difference', 'better', 'trend', 'trends',
            'suggest', 'suggestion', 'advice', 'recommend'
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

    def _is_branch_comparison_query(self, comment_text):
        """Check if this is a branch comparison query"""
        clean_text = self._clean_text_formatting(comment_text)
        text_lower = clean_text.lower().strip()

        # Comparison patterns
        comparison_patterns = [
            'compare', 'comparison', 'vs', 'versus', 'difference between',
            'better', 'which is better', 'cse vs ece', 'ece vs cse',
            'mechanical vs chemical', 'difference', 'choose between'
        ]

        # Must contain comparison pattern
        has_comparison = any(pattern in text_lower for pattern in comparison_patterns)

        # Must mention at least two branches or ask for comparison
        branch_terms = [
            'cse', 'computer', 'ece', 'electronics', 'eee', 'electrical',
            'mechanical', 'mech', 'chemical', 'chem', 'civil', 'manufacturing',
            'mnc', 'math', 'mathematics', 'computing', 'eni', 'instrumentation',
            'biology', 'bio', 'physics', 'chemistry', 'economics', 'pharmacy'
        ]

        words = text_lower.split()
        branch_count = sum(1 for word in words if word in branch_terms)

        return has_comparison and (branch_count >= 2 or 'which' in text_lower)

    def _is_trend_query(self, comment_text):
        """Check if this is a trends/previous year query"""
        clean_text = self._clean_text_formatting(comment_text)
        text_lower = clean_text.lower().strip()

        # Trend patterns
        trend_patterns = [
            'trend', 'trends', 'previous year', 'last year', 'past years',
            'history', 'over years', 'increasing', 'decreasing', 'pattern',
            'how has', 'change over', 'yearly', 'annual'
        ]

        # Must contain trend pattern
        has_trend = any(pattern in text_lower for pattern in trend_patterns)

        # Must mention cutoff or branch
        cutoff_branch_terms = [
            'cutoff', 'cut-off', 'score', 'marks', 'cse', 'ece', 'mechanical',
            'chemical', 'branch', 'admission'
        ]

        has_cutoff_branch = any(term in text_lower for term in cutoff_branch_terms)

        return has_trend and has_cutoff_branch

    def _is_suggestion_query(self, comment_text):
        """Check if this is asking for suggestions/advice"""
        clean_text = self._clean_text_formatting(comment_text)
        text_lower = clean_text.lower().strip()

        # Suggestion patterns
        suggestion_patterns = [
            'suggest', 'suggestion', 'advice', 'recommend', 'what should i',
            'help me choose', 'guide me', 'confused', 'dilemma', 'options',
            'what to do', 'best option', 'which branch', 'which campus'
        ]

        # Must contain suggestion pattern
        has_suggestion = any(pattern in text_lower for pattern in suggestion_patterns)

        # Must mention score or be asking for branch/campus advice
        context_terms = [
            'score', 'marks', 'got', 'branch', 'campus', 'college',
            'admission', 'choose', 'select', 'pick'
        ]

        has_context = any(term in text_lower for term in context_terms)

        return has_suggestion and has_context

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

        # Complete cutoff data (2024-25 Official BITS Data)
        cutoff_data = {
            'pilani': {
                'computer science': 327, 'cse': 327, 'cs': 327, 'computer': 327,
                'electronics and communication': 314, 'ece': 314, 'electronics': 314, 'communication': 314,
                'electrical and electronics': 292, 'eee': 292, 'electrical': 292,
                'mechanical': 266, 'mech': 266, 'mechanical engineering': 266,
                'chemical': 247, 'chemical engineering': 247, 'chem': 247,
                'civil': 238, 'civil engineering': 238,
                'manufacturing': 243, 'manufacturing engineering': 243, 'manuf': 243,
                'mathematics and computing': 318, 'math and computing': 318, 'mathematics computing': 318, 'mnc': 318,
                'pharmacy': 165, 'pharm': 165, 'b.pharm': 165,
                'biological sciences': 236, 'biology': 236, 'bio': 236, 'biological': 236,
                'chemistry msc': 241, 'msc chemistry': 241,
                'mathematics msc': 256, 'msc mathematics': 256, 'msc math': 256, 'msc maths': 256, 'math': 256, 'maths': 256, 'mathematics': 256,
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
                'mathematics and computing': 295, 'math and computing': 295, 'mathematics computing': 295, 'mnc': 295,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 236, 'msc chemistry': 236,
                'mathematics msc': 249, 'msc mathematics': 249, 'msc math': 249, 'msc maths': 249, 'math': 249, 'maths': 249, 'mathematics': 249,
                'economics': 263, 'eco': 263, 'msc economics': 263,
                'physics': 248, 'phy': 248, 'msc physics': 248,
                'electronics and instrumentation': 270, 'instrumentation': 270, 'instru': 270, 'eni': 270
            },
            'hyderabad': {
                'computer science': 298, 'cse': 298, 'cs': 298, 'computer': 298,
                'electronics and communication': 284, 'ece': 284, 'electronics': 284, 'communication': 284,
                'electrical and electronics': 275, 'eee': 275, 'electrical': 275,
                'mechanical': 251, 'mech': 251, 'mechanical engineering': 251,
                'chemical': 238, 'chemical engineering': 238, 'chem': 238,
                'civil': 235, 'civil engineering': 235,
                'mathematics and computing': 293, 'math and computing': 293, 'mathematics computing': 293, 'mnc': 293,
                'pharmacy': 161, 'pharm': 161, 'b.pharm': 161,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 235, 'msc chemistry': 235,
                'mathematics msc': 247, 'msc mathematics': 247, 'msc math': 247, 'msc maths': 247, 'math': 247, 'maths': 247, 'mathematics': 247,
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

        # Handle generic "cutoff" query more helpfully
        if not specific_branch and not specific_campus and clean_query.strip().lower() in ['cutoff', 'cut-off', 'cutoffs']:
            return self._generate_generic_cutoff_help(author)

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

        # Complete cutoff data (2024-25 Official BITS Data)
        cutoff_data = {
            'pilani': {
                'computer science': 327, 'cse': 327, 'cs': 327, 'computer': 327,
                'electronics and communication': 314, 'ece': 314, 'electronics': 314, 'communication': 314,
                'electrical and electronics': 292, 'eee': 292, 'electrical': 292,
                'mechanical': 266, 'mech': 266, 'mechanical engineering': 266,
                'chemical': 247, 'chemical engineering': 247, 'chem': 247,
                'civil': 238, 'civil engineering': 238,
                'manufacturing': 243, 'manufacturing engineering': 243, 'manuf': 243,
                'mathematics and computing': 318, 'math and computing': 318, 'mathematics computing': 318, 'mnc': 318,
                'pharmacy': 165, 'pharm': 165, 'b.pharm': 165,
                'biological sciences': 236, 'biology': 236, 'bio': 236, 'biological': 236,
                'chemistry msc': 241, 'msc chemistry': 241,
                'mathematics msc': 256, 'msc mathematics': 256, 'msc math': 256, 'msc maths': 256, 'math': 256, 'maths': 256, 'mathematics': 256,
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
                'mathematics and computing': 295, 'math and computing': 295, 'mathematics computing': 295, 'mnc': 295,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 236, 'msc chemistry': 236,
                'mathematics msc': 249, 'msc mathematics': 249, 'msc math': 249, 'msc maths': 249, 'math': 249, 'maths': 249, 'mathematics': 249,
                'economics': 263, 'eco': 263, 'msc economics': 263,
                'physics': 248, 'phy': 248, 'msc physics': 248,
                'electronics and instrumentation': 270, 'instrumentation': 270, 'instru': 270, 'eni': 270
            },
            'hyderabad': {
                'computer science': 298, 'cse': 298, 'cs': 298, 'computer': 298,
                'electronics and communication': 284, 'ece': 284, 'electronics': 284, 'communication': 284,
                'electrical and electronics': 275, 'eee': 275, 'electrical': 275,
                'mechanical': 251, 'mech': 251, 'mechanical engineering': 251,
                'chemical': 238, 'chemical engineering': 238, 'chem': 238,
                'civil': 235, 'civil engineering': 235,
                'mathematics and computing': 293, 'math and computing': 293, 'mathematics computing': 293, 'mnc': 293,
                'pharmacy': 161, 'pharm': 161, 'b.pharm': 161,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 235, 'msc chemistry': 235,
                'mathematics msc': 247, 'msc mathematics': 247, 'msc math': 247, 'msc maths': 247, 'math': 247, 'maths': 247, 'mathematics': 247,
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

    def _generate_branch_comparison_response(self, author, query):
        """Generate branch comparison response with placement data"""
        query_lower = query.lower()

        # Placement data (based on recent BITS placement reports and industry data)
        placement_data = {
            'cse': {'avg': 28, 'median': 22, 'highest': 65, 'top_companies': 'Google, Microsoft, Amazon'},
            'ece': {'avg': 24, 'median': 18, 'highest': 55, 'top_companies': 'Intel, Qualcomm, Samsung'},
            'eee': {'avg': 18, 'median': 14, 'highest': 45, 'top_companies': 'Siemens, ABB, L&T'},
            'mechanical': {'avg': 16, 'median': 12, 'highest': 40, 'top_companies': 'Tata Motors, Mahindra, Bajaj'},
            'chemical': {'avg': 17, 'median': 13, 'highest': 42, 'top_companies': 'Reliance, ONGC, ITC'},
            'civil': {'avg': 14, 'median': 10, 'highest': 35, 'top_companies': 'L&T, Tata Projects, DLF'},
            'mnc': {'avg': 26, 'median': 20, 'highest': 60, 'top_companies': 'Goldman Sachs, JP Morgan, Google'}
        }

        # Get comprehensive branch info for any comparison
        def get_branch_info(branch_key):
            branch_descriptions = {
                'cse': {'name': 'Computer Science', 'focus': 'Software, AI/ML, algorithms', 'emoji': '💻'},
                'ece': {'name': 'Electronics & Communication', 'focus': 'Hardware+Software, VLSI, embedded', 'emoji': '⚡'},
                'eee': {'name': 'Electrical & Electronics', 'focus': 'Power systems, electrical machines', 'emoji': '🔌'},
                'mechanical': {'name': 'Mechanical', 'focus': 'Automotive, aerospace, manufacturing', 'emoji': '🔧'},
                'chemical': {'name': 'Chemical', 'focus': 'Process industries, pharma, petrochemicals', 'emoji': '⚗️'},
                'civil': {'name': 'Civil', 'focus': 'Construction, infrastructure, urban planning', 'emoji': '🏗️'},
                'mnc': {'name': 'Math & Computing', 'focus': 'Mathematics, programming, finance', 'emoji': '🧮'},
                'eni': {'name': 'Electronics & Instrumentation', 'focus': 'Process control, automation, IoT', 'emoji': '🎛️'},
                'manufacturing': {'name': 'Manufacturing', 'focus': 'Production, industrial engineering', 'emoji': '🏭'},
                'pharmacy': {'name': 'Pharmacy', 'focus': 'Drug development, pharmaceutical industry', 'emoji': '💊'},
                'biology': {'name': 'M.Sc Biology', 'focus': 'Life sciences, research, biotechnology', 'emoji': '🧬'},
                'physics': {'name': 'M.Sc Physics', 'focus': 'Research, academia, tech applications', 'emoji': '⚛️'},
                'chemistry': {'name': 'M.Sc Chemistry', 'focus': 'Research, chemical industry, academia', 'emoji': '🧪'},
                'mathematics': {'name': 'M.Sc Mathematics', 'focus': 'Research, finance, data science', 'emoji': '📊'},
                'economics': {'name': 'M.Sc Economics', 'focus': 'Policy, consulting, financial analysis', 'emoji': '📈'}
            }
            return branch_descriptions.get(branch_key, {'name': branch_key.upper(), 'focus': 'Engineering/Science', 'emoji': '🎓'})

        # First check for cross-campus comparisons (e.g., "goa cse vs pilani ece")
        campus_branch_pattern = self._detect_campus_branch_comparison(query_lower)
        if campus_branch_pattern:
            return self._generate_cross_campus_comparison(author, campus_branch_pattern, placement_data)

        # Detect any branch comparisons using universal detection
        detected_branches = self._detect_any_branch_comparison(query_lower)
        if detected_branches:
            return self._generate_universal_branch_comparison(author, detected_branches, placement_data, get_branch_info)

        # If no specific comparison detected, show generic help
        response = f"Hey {author}! 🤔 I can compare ANY branches for you:\n\n"
        response += "**Engineering Branches:**\n"
        response += "• CSE, ECE, EEE, Mechanical, Chemical, Civil, MnC, ENI\n\n"
        response += "**M.Sc Programs:**\n"
        response += "• Math, Physics, Chemistry, Biology, Economics\n\n"
        response += "**Examples:**\n"
        response += "• *'compare CSE vs ECE'*\n"
        response += "• *'mechanical vs chemical difference'*\n"
        response += "• *'goa cse vs pilani ece'* (cross-campus!)\n\n"
        response += "Pro tip: The best branch is the one that excites you! 🚀"

        return response

    def _detect_any_branch_comparison(self, query):
        """Detect any two branches being compared"""
        # All possible branch keywords (avoid partial matches)
        branch_keywords = {
            'cse': ['computer science', 'cse', 'computer'],  # Removed 'cs' to avoid msc conflict
            'ece': ['electronics and communication', 'electronics communication', 'ece'],
            'eee': ['electrical and electronics', 'electrical electronics', 'eee'],
            'mechanical': ['mechanical', 'mech'],
            'chemical': ['chemical', 'chem'],
            'civil': ['civil'],
            'mnc': ['mathematics and computing', 'math and computing', 'mnc'],
            'eni': ['electronics and instrumentation', 'instrumentation', 'eni'],
            'manufacturing': ['manufacturing', 'manuf'],
            'pharmacy': ['pharmacy', 'pharm'],
            'biology': ['biological sciences', 'msc biology', 'biology', 'bio'],
            'physics': ['msc physics', 'physics', 'phy'],
            'chemistry': ['msc chemistry', 'chemistry'],  # Removed 'chem' to avoid chemical conflict
            'mathematics': ['msc mathematics', 'mathematics', 'maths', 'math'],
            'economics': ['msc economics', 'economics', 'eco']
        }

        # Find all branches mentioned in query (prioritize longer matches)
        detected_branches = []
        # Sort keywords by length (longest first) to avoid partial matches
        for branch_key, keywords in branch_keywords.items():
            sorted_keywords = sorted(keywords, key=len, reverse=True)
            if any(keyword in query for keyword in sorted_keywords):
                if branch_key not in detected_branches:
                    detected_branches.append(branch_key)

        # Return if we found exactly 2 different branches
        if len(detected_branches) >= 2:
            return detected_branches[:2]  # Take first 2

        return None

    def _generate_universal_branch_comparison(self, author, branches, placement_data, get_branch_info):
        """Generate comparison for any two branches"""
        branch1, branch2 = branches

        # Get branch info
        info1 = get_branch_info(branch1)
        info2 = get_branch_info(branch2)

        # Get cutoff data for comparison
        cutoff_data = self._get_cutoff_data()

        greeting = self._get_random_greeting(author)
        response = f"🔥 **{greeting} here's {info1['name']} vs {info2['name']}:**\n\n"

        # Branch 1 details
        response += f"**{info1['emoji']} {info1['name'].upper()}:**\n"
        response += f"• Focus: {info1['focus']}\n"
        if branch1 in placement_data:
            p1 = placement_data[branch1]
            response += f"• Packages: Avg ₹{p1['avg']}L, Median ₹{p1['median']}L, Highest ₹{p1['highest']}L\n"
            response += f"• Top Companies: {p1['top_companies']}\n"

        # Show cutoffs across campuses
        response += f"• Cutoffs: "
        cutoffs1 = []
        for campus in ['pilani', 'goa', 'hyderabad']:
            cutoff = cutoff_data[campus].get(branch1, None)
            if cutoff:
                cutoffs1.append(f"{campus.title()} {cutoff}")
        response += ", ".join(cutoffs1) + "\n\n"

        # Branch 2 details
        response += f"**{info2['emoji']} {info2['name'].upper()}:**\n"
        response += f"• Focus: {info2['focus']}\n"
        if branch2 in placement_data:
            p2 = placement_data[branch2]
            response += f"• Packages: Avg ₹{p2['avg']}L, Median ₹{p2['median']}L, Highest ₹{p2['highest']}L\n"
            response += f"• Top Companies: {p2['top_companies']}\n"

        # Show cutoffs across campuses
        response += f"• Cutoffs: "
        cutoffs2 = []
        for campus in ['pilani', 'goa', 'hyderabad']:
            cutoff = cutoff_data[campus].get(branch2, None)
            if cutoff:
                cutoffs2.append(f"{campus.title()} {cutoff}")
        response += ", ".join(cutoffs2) + "\n\n"

        # Analysis
        if branch1 in placement_data and branch2 in placement_data:
            avg_diff = placement_data[branch1]['avg'] - placement_data[branch2]['avg']
            if avg_diff > 0:
                response += f"💰 **Package Analysis:** {info1['name']} has ₹{avg_diff}L higher average\n"
            elif avg_diff < 0:
                response += f"💰 **Package Analysis:** {info2['name']} has ₹{abs(avg_diff)}L higher average\n"
            else:
                response += f"💰 **Package Analysis:** Both have similar average packages\n"

        # Add humorous ending
        response += f"\n{self._get_random_humor('comparison_ending')}"

        return response

    def _detect_branch_for_trends(self, query):
        """Detect branch for trend analysis - works for ALL branches"""
        # Comprehensive branch mapping (avoid partial matches)
        branch_mappings = {
            'cse': ['computer science', 'cse', 'computer'],
            'ece': ['electronics and communication', 'electronics communication', 'ece', 'electronics'],
            'eee': ['electrical and electronics', 'electrical electronics', 'eee', 'electrical'],
            'mechanical': ['mechanical', 'mech'],
            'chemical': ['chemical', 'chem'],
            'civil': ['civil'],
            'mnc': ['mathematics and computing', 'math and computing', 'mnc'],
            'eni': ['electronics and instrumentation', 'instrumentation', 'eni'],
            'manufacturing': ['manufacturing', 'manuf'],
            'pharmacy': ['pharmacy', 'pharm'],
            'biology': ['biological sciences', 'msc biology', 'biology', 'bio'],
            'physics': ['msc physics', 'physics', 'phy'],
            'chemistry': ['msc chemistry', 'chemistry'],
            'mathematics': ['msc mathematics', 'mathematics', 'maths', 'math'],
            'economics': ['msc economics', 'economics', 'eco']
        }

        # Find the branch (prioritize longer matches)
        for branch_key, keywords in branch_mappings.items():
            sorted_keywords = sorted(keywords, key=len, reverse=True)
            if any(keyword in query for keyword in sorted_keywords):
                return branch_key

        return None

    def _detect_campus_branch_comparison(self, query):
        """Detect cross-campus branch comparisons like 'goa cse vs pilani ece'"""
        # Campus patterns
        campuses = {
            'pilani': ['pilani', 'bits pilani'],
            'goa': ['goa', 'bits goa', 'k k birla goa'],
            'hyderabad': ['hyderabad', 'hyd', 'bits hyderabad', 'bits hyd']
        }

        # Branch patterns
        branches = {
            'cse': ['cse', 'computer science', 'cs', 'computer'],
            'ece': ['ece', 'electronics and communication', 'electronics'],
            'eee': ['eee', 'electrical and electronics', 'electrical'],
            'mechanical': ['mechanical', 'mech'],
            'chemical': ['chemical', 'chem'],
            'civil': ['civil'],
            'mnc': ['mnc', 'math and computing', 'mathematics and computing']
        }

        # Look for patterns like "campus1 branch1 vs campus2 branch2"
        words = query.split()

        # Find campus-branch combinations
        combinations = []
        for i, word in enumerate(words):
            for campus_key, campus_patterns in campuses.items():
                if any(pattern in word for pattern in campus_patterns):
                    # Look for branch nearby
                    for j in range(max(0, i-2), min(len(words), i+3)):
                        for branch_key, branch_patterns in branches.items():
                            if any(pattern in words[j] for pattern in branch_patterns):
                                combinations.append((campus_key, branch_key))
                                break

        # If we found 2 different combinations, it's a cross-campus comparison
        if len(combinations) >= 2 and combinations[0] != combinations[1]:
            return combinations[:2]

        return None

    def _generate_cross_campus_comparison(self, author, combinations, placement_data):
        """Generate cross-campus branch comparison"""
        (campus1, branch1), (campus2, branch2) = combinations

        # Get cutoff data
        cutoff_data = self._get_cutoff_data()

        # Get cutoffs
        cutoff1 = cutoff_data[campus1].get(branch1, 'N/A')
        cutoff2 = cutoff_data[campus2].get(branch2, 'N/A')

        response = f"🔥 **{author.upper()}, here's {campus1.upper()} {branch1.upper()} vs {campus2.upper()} {branch2.upper()}:**\n\n"

        # Campus info
        campus_info = {
            'pilani': {'emoji': '🏛️', 'vibe': 'OG campus, traditional culture, harsh weather'},
            'goa': {'emoji': '🏖️', 'vibe': 'Beach vibes, chill atmosphere, best weather'},
            'hyderabad': {'emoji': '🏙️', 'vibe': 'Modern campus, tech city, growing connections'}
        }

        # Option 1
        response += f"**{campus_info[campus1]['emoji']} {campus1.upper()} {branch1.upper()}:**\n"
        response += f"• Cutoff: **{cutoff1}/390**\n"
        if branch1 in placement_data:
            response += f"• Avg Package: ₹{placement_data[branch1]['avg']}L\n"
            response += f"• Top Companies: {placement_data[branch1]['top_companies']}\n"
        response += f"• Campus Vibe: {campus_info[campus1]['vibe']}\n\n"

        # Option 2
        response += f"**{campus_info[campus2]['emoji']} {campus2.upper()} {branch2.upper()}:**\n"
        response += f"• Cutoff: **{cutoff2}/390**\n"
        if branch2 in placement_data:
            response += f"• Avg Package: ₹{placement_data[branch2]['avg']}L\n"
            response += f"• Top Companies: {placement_data[branch2]['top_companies']}\n"
        response += f"• Campus Vibe: {campus_info[campus2]['vibe']}\n\n"

        # Analysis
        if isinstance(cutoff1, int) and isinstance(cutoff2, int):
            diff = abs(cutoff1 - cutoff2)
            if cutoff1 > cutoff2:
                response += f"📊 **Cutoff Analysis:** {campus1.upper()} {branch1.upper()} is {diff} points higher\n"
            elif cutoff2 > cutoff1:
                response += f"📊 **Cutoff Analysis:** {campus2.upper()} {branch2.upper()} is {diff} points higher\n"
            else:
                response += f"📊 **Cutoff Analysis:** Both have same cutoff!\n"

        # Verdict
        humor_lines = [
            "🎯 **Bottom Line:** Both are solid choices - pick based on your vibe preference!",
            "🤔 **Reality Check:** Success depends more on you than the campus!",
            "🎭 **Plot Twist:** You'll love whichever you choose after 4 years!",
            "🚀 **Truth Bomb:** Alumni from both are killing it in their careers!"
        ]

        import random
        response += f"\n{random.choice(humor_lines)}"

        return response

    def _get_random_humor(self, category):
        """Get random humorous lines for different categories"""
        humor_bank = {
            'cutoff_ending': [
                "Numbers don't define you - but they sure love to roast you! 💀",
                "Remember: Your worth isn't measured in BITSAT points! 🌟",
                "Plot twist: Work hard enough and cutoffs become irrelevant! 💪",
                "These cutoffs are scarier than my coding assignments! 👻",
                "Cutoffs are temporary, but the trauma is permanent! 😅",
                "Fun fact: Every topper was once crying over cutoffs! 😭"
            ],
            'comparison_ending': [
                "Choose wisely - your future self will either thank you or haunt you! 👻",
                "Both are great, but one might suit your vibe better! 🎭",
                "Remember: It's not just about cutoffs, it's about passion! 🔥",
                "Plot twist: Success depends more on you than the branch! 🌟",
                "Either way, you'll be complaining about assignments in 6 months! 😂",
                "Pro tip: Ask seniors, not Reddit bots! 🤖"
            ],
            'trend_ending': [
                "Remember: Past performance doesn't guarantee future results! 📊",
                "Cutoffs go up faster than your motivation during prep! 😅",
                "Plot twist: Work hard enough and trends won't matter! 💪",
                "These trends are scarier than horror movies! 👻",
                "Moral: Start preparing now, not after seeing trends! 📚",
                "Reality check: Trends change, but hard work never fails! 🔥"
            ],
            'suggestion_ending': [
                "Remember: Success is 10% college, 90% your effort! 🌟",
                "Your journey matters more than your destination! 🚀",
                "Every BITS student has a success story - write yours! 💪",
                "The best branch is the one that excites you every morning! ✨",
                "Plot twist: You'll love whatever you choose after 4 years! 🎭",
                "Reality: Alumni from all branches are killing it! 🔥"
            ]
        }

        import random
        return random.choice(humor_bank.get(category, ["Keep grinding! 💪"]))

    def _get_random_greeting(self, author):
        """Get random humorous greetings"""
        greetings = [
            f"Yo {author}!",
            f"Arre {author}!",
            f"Dekh {author},",
            f"Bhai {author},",
            f"Listen up {author}!",
            f"Alright {author},",
            f"Hey {author}!",
            f"Sup {author}!"
        ]

        import random
        return random.choice(greetings)

    def _generate_trend_response(self, author, query):
        """Generate trends/previous year response"""
        query_lower = query.lower()

        # Comprehensive historical trend data (Official BITS Data - 2022-2024 confirmed)
        trend_data = {
            'cse': {
                'pilani': {'2024': 327, '2023': 331, '2022': 320},
                'goa': {'2024': 301, '2023': 295, '2022': 286},
                'hyderabad': {'2024': 298, '2023': 284, '2022': 279}
            },
            'ece': {
                'pilani': {'2024': 314, '2023': 296, '2022': 279},
                'goa': {'2024': 287, '2023': 267, '2022': 256},
                'hyderabad': {'2024': 284, '2023': 265, '2022': 252}
            },
            'eee': {
                'pilani': {'2024': 292, '2023': 272, '2022': 258},
                'goa': {'2024': 278, '2023': 252, '2022': 237},
                'hyderabad': {'2024': 275, '2023': 251, '2022': 230}
            },
            'mechanical': {
                'pilani': {'2024': 266, '2023': 244, '2022': 223},
                'goa': {'2024': 254, '2023': 223, '2022': 191},
                'hyderabad': {'2024': 251, '2023': 218, '2022': 182}
            },
            'chemical': {
                'pilani': {'2024': 247, '2023': 224, '2022': 191},
                'goa': {'2024': 239, '2023': 209, '2022': 165},
                'hyderabad': {'2024': 238, '2023': 207, '2022': 162}
            },
            'civil': {
                'pilani': {'2024': 238, '2023': 213, '2022': 167},
                'hyderabad': {'2024': 235, '2023': 204, '2022': 158}
            },
            'mnc': {
                'pilani': {'2024': 318, '2023': None, '2022': None},  # MnC added in 2024
                'goa': {'2024': 295, '2023': None, '2022': None},
                'hyderabad': {'2024': 293, '2023': None, '2022': None}
            },
            'eni': {
                'pilani': {'2024': 282, '2023': 266, '2022': 249},
                'goa': {'2024': 270, '2023': 244, '2022': 224},
                'hyderabad': {'2024': 270, '2023': 244, '2022': 222}
            },
            'manufacturing': {
                'pilani': {'2024': 243, '2023': 220, '2022': 184}
            },
            'pharmacy': {
                'pilani': {'2024': 165, '2023': 153, '2022': 125},
                'hyderabad': {'2024': 161, '2023': 135, '2022': 109}
            },
            'biology': {
                'pilani': {'2024': 236, '2023': 212, '2022': 171},
                'goa': {'2024': 234, '2023': 204, '2022': 164},
                'hyderabad': {'2024': 234, '2023': 204, '2022': 158}
            },
            'physics': {
                'pilani': {'2024': 254, '2023': 235, '2022': 214},
                'goa': {'2024': 248, '2023': 222, '2022': 188},
                'hyderabad': {'2024': 245, '2023': 219, '2022': 173}
            },
            'chemistry': {
                'pilani': {'2024': 241, '2023': 213, '2022': 168},
                'goa': {'2024': 236, '2023': 205, '2022': 163},
                'hyderabad': {'2024': 235, '2023': 205, '2022': 160}
            },
            'mathematics': {
                'pilani': {'2024': 256, '2023': 236, '2022': 214},
                'goa': {'2024': 249, '2023': 221, '2022': 187},
                'hyderabad': {'2024': 247, '2023': 219, '2022': 177}
            },
            'economics': {
                'pilani': {'2024': 271, '2023': 257, '2022': 247},
                'goa': {'2024': 263, '2023': 239, '2022': 230},
                'hyderabad': {'2024': 261, '2023': 236, '2022': 220}
            }
        }

        # Universal branch detection for trends
        detected_branch = self._detect_branch_for_trends(query_lower)

        # Detect campus
        detected_campus = None
        if 'pilani' in query_lower:
            detected_campus = 'pilani'
        elif 'goa' in query_lower:
            detected_campus = 'goa'
        elif 'hyderabad' in query_lower or 'hyd' in query_lower:
            detected_campus = 'hyderabad'

        if detected_branch and detected_branch in trend_data:
            response = f"📈 **{author.upper()}, here are the {detected_branch.upper()} cutoff trends:**\n\n"

            if detected_campus and detected_campus in trend_data[detected_branch]:
                # Specific campus trend
                campus_data = trend_data[detected_branch][detected_campus]
                response += f"**{detected_campus.upper()} CAMPUS - {detected_branch.upper()}:**\n\n"
                response += "| Year | Cutoff | Change |\n"
                response += "|------|--------|--------|\n"

                years = sorted(campus_data.keys(), reverse=True)
                for i, year in enumerate(years):
                    cutoff = campus_data[year]
                    if i < len(years) - 1:
                        prev_cutoff = campus_data[years[i+1]]
                        change = cutoff - prev_cutoff
                        change_str = f"+{change}" if change > 0 else str(change)
                        trend_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    else:
                        change_str = "-"
                        trend_emoji = ""

                    response += f"| {year} | **{cutoff}** | {change_str} {trend_emoji} |\n"

                # Calculate trends and predictions (using available data)
                if '2024' in campus_data and '2022' in campus_data and campus_data['2022'] is not None:
                    two_year_change = campus_data['2024'] - campus_data['2022']
                    avg_change = two_year_change / 2
                    response += f"\n📊 **2-Year Trend (2022-2024):** +{two_year_change} points ({avg_change:.1f}/year average)\n"

                    # 2025 Prediction based on recent trend
                    predicted_2025 = campus_data['2024'] + int(avg_change)
                    response += f"🔮 **2025 Prediction:** ~{predicted_2025} (±5 points)\n"
                elif '2024' in campus_data and '2023' in campus_data and campus_data['2023'] is not None:
                    one_year_change = campus_data['2024'] - campus_data['2023']
                    response += f"\n📊 **1-Year Change (2023-2024):** {one_year_change:+d} points\n"

                    # Conservative prediction
                    predicted_2025 = campus_data['2024'] + one_year_change
                    response += f"🔮 **2025 Prediction:** ~{predicted_2025} (±7 points)\n"

            else:
                # All campuses trend
                response += f"**ALL CAMPUSES - {detected_branch.upper()}:**\n\n"
                for campus in ['pilani', 'goa', 'hyderabad']:
                    if campus in trend_data[detected_branch]:
                        campus_data = trend_data[detected_branch][campus]
                        current = campus_data['2024']
                        if '2022' in campus_data and campus_data['2022'] is not None:
                            old = campus_data['2022']
                            change = current - old
                            response += f"🏛️ **{campus.upper()}:** {old} → {current} (+{change} in 2 years)\n"
                        elif '2023' in campus_data and campus_data['2023'] is not None:
                            old = campus_data['2023']
                            change = current - old
                            response += f"🏛️ **{campus.upper()}:** {old} → {current} ({change:+d} in 1 year)\n"
                        else:
                            response += f"🏛️ **{campus.upper()}:** {current} (2024 data)\n"

                response += f"\n📈 **Overall Pattern:** Most branches rising 3-15 points per year\n"

            # Add prediction
            response += f"\n🔮 **2025 Prediction:** Expect 3-8 point increase based on recent trends\n"
            response += f"⚠️ **Reality Check:** Trends can change based on difficulty & applications!\n\n"

            # Add humor
            humor_lines = [
                "Remember: Past performance doesn't guarantee future results! 📊",
                "Cutoffs go up faster than your motivation during prep! 😅",
                "Plot twist: Work hard enough and trends won't matter! 💪",
                "These trends are scarier than horror movies! 👻"
            ]
            import random
            response += random.choice(humor_lines)

        else:
            # Comprehensive trend response showing all available branches
            response = f"📈 **{author}, I can show cutoff trends for ALL branches:**\n\n"
            response += "**🔥 High-Demand Branches:**\n"
            response += "• CSE, ECE, EEE, MnC (Math & Computing)\n\n"
            response += "**⚙️ Core Engineering:**\n"
            response += "• Mechanical, Chemical, Civil, ENI, Manufacturing\n\n"
            response += "**🧬 M.Sc Programs:**\n"
            response += "• Mathematics, Physics, Chemistry, Biology, Economics\n\n"
            response += "**💊 Other Programs:**\n"
            response += "• Pharmacy\n\n"
            response += "**Usage Examples:**\n"
            response += "• *'CSE cutoff trends'* - for all campuses\n"
            response += "• *'Mechanical trends pilani'* - for specific campus\n"
            response += "• *'M.Sc Physics previous year cutoffs'*\n\n"
            response += "📊 **General Trend:** Most cutoffs rising 4-7 points annually!\n"
            response += "🔮 **2025 Prediction:** Expect continued upward trend!"

        return response

    def _generate_suggestion_response(self, author, query):
        """Generate smart suggestions based on user query"""
        query_lower = query.lower()

        # Extract score if mentioned
        import re
        score_match = re.search(r'\b(\d{2,3})\b', query_lower)
        user_score = int(score_match.group(1)) if score_match else None

        if user_score:
            # Score-based suggestions
            response = f"🎯 **{author.upper()}, here are smart suggestions for {user_score}/390:**\n\n"

            if user_score >= 320:
                response += "🔥 **EXCELLENT SCORE! You're in the elite zone:**\n"
                response += "✅ **100% Safe:** CSE/ECE at any campus, MnC anywhere\n"
                response += "🎯 **Go For:** Pilani CSE (prestige + ₹28L avg package)\n"
                response += "🏖️ **Alternative:** Goa CSE (beach life + ₹26L avg package)\n"
                response += "💡 **Pro Tip:** All top branches open - choose by interest!\n\n"
                response += "🏆 **Reality:** You're in the top 1% - any choice will be golden!"

            elif user_score >= 300:
                response += "💪 **GREAT SCORE! Multiple excellent options:**\n"
                response += "✅ **Very Safe:** CSE Goa/Hyd (₹26L avg), ECE Pilani (₹24L avg)\n"
                response += "🎯 **Stretch Goal:** CSE Pilani (327 cutoff - you're close!)\n"
                response += "🔄 **Smart Backup:** ECE/EEE at all campuses\n"
                response += "💡 **MnC Option:** Math & Computing (₹26L avg, finance opportunities)\n\n"
                response += "🎭 **Strategy:** Apply CSE everywhere, ECE as solid backup!"

            elif user_score >= 280:
                response += "👍 **SOLID SCORE! Good engineering options:**\n"
                response += "✅ **Safe:** ECE Goa/Hyd, EEE/Mechanical all campuses\n"
                response += "🎯 **Stretch:** ECE Pilani, CSE Goa/Hyd\n"
                response += "💡 **Smart Move:** Consider EEE - great scope!\n\n"
                response += "🚀 **Reality:** Core branches have excellent opportunities too!"

            elif user_score >= 260:
                response += "🎯 **DECENT SCORE! Core engineering awaits:**\n"
                response += "✅ **Safe:** Mechanical/Chemical all campuses\n"
                response += "🎯 **Possible:** EEE Goa/Hyd\n"
                response += "💡 **Consider:** M.Sc programs (great for higher studies)\n\n"
                response += "💪 **Truth Bomb:** Core branches = solid career foundation!"

            elif user_score >= 240:
                response += "📚 **EXPLORE M.Sc PROGRAMS! Hidden gems:**\n"
                response += "✅ **Excellent:** M.Sc Math, Physics, Chemistry\n"
                response += "🎯 **Possible:** Chemical Engineering\n"
                response += "💡 **Secret:** M.Sc → PhD → Research career!\n\n"
                response += "🌟 **Plot Twist:** M.Sc students often outshine B.E. in placements!"

            else:
                response += "🤔 **CHALLENGING SCORE, but don't lose hope:**\n"
                response += "✅ **Consider:** M.Sc programs, Pharmacy\n"
                response += "🎯 **Alternative:** Other good colleges (VIT, SRM)\n"
                response += "💡 **Reality Check:** BITS might be tough this year\n\n"
                response += "💪 **Remember:** Your worth isn't defined by one exam!"

        else:
            # General suggestions without score
            if 'branch' in query_lower or 'choose' in query_lower:
                response = f"🤔 **{author}, here's how to choose the right branch:**\n\n"
                response += "**🔥 High Demand (Competitive):**\n"
                response += "• CSE: Software, tech companies, highest packages\n"
                response += "• ECE: Hardware + software, versatile\n\n"
                response += "**⚡ Core Engineering (Stable):**\n"
                response += "• Mechanical: Broad applications, evergreen\n"
                response += "• EEE: Power sector, government jobs\n"
                response += "• Chemical: Process industries, good packages\n\n"
                response += "**📚 M.Sc Programs (Underrated):**\n"
                response += "• Math/Physics: Research, academia, finance\n"
                response += "• Economics: Policy, consulting, analytics\n\n"
                response += "💡 **Golden Rule:** Choose based on interest, not just cutoffs!"

            elif 'campus' in query_lower:
                response = f"🏫 **{author}, here's the campus breakdown:**\n\n"
                response += "**🏛️ PILANI (The OG):**\n"
                response += "• Prestige factor, alumni network\n"
                response += "• Traditional campus culture\n"
                response += "• Harsh weather (extreme hot/cold)\n\n"
                response += "**🏖️ GOA (The Chill):**\n"
                response += "• Best weather, beach vibes\n"
                response += "• Relaxed atmosphere\n"
                response += "• Great for work-life balance\n\n"
                response += "**🏙️ HYDERABAD (The Modern):**\n"
                response += "• Newest campus, modern facilities\n"
                response += "• Tech city advantages\n"
                response += "• Growing industry connections\n\n"
                response += "🎯 **Truth:** All campuses have excellent academics!"

            else:
                response = f"🎯 **{author}, I can help you with:**\n\n"
                response += "**📊 Score-based suggestions:**\n"
                response += "• *'I got 285 marks, suggest branches'*\n\n"
                response += "**🎓 Branch selection:**\n"
                response += "• *'Help me choose branch'*\n\n"
                response += "**🏫 Campus selection:**\n"
                response += "• *'Which campus should I choose'*\n\n"
                response += "💡 **Pro Tip:** Mention your score for personalized advice!"

        # Add motivational ending
        motivational_endings = [
            "\n\n🌟 Remember: Success is 10% college, 90% your effort!",
            "\n\n🚀 Your journey matters more than your destination!",
            "\n\n💪 Every BITS student has a success story - write yours!",
            "\n\n✨ The best branch is the one that excites you every morning!"
        ]

        import random
        response += random.choice(motivational_endings)

        return response

    def _format_cutoff_response(self, author, cutoff_data, specific_branch, specific_campus):
        """Format the cutoff response based on query specificity"""

        # Dark and funny intros based on query type
        greeting = self._get_random_greeting(author)
        if specific_branch and specific_campus:
            intros = [
                f"{greeting} {specific_branch.upper()} at {specific_campus.upper()}? Time for some brutal honesty",
                f"{greeting} {specific_branch.upper()} {specific_campus.upper()} cutoff? Prepare for emotional damage",
                f"{greeting} {specific_campus.upper()} {specific_branch.upper()} ka scene - reality check incoming",
                f"{greeting} {specific_branch.upper()} for {specific_campus.upper()}? Here's your dose of harsh truth",
                f"{greeting} {specific_campus.upper()} {specific_branch.upper()} numbers? Brace for impact",
                f"{greeting} {specific_branch.upper()} at {specific_campus.upper()}? Hold onto your dreams"
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

        # Use random humorous ending
        ending = self._get_random_humor('cutoff_ending')

        response += f"\n{ending}\n"

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
                        error_msg = str(e).lower()
                        if "403" in error_msg or "forbidden" in error_msg:
                            logger.error(f"403 FORBIDDEN - Failed to reply to comment {comment.id}: {e}")
                            logger.error("Possible causes:")
                            logger.error("1. Bot account might be shadowbanned or restricted")
                            logger.error("2. Subreddit restrictions on new accounts/bots")
                            logger.error("3. Comment thread might be locked/archived")
                            logger.error("4. Insufficient karma to post in subreddit")
                            logger.error("5. Rate limiting (too many requests)")

                            # Check if we can still access the comment
                            try:
                                comment.refresh()
                                if hasattr(comment, 'locked') and comment.locked:
                                    logger.error("Comment thread is LOCKED")
                                if hasattr(comment, 'archived') and comment.archived:
                                    logger.error("Comment thread is ARCHIVED")
                            except:
                                logger.error("Cannot access comment details - might be deleted/removed")

                        elif "429" in error_msg or "rate" in error_msg:
                            logger.error(f"RATE LIMITED - Failed to reply to comment {comment.id}: {e}")
                            logger.error("Waiting longer before next attempt...")
                            time.sleep(60)  # Wait 1 minute for rate limiting
                        else:
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
