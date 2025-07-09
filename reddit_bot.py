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
            # Check if all required environment variables are present
            required_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD']
            missing_vars = [var for var in required_vars if not os.getenv(var)]

            if missing_vars:
                logger.error(f"Missing environment variables: {missing_vars}")
                return False

            logger.info("Creating Reddit instance...")
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                username=os.getenv('REDDIT_USERNAME'),
                password=os.getenv('REDDIT_PASSWORD'),
                user_agent=f'BITSATBot/1.0 by {os.getenv("REDDIT_USERNAME")}'
            )

            # Test authentication
            logger.info("Testing authentication...")
            user = self.reddit.user.me()
            logger.info(f"✅ Authenticated as: {user}")

            # Test subreddit access
            logger.info("Testing subreddit access...")
            self.subreddit = self.reddit.subreddit('bitsatards')
            logger.info(f"✅ Connected to r/{self.subreddit.display_name}")

            return True

        except Exception as e:
            error_msg = str(e).lower()
            if "403" in error_msg or "forbidden" in error_msg:
                logger.error("❌ 403 FORBIDDEN - Possible causes:")
                logger.error("   • Wrong username/password")
                logger.error("   • Account suspended/banned")
                logger.error("   • Two-factor authentication enabled")
                logger.error("   • Rate limited")
            elif "401" in error_msg or "unauthorized" in error_msg:
                logger.error("❌ 401 UNAUTHORIZED - Check client_id/client_secret")
            else:
                logger.error(f"❌ Authentication failed: {e}")

            logger.error("Failed to authenticate. Please check your credentials.")
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

        # Check queries in priority order (most specific first)

        # 1. Check for trend queries first (most specific)
        if self._is_trend_query(comment.body):
            return True

        # 2. Check for chance queries
        if self._is_chance_query(comment.body):
            return True

        # 3. Check for admission queries (can I get, will I qualify, etc.)
        if self._is_admission_query(comment.body):
            return True

        # 4. Check for branch comparison queries
        if self._is_branch_comparison_query(comment.body):
            return True

        # 5. Check for suggestion queries
        if self._is_suggestion_query(comment.body):
            return True

        return False
    
    def generate_response(self, comment) -> str:
        """Generate intelligent response based on comment analysis"""
        comment_text = comment.body.strip()
        author_name = comment.author.name if comment.author else "anonymous"

        # Handle ! commands first
        if comment_text.startswith('!'):
            command = comment_text[1:].strip().lower()
            if command == 'help':
                return self._generate_help_response(author_name)
            else:
                # All other ! commands are cutoff related
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

        # Check if this is a chance query
        if self._is_chance_query(comment_text):
            return self._generate_chance_response(author_name, comment_text)

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

        # Strong comparison patterns (must have explicit comparison words)
        comparison_patterns = [
            'compare', 'comparison', 'vs', 'versus', 'difference between',
            'better', 'which is better', 'difference', 'choose between'
        ]

        # Must contain comparison pattern
        has_comparison = any(pattern in text_lower for pattern in comparison_patterns)

        # Enhanced branch detection including campus-branch combinations
        branch_terms = [
            'cse', 'computer', 'ece', 'electronics', 'eee', 'electrical',
            'mechanical', 'mech', 'chemical', 'chem', 'civil', 'manufacturing',
            'mnc', 'math', 'mathematics', 'computing', 'eni', 'instrumentation',
            'biology', 'bio', 'physics', 'chemistry', 'economics', 'pharmacy', 'eco'
        ]

        # Campus terms
        campus_terms = ['pilani', 'goa', 'hyderabad', 'hyd']

        words = text_lower.split()
        branch_count = sum(1 for word in words if word in branch_terms)
        campus_count = sum(1 for word in words if word in campus_terms)

        # It's a comparison ONLY if:
        # 1. Has explicit comparison keywords AND multiple branches/campuses
        # 2. OR has "vs" with multiple branches
        is_comparison = (has_comparison and (branch_count >= 2 or (campus_count >= 2 and branch_count >= 1))) or \
                       ('vs' in text_lower and (branch_count >= 2 or campus_count >= 2))

        return is_comparison

    def _is_trend_query(self, comment_text):
        """Check if this is a trends/previous year query (improved specificity)"""
        clean_text = self._clean_text_formatting(comment_text)
        text_lower = clean_text.lower().strip()

        # Strong trend indicators
        strong_trend_patterns = [
            'trend', 'trends', 'previous year', 'last year', 'past years',
            'history', 'historical', 'over years', 'year wise', 'yearly',
            'cutoff trend', 'cutoff history', 'previous cutoff', 'past cutoff',
            'how has', 'change over', 'annual', 'over time'
        ]

        # Exclude comparison patterns to avoid conflicts
        comparison_exclusions = [
            'vs', 'versus', 'compare', 'comparison', 'difference between',
            'better', 'which is better', 'choose between'
        ]

        # Must contain strong trend pattern
        has_trend = any(pattern in text_lower for pattern in strong_trend_patterns)

        # Must NOT contain comparison patterns
        has_comparison = any(pattern in text_lower for pattern in comparison_exclusions)

        # Must mention cutoff or branch
        cutoff_branch_terms = [
            'cutoff', 'cut-off', 'score', 'marks', 'cse', 'ece', 'mechanical',
            'chemical', 'branch', 'admission', 'math', 'maths', 'eee', 'civil'
        ]

        has_cutoff_branch = any(term in text_lower for term in cutoff_branch_terms)

        # Only return true if it's clearly a trend query and NOT a comparison
        return has_trend and has_cutoff_branch and not has_comparison

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

    def _is_chance_query(self, comment_text):
        """Check if this is asking for admission chances with specific score"""
        clean_text = self._clean_text_formatting(comment_text)
        text_lower = clean_text.lower().strip()

        # Chance patterns
        chance_patterns = [
            'chance', 'chances', 'probability', 'likely', 'possibility',
            'any chance', 'what are my chances', 'chances of getting',
            'can i get', 'will i get', 'possible to get'
        ]

        # Must contain chance pattern
        has_chance = any(pattern in text_lower for pattern in chance_patterns)

        # Must mention score/marks and branch
        import re
        has_score = bool(re.search(r'\b(\d{2,3})\b', text_lower))

        branch_terms = [
            'cse', 'computer', 'ece', 'electronics', 'eee', 'electrical',
            'mechanical', 'mech', 'chemical', 'chem', 'civil', 'manufacturing',
            'mnc', 'math', 'mathematics', 'computing', 'eni', 'instrumentation',
            'biology', 'bio', 'physics', 'chemistry', 'economics', 'pharmacy'
        ]

        has_branch = any(term in text_lower for term in branch_terms)

        return has_chance and has_score and has_branch

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
        """Generate detailed comparison for any two branches"""
        branch1, branch2 = branches

        # Get branch info
        info1 = get_branch_info(branch1)
        info2 = get_branch_info(branch2)

        # Get cutoff data for comparison
        cutoff_data = self._get_cutoff_data()

        greeting = self._get_random_greeting(author)
        response = f"**{greeting}, here's the {info1['name']} vs {info2['name']} breakdown:**\n\n"

        # Create detailed comparison table
        response += f"**COMPREHENSIVE COMPARISON**\n\n"
        response += f"| Aspect | {info1['name']} | {info2['name']} |\n"
        response += f"|--------|{'-' * len(info1['name'])}|{'-' * len(info2['name'])}|\n"
        response += f"| **Focus Area** | {info1['focus']} | {info2['focus']} |\n"

        # Placement comparison
        if branch1 in placement_data and branch2 in placement_data:
            p1, p2 = placement_data[branch1], placement_data[branch2]
            response += f"| **Average Package** | ₹{p1['avg']}L | ₹{p2['avg']}L |\n"
            response += f"| **Median Package** | ₹{p1['median']}L | ₹{p2['median']}L |\n"
            response += f"| **Highest Package** | ₹{p1['highest']}L | ₹{p2['highest']}L |\n"
            response += f"| **Top Recruiters** | {p1['top_companies']} | {p2['top_companies']} |\n"
        elif branch1 in placement_data:
            p1 = placement_data[branch1]
            response += f"| **Average Package** | ₹{p1['avg']}L | Limited data |\n"
            response += f"| **Top Recruiters** | {p1['top_companies']} | Varies by specialization |\n"
        elif branch2 in placement_data:
            p2 = placement_data[branch2]
            response += f"| **Average Package** | Limited data | ₹{p2['avg']}L |\n"
            response += f"| **Top Recruiters** | Varies by specialization | {p2['top_companies']} |\n"

        # Cutoff comparison across campuses
        response += f"\n**CUTOFF COMPARISON (2024-25)**\n\n"
        response += f"| Campus | {info1['name']} | {info2['name']} | Difference |\n"
        response += f"|--------|{'-' * len(info1['name'])}|{'-' * len(info2['name'])}|----------|\n"

        for campus in ['pilani', 'goa', 'hyderabad']:
            cutoff1 = cutoff_data[campus].get(branch1, None)
            cutoff2 = cutoff_data[campus].get(branch2, None)

            if cutoff1 and cutoff2:
                diff = cutoff1 - cutoff2
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                response += f"| {campus.title()} | {cutoff1} | {cutoff2} | {diff_str} |\n"
            elif cutoff1:
                response += f"| {campus.title()} | {cutoff1} | Not offered | - |\n"
            elif cutoff2:
                response += f"| {campus.title()} | Not offered | {cutoff2} | - |\n"

        # Detailed analysis
        response += f"\n**ANALYSIS:**\n"

        # Package analysis
        if branch1 in placement_data and branch2 in placement_data:
            p1, p2 = placement_data[branch1], placement_data[branch2]
            avg_diff = p1['avg'] - p2['avg']
            if avg_diff > 2:
                response += f"• Package advantage: {info1['name']} leads by ₹{avg_diff}L average\n"
            elif avg_diff < -2:
                response += f"• Package advantage: {info2['name']} leads by ₹{abs(avg_diff)}L average\n"
            else:
                response += f"• Package parity: Both branches have similar placement outcomes\n"

        # Cutoff analysis
        avg_cutoffs = {}
        for branch, branch_name in [(branch1, info1['name']), (branch2, info2['name'])]:
            cutoffs = [cutoff_data[campus].get(branch) for campus in ['pilani', 'goa', 'hyderabad']]
            valid_cutoffs = [c for c in cutoffs if c is not None]
            if valid_cutoffs:
                avg_cutoffs[branch_name] = sum(valid_cutoffs) / len(valid_cutoffs)

        if len(avg_cutoffs) == 2:
            names = list(avg_cutoffs.keys())
            diff = avg_cutoffs[names[0]] - avg_cutoffs[names[1]]
            if abs(diff) > 10:
                higher = names[0] if diff > 0 else names[1]
                response += f"• Competition: {higher} is significantly more competitive (avg {abs(diff):.0f} points higher)\n"
            else:
                response += f"• Competition: Both branches have similar competition levels\n"

        # Career prospects
        career_insights = {
            'cse': 'Highest demand, remote work options, rapid industry growth',
            'ece': 'Hardware+software versatility, good for higher studies, stable demand',
            'eee': 'Core engineering, government opportunities, power sector focus',
            'mechanical': 'Most versatile, evergreen demand, broad industry applications',
            'chemical': 'Specialized roles, process industries, research opportunities',
            'civil': 'Infrastructure focus, government projects, steady demand',
            'mnc': 'Finance+tech combination, quantitative roles, emerging field'
        }

        if branch1 in career_insights:
            response += f"• {info1['name']} prospects: {career_insights[branch1]}\n"
        if branch2 in career_insights:
            response += f"• {info2['name']} prospects: {career_insights[branch2]}\n"

        # Final verdict with humor
        response += f"\n**FINAL VERDICT:**\n"
        response += f"{self._get_random_humor('comparison_ending')}"

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
        """Detect cross-campus branch comparisons like 'goa cse vs pilani ece' or 'pilani mech vs goa eco'"""
        # Campus patterns
        campuses = {
            'pilani': ['pilani'],
            'goa': ['goa'],
            'hyderabad': ['hyderabad', 'hyd']
        }

        # Enhanced branch patterns including abbreviations
        branches = {
            'cse': ['cse', 'computer science', 'computer'],
            'ece': ['ece', 'electronics and communication', 'electronics', 'eco'],  # Added 'eco' for ECE
            'eee': ['eee', 'electrical and electronics', 'electrical'],
            'mechanical': ['mechanical', 'mech'],
            'chemical': ['chemical', 'chem'],
            'civil': ['civil'],
            'mnc': ['mnc', 'math and computing', 'mathematics and computing'],
            'eni': ['eni', 'electronics and instrumentation', 'instrumentation'],
            'manufacturing': ['manufacturing', 'manuf'],
            'pharmacy': ['pharmacy', 'pharm'],
            'biology': ['biology', 'bio', 'biological sciences'],
            'physics': ['physics', 'phy'],
            'chemistry': ['chemistry'],
            'mathematics': ['mathematics', 'math', 'maths'],
            'economics': ['economics', 'eco']  # Economics also uses 'eco'
        }

        # Look for patterns like "campus1 branch1 vs campus2 branch2"
        words = query.lower().split()

        # Find campus-branch combinations
        combinations = []

        # Method 1: Look for adjacent campus-branch pairs
        for i, word in enumerate(words):
            for campus_key, campus_patterns in campuses.items():
                if word in campus_patterns:
                    # Look for branch in next few words
                    for j in range(i+1, min(len(words), i+4)):
                        if words[j] not in ['vs', 'versus', 'and', 'or', 'with']:
                            for branch_key, branch_patterns in branches.items():
                                if words[j] in branch_patterns:
                                    combinations.append((campus_key, branch_key))
                                    break
                            break

        # Method 2: Look for branch-campus pairs (reverse order)
        for i, word in enumerate(words):
            for branch_key, branch_patterns in branches.items():
                if word in branch_patterns:
                    # Look for campus in previous or next few words
                    search_range = list(range(max(0, i-3), i)) + list(range(i+1, min(len(words), i+4)))
                    for j in search_range:
                        if words[j] not in ['vs', 'versus', 'and', 'or', 'with']:
                            for campus_key, campus_patterns in campuses.items():
                                if words[j] in campus_patterns:
                                    combinations.append((campus_key, branch_key))
                                    break

        # Remove duplicates while preserving order
        unique_combinations = []
        for combo in combinations:
            if combo not in unique_combinations:
                unique_combinations.append(combo)

        # If we found 2 different combinations, it's a cross-campus comparison
        if len(unique_combinations) >= 2:
            return unique_combinations[:2]

        return None

    def _generate_cross_campus_comparison(self, author, combinations, placement_data):
        """Generate detailed cross-campus branch comparison"""
        (campus1, branch1), (campus2, branch2) = combinations

        # Get cutoff data
        cutoff_data = self._get_cutoff_data()

        # Get cutoffs
        cutoff1 = cutoff_data[campus1].get(branch1, 'N/A')
        cutoff2 = cutoff_data[campus2].get(branch2, 'N/A')

        greeting = self._get_random_greeting(author)
        response = f"**{greeting}, here's the detailed comparison:**\n\n"

        # Campus info with more details
        campus_info = {
            'pilani': {
                'vibe': 'Original campus, traditional culture, extreme weather',
                'pros': 'Highest prestige, strong alumni network, established reputation',
                'cons': 'Harsh climate, conservative environment, highest competition'
            },
            'goa': {
                'vibe': 'Beach campus, relaxed atmosphere, pleasant weather',
                'pros': 'Best weather, chill vibe, good work-life balance',
                'cons': 'Fewer industry connections, party reputation, limited research'
            },
            'hyderabad': {
                'vibe': 'Modern campus, tech city advantages, growing reputation',
                'pros': 'Tech hub location, modern facilities, industry proximity',
                'cons': 'Newest campus, still building reputation, limited alumni network'
            }
        }

        # Detailed comparison table
        response += f"**DETAILED COMPARISON TABLE**\n\n"
        response += "| Aspect | " + f"{campus1.title()} {branch1.upper()}" + " | " + f"{campus2.title()} {branch2.upper()}" + " |\n"
        response += "|--------|" + "-" * (len(campus1) + len(branch1) + 1) + "|" + "-" * (len(campus2) + len(branch2) + 1) + "|\n"
        response += f"| **Cutoff 2024** | {cutoff1} | {cutoff2} |\n"

        # Add placement data if available
        if branch1 in placement_data and branch2 in placement_data:
            p1, p2 = placement_data[branch1], placement_data[branch2]
            response += f"| **Avg Package** | ₹{p1['avg']}L | ₹{p2['avg']}L |\n"
            response += f"| **Highest Package** | ₹{p1['highest']}L | ₹{p2['highest']}L |\n"
            response += f"| **Top Companies** | {p1['top_companies'][:30]}... | {p2['top_companies'][:30]}... |\n"
        elif branch1 in placement_data:
            p1 = placement_data[branch1]
            response += f"| **Avg Package** | ₹{p1['avg']}L | Data not available |\n"
        elif branch2 in placement_data:
            p2 = placement_data[branch2]
            response += f"| **Avg Package** | Data not available | ₹{p2['avg']}L |\n"

        response += f"| **Campus Vibe** | {campus_info[campus1]['vibe']} | {campus_info[campus2]['vibe']} |\n"
        response += f"| **Pros** | {campus_info[campus1]['pros']} | {campus_info[campus2]['pros']} |\n"
        response += f"| **Cons** | {campus_info[campus1]['cons']} | {campus_info[campus2]['cons']} |\n"

        # Analysis
        response += f"\n**ANALYSIS:**\n"
        if isinstance(cutoff1, int) and isinstance(cutoff2, int):
            diff = abs(cutoff1 - cutoff2)
            if cutoff1 > cutoff2:
                response += f"• Cutoff difference: {campus1.title()} {branch1.upper()} is {diff} points higher\n"
                response += f"• Competition: {campus1.title()} {branch1.upper()} is more competitive\n"
            elif cutoff2 > cutoff1:
                response += f"• Cutoff difference: {campus2.title()} {branch2.upper()} is {diff} points higher\n"
                response += f"• Competition: {campus2.title()} {branch2.upper()} is more competitive\n"
            else:
                response += f"• Both have identical cutoffs - equally competitive\n"

        # Package comparison
        if branch1 in placement_data and branch2 in placement_data:
            p1, p2 = placement_data[branch1], placement_data[branch2]
            if p1['avg'] > p2['avg']:
                response += f"• Package advantage: {branch1.upper()} has ₹{p1['avg'] - p2['avg']}L higher average\n"
            elif p2['avg'] > p1['avg']:
                response += f"• Package advantage: {branch2.upper()} has ₹{p2['avg'] - p1['avg']}L higher average\n"
            else:
                response += f"• Both branches have similar placement packages\n"

        # Final verdict with humor
        response += f"\n**VERDICT:**\n"
        response += f"{self._get_random_humor('comparison_ending')}"

        return response

    def _get_random_humor(self, category):
        """Get random humorous lines for different categories - more unique and funny"""
        humor_bank = {
            'cutoff_ending': [
                "Numbers don't define you, but they sure love to humble you daily.",
                "Fun fact: Every BITS topper was once googling 'backup colleges' at 3 AM.",
                "These cutoffs hit harder than reality after JEE results.",
                "Cutoffs are like your ex - they keep rising when you least expect it.",
                "Remember when 300 seemed impossible? Now it's barely enough for Civil.",
                "BITSAT cutoffs: Making students question their life choices since 1964.",
                "Plot twist: The real treasure was the anxiety we gained along the way.",
                "Cutoffs rise faster than petrol prices and your parents' expectations."
            ],
            'comparison_ending': [
                "Choose wisely - your future therapist will want to know why.",
                "Both branches are great, but one will make you cry less during exams.",
                "Pro tip: The branch doesn't matter if you're gonna bunk classes anyway.",
                "Either way, you'll end up coding for a living. Welcome to reality.",
                "Plot twist: Your branch choice matters less than your WiFi speed.",
                "Remember: Every branch leads to the same destination - corporate slavery.",
                "Fun fact: 90% of BITS students end up in IT regardless of branch.",
                "Choose based on passion, not package. (Just kidding, choose package.)"
            ],
            'trend_ending': [
                "Past trends are like weather forecasts - mostly wrong but oddly specific.",
                "These trends change faster than your study schedule during exams.",
                "Cutoff trends: The only graph that always goes up (unlike your marks).",
                "Moral of the story: Start preparing yesterday, panic today.",
                "Trends show cutoffs rising, but your motivation keeps falling.",
                "Reality check: By the time you analyze trends, cutoffs have already moved.",
                "These numbers are more unpredictable than your mood during prep.",
                "Cutoff trends: Making students lose sleep since the dawn of time."
            ],
            'suggestion_ending': [
                "Success is 10% college, 90% surviving the mess food.",
                "Your branch matters less than your ability to handle all-nighters.",
                "Every BITS student has a story - most involve crying in the library.",
                "The best branch is the one where you can still maintain your sanity.",
                "Plot twist: You'll forget your branch name after the first semester.",
                "Reality check: All branches lead to the same placement companies.",
                "Remember: BITS changes you, not the other way around.",
                "Fun fact: Your branch choice will be irrelevant in 5 years anyway."
            ],
            'admission_ending': [
                "Admission chances are like the weather - unpredictable and disappointing.",
                "Your score is decent, but BITSAT cutoffs have trust issues.",
                "Remember: Hope for the best, prepare for disappointment.",
                "Admission probability: Somewhere between 'maybe' and 'start praying'.",
                "Your chances look good, but so did your JEE prep schedule.",
                "Plot twist: Sometimes miracles happen, sometimes they don't.",
                "Keep calm and have backup plans. Lots of backup plans.",
                "Admission is like love - you never know until you try."
            ]
        }

        import random
        return random.choice(humor_bank.get(category, ["Keep grinding, the struggle is real."]))

    def _get_random_greeting(self, author):
        """Get random humorous greetings with more personality"""
        greetings = [
            f"Arre {author}",
            f"Dekh {author}",
            f"Bhai {author}",
            f"Listen {author}",
            f"Alright {author}",
            f"Yaar {author}",
            f"Buddy {author}",
            f"Dude {author}",
            f"Mate {author}",
            f"Boss {author}",
            f"Champ {author}",
            f"Kiddo {author}"
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
                greeting = self._get_random_greeting(author)
                response = f"**{greeting}, here are the {detected_campus.upper()} {detected_branch.upper()} cutoffs:**\n\n"

                # First show the last 3 years cutoffs clearly
                response += "**RECENT CUTOFFS (Last 3 Years)**\n\n"
                response += "| Year | Cutoff Score | Status |\n"
                response += "|------|-------------|--------|\n"

                years = sorted(campus_data.keys(), reverse=True)
                recent_years = years[:3]  # Last 3 years

                for year in recent_years:
                    cutoff = campus_data[year]
                    if cutoff is not None:
                        status = "Latest" if year == years[0] else "Previous"
                        response += f"| {year} | **{cutoff}** | {status} |\n"

                # Then show detailed trend analysis
                response += f"\n**DETAILED TREND ANALYSIS**\n\n"
                response += "| Year | Cutoff | Year-on-Year Change | Trend Pattern |\n"
                response += "|------|--------|-------------------|---------------|\n"

                for i, year in enumerate(years):
                    cutoff = campus_data[year]
                    if cutoff is not None:
                        if i < len(years) - 1:
                            prev_year = years[i+1]
                            prev_cutoff = campus_data[prev_year]
                            if prev_cutoff is not None:
                                change = cutoff - prev_cutoff
                                change_str = f"+{change}" if change > 0 else str(change)
                                if change > 15:
                                    trend_desc = "Sharp Rise"
                                elif change > 5:
                                    trend_desc = "Rising"
                                elif change > -5:
                                    trend_desc = "Stable"
                                elif change > -15:
                                    trend_desc = "Falling"
                                else:
                                    trend_desc = "Sharp Fall"
                            else:
                                change_str = "-"
                                trend_desc = "No data"
                        else:
                            change_str = "-"
                            trend_desc = "Baseline year"

                        response += f"| {year} | {cutoff} | {change_str} | {trend_desc} |\n"

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
        """Generate detailed, accurate and informative suggestions based on user query"""
        query_lower = query.lower()

        # Extract score if mentioned
        import re
        score_match = re.search(r'\b(\d{2,3})\b', query_lower)
        user_score = int(score_match.group(1)) if score_match else None

        if user_score:
            greeting = self._get_random_greeting(author)
            response = f"**{greeting}, here's your detailed roadmap for {user_score}/390:**\n\n"

            if user_score >= 330:
                response += "**EXCEPTIONAL SCORE - TOP 0.5% TERRITORY**\n\n"
                response += "| Branch | Campus | Probability | Package Range | Why Choose |\n"
                response += "|--------|--------|-------------|---------------|------------|\n"
                response += "| CSE | Pilani | 100% | ₹25-65L | Ultimate prestige, best alumni network |\n"
                response += "| CSE | Goa/Hyd | 100% | ₹24-60L | Excellent academics, better lifestyle |\n"
                response += "| ECE | Pilani | 100% | ₹22-55L | Hardware+software, VLSI opportunities |\n"
                response += "| MnC | Any | 100% | ₹24-60L | Finance+tech combo, quant roles |\n\n"
                response += "**STRATEGIC ADVICE:**\n"
                response += "• Primary choice: Pilani CSE (if you want maximum prestige)\n"
                response += "• Lifestyle choice: Goa CSE (beach campus, relaxed environment)\n"
                response += "• Unique option: MnC (emerging field, finance sector opportunities)\n"
                response += "• Reality check: You can literally choose based on campus preference\n\n"

            elif user_score >= 315:
                response += "**EXCELLENT SCORE - TOP 1% CATEGORY**\n\n"
                response += "| Branch | Campus | Probability | Package Range | Strategy |\n"
                response += "|--------|--------|-------------|---------------|----------|\n"
                response += "| CSE | Pilani | 85% | ₹25-65L | Stretch goal, worth the risk |\n"
                response += "| CSE | Goa/Hyd | 100% | ₹24-60L | Very safe, excellent choice |\n"
                response += "| ECE | Pilani | 100% | ₹22-55L | Safe backup, great prospects |\n"
                response += "| MnC | Any | 100% | ₹24-60L | Unique path, finance opportunities |\n\n"
                response += "**RECOMMENDED STRATEGY:**\n"
                response += "• First preference: CSE at all campuses (Pilani is achievable)\n"
                response += "• Safe backup: ECE Pilani (guaranteed admission)\n"
                response += "• Consider: MnC if interested in finance+tech combination\n"
                response += "• Campus tip: Goa offers best work-life balance\n\n"

            elif user_score >= 300:
                response += "**GREAT SCORE - MULTIPLE EXCELLENT OPTIONS**\n\n"
                response += "**ADMISSION PROBABILITY ANALYSIS**\n\n"
                response += "| Branch | Campus | Cutoff 2024 | Your Score | Admission Chance | Risk Level |\n"
                response += "|--------|--------|-------------|------------|------------------|------------|\n"
                response += f"| CSE | Goa | 301 | {user_score} | 95% | Very Low |\n"
                response += f"| CSE | Hyderabad | 298 | {user_score} | 98% | Very Low |\n"
                response += f"| CSE | Pilani | 327 | {user_score} | 60% | Moderate |\n"
                response += f"| ECE | Pilani | 314 | {user_score} | 100% | None |\n"
                response += f"| ECE | Goa/Hyd | 287/284 | {user_score} | 100% | None |\n"
                response += f"| MnC | Any | 318/295/293 | {user_score} | 100% | None |\n\n"

                response += "**PLACEMENT & CAREER PROSPECTS**\n\n"
                response += "| Branch | Avg Package | Median | Highest | Top Companies | Career Growth |\n"
                response += "|--------|-------------|--------|---------|---------------|---------------|\n"
                response += "| CSE | ₹28L | ₹22L | ₹65L | Google, Microsoft, Amazon | Excellent |\n"
                response += "| ECE | ₹24L | ₹18L | ₹55L | Intel, Qualcomm, Samsung | Very Good |\n"
                response += "| MnC | ₹26L | ₹20L | ₹60L | Goldman Sachs, JP Morgan | Excellent |\n\n"

                response += "**STRATEGIC RECOMMENDATIONS:**\n"
                response += "• **Primary Strategy:** Apply CSE at all campuses, ECE Pilani as guaranteed backup\n"
                response += "• **Pilani CSE:** Achievable but competitive - you're 27 points above cutoff\n"
                response += "• **Safe Choices:** CSE Goa/Hyd (very high probability), ECE Pilani (guaranteed)\n"
                response += "• **Hidden Gem:** MnC if you're strong in math - finance sector loves this combo\n"
                response += "• **Campus Decision:** Pilani (prestige) vs Goa (lifestyle) vs Hyderabad (modern)\n\n"

            elif user_score >= 285:
                response += "**SOLID SCORE - GOOD ENGINEERING OPTIONS**\n\n"
                response += "**ADMISSION ANALYSIS BY BRANCH**\n\n"
                response += "| Branch | Campus | Cutoff 2024 | Gap | Admission Chance | Recommendation |\n"
                response += "|--------|--------|-------------|-----|------------------|----------------|\n"
                response += f"| ECE | Goa | 287 | +{user_score-287} | 95% | Excellent choice |\n"
                response += f"| ECE | Hyderabad | 284 | +{user_score-284} | 98% | Very safe option |\n"
                response += f"| ECE | Pilani | 314 | {user_score-314} | 70% | Stretch but possible |\n"
                response += "| EEE | All campuses | 292/278/275 | Positive | 100% | Guaranteed admission |\n"
                response += "| ENI | All campuses | 282/270/270 | Positive | 100% | Emerging field |\n"
                response += "| MnC | Goa/Hyd | 295/293 | {user_score-295} | 85% | High-reward option |\n\n"

                response += "**CAREER PROSPECTS & PACKAGES**\n\n"
                response += "| Branch | Industry Focus | Avg Package | Job Security | Growth Potential |\n"
                response += "|--------|----------------|-------------|--------------|------------------|\n"
                response += "| ECE | Hardware+Software | ₹24L | High | Excellent |\n"
                response += "| EEE | Power & Electronics | ₹18L | Very High | Good |\n"
                response += "| ENI | Automation & Control | ₹18L | High | Very Good |\n"
                response += "| MnC | Finance+Tech | ₹26L | High | Excellent |\n\n"

                response += "**STRATEGIC RECOMMENDATIONS:**\n"
                response += "• **Primary Target:** ECE Goa/Hyd (high probability, excellent prospects)\n"
                response += "• **Stretch Goal:** ECE Pilani (you're 29 points below, but trends vary)\n"
                response += "• **Safe Backup:** EEE at any campus (guaranteed, underrated branch)\n"
                response += "• **Unique Option:** ENI (instrumentation + IoT focus, growing demand)\n"
                response += "• **High Reward:** MnC if math is your strength (finance sector premium)\n\n"

            elif user_score >= 270:
                response += "**DECENT SCORE - CORE ENGINEERING TERRITORY**\n\n"
                response += "| Branch | Campus | Probability | Package Range | Industry Demand |\n"
                response += "|--------|--------|-------------|---------------|----------------|\n"
                response += "| EEE | All | 100% | ₹16-45L | Power sector, government jobs |\n"
                response += "| Mechanical | All | 95% | ₹14-40L | Most versatile, evergreen demand |\n"
                response += "| ENI | All | 100% | ₹18-40L | Process control, automation |\n"
                response += "| Chemical | Goa/Hyd | 85% | ₹15-42L | Process industries, research |\n"
                response += "| M.Sc Economics | All | 100% | ₹12-35L | Policy, consulting, analytics |\n\n"
                response += "**STRATEGIC INSIGHTS:**\n"
                response += "• Reality check: Core engineering branches are undervalued but solid\n"
                response += "• EEE advantage: Government sector opportunities, PSU placements\n"
                response += "• Mechanical truth: Most versatile branch, opportunities everywhere\n"
                response += "• Chemical prospects: Specialized roles, higher packages in specific sectors\n"
                response += "• M.Sc option: Economics is excellent for policy/consulting careers\n"
                response += "• Long-term view: Core branches often have better job security\n\n"

            elif user_score >= 250:
                response += "**MODERATE SCORE - STRATEGIC CHOICES NEEDED**\n\n"
                response += "| Branch | Campus | Probability | Package Range | Career Path |\n"
                response += "|--------|--------|-------------|---------------|-------------|\n"
                response += "| Mechanical | All | 90% | ₹14-40L | Manufacturing, automotive, aerospace |\n"
                response += "| Chemical | All | 85% | ₹15-42L | Process industries, pharma, oil&gas |\n"
                response += "| Civil | Pilani/Hyd | 95% | ₹12-35L | Infrastructure, construction, govt |\n"
                response += "| M.Sc Math | All | 100% | ₹15-50L | Finance, data science, research |\n"
                response += "| M.Sc Physics | All | 100% | ₹14-45L | Research, tech, academia |\n"
                response += "| M.Sc Economics | All | 100% | ₹12-35L | Policy, consulting, banking |\n\n"
                response += "**DETAILED GUIDANCE:**\n"
                response += "• Engineering reality: Core branches offer solid, stable careers\n"
                response += "• Mechanical advantage: Broadest scope, can work in any industry\n"
                response += "• Chemical prospects: Specialized knowledge, good in process industries\n"
                response += "• M.Sc surprise: Often better placement outcomes than expected\n"
                response += "• Math M.Sc secret: Finance sector loves math graduates (₹15-50L range)\n"
                response += "• Physics M.Sc path: Research → PhD → Academia or tech industry\n"
                response += "• Economics M.Sc: Policy research, think tanks, consulting firms\n\n"

            elif user_score >= 230:
                response += "**CHALLENGING SCORE - M.Sc PROGRAMS SHINE**\n\n"
                response += "| Program | Campus | Probability | Package Range | Career Trajectory |\n"
                response += "|---------|--------|-------------|---------------|-------------------|\n"
                response += "| M.Sc Mathematics | All | 100% | ₹15-50L | Finance, data science, quant roles |\n"
                response += "| M.Sc Physics | All | 100% | ₹14-45L | Research, tech companies, academia |\n"
                response += "| M.Sc Chemistry | All | 100% | ₹13-40L | Pharma, research, chemical industry |\n"
                response += "| M.Sc Biology | All | 100% | ₹12-38L | Biotech, pharma, research |\n"
                response += "| M.Sc Economics | All | 100% | ₹12-35L | Policy, consulting, banking |\n"
                response += "| Pharmacy | Pilani/Hyd | 90% | ₹10-30L | Pharma industry, regulatory affairs |\n\n"
                response += "**M.Sc PROGRAM INSIGHTS:**\n"
                response += "• Hidden truth: M.Sc students often outperform B.E. in placements\n"
                response += "• Mathematics advantage: Quant roles in finance (₹20-50L packages)\n"
                response += "• Physics pathway: Research → tech companies → high packages\n"
                response += "• Chemistry prospects: Pharma R&D, process development\n"
                response += "• Biology future: Biotech boom, pharmaceutical research\n"
                response += "• Economics scope: Policy research, economic consulting\n"
                response += "• Dual degree option: M.Sc → M.E. (5-year integrated program)\n\n"

            else:
                response += "**BELOW 230 - ALTERNATIVE STRATEGIES**\n\n"
                response += "| Option | Probability | Package Range | Strategic Advice |\n"
                response += "|--------|-------------|---------------|------------------|\n"
                response += "| M.Sc Programs | 70% | ₹10-35L | Still possible, worth trying |\n"
                response += "| Pharmacy | 60% | ₹8-25L | Specialized field, decent prospects |\n"
                response += "| Other Colleges | 100% | ₹8-30L | VIT, SRM, Manipal - good alternatives |\n"
                response += "| Drop Year | - | Future potential | Prepare better, try again |\n\n"
                response += "**REALISTIC ASSESSMENT:**\n"
                response += "• BITS reality: Might be challenging with current score\n"
                response += "• M.Sc option: Still worth applying, cutoffs can vary\n"
                response += "• Alternative colleges: VIT, SRM, Manipal offer good programs\n"
                response += "• Drop year consideration: If BITS is your dream, prepare better\n"
                response += "• Important reminder: Success depends more on effort than college\n"
                response += "• Career truth: Many successful people didn't go to top colleges\n\n"

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

        # General query - show ALL branches from ALL campuses - CLEAN TABLE FORMAT
        else:
            response += "**BITSAT 2024-25 CUTOFFS - ALL BRANCHES**\n\n"

            # Create a clean comprehensive table
            response += "| Branch | Pilani | Goa | Hyderabad | Type |\n"
            response += "|--------|--------|-----|-----------|------|\n"

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

            # Add program type to branches
            branch_types = {
                'computer science': 'B.E.', 'electronics and communication': 'B.E.', 'electrical and electronics': 'B.E.',
                'mechanical': 'B.E.', 'chemical': 'B.E.', 'civil': 'B.E.', 'manufacturing': 'B.E.',
                'mathematics and computing': 'B.E.', 'electronics and instrumentation': 'B.E.',
                'biological sciences': 'M.Sc', 'chemistry msc': 'M.Sc', 'mathematics msc': 'M.Sc',
                'economics': 'M.Sc', 'physics': 'M.Sc', 'pharmacy': 'B.Pharm'
            }

            for branch_key, display_name in all_branches:
                pilani_score = cutoff_data['pilani'].get(branch_key, '-')
                goa_score = cutoff_data['goa'].get(branch_key, '-')
                hyd_score = cutoff_data['hyderabad'].get(branch_key, '-')

                # Only show row if at least one campus has this branch
                if pilani_score != '-' or goa_score != '-' or hyd_score != '-':
                    # Clean format without excessive bold
                    pilani_display = str(pilani_score) if pilani_score != '-' else '-'
                    goa_display = str(goa_score) if goa_score != '-' else '-'
                    hyd_display = str(hyd_score) if hyd_score != '-' else '-'
                    program_type = branch_types.get(branch_key, 'B.E.')

                    response += f"| {display_name} | {pilani_display} | {goa_display} | {hyd_display} | {program_type} |\n"

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

        # Retry authentication up to 3 times
        max_auth_retries = 3
        for attempt in range(max_auth_retries):
            logger.info(f"🔐 Authentication attempt {attempt + 1}/{max_auth_retries}")
            if self.authenticate():
                break
            elif attempt < max_auth_retries - 1:
                logger.info(f"⏳ Retrying authentication in 60 seconds...")
                time.sleep(60)
            else:
                logger.error("❌ Failed to authenticate after 3 attempts. Exiting.")
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
                error_msg = str(e).lower()

                if "403" in error_msg or "forbidden" in error_msg:
                    logger.error(f"❌ 403 FORBIDDEN: {e}")
                    logger.error("   Possible causes:")
                    logger.error("   • Account banned/suspended")
                    logger.error("   • Rate limited")
                    logger.error("   • Permission issues")
                    logger.error("   • Wrong credentials")
                elif "429" in error_msg or "rate" in error_msg:
                    logger.error(f"⏰ RATE LIMITED: {e}")
                    logger.info("Waiting 5 minutes for rate limit to reset...")
                    time.sleep(300)  # Wait 5 minutes
                    continue
                elif "401" in error_msg or "unauthorized" in error_msg:
                    logger.error(f"❌ 401 UNAUTHORIZED: {e}")
                    logger.error("   Check client_id and client_secret")
                else:
                    logger.error(f"💥 Unexpected error: {e}")

                logger.info("🔄 Restarting in 60 seconds...")
                time.sleep(60)

                # Try to reconnect
                try:
                    logger.info("🔐 Attempting to reconnect...")
                    if self.authenticate():
                        logger.info("✅ Reconnected successfully")
                    else:
                        logger.error("❌ Reconnection failed")
                except Exception as reconnect_error:
                    logger.error(f"❌ Reconnection error: {reconnect_error}")
                    time.sleep(60)

    def _generate_help_response(self, author):
        """Generate comprehensive help response in clean table format"""
        response = f"**BITSAT Bot Help Guide**\n\n"

        response += "## **AVAILABLE FEATURES**\n\n"
        response += "| Feature | Command/Query | Example |\n"
        response += "|---------|---------------|----------|\n"
        response += "| **Cutoff Queries** | `!cutoff [branch] [campus]` | `!cutoff cse pilani` |\n"
        response += "| | Natural language | `goa mechanical cutoff` |\n"
        response += "| **Branch Comparisons** | `compare [branch1] vs [branch2]` | `compare cse vs ece` |\n"
        response += "| | Cross-campus | `goa cse vs pilani ece` |\n"
        response += "| **Cutoff Trends** | `[branch] trends [campus]` | `cse trends pilani` |\n"
        response += "| | Historical data | `mechanical previous year cutoffs` |\n"
        response += "| **Smart Suggestions** | `suggest for [score] marks` | `suggest for 285 marks` |\n"
        response += "| | Branch selection | `help me choose branch` |\n"
        response += "| **Admission Queries** | `can i get [branch] with [score]` | `can i get cse with 310` |\n"
        response += "| | Qualification check | `will i qualify for ece with 290` |\n\n"

        response += "## **SUPPORTED BRANCHES**\n\n"
        response += "| Category | Branches |\n"
        response += "|----------|----------|\n"
        response += "| **Engineering** | CSE, ECE, EEE, Mechanical, Chemical, Civil, MnC, ENI, Manufacturing |\n"
        response += "| **M.Sc Programs** | Mathematics, Physics, Chemistry, Biology, Economics |\n"
        response += "| **Other** | Pharmacy |\n\n"

        response += "## **SUPPORTED CAMPUSES**\n\n"
        response += "| Campus | Location | Specialties |\n"
        response += "|--------|----------|-------------|\n"
        response += "| **Pilani** | Rajasthan | Original campus, highest cutoffs |\n"
        response += "| **Goa** | Goa | Beach campus, moderate cutoffs |\n"
        response += "| **Hyderabad** | Telangana | Modern campus, growing reputation |\n\n"

        response += "## **DATA ACCURACY**\n\n"
        response += "| Data Type | Source | Years |\n"
        response += "|-----------|--------|-------|\n"
        response += "| **Cutoffs** | Official BITS website | 2024-25 |\n"
        response += "| **Trends** | Historical BITS data | 2022-2024 |\n"
        response += "| **Placements** | Industry reports | Recent data |\n"
        response += "| **Predictions** | Statistical analysis | 2025 forecast |\n\n"

        response += "## **QUICK EXAMPLES**\n\n"
        response += "| Query Type | Example Input |\n"
        response += "|------------|---------------|\n"
        response += "| Basic cutoff | `!cutoff cse` |\n"
        response += "| Specific campus | `pilani ece cutoff` |\n"
        response += "| Comparison | `mechanical vs chemical` |\n"
        response += "| Trends | `cse cutoff trends` |\n"
        response += "| Suggestions | `suggest for 295 marks` |\n"
        response += "| Admission check | `can i get ece with 285` |\n\n"

        response += "**Note:** Bot understands both English and Hinglish. Responds only to relevant BITSAT queries.\n\n"
        response += "---\n"
        response += "*Created by [u/Difficult-Dig7627](https://www.reddit.com/user/Difficult-Dig7627/) for r/bitsatards*"

        return response

    def _generate_chance_response(self, author, query):
        """Generate admission chance response for specific branch and score"""
        query_lower = query.lower()

        # Extract score
        import re
        score_match = re.search(r'\b(\d{2,3})\b', query_lower)
        user_score = int(score_match.group(1)) if score_match else None

        if not user_score:
            return f"Hey {author}, I couldn't find your score in the query. Please mention your BITSAT score!"

        # Extract branch using the same detection as trends
        detected_branch = self._detect_branch_for_trends(query_lower)

        if not detected_branch:
            return f"Hey {author}, I couldn't identify the branch you're asking about. Please mention a specific branch!"

        # Get cutoff data
        cutoff_data = self._get_cutoff_data()

        greeting = self._get_random_greeting(author)
        response = f"**{greeting}, here's your admission chance analysis:**\n\n"

        # Branch display names
        branch_names = {
            'cse': 'Computer Science', 'ece': 'Electronics & Communication',
            'eee': 'Electrical & Electronics', 'mechanical': 'Mechanical',
            'chemical': 'Chemical', 'civil': 'Civil', 'mnc': 'Math & Computing',
            'eni': 'Electronics & Instrumentation', 'manufacturing': 'Manufacturing',
            'pharmacy': 'Pharmacy', 'biology': 'M.Sc Biology', 'physics': 'M.Sc Physics',
            'chemistry': 'M.Sc Chemistry', 'mathematics': 'M.Sc Mathematics', 'economics': 'M.Sc Economics'
        }

        branch_name = branch_names.get(detected_branch, detected_branch.upper())
        response += f"**ADMISSION CHANCES FOR {branch_name.upper()} WITH {user_score}/390**\n\n"

        # Campus-wise analysis
        response += "| Campus | 2024 Cutoff | Your Score | Gap | Admission Chance | Verdict |\n"
        response += "|--------|-------------|------------|-----|------------------|----------|\n"

        campuses = ['pilani', 'goa', 'hyderabad']
        chances_found = False
        best_gap = -999
        best_campus = None

        for campus in campuses:
            cutoff = cutoff_data.get(campus, {}).get(detected_branch)
            if cutoff:
                chances_found = True
                gap = user_score - cutoff

                if gap > best_gap:
                    best_gap = gap
                    best_campus = campus

                if gap >= 15:
                    chance, verdict = "95%+", "Excellent"
                elif gap >= 8:
                    chance, verdict = "85-95%", "Very Good"
                elif gap >= 3:
                    chance, verdict = "70-85%", "Good"
                elif gap >= 0:
                    chance, verdict = "50-70%", "Possible"
                elif gap >= -8:
                    chance, verdict = "20-40%", "Challenging"
                elif gap >= -15:
                    chance, verdict = "5-15%", "Very Difficult"
                else:
                    chance, verdict = "<5%", "Extremely Difficult"

                gap_str = f"+{gap}" if gap >= 0 else str(gap)
                response += f"| {campus.title()} | {cutoff} | {user_score} | {gap_str} | {chance} | {verdict} |\n"

        if not chances_found:
            response += f"| - | Not offered | {user_score} | - | 0% | Not available |\n"
            response += f"\n**{branch_name} is not offered at any BITS campus.**\n\n"
            return response

        # Overall assessment
        response += f"\n**DETAILED ANALYSIS:**\n"

        if best_gap >= 10:
            response += f"• **Strong Position:** You're well above cutoffs, especially at {best_campus.title()} (+{best_gap} points)\n"
            response += f"• **Strategy:** Apply confidently, you can choose based on campus preference\n"
        elif best_gap >= 0:
            response += f"• **Decent Position:** You're above cutoffs but margins are tight\n"
            response += f"• **Strategy:** Apply but have backup branches ready\n"
        elif best_gap >= -10:
            response += f"• **Borderline Case:** You're close to cutoffs, outcome depends on competition\n"
            response += f"• **Strategy:** Apply as stretch goal, focus on safer alternatives\n"
        else:
            response += f"• **Challenging Situation:** Significantly below last year's cutoffs\n"
            response += f"• **Strategy:** Consider this unlikely, explore other options\n"

        response += f"• **Reality Check:** Cutoffs can vary ±5-10 points based on paper difficulty and competition\n"
        response += f"• **Important:** This analysis is based on 2024 data, actual results may differ\n\n"

        # Add humorous ending
        response += f"{self._get_random_humor('admission_ending')}"

        return response

if __name__ == "__main__":
    bot = BITSATBot()
    bot.run()
