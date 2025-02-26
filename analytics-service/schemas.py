"""
Pydantic schemas for the Analytics Service.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

class EventBase(BaseModel):
    event_type: str
    tenant_id: str
    timestamp: datetime
    event_id: str

class TaskEventData(EventBase):
    task_id: str
    project_id: str
    user_id: str
    status: Optional[str]
    metadata: Optional[Dict[str, Any]]

class URLEventData(EventBase):
    url_id: str
    short_code: str
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    referrer: Optional[str]
    metadata: Optional[Dict[str, Any]]

class AnalyticsSummary(BaseModel):
    total_projects: int
    total_tasks: int
    tasks_completed: int
    tasks_in_progress: int
    average_completion_time: Optional[float]
    total_urls: int
    total_url_clicks: int
    top_projects: List[Dict[str, Any]]
    top_urls: List[Dict[str, Any]]