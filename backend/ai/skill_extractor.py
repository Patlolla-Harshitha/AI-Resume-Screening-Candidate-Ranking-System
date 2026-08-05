"""
Comprehensive skill extractor with an extensive taxonomy of technical and soft skills.
Supports rule-based matching and fuzzy matching via RapidFuzz.
New skill categories can be added by extending SKILL_TAXONOMY.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from rapidfuzz import fuzz, process

from utils.logger import get_logger
from utils.text_utils import normalize_whitespace

logger = get_logger("ai.skill_extractor")

# ---------------------------------------------------------------------------
# Skill Taxonomy — extend by adding entries to any category
# ---------------------------------------------------------------------------
SKILL_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C", "C++", "C#", "Go", "Rust",
        "Kotlin", "Swift", "Ruby", "PHP", "Scala", "R", "MATLAB", "Perl", "Bash",
        "Shell", "PowerShell", "Dart", "Lua", "Haskell", "Elixir", "Clojure",
        "Fortran", "COBOL", "Assembly", "Julia", "Groovy", "F#", "VB.NET", "Apex",
        "PL/SQL", "T-SQL", "VHDL", "Verilog", "Prolog", "Lisp", "Erlang",
    ],
    "Web Frameworks": [
        "React", "React.js", "ReactJS", "Angular", "AngularJS", "Vue", "Vue.js", "VueJS",
        "Next.js", "Nuxt.js", "Svelte", "Gatsby", "Remix", "Astro", "Ember.js",
        "FastAPI", "Django", "Flask", "Express", "Express.js", "NestJS", "Spring Boot",
        "Spring", "Ruby on Rails", "Laravel", "Symfony", "ASP.NET", "ASP.NET Core",
        "Gin", "Echo", "Fiber", "Actix", "Rocket", "Phoenix", "Sinatra",
        "Hapi.js", "Koa.js", "Fastify", "Strapi", "Sails.js",
    ],
    "Mobile Development": [
        "React Native", "Flutter", "SwiftUI", "UIKit", "Android SDK", "Xamarin",
        "Ionic", "Cordova", "Expo", "Kotlin Multiplatform",
    ],
    "Databases": [
        "PostgreSQL", "MySQL", "SQLite", "SQL Server", "Oracle", "MariaDB",
        "MongoDB", "Redis", "Cassandra", "DynamoDB", "Elasticsearch", "Solr",
        "CouchDB", "Neo4j", "InfluxDB", "TimescaleDB", "Snowflake", "BigQuery",
        "Redshift", "Hive", "HBase", "Firebase", "Supabase", "PlanetScale",
        "CockroachDB", "RethinkDB", "ArangoDB", "Realm",
    ],
    "Cloud Platforms": [
        "AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP",
        "Google Cloud", "Google Cloud Platform", "Heroku", "DigitalOcean",
        "Linode", "Vercel", "Netlify", "Cloudflare", "IBM Cloud", "Oracle Cloud",
        "Alibaba Cloud", "OVHcloud",
    ],
    "Cloud Services": [
        "EC2", "S3", "Lambda", "RDS", "ECS", "EKS", "CloudFormation", "CloudWatch",
        "IAM", "VPC", "Route 53", "CloudFront", "SNS", "SQS", "API Gateway",
        "Azure Functions", "Azure DevOps", "Azure Blob Storage", "Azure AKS",
        "Google Kubernetes Engine", "GKE", "Cloud Run", "Pub/Sub", "Cloud Storage",
        "BigQuery", "Vertex AI",
    ],
    "DevOps & CI/CD": [
        "Docker", "Kubernetes", "Helm", "Jenkins", "GitHub Actions", "GitLab CI",
        "CircleCI", "Travis CI", "Bitbucket Pipelines", "ArgoCD", "Terraform",
        "Ansible", "Puppet", "Chef", "Vagrant", "Packer", "Prometheus", "Grafana",
        "Datadog", "New Relic", "Splunk", "ELK Stack", "Elasticsearch Logstash Kibana",
        "Vault", "Consul", "Istio", "Linkerd", "Nginx", "Apache", "HAProxy",
        "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence",
    ],
    "AI/ML": [
        "Machine Learning", "Deep Learning", "Neural Networks", "NLP",
        "Natural Language Processing", "Computer Vision", "Reinforcement Learning",
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "sklearn",
        "Hugging Face", "Transformers", "BERT", "GPT", "LLM", "Large Language Model",
        "Sentence Transformers", "spaCy", "NLTK", "Gensim", "OpenCV",
        "XGBoost", "LightGBM", "CatBoost", "Random Forest",
        "SVM", "Support Vector Machine", "Linear Regression", "Logistic Regression",
        "K-Means", "DBSCAN", "PCA", "t-SNE", "UMAP",
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
        "MLflow", "Weights & Biases", "DVC", "Kubeflow", "Airflow",
        "LangChain", "LlamaIndex", "RAG", "Vector Database", "Pinecone", "Weaviate",
        "FAISS", "Chroma", "Milvus", "OpenAI API", "Anthropic Claude",
    ],
    "Data Engineering": [
        "Apache Spark", "Spark", "Kafka", "Apache Kafka", "Flink", "Hadoop",
        "Hive", "Presto", "dbt", "Airflow", "Luigi", "Prefect", "Dagster",
        "Databricks", "Delta Lake", "Iceberg", "ETL", "ELT", "Data Pipeline",
        "Data Warehouse", "Data Lake", "Data Lakehouse",
    ],
    "Testing": [
        "Pytest", "unittest", "Jest", "Mocha", "Chai", "Cypress", "Playwright",
        "Selenium", "Puppeteer", "JUnit", "TestNG", "RSpec", "PHPUnit",
        "Postman", "Newman", "K6", "Locust", "JMeter",
        "TDD", "BDD", "Integration Testing", "Unit Testing", "E2E Testing",
    ],
    "APIs & Protocols": [
        "REST", "RESTful", "GraphQL", "gRPC", "WebSocket", "WebSockets",
        "SOAP", "OpenAPI", "Swagger", "JSON", "XML", "Protobuf",
        "OAuth", "OAuth2", "JWT", "OpenID Connect", "SAML",
        "HTTP", "HTTPS", "TCP/IP", "MQTT", "AMQP", "WebRTC",
    ],
    "Security": [
        "Cybersecurity", "Information Security", "Penetration Testing",
        "OWASP", "SSL/TLS", "PKI", "Cryptography", "IAM", "Zero Trust",
        "SIEM", "SOC", "Vulnerability Assessment", "VAPT",
        "Kali Linux", "Metasploit", "Burp Suite", "Wireshark",
        "ISO 27001", "SOC 2", "GDPR", "HIPAA", "PCI DSS",
    ],
    "Version Control": [
        "Git", "GitHub", "GitLab", "Bitbucket", "SVN", "Mercurial",
        "Git Flow", "Trunk Based Development",
    ],
    "Project Management": [
        "Agile", "Scrum", "Kanban", "SAFe", "Waterfall", "Lean",
        "Jira", "Confluence", "Trello", "Asana", "Notion",
        "Product Management", "Sprint Planning", "Retrospective",
    ],
    "Soft Skills": [
        "Communication", "Leadership", "Teamwork", "Team Player", "Problem Solving",
        "Critical Thinking", "Analytical", "Creativity", "Innovation",
        "Time Management", "Adaptability", "Attention to Detail",
        "Collaboration", "Mentoring", "Presentation", "Negotiation",
        "Decision Making", "Conflict Resolution", "Empathy", "Emotional Intelligence",
        "Project Management", "Stakeholder Management", "Client Relations",
        "Cross-functional", "Self-motivated", "Result-oriented",
    ],
    "Design & UI/UX": [
        "Figma", "Adobe XD", "Sketch", "InVision", "Zeplin", "Photoshop",
        "Illustrator", "UX Design", "UI Design", "Wireframing", "Prototyping",
        "User Research", "Usability Testing", "Design Systems",
        "Material Design", "Tailwind CSS", "Bootstrap", "Ant Design",
    ],
    "Blockchain": [
        "Blockchain", "Ethereum", "Solidity", "Web3.js", "Hardhat", "Truffle",
        "Smart Contracts", "NFT", "DeFi", "Hyperledger", "Polkadot",
    ],
    "Embedded & IoT": [
        "Arduino", "Raspberry Pi", "RTOS", "Embedded C", "FreeRTOS",
        "IoT", "MQTT", "Zigbee", "LoRa", "CAN Bus", "UART", "SPI", "I2C",
    ],
    "Operating Systems": [
        "Linux", "Ubuntu", "CentOS", "Debian", "Red Hat", "RHEL",
        "Windows Server", "macOS", "UNIX", "FreeBSD",
    ],
    "Certifications Domains": [
        "AWS Certified", "Azure Certified", "GCP Certified", "CKA", "CKAD",
        "PMP", "Scrum Master", "CSM", "CISSP", "CEH", "OSCP", "CompTIA",
        "Oracle Certified", "Salesforce Certified", "Google Certified",
    ],
}

# Build a flat lookup: lowercase skill -> (canonical skill, category)
_SKILL_LOOKUP: Dict[str, Tuple[str, str]] = {}
for _category, _skills in SKILL_TAXONOMY.items():
    for _skill in _skills:
        _SKILL_LOOKUP[_skill.lower()] = (_skill, _category)


@dataclass
class ExtractedSkills:
    """Container for structured skill extraction results."""

    all_skills: List[str] = field(default_factory=list)
    categorized: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {"all_skills": self.all_skills, "categorized": self.categorized}


class SkillExtractor:
    """
    Multi-strategy skill extractor that combines:
    1. Direct string matching (case-insensitive)
    2. Regex word-boundary matching for multi-word skills
    3. Optional fuzzy matching via RapidFuzz (for slight misspellings)
    """

    def __init__(self, fuzzy_threshold: int = 88, use_fuzzy: bool = True) -> None:
        """
        Args:
            fuzzy_threshold: Minimum RapidFuzz score (0–100) to accept a fuzzy match.
            use_fuzzy:       Whether to enable fuzzy matching (slightly slower).
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.use_fuzzy = use_fuzzy
        self._skill_names_lower: List[str] = list(_SKILL_LOOKUP.keys())
        logger.debug(
            "SkillExtractor initialized with %d skills across %d categories",
            len(_SKILL_LOOKUP),
            len(SKILL_TAXONOMY),
        )

    def extract(self, text: str) -> ExtractedSkills:
        """
        Extract skills from the given text.

        Args:
            text: Resume or job description text.

        Returns:
            ExtractedSkills: All matched skills with categories.
        """
        if not text:
            return ExtractedSkills()

        text_lower = normalize_whitespace(text).lower()
        found: Dict[str, str] = {}  # canonical_skill -> category

        # --- Strategy 1: Direct exact match with word boundaries ---
        for skill_lower, (canonical, category) in _SKILL_LOOKUP.items():
            # Use word boundary regex to avoid partial matches
            pattern = r"\b" + re.escape(skill_lower) + r"\b"
            if re.search(pattern, text_lower):
                found[canonical] = category

        # --- Strategy 2: Fuzzy matching for unmatched tokens ---
        if self.use_fuzzy:
            # Tokenize into n-grams (1–3 words)
            words = text_lower.split()
            candidates: Set[str] = set()
            for n in range(1, 4):
                for i in range(len(words) - n + 1):
                    ngram = " ".join(words[i: i + n])
                    if len(ngram) >= 3:
                        candidates.add(ngram)

            for candidate in candidates:
                if candidate in _SKILL_LOOKUP:
                    continue  # Already found by exact match
                result = process.extractOne(
                    candidate,
                    self._skill_names_lower,
                    scorer=fuzz.ratio,
                    score_cutoff=self.fuzzy_threshold,
                )
                if result:
                    matched_lower = result[0]
                    canonical, category = _SKILL_LOOKUP[matched_lower]
                    found[canonical] = category

        # Build categorized output
        categorized: Dict[str, List[str]] = {}
        for canonical, category in found.items():
            categorized.setdefault(category, []).append(canonical)

        # Sort within each category for consistent output
        for cat in categorized:
            categorized[cat] = sorted(set(categorized[cat]))

        all_skills = sorted(found.keys())

        logger.debug("Extracted %d skills from text (%d chars)", len(all_skills), len(text))

        return ExtractedSkills(all_skills=all_skills, categorized=categorized)

    def extract_from_list(self, texts: List[str]) -> List[ExtractedSkills]:
        """
        Batch extract skills from multiple texts.

        Args:
            texts: List of text strings.

        Returns:
            List[ExtractedSkills]: One result per input text.
        """
        return [self.extract(t) for t in texts]

    @staticmethod
    def get_all_skill_names() -> List[str]:
        """Return the canonical names of all skills in the taxonomy."""
        return [canonical for canonical, _ in _SKILL_LOOKUP.values()]

    @staticmethod
    def get_categories() -> List[str]:
        """Return all skill category names."""
        return list(SKILL_TAXONOMY.keys())


# Module-level singleton
_extractor_instance: Optional[SkillExtractor] = None


def get_skill_extractor() -> SkillExtractor:
    """Return the singleton SkillExtractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = SkillExtractor()
    return _extractor_instance
