"""多智能体模块 — Master Agent + Sub-Agent + FAQ 兜底。"""

from app.agents.master_agent import MasterAgent
from app.agents.schedule_agent import ScheduleAgent
from app.agents.repair_agent import RepairAgent
from app.agents.scholarship_agent import ScholarshipAgent
from app.agents.notice_agent import NoticeAgent
from app.agents.faq_agent import FAQAgent

__all__ = [
    "MasterAgent",
    "ScheduleAgent",
    "RepairAgent",
    "ScholarshipAgent",
    "NoticeAgent",
    "FAQAgent",
]
