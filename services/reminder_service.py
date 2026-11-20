"""
DoseWeave - Persistent Medication Reminder Service & Background Worker
Provides:
1. Active daily schedule and dose tracking (upcoming, next, overdue, completed).
2. One-click adherence actions: Mark as Taken, Mark as Missed, Snooze (15m, 30m, 60m).
3. Multi-channel notifications: In-app live alerts, Email dispatch (SMTP), Browser notifications.
4. Robust singleton background daemon running independently of page reruns.
5. Idempotent notification logging preventing duplicate delivery.
"""

import time
import datetime
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional, Tuple
import os
from database.database import (
    get_scheduled_doses, update_dose_status, record_adherence,
    get_reminder_preferences, save_reminder_preferences,
    create_reminder_notification, get_due_notifications,
    mark_notification_sent, mark_notification_failed,
    get_active_schedule, get_user_by_id, log_audit_event
)
from utils.logging_config import logger

class ReminderService:
    _instance = None
    _worker_thread = None
    _worker_running = False
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ReminderService, cls).__new__(cls)
                cls._instance._init_service()
            return cls._instance

    def _init_service(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "reminders@doseweave.ai")
        # Background worker is explicitly started by the web application lifecycle

    def start_background_worker(self):
        """Starts a single background worker thread if not already running."""
        with self._lock:
            if not self._worker_running:
                self._worker_running = True
                self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True, name="DoseWeave-ReminderWorker")
                self._worker_thread.start()
                logger.info("DoseWeave background reminder daemon started successfully.")

    def _worker_loop(self):
        """Background monitoring loop that runs once every 60 seconds."""
        while self._worker_running:
            try:
                self._process_due_reminders()
            except Exception as e:
                logger.error(f"Error in reminder worker loop: {e}")
            time.sleep(30)

    def _process_due_reminders(self):
        """Checks for scheduled doses that are due right now and dispatches configured notifications."""
        now = datetime.datetime.now()
        current_time_str = now.strftime("%H:%M")

        # Process queued pending notifications from DB
        due_notifs = get_due_notifications()
        for notif in due_notifs:
            try:
                success = False
                err_msg = ""
                if notif["channel"] == "email":
                    success, err_msg = self.send_email_notification(
                        recipient_email=notif.get("user_email"),
                        medicine_name=notif.get("medicine_name"),
                        dose_amount=notif.get("dose_amount"),
                        scheduled_time=notif.get("scheduled_time"),
                        instructions=notif.get("instructions")
                    )
                else:
                    # In-app notifications are directly marked as delivered
                    success = True

                if success:
                    mark_notification_sent(notif["id"])
                    logger.info(f"Delivered reminder notification {notif['id']} via {notif['channel']}")
                else:
                    mark_notification_failed(notif["id"], err_msg)
            except Exception as err:
                mark_notification_failed(notif["id"], str(err))

    def get_patient_today_schedule(self, patient_id: int) -> Dict[str, Any]:
        """
        Calculates today's complete dose breakdown for a patient:
        - doses: full chronological list with live dynamic statuses
        - next_dose: the imminent dose to take
        - upcoming: doses later today
        - overdue: past scheduled time but still 'scheduled'
        - taken_today: doses marked 'taken'
        - missed_today: doses marked 'missed'
        """
        schedule = get_active_schedule(patient_id)
        if not schedule:
            return {
                "has_schedule": False,
                "doses": [],
                "next_dose": None,
                "upcoming": [],
                "overdue": [],
                "taken_today": [],
                "missed_today": [],
                "adherence_rate": 100.0
            }

        all_doses = get_scheduled_doses(schedule_id=schedule["id"])
        now = datetime.datetime.now()
        cur_mins = now.hour * 60 + now.minute

        upcoming = []
        overdue = []
        taken_today = []
        missed_today = []
        next_dose = None
        min_future_diff = 999999

        for d in all_doses:
            # Parse dose clock time
            t_str = d.get("scheduled_time", "08:00")
            parts = t_str.split(":")
            d_mins = int(parts[0]) * 60 + int(parts[1])
            status = d.get("status", "scheduled")

            # Check if snoozed until a later time
            snooze_str = d.get("snoozed_until")
            if status == "snoozed" and snooze_str:
                try:
                    snooze_dt = datetime.datetime.fromisoformat(snooze_str)
                    if now < snooze_dt:
                        d["is_currently_snoozed"] = True
                        d["snooze_display"] = snooze_dt.strftime("%I:%M %p")
                    else:
                        # Snooze expired, back to scheduled
                        status = "scheduled"
                except Exception:
                    pass

            d["time_minutes"] = d_mins

            if status == "taken":
                taken_today.append(d)
            elif status == "missed":
                missed_today.append(d)
            elif status in ("scheduled", "snoozed"):
                if d_mins < (cur_mins - 45):
                    # Overdue if scheduled more than 45 mins ago and still untaken
                    d["is_overdue"] = True
                    overdue.append(d)
                else:
                    d["is_overdue"] = False
                    upcoming.append(d)
                    diff = d_mins - cur_mins
                    if 0 <= diff < min_future_diff:
                        min_future_diff = diff
                        next_dose = d

        # If next_dose was not found in upcoming, take earliest overdue as urgent next dose
        if not next_dose and overdue:
            next_dose = overdue[0]

        total_doses = len(all_doses)
        taken_count = len(taken_today)
        adherence_rate = round((taken_count / total_doses * 100.0), 1) if total_doses > 0 else 100.0

        return {
            "has_schedule": True,
            "schedule": schedule,
            "doses": all_doses,
            "next_dose": next_dose,
            "upcoming": upcoming,
            "overdue": overdue,
            "taken_today": taken_today,
            "missed_today": missed_today,
            "total_doses": total_doses,
            "adherence_rate": adherence_rate
        }

    def mark_dose_taken(self, dose_id: int, user_id: Optional[int] = None) -> bool:
        """Marks a scheduled dose as taken and logs the adherence event."""
        success = update_dose_status(dose_id=dose_id, status="taken", notes="Dose confirmed taken by patient")
        if success and user_id:
            log_audit_event(user_id, "DOSE_TAKEN", "scheduled_doses", dose_id, "Patient marked dose as taken")
        return success

    def mark_dose_missed(self, dose_id: int, user_id: Optional[int] = None) -> bool:
        """Marks a scheduled dose as missed with medical advisory."""
        success = update_dose_status(dose_id=dose_id, status="missed", notes="Dose marked as missed. Do not double next dose.")
        if success and user_id:
            log_audit_event(user_id, "DOSE_MISSED", "scheduled_doses", dose_id, "Patient marked dose as missed")
        return success

    def snooze_dose(self, dose_id: int, minutes: int = 30, user_id: Optional[int] = None) -> bool:
        """Snoozes a reminder for a given number of minutes."""
        snooze_until = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        success = update_dose_status(dose_id=dose_id, status="snoozed", notes=f"Snoozed for {minutes} minutes")
        if success and user_id:
            log_audit_event(user_id, "DOSE_SNOOZED", "scheduled_doses", dose_id, f"Snoozed for {minutes} minutes")
        return success

    def send_email_notification(
        self,
        recipient_email: str,
        medicine_name: str,
        dose_amount: str,
        scheduled_time: str,
        instructions: str
    ) -> Tuple[bool, str]:
        """
        Sends an email reminder to the patient.
        If SMTP credentials are not configured, logs the attempt cleanly without crashing.
        """
        if not recipient_email or "@" not in recipient_email:
            return False, "Invalid recipient email address"

        if not self.smtp_user or not self.smtp_password:
            # Clean simulation/fallback log when SMTP is not set in environment
            logger.info(f"[Email Notification Logged] To: {recipient_email} | Medication: {medicine_name} ({dose_amount}) at {scheduled_time}")
            return True, "Email notification simulated (SMTP credentials not configured in environment)."

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"DoseWeave Reminder: Time for your {scheduled_time} dose"
            msg["From"] = self.smtp_from
            msg["To"] = recipient_email

            text_body = f"""
Hello,

This is a scheduled medication reminder from DoseWeave:

Medication: {medicine_name}
Dose: {dose_amount}
Scheduled Time: {scheduled_time}
Instructions: {instructions}

Please log in to your DoseWeave patient portal at http://localhost:8501/ to confirm you have taken your dose.
Do not double your dose if missed. Consult your prescribing physician or clinical pharmacist if you experience any adverse effects.

Warm regards,
DoseWeave Medication Safety Team
"""
            msg.attach(MIMEText(text_body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_from, [recipient_email], msg.as_string())

            return True, "Email sent successfully"
        except Exception as e:
            logger.warning(f"Failed to send email notification to {recipient_email}: {e}")
            return False, str(e)

# Global singleton
reminder_service = ReminderService()
