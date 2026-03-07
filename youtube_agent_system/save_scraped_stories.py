# Save scraped Reddit stories to knowledge base
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_agent_system import knowledge_base
from youtube_agent_system.tools.reddit_browser_scraper import calculate_viral_score

# Stories scraped from r/AmItheAsshole via browser
stories = [
    {
        'id': 'aita_naked_room_001',
        'subreddit': 'AmItheAsshole',
        'category': 'AITA',
        'title': 'AITA for sleeping naked in my own room?',
        'content': '''throw away account cause i don't want my roommate to see this. since i was a teenager i've always slept naked. i always get too hot at night and its just generally way more comfortable for me to sleep that way. whenever i leave my room i'm always dressed, or at the very least have shorts or something on if i'm going to/from the shower. my roommate knows this and up to this point has had no problem with it and we always knock on each others doors anyway to be polite. the issue started when he brought over his girlfriend to stay a couple nights. we all get along pretty well and have all hung out a few times before, but this was the first time she had come over and spent the night. we had all gone out drinking and got home pretty late so once we all walked in we just went straight to sleep. i, of course, went to bed with my usual routine of getting naked and hopping in bed. well, sometime during the night my roommate's girlfriend needed to use the bathroom, but she didn't know which room it was. my room and the bathroom are right next to each other and she opened my door by mistake. i have a vague memory of her opening my door, but i was half asleep and when she closed it i went right back to sleep. the next morning i woke up and my roommate and his girlfriend were upset with me because when she walked in she saw everything and she was mad i would sleep naked when a guest was over in the first place. they both said i need to start wearing clothes to sleep since my roommate's girlfriend is gonna probably be sleeping over more often and it makes her uncomfortable.''',
        'score': 9524,
        'word_count': 350,
    },
    {
        'id': 'aita_sister_wedding_002',
        'subreddit': 'AmItheAsshole',
        'category': 'AITA', 
        'title': "AITA for telling my sister not to come to my wedding if she kept bringing up her miscarriage?",
        'content': '''3 years ago my younger sister Jen had a miscarriage at 9 weeks. She and her partner Scott were devastated. I was there for them as much as I could be but it was a tough time for them. A few months later Scott left Jen: Jen said it was because of the miscarriage. Her and Scott had a close knit group of friends and I found it odd no one has checked on her so I rang her best friend to suggest a girls night. She told me the reason they had broke up: Jen had slept with someone else. When he confronted her she blamed the miscarriage. 9 months ago I got engaged and asked Jen to be my MoH. At our engagement party Jen became inconsolable at seeing our friends baby. Everyone's focus - including mine - was on Jen all night. Since then anything to do with the wedding, she brings up her miscarriage - but only at events related to my wedding. I asked her to help me pick flowers and she lost it when she saw baby blue roses. When we went wedding dress shopping and she picked out a maternity bridesmaid dress and asked to try it on so that she could see how she would have looked. She planned my hen party which I was so grateful for but I found out after she'd sent everyone a list of rules which included no talking about pregnancy or kids.''',
        'score': 9384,
        'word_count': 300,
    },
    {
        'id': 'aita_cat_food_003',
        'subreddit': 'AmItheAsshole',
        'category': 'AITA',
        'title': "AITA for asking my boyfriend's dad whether he planned on eating his pet cat?",
        'content': '''I (19F) met my boyfriend (26M)'s parents for the first time last weekend over lunch. He warned me his parents could be a little bit weird so I was prepared for that but during the lunch they made repeated jabs at me for my age which I did not appreciate. The topic of pets came up in the conversation and I told them about my pet rabbits. When his dad heard this he asked whether I was raising them for food and at this point I was quite offended and said "well are you raising that cat for food?" and pointed at their cat, to which he said something to the effect of "don't talk back" which I found quite infantilising and a bit creepy. I excused myself from the lunch.''',
        'score': 7428,
        'word_count': 140,
    },
    {
        'id': 'aita_group_plan_004',
        'subreddit': 'AmItheAsshole',
        'category': 'AITA',
        'title': 'AITA for quietly leaving a group plan after being left out of the conversation?',
        'content': '''Last weekend, a small group of friends (5 of us total) made plans to meet up for dinner and then walk around a local street fair. The plan itself was casual, but it was something we'd all agreed on earlier in the week. I cleared my evening for it. The day of, we were coordinating through a group chat. I messaged asking what time we were meeting and where exactly. No one responded. About 15 minutes later, I saw two people in the chat sending memes to each other, so I figured they'd seen my message and would answer soon. They didn't. I sent a follow-up about 20 minutes later asking if plans had changed. Still nothing. At that point, I assumed maybe everyone was already together and just forgot to loop me in. I went ahead and drove to the general area we'd talked about, thinking I'd figure it out when I got there. I parked, walked around for a bit, and kept checking my phone. Eventually I saw on social media that two of them were already at a restaurant nearby. I didn't want to cause a scene or make things awkward, so instead of confronting anyone, I just went home.''',
        'score': 7013,
        'word_count': 230,
    },
    {
        'id': 'aita_concert_ticket_005',
        'subreddit': 'AmItheAsshole',
        'category': 'AITA',
        'title': 'AITA for not buying my niece a concert ticket for Christmas?',
        'content': '''So in addition to our regular presents we've gotten our daughter a ticket to a concert happening on the 30th. I'm going too, primarily because I need to take her, but also I like that band's music and I want to go with her it'll be a nice experience. Today, my sister in law called me and asked what we were doing on New Year's Eve. I said I'm not sure I'll probably be super tired from the drive back and told her we've gotten our daughter a surprise concert ticket. She seemed a bit disappointed and said her daughter would have loved to go too, asked if tickets were available, I said I didn't know, and she reiterated her daughter would have loved to go too. I hate saying it, and please don't take this the wrong way but my husband has his business and I'm a working professional too, and our daughter is an only child, so I understand the difference in spending constraints.''',
        'score': 6062,
        'word_count': 180,
    },
]

# Calculate viral scores and save each story
print("Saving scraped Reddit stories to knowledge base...")
for story in stories:
    story['viral_score'] = calculate_viral_score(story)
    knowledge_base.save_reddit_story(
        story_id=story['id'],
        story_data=story,
        metadata={'category': story['category'], 'subreddit': story['subreddit']}
    )
    print(f"  Saved: {story['title'][:50]}... (viral_score: {story['viral_score']})")

# Show stats
print("\nKnowledge base stats:")
stats = knowledge_base.get_knowledge_base_stats()
print(f"  Reddit stories: {stats['reddit_stories']}")
print(f"  Rival videos: {stats['rival_videos_analyzed']}")
print(f"  Total patterns: {stats['patterns_saved']}")

# Get top stories
print("\nTop stories by viral score:")
top_stories = knowledge_base.get_top_reddit_stories(n=5)
for s in top_stories:
    print(f"  [{s['viral_score']}] {s['title'][:50]}...")

print("\nDone!")
