def format_deadline_phrase(deadline):
    """
    Formulates a natural preposition prefix for the deadline if needed.
    """
    if not deadline or deadline == "Not Applicable":
        return "Not Applicable"
        
    dl_lower = deadline.lower().strip()
    
    # If it already starts with a preposition or standard indicator, return as is
    if (dl_lower.startswith('by') or 
        dl_lower.startswith('within') or 
        dl_lower.startswith('before') or
        dl_lower.startswith('this') or
        dl_lower.startswith('tomorrow') or
        dl_lower.startswith('next')):
        return deadline
        
    return f"by {deadline}"

def generate_followup_email(assignee, action_item, deadline, priority):
    """
    Generates a structured single-task follow-up email.
    """
    assignee_name = str(assignee).strip()
    action = str(action_item).strip()
    prio_str = str(priority).capitalize()
    
    if action and not action[0].isupper():
        action = action[0].upper() + action[1:]
        
    formatted_deadline = format_deadline_phrase(deadline)
    subject = f"Follow-up: {action}"
    
    body = (
        f"Hi {assignee_name},\n\n"
        f"This is a follow-up regarding the task discussed in the meeting.\n\n"
        f"Task:\n{action}\n\n"
        f"Deadline:\n{formatted_deadline}\n\n"
        f"Priority:\n{prio_str}\n\n"
        f"Please complete the task within the specified deadline.\n\n"
        f"Regards,\n"
        f"AI Meeting Follow-Up Agent"
    )
    return {"subject": subject, "body": body}

def generate_followup_sms(assignee, action_item, deadline, priority):
    """
    Generates a concise single-task follow-up SMS.
    """
    assignee_name = str(assignee).strip()
    action = str(action_item).strip()
    prio_str = str(priority).capitalize()
    
    dl_lower = deadline.lower().strip() if deadline else ""
    if dl_lower.startswith('by') or dl_lower.startswith('within') or dl_lower.startswith('before'):
        deadline_text = dl_lower
    elif dl_lower in ['tomorrow', 'this afternoon', 'next week']:
        deadline_text = f"by {dl_lower}"
    else:
        deadline_text = f"by {dl_lower}" if dl_lower else ""
        
    if deadline_text:
        sms = f"Hi {assignee_name}, reminder to work on {action.lower()} {deadline_text}. Priority: {prio_str}."
    else:
        sms = f"Hi {assignee_name}, reminder to work on {action.lower()}. Priority: {prio_str}."
    return sms

def generate_multi_followup_email(action_items):
    """
    Generates a consolidated meeting follow-up email containing all action items.
    """
    if not action_items:
        return {
            "subject": "Meeting Follow-Up — No Actions Required",
            "body": (
                "Hi team,\n\n"
                "This is a follow-up summary from our recent meeting. No action items were assigned.\n\n"
                "Regards,\n"
                "AI Meeting Follow-Up Agent"
            )
        }
        
    subject = "Meeting Follow-Up — Action Items"
    
    body = (
        "Hi team,\n\n"
        "Here are the action items discussed in the meeting:\n\n"
    )
    
    for i, item in enumerate(action_items, 1):
        assignee = item.get("assignee", "Not Applicable")
        action = item.get("action_item", "Not Applicable")
        deadline = format_deadline_phrase(item.get("deadline", "Not Applicable"))
        priority = str(item.get("priority", "medium")).capitalize()
        
        body += (
            f"{i}. {assignee}\n"
            f"   Task: {action}\n"
            f"   Deadline: {deadline}\n"
            f"   Priority: {priority}\n\n"
        )
        
    body += (
        "Please complete the assigned tasks within the specified deadlines.\n\n"
        "Regards,\n"
        "AI Meeting Follow-Up Agent"
    )
    
    return {
        "subject": subject,
        "body": body
    }

def generate_multi_followup_sms(action_items):
    """
    Generates a combined, concise SMS reminder listing key task items.
    """
    if not action_items:
        return "No follow-up action required."
        
    sms = "Meeting Follow-Up:"
    for i, item in enumerate(action_items, 1):
        assignee = item.get("assignee", "Not Applicable")
        action = item.get("action_item", "Not Applicable")
        deadline = item.get("deadline", "Not Applicable")
        # Keep SMS extremely short
        sms += f" {i}. {assignee} ({action}: {deadline})"
        
    if len(sms) > 200:
        sms = sms[:197] + "..."
        
    return sms
