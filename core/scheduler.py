import schedule
import time
import datetime
from core.task import Task, TaskPriority

def _run_scheduler(self):
    """Run the scheduler for periodic tasks"""
    # Set up daily jobs
    schedule.every().day.at("08:00").do(self._morning_routine)
    schedule.every().day.at("17:00").do(self._evening_routine)
    
    # Set up hourly jobs
    schedule.every().hour.do(self._hourly_check)
    
    # Set up weekly jobs
    schedule.every().monday.at("09:00").do(self._weekly_planning)
    schedule.every().friday.at("16:00").do(self._weekly_review)
    
    while self.running:
        schedule.run_pending()
        time.sleep(1)

def _morning_routine(self):
    """Morning routine tasks"""
    # Add various morning tasks to the queue
    self.add_task(Task(
        id=f"morning-review-{datetime.date.today()}",
        description="Review overnight customer support tickets and prioritize responses",
        agent_name="customer_support",
        priority=TaskPriority.HIGH
    ))
    
    self.add_task(Task(
        id=f"daily-standup-{datetime.date.today()}",
        description="Prepare daily standup agenda and project status updates",
        agent_name="admin",
        priority=TaskPriority.MEDIUM
    ))
    
    self.add_task(Task(
        id=f"social-content-{datetime.date.today()}",
        description="Schedule today's social media posts based on content calendar",
        agent_name="marketing",
        priority=TaskPriority.MEDIUM
    ))

def _evening_routine(self):
    """Evening routine tasks"""
    self.add_task(Task(
        id=f"daily-summary-{datetime.date.today()}",
        description="Generate end-of-day summary report for all departments",
        agent_name="orchestrator",
        priority=TaskPriority.MEDIUM
    ))
    
    self.add_task(Task(
        id=f"cash-position-{datetime.date.today()}",
        description="Update daily cash position and next-day forecast",
        agent_name="finance",
        priority=TaskPriority.MEDIUM
    ))

def _hourly_check(self):
    """Hourly check tasks"""
    # Check for new tickets
    self.add_task(Task(
        id=f"support-check-{datetime.datetime.now().strftime('%Y%m%d-%H')}",
        description="Check for new high-priority support tickets",
        agent_name="customer_support",
        priority=TaskPriority.HIGH
    ))
    
    # Check development progress
    self.add_task(Task(
        id=f"dev-check-{datetime.datetime.now().strftime('%Y%m%d-%H')}",
        description="Check for blocked development tasks and PR status",
        agent_name="development",
        priority=TaskPriority.MEDIUM
    ))

def _weekly_planning(self):
    """Weekly planning tasks"""
    self.add_task(Task(
        id=f"sprint-planning-{datetime.date.today()}",
        description="Prepare sprint planning materials and resource allocations",
        agent_name="development",
        priority=TaskPriority.HIGH
    ))
    
    self.add_task(Task(
        id=f"content-planning-{datetime.date.today()}",
        description="Plan next week's content calendar and marketing activities",
        agent_name="marketing",
        priority=TaskPriority.MEDIUM
    ))
    
    self.add_task(Task(
        id=f"cash-forecast-{datetime.date.today()}",
        description="Generate weekly cash flow forecast and payment schedule",
        agent_name="finance",
        priority=TaskPriority.HIGH
    ))

def _weekly_review(self):
    """Weekly review tasks"""
    self.add_task(Task(
        id=f"week-review-{datetime.date.today()}",
        description="Generate weekly performance report across all departments",
        agent_name="orchestrator",
        priority=TaskPriority.HIGH
    ))
    
    self.add_task(Task(
        id=f"marketing-metrics-{datetime.date.today()}",
        description="Analyze weekly marketing metrics and campaign performance",
        agent_name="marketing",
        priority=TaskPriority.MEDIUM
    ))
