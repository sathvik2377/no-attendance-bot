# 🤖 No_Attendance_Bot

A sassy, dark humor Reddit bot for r/bitsatards that provides BITSAT cutoff data with unhinged commentary and motivational roasting.

## 🎯 Features

- **Intelligent Natural Language Processing**: Understands specific cutoff queries without special commands
- **Complete BITSAT 2024 Cutoff Data**: All campuses (Pilani, Goa, Hyderabad) and branches
- **Dark Humor & Hinglish**: Unique responses with psychological warfare disguised as motivation
- **Selective Responses**: Only responds to direct cutoff questions and ! commands (no spam)
- **Bot-Proof**: Won't reply to AutoModerator or other bots
- **Fast Response Time**: 5-15 seconds response time
- **24/7 Ready**: Designed for continuous cloud deployment

## 🧠 How It Works

The bot is highly selective and only responds to:
1. **Direct commands** starting with "!" 
2. **Specific cutoff questions** with clear intent
3. **Human users only** (ignores all bots including AutoModerator)

## 💬 Supported Queries

### Direct Commands (with ! prefix)
- `!cutoff` - Shows all campus and branch cutoffs
- `!cutoff for CSE` - CSE cutoffs across all campuses
- `!cutoff for Goa` - All Goa campus cutoffs
- `!cutoff for mechanical in Pilani` - Specific branch + campus

### Natural Language (Very Specific Questions Only)
- "What is the cutoff for CSE?"
- "Tell me the cutoff for Goa"
- "Cutoff kya hai for Pilani?"
- "How many marks needed for mechanical?"
- "Required marks for biology"

### ❌ Won't Respond To:
- General BITSAT discussions
- Casual mentions of campuses/branches
- Study tips or preparation advice
- AutoModerator or bot comments
- Random conversations

## 📊 Cutoff Data Coverage

**Campuses:**
- 🏛️ Pilani Campus (All branches)
- 🏖️ Goa Campus (All branches) 
- 🏙️ Hyderabad Campus (All branches)

**Branches:**
- **Engineering**: CSE, ECE, EEE, Mechanical, Chemical, Civil, Manufacturing, Math & Computing, Instrumentation
- **M.Sc**: Biology, Chemistry, Physics, Economics, Mathematics
- **Pharmacy**: B.Pharm

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Reddit account and app credentials
- Required packages (see requirements.txt)

### Local Installation

1. **Clone the repository:**
```bash
git clone https://github.com/sathvik2377/no-attendance-bot.git
cd no-attendance-bot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
Create a `.env` file with:
```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
```

4. **Run the bot:**
```bash
python reddit_bot.py
```

## ☁️ Cloud Deployment (24/7)

### Railway (Recommended - $5/month for unlimited)
1. Fork this repository
2. Go to https://railway.app
3. Connect your GitHub repo
4. Add environment variables in Railway dashboard
5. Deploy automatically

### Free Options (Limited Hours)
- **Render**: 750 hours/month free
- **Railway Free**: 500 hours/month
- **Fly.io**: Free tier available

## 📝 Response Style Examples

### Sample Cutoff Response:
```
Arre username, CSE at PILANI? Prepare for emotional damage:

🏛️ PILANI CAMPUS
The original dream crusher

• CSE: 327/390

Numbers don't define you - but they sure love to roast you! 💀
Cutoff dekh ke cry mat kar, grind kar! Tears won't get you admission 😈

📊 More detailed trauma: https://www.bitsadmission.com/FD/BITSAT_cutoffs.html?06012025
```

### Sample Command Response:
```
Arre username, complete BITSAT cutoff apocalypse incoming:

🏛️ PILANI CAMPUS - The original dream crusher
• CSE: 327/390 • ECE: 315/390 • EEE: 298/390

🏖️ GOA CAMPUS - Where dreams go to die by the beach  
• CSE: 312/390 • ECE: 301/390 • EEE: 285/390

🏙️ HYDERABAD CAMPUS - Tech city trauma center
• CSE: 318/390 • ECE: 307/390 • EEE: 291/390

BITSAT is temporary, but the emotional damage is forever! 💪😈
```

## 🛡️ Safety Features

- **Selective Response System**: Only responds to specific cutoff queries
- **Bot Detection**: Ignores AutoModerator and other bots
- **Anti-Spam**: Prevents duplicate responses
- **Error Handling**: Auto-restart on network issues
- **Rate Limiting**: Respects Reddit API limits

## 📋 File Structure

```
├── reddit_bot.py          # Main bot code
├── requirements.txt       # Python dependencies  
├── Procfile              # For Railway deployment
├── runtime.txt           # Python version specification
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore file (protects credentials)
└── README.md             # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## ⚠️ Disclaimer

This bot contains dark humor and sarcastic responses. It's designed for entertainment and information purposes within the r/bitsatards community. The roasting is all in good fun - don't take it personally! 

## 📄 License

This project is open source. Use responsibly and follow Reddit's content policy and subreddit rules.

## 🆘 Support

If you encounter issues:
1. Check the logs in `bot.log`
2. Verify your Reddit API credentials
3. Ensure you have the latest dependencies
4. Check Reddit API status
5. Open an issue on GitHub

## 🔗 Links

- **Repository**: https://github.com/sathvik2377/no-attendance-bot
- **Deploy on Railway**: https://railway.app
- **BITS Official Cutoffs**: https://www.bitsadmission.com/FD/BITSAT_cutoffs.html

---

**Made with 💀 and dark humor for the r/bitsatards community**

*Remember: BITSAT is temporary, but the trauma is forever! Stay strong! 💪*

**Bot Status**: Currently deployed and roasting students 24/7 😈
