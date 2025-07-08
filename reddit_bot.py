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
    
    def should_respond(self, comment) -> bool:
        """Determine if the bot should respond to a comment"""
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

        # Always respond to comments starting with "!"
        if comment_text.startswith('!'):
            return True

        # Only respond to VERY SPECIFIC cutoff queries (not general comments)
        if self._is_specific_cutoff_query(comment.body):
            return True

        return False
    
    def generate_response(self, comment) -> str:
        """Generate intelligent response based on comment analysis"""
        comment_text = comment.body.strip()
        author_name = comment.author.name if comment.author else "anonymous"

        # Check if this is a cutoff-related query
        if self._is_specific_cutoff_query(comment_text):
            return self._generate_cutoff_response(author_name, comment_text)

        # For "!" commands that aren't cutoff-related
        if comment_text.startswith('!'):
            clean_text = comment_text[1:].strip()
            words = clean_text.lower().split()
            meaningful_words = [w for w in words if len(w) > 3 and w not in
                              ['that', 'this', 'with', 'have', 'will', 'been', 'from', 'they', 'were', 'said', 'what', 'when', 'where', 'how']]
            return self._create_unique_response(author_name, clean_text, meaningful_words)

        # This shouldn't happen with current logic, but just in case
        return self._create_unique_response(author_name, comment_text, [])

    def _is_specific_cutoff_query(self, comment_text):
        """Only respond to VERY SPECIFIC cutoff queries"""
        text_lower = comment_text.lower().strip()

        # Must be a direct question or request
        question_starters = [
            'what is the cutoff', 'what was the cutoff', 'what are the cutoffs',
            'tell me the cutoff', 'show me the cutoff', 'give me the cutoff',
            'what is cutoff', 'what was cutoff', 'cutoff kya hai', 'cutoff batao',
            'kitne marks chahiye', 'how many marks', 'required marks', 'minimum marks',
            'admission cutoff', 'entrance cutoff', 'qualifying marks'
        ]

        # Must contain specific campus or branch terms
        specific_terms = [
            'pilani', 'goa', 'hyderabad', 'hyd', 'bits',
            'cse', 'computer science', 'ece', 'electronics', 'electrical', 'eee',
            'mechanical', 'mech', 'chemical', 'chem', 'civil', 'biology', 'bio',
            'physics', 'phy', 'chemistry', 'economics', 'eco', 'pharmacy', 'pharm',
            'mathematics', 'math', 'maths', 'manufacturing', 'instrumentation'
        ]

        # Check if it's a direct cutoff question
        has_question_starter = any(starter in text_lower for starter in question_starters)
        has_specific_term = any(term in text_lower for term in specific_terms)

        # Must have both question format AND specific terms
        return has_question_starter and has_specific_term

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

        # Create unique seed for this response
        unique_seed = f"{author}{comment_text}{time.time()}"
        seed_hash = int(hashlib.md5(unique_seed.encode()).hexdigest()[:8], 16)
        random.seed(seed_hash)

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
                'mathematics and computing': 318, 'mathematics': 318, 'math': 318, 'maths': 318,
                'pharmacy': 165, 'pharm': 165, 'b.pharm': 165,
                'biological sciences': 236, 'biology': 236, 'bio': 236, 'biological': 236,
                'chemistry msc': 241, 'msc chemistry': 241,
                'economics': 271, 'eco': 271, 'msc economics': 271,
                'physics': 254, 'phy': 254, 'msc physics': 254,
                'electronics and instrumentation': 282, 'instrumentation': 282, 'instru': 282
            },
            'goa': {
                'computer science': 301, 'cse': 301, 'cs': 301, 'computer': 301,
                'electronics and communication': 287, 'ece': 287, 'electronics': 287, 'communication': 287,
                'electrical and electronics': 278, 'eee': 278, 'electrical': 278,
                'mechanical': 254, 'mech': 254, 'mechanical engineering': 254,
                'chemical': 239, 'chemical engineering': 239, 'chem': 239,
                'mathematics and computing': 295, 'mathematics': 295, 'math': 295, 'maths': 295,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 236, 'msc chemistry': 236,
                'economics': 263, 'eco': 263, 'msc economics': 263,
                'physics': 243, 'phy': 243, 'msc physics': 243,
                'electronics and instrumentation': 270, 'instrumentation': 270, 'instru': 270
            },
            'hyderabad': {
                'computer science': 298, 'cse': 298, 'cs': 298, 'computer': 298,
                'electronics and communication': 284, 'ece': 284, 'electronics': 284, 'communication': 284,
                'electrical and electronics': 275, 'eee': 275, 'electrical': 275,
                'mechanical': 251, 'mech': 251, 'mechanical engineering': 251,
                'chemical': 238, 'chemical engineering': 238, 'chem': 238,
                'civil': 235, 'civil engineering': 235,
                'mathematics and computing': 293, 'mathematics': 293, 'math': 293, 'maths': 293,
                'pharmacy': 161, 'pharm': 161, 'b.pharm': 161,
                'biological sciences': 234, 'biology': 234, 'bio': 234, 'biological': 234,
                'chemistry msc': 235, 'msc chemistry': 235,
                'economics': 261, 'eco': 261, 'msc economics': 261,
                'physics': 245, 'phy': 245, 'msc physics': 245,
                'electronics and instrumentation': 270, 'instrumentation': 270, 'instru': 270
            }
        }

        # Parse the query intelligently
        query = comment_text.lower()
        specific_branch = None
        specific_campus = None

        # Enhanced branch detection with context understanding
        branch_matches = []
        for campus in cutoff_data:
            for branch in cutoff_data[campus]:
                if branch in query:
                    branch_matches.append(branch)

        # Get the longest match (most specific)
        if branch_matches:
            specific_branch = max(branch_matches, key=len)

        # Enhanced campus detection with variations
        campus_patterns = {
            'pilani': ['pilani', 'pilani campus', 'bits pilani'],
            'goa': ['goa', 'goa campus', 'bits goa', 'k k birla goa'],
            'hyderabad': ['hyderabad', 'hyd', 'hyderabad campus', 'bits hyderabad', 'bits hyd']
        }

        for campus, patterns in campus_patterns.items():
            if any(pattern in query for pattern in patterns):
                specific_campus = campus
                break

        return self._format_cutoff_response(author, cutoff_data, specific_branch, specific_campus)

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
                # Specific branch + campus
                score = cutoff_data[specific_campus].get(specific_branch, 'N/A')
                campus_emoji, campus_desc = campus_info[specific_campus]
                response += f"{campus_emoji}\n"
                response += f"• {specific_branch.upper()}: **{score}/390**\n\n"
                response += f"*{campus_desc} - {specific_branch.upper()} cutoff specifically*\n"
            else:
                # Specific branch, all campuses
                response += f"**{specific_branch.upper()} CUTOFFS ACROSS CAMPUSES:**\n\n"
                for campus in ['pilani', 'goa', 'hyderabad']:
                    score = cutoff_data[campus].get(specific_branch, 'N/A')
                    if score != 'N/A':
                        campus_emoji, _ = campus_info[campus]
                        response += f"{campus_emoji}\n• {score}/390\n\n"

        # Specific campus query
        elif specific_campus:
            campus_emoji, campus_desc = campus_info[specific_campus]
            response += f"{campus_emoji}\n*{campus_desc}*\n\n"

            # Group branches by type
            engineering = ['cse', 'ece', 'eee', 'mechanical', 'chemical', 'civil', 'manufacturing', 'mathematics', 'instrumentation']
            science = ['biology', 'chemistry', 'economics', 'physics']
            pharmacy = ['pharmacy']

            for branch in engineering:
                if branch in cutoff_data[specific_campus]:
                    score = cutoff_data[specific_campus][branch]
                    response += f"• {branch.upper()}: {score}/390\n"

            if any(b in cutoff_data[specific_campus] for b in science):
                response += "\n**M.Sc Programs:**\n"
                for branch in science:
                    if branch in cutoff_data[specific_campus]:
                        score = cutoff_data[specific_campus][branch]
                        response += f"• {branch.upper()}: {score}/390\n"

            if any(b in cutoff_data[specific_campus] for b in pharmacy):
                response += "\n**Pharmacy:**\n"
                for branch in pharmacy:
                    if branch in cutoff_data[specific_campus]:
                        score = cutoff_data[specific_campus][branch]
                        response += f"• {branch.upper()}: {score}/390\n"

        # General query - show ALL branches from ALL campuses
        else:
            response += "**🎯 BITSAT 2024 COMPLETE CUTOFFS:**\n\n"
            for campus in ['pilani', 'goa', 'hyderabad']:
                campus_emoji, campus_desc = campus_info[campus]
                response += f"{campus_emoji}\n*{campus_desc}*\n\n"

                # Engineering branches
                engineering_branches = [
                    ('computer science', 'CSE'),
                    ('electronics and communication', 'ECE'),
                    ('electrical and electronics', 'EEE'),
                    ('mechanical', 'MECHANICAL'),
                    ('chemical', 'CHEMICAL'),
                    ('civil', 'CIVIL'),
                    ('manufacturing', 'MANUFACTURING'),
                    ('mathematics and computing', 'MATH & COMPUTING'),
                    ('electronics and instrumentation', 'INSTRUMENTATION')
                ]

                response += "**Engineering:**\n"
                for branch_key, display_name in engineering_branches:
                    if branch_key in cutoff_data[campus]:
                        score = cutoff_data[campus][branch_key]
                        response += f"• {display_name}: {score}/390\n"

                # Science branches
                science_branches = [
                    ('biological sciences', 'BIOLOGY'),
                    ('chemistry msc', 'CHEMISTRY'),
                    ('economics', 'ECONOMICS'),
                    ('physics', 'PHYSICS')
                ]

                if any(branch_key in cutoff_data[campus] for branch_key, _ in science_branches):
                    response += "\n**M.Sc Programs:**\n"
                    for branch_key, display_name in science_branches:
                        if branch_key in cutoff_data[campus]:
                            score = cutoff_data[campus][branch_key]
                            response += f"• {display_name}: {score}/390\n"

                # Pharmacy
                if 'pharmacy' in cutoff_data[campus]:
                    response += "\n**Pharmacy:**\n"
                    score = cutoff_data[campus]['pharmacy']
                    response += f"• B.PHARM: {score}/390\n"

                response += "\n"

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
        """Main bot loop"""
        if not self.authenticate():
            logger.error("Failed to authenticate. Please check your credentials.")
            return
        
        logger.info("BITSAT Bot started successfully!")
        logger.info(f"Monitoring r/{self.subreddit.display_name}")
        
        while True:
            try:
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
