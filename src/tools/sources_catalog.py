from dataclasses import dataclass


@dataclass(frozen=True)
class OpportunitySource:
    name: str
    url: str
    category: str
    description: str
    feed_url: str | None = None


SOURCES_CATALOG: tuple[OpportunitySource, ...] = (
    # African & Ethiopian Opportunities (14 sources)
    OpportunitySource("EthioScholarship", "https://scholarship.et", "african", "Ethiopian scholarship & fellowship portal"),
    OpportunitySource("EthioOpportunity", "https://www.ethioopportunity.com", "african", "Ethiopian youth jobs, grants & study calls"),
    OpportunitySource("Opportunities for Africans", "https://www.opportunitiesforafricans.com", "african", "Pan-African youth fellowships & grants", "https://www.opportunitiesforafricans.com/feed/"),
    OpportunitySource("Shega Media", "https://shega.co", "african", "Ethiopian tech ecosystem, startups & innovations", "https://shega.co/feed/"),
    OpportunitySource("TechCabal", "https://techcabal.com", "african", "African tech industry, funding & fellowship coverage", "https://techcabal.com/feed/"),
    OpportunitySource("Disrupt Africa", "https://disrupt-africa.com", "african", "African startup competitions & funding rounds", "https://disrupt-africa.com/feed/"),
    OpportunitySource("Opportunity Desk", "https://opportunitydesk.org", "african", "Global & African youth opportunities portal", "https://opportunitydesk.org/feed/"),
    OpportunitySource("Scholars4Dev", "https://www.scholars4dev.com", "african", "International scholarships for developing countries", "https://www.scholars4dev.com/feed/"),
    OpportunitySource("AfterSchoolAfrica", "https://afterschoolafrica.com", "african", "African scholarships and young leader programs", "https://afterschoolafrica.com/feed/"),
    OpportunitySource("ALX Africa", "https://alxafrica.com", "african", "Tech fellowships, software engineering & cloud training"),
    OpportunitySource("AIMS Africa", "https://aims.ac.za", "african", "Data science & AI master's fellowships across Africa"),
    OpportunitySource("Deep Learning Indaba", "https://deeplearningindaba.com", "african", "African AI grants, travel awards & workshops"),
    OpportunitySource("Zindi Africa", "https://zindi.africa", "african", "African machine learning hackathons & data challenges"),
    OpportunitySource("Mastercard Foundation", "https://mastercardfdn.org", "african", "Fully-funded education & leadership in Africa"),

    # Global Hackathons & Coding Challenges (10 sources)
    OpportunitySource("Devpost", "https://devpost.com", "hackathon", "Global hackathon platform for online developer competitions"),
    OpportunitySource("Lablab.ai", "https://lablab.ai", "hackathon", "Global generative AI hackathons & model challenges"),
    OpportunitySource("DoraHacks", "https://dorahacks.io", "hackathon", "Open-source developer bounties, grants & hackathons"),
    OpportunitySource("HackerEarth", "https://hackerearth.com", "hackathon", "International developer challenges & hiring sprints"),
    OpportunitySource("TAIKAI", "https://taikai.network", "hackathon", "Virtual hackathons, web3 challenges & open competitions"),
    OpportunitySource("Kaggle Competitions", "https://kaggle.com/competitions", "hackathon", "World premier data science and ML competitions"),
    OpportunitySource("Major League Hacking", "https://mlh.io", "hackathon", "Global student hackathon league and innovation seasons"),
    OpportunitySource("Unstop", "https://unstop.com", "hackathon", "International tech competitions & student hackathons"),
    OpportunitySource("ETHGlobal", "https://ethglobal.com", "hackathon", "Smart contract and decentralized systems hackathons"),
    OpportunitySource("Google AI Competitions", "https://ai.google.dev/competition", "hackathon", "Google developer and Gemini API challenges"),

    # Prestigious Global Fellowships & Grants (12 sources)
    OpportunitySource("IREX Community Solutions", "https://www.irex.org", "fellowship", "Global community leadership fellowships"),
    OpportunitySource("Hurford Youth Fellowship", "https://hurfordfellows.ned.org", "fellowship", "Global youth leadership and civic tech fellowship"),
    OpportunitySource("EDSAFE AI Alliance", "https://edsafeai.org", "fellowship", "Policy, education & AI safety fellowships"),
    OpportunitySource("Schmidt Science Fellows", "https://schmidtsciencefellows.org", "fellowship", "Interdisciplinary postdoctoral research fellowships"),
    OpportunitySource("Echoing Green", "https://www.echoinggreen.org", "fellowship", "Seed funding and fellowship for emerging social innovators"),
    OpportunitySource("Obama Foundation Leaders", "https://www.obama.org", "fellowship", "Global leadership fellowship with cross-regional mentors"),
    OpportunitySource("CODESRIA Fellowships", "https://www.codesria.org", "fellowship", "African research grants & academic fellowships"),
    OpportunitySource("JIAS Johannesburg Institute", "https://jias.joburg", "fellowship", "Advanced study writing and research fellowships"),
    OpportunitySource("Rotary Peace Fellowships", "https://rotary.org", "fellowship", "Fully funded master's and professional certificates"),
    OpportunitySource("CIFAR Azrieli Scholars", "https://cifar.ca", "fellowship", "Early-career research acceleration program"),
    OpportunitySource("Mozilla Tech Fellowships", "https://mozillafoundation.org", "fellowship", "Tech policy, open-source & ethical AI fellows"),
    OpportunitySource("Shuttleworth Foundation", "https://www.shuttleworthfoundation.org", "fellowship", "Grants for open-source innovators"),

    # International Scholarships for Students & Freshers (10 sources)
    OpportunitySource("DAAD Germany", "https://www.daad.de", "scholarship", "German academic study & research scholarships"),
    OpportunitySource("Chevening UK", "https://www.chevening.org", "scholarship", "UK Government fully funded international master's"),
    OpportunitySource("Fulbright Foreign Student", "https://foreign.fulbrightonline.org", "scholarship", "US graduate study & research scholarships"),
    OpportunitySource("Erasmus Mundus", "https://erasmus-plus.ec.europa.eu", "scholarship", "EU fully-funded joint master's degrees in Europe"),
    OpportunitySource("Türkiye Bursları", "https://www.turkiyeburslari.gov.tr", "scholarship", "Full government scholarships for international students"),
    OpportunitySource("MEXT Japan", "https://www.mext.go.jp", "scholarship", "Japanese Ministry of Education scholarships"),
    OpportunitySource("Chinese Government CSC", "https://csc.edu.cn", "scholarship", "Fully-funded Chinese university scholarships"),
    OpportunitySource("Gates Cambridge", "https://www.gatescambridge.org", "scholarship", "University of Cambridge full postgraduate scholarships"),
    OpportunitySource("Rhodes Trust Oxford", "https://www.rhodeshouse.ox.ac.uk", "scholarship", "International graduate scholarship at Oxford"),
    OpportunitySource("Commonwealth Scholarships", "https://commonwealthscholarships.org", "scholarship", "UK scholarships for developing Commonwealth nations"),

    # Cutting-Edge AI & Tech News Feeds (10 sources)
    OpportunitySource("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/", "ai_news", "Breaking AI startups, tools & models", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    OpportunitySource("VentureBeat AI", "https://venturebeat.com/category/ai/", "ai_news", "Enterprise AI & foundation model benchmarks", "https://venturebeat.com/category/ai/feed/"),
    OpportunitySource("Hacker News", "https://news.ycombinator.com", "ai_news", "Top tech discussions and open launches"),
    OpportunitySource("ArXiv cs.AI", "https://arxiv.org/list/cs.AI/recent", "ai_news", "Latest AI & machine learning research papers", "http://export.arxiv.org/rss/cs.AI"),
    OpportunitySource("Hugging Face Daily", "https://huggingface.co/papers", "ai_news", "Daily curated AI research papers & open models"),
    OpportunitySource("MIT News AI", "https://news.mit.edu/topic/artificial-intelligence2", "ai_news", "Breakthrough robotics & computing research", "https://news.mit.edu/rss/topic/artificial-intelligence2"),
    OpportunitySource("The Verge AI", "https://theverge.com/ai-artificial-intelligence", "ai_news", "Consumer AI, tech policy & industry updates", "https://www.theverge.com/rss/index.xml"),
    OpportunitySource("Wired AI", "https://wired.com/category/artificial-intelligence/", "ai_news", "Deep-dive tech journalism & AI insights", "https://www.wired.com/feed/category/ai/latest/rss"),
    OpportunitySource("GitHub Trending", "https://github.com/trending", "ai_news", "Trending developer repositories & AI packages"),
    OpportunitySource("Simon Willison Weblog", "https://simonwillison.net", "ai_news", "AI engineering, prompt injection & open tools", "https://simonwillison.net/atom/everything/"),
)


def get_all_sources() -> tuple[OpportunitySource, ...]:
    """Return all sources in the 50+ sources catalog."""
    return SOURCES_CATALOG


def get_sources_by_category(category: str) -> list[OpportunitySource]:
    """Filter sources by specific category."""
    return [s for s in SOURCES_CATALOG if s.category == category]


def get_feed_sources(category: str | None = None) -> list[OpportunitySource]:
    """Return sources with active RSS / Atom feeds."""
    return [s for s in SOURCES_CATALOG if s.feed_url and (not category or s.category == category)]


def get_total_source_count() -> int:
    """Return the total number of sources registered."""
    return len(SOURCES_CATALOG)
