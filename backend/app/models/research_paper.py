import uuid
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Uuid, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ResearchPaper(Base):
    __tablename__ = "research_papers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(500), nullable=True, index=True)
    doi = Column(String(500), nullable=True, unique=True, index=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    published_year = Column(Integer, nullable=True)
    journal = Column(String(500), nullable=True)
    volume = Column(String(50), nullable=True)
    issue = Column(String(50), nullable=True)
    pages = Column(String(100), nullable=True)
    open_access_url = Column(String(1000), nullable=True)
    is_open_access = Column(Boolean, default=False)
    citation_count = Column(Integer, default=0)
    language = Column(String(10), default="en")
    source_id = Column(Uuid(as_uuid=True), ForeignKey("research_sources.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    source = relationship("ResearchSource", back_populates="papers")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    topics = relationship("PaperTopic", back_populates="paper", cascade="all, delete-orphan")
    outgoing_citations = relationship(
        "PaperCitation", foreign_keys="PaperCitation.paper_id",
        back_populates="paper", cascade="all, delete-orphan"
    )
    datasets = relationship("PaperDataset", back_populates="paper", cascade="all, delete-orphan")
    methods = relationship("PaperMethod", back_populates="paper", cascade="all, delete-orphan")
    theories = relationship("PaperTheory", back_populates="paper", cascade="all, delete-orphan")
    policy_areas = relationship("PaperPolicyArea", back_populates="paper", cascade="all, delete-orphan")


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(Uuid(as_uuid=True), ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(500), nullable=False)
    affiliation = Column(String(500), nullable=True)
    orcid = Column(String(100), nullable=True)
    position = Column(Integer, nullable=True)  # author order

    paper = relationship("ResearchPaper", back_populates="authors")


class PaperTopic(Base):
    __tablename__ = "paper_topics"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(Uuid(as_uuid=True), ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(255), nullable=False)
    score = Column(Float, nullable=True)  # relevance score from source

    paper = relationship("ResearchPaper", back_populates="topics")


class PaperCitation(Base):
    __tablename__ = "paper_citations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(Uuid(as_uuid=True), ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False)
    cited_doi = Column(String(500), nullable=True)
    cited_title = Column(Text, nullable=True)
    cited_year = Column(Integer, nullable=True)

    paper = relationship("ResearchPaper", foreign_keys=[paper_id], back_populates="outgoing_citations")


class PaperDataset(Base):
    __tablename__ = "paper_datasets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(Uuid(as_uuid=True), ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False)
    dataset_name = Column(String(500), nullable=False)
    dataset_url = Column(String(1000), nullable=True)
    african_specific = Column(Boolean, default=False)

    paper = relationship("ResearchPaper", back_populates="datasets")


class PaperMethod(Base):
    __tablename__ = "paper_methods"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(Uuid(as_uuid=True), ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False)
    method_name = Column(String(255), nullable=False)
    method_type = Column(String(100), nullable=True)  # econometric | qualitative | mixed | ML

    paper = relationship("ResearchPaper", back_populates="methods")


class PaperTheory(Base):
    __tablename__ = "paper_theories"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(Uuid(as_uuid=True), ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False)
    theory_name = Column(String(255), nullable=False)
    field = Column(String(100), nullable=True)

    paper = relationship("ResearchPaper", back_populates="theories")


class PaperPolicyArea(Base):
    __tablename__ = "paper_policy_areas"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(Uuid(as_uuid=True), ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False)
    area = Column(String(255), nullable=False)
    sdg_goal = Column(Integer, nullable=True)

    paper = relationship("ResearchPaper", back_populates="policy_areas")
