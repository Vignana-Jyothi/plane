import json
from rest_framework import generics, status
from rest_framework.response import Response
from django.utils import timezone
from plane.db.models import Issue, Workspace
from plane.vj_startups.models.extension import VJIssueExtension
from plane.vj_startups.services.onboarding_service import OnboardingService

class BotProxyEndpoint(generics.GenericAPIView):
    # Public endpoint since Discord bot might not have auth tokens yet
    # In a real scenario, protect with a static bot token in headers
    permission_classes = []
    
    def get(self, request, *args, **kwargs):
        sheet = request.query_params.get("sheet")
        
        if sheet == "Tasks":
            workspace = Workspace.objects.filter(slug=OnboardingService.WORKSPACE_SLUG).first()
            if not workspace:
                return Response([])
                
            issues = Issue.objects.filter(workspace=workspace, project__identifier="COMMON")
            
            # Bot expects 2D array:
            # 0:id, 1:title, 2:desc, 3:status, 6:assignee, 7:wing, 19:freq, 20:last_sent
            
            data = [
                # Headers for row 0
                ["id", "title", "desc", "status", "4", "5", "assignee", "wing", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "freq", "last_sent"]
            ]
            
            for issue in issues:
                assignee = issue.assignees.first()
                assignee_name = assignee.email if assignee else ""
                
                ext, _ = VJIssueExtension.objects.get_or_create(issue=issue)
                wing_name = ext.startup.name if ext.startup else "General"
                
                row = [""] * 21
                row[0] = str(issue.id)
                row[1] = issue.name
                row[2] = issue.description_html or ""
                row[3] = issue.state.name if issue.state else "Todo"
                row[6] = assignee_name
                row[7] = wing_name
                row[19] = ext.reminder_frequency_hours
                row[20] = str(ext.last_reminder_sent.isoformat()) if ext.last_reminder_sent else ""
                
                data.append(row)
                
            return Response(data)
            
        elif sheet == "ReminderChannels":
            # Just mock it for now since we haven't built the ReminderChannels model in Plane
            data = [
                ["wing_name", "channel_id"]
            ]
            return Response(data)
            
        return Response([])

    def post(self, request, *args, **kwargs):
        sheet = request.query_params.get("sheet")
        payload = request.data
        
        if sheet == "TasksUpdate":
            task_id = payload.get("task_id")
            if task_id:
                issue = Issue.objects.filter(id=task_id).first()
                if issue:
                    ext, _ = VJIssueExtension.objects.get_or_create(issue=issue)
                    if "last_reminder_sent" in payload:
                        ext.last_reminder_sent = timezone.now()
                        ext.save()
                    return Response({"success": True})
                    
        return Response({"success": True})
