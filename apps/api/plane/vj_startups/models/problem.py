from django.db import models
from django.conf import settings
from plane.db.models import BaseModel

class ProblemStatement(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, default="open")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="problem_statements"
    )
    upvotes = models.IntegerField(default=0)
    validation_score = models.FloatField(default=0.0)
    public = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Problem Statement"
        verbose_name_plural = "Problem Statements"
        db_table = "vj_problem_statements"

    def __str__(self):
        return self.title

class SolutionProposal(BaseModel):
    problem = models.ForeignKey(ProblemStatement, on_delete=models.CASCADE, related_name="solutions")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="solution_proposals"
    )
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default="proposed")

    class Meta:
        verbose_name = "Solution Proposal"
        verbose_name_plural = "Solution Proposals"
        db_table = "vj_solution_proposals"

    def __str__(self):
        return f"Solution to {self.problem.title}"
