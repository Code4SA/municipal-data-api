from django.conf.urls import include, url
from rest_framework import routers
from .. import views

router = routers.DefaultRouter()
router.register(r'financial_years', views.FinancialYearViewSet)
router.register(r'budget_phases', views.BudgetPhaseViewSet)
router.register(r'projects', views.ProjectViewSet)
#router.register("search", views.ProjectSearchView, base_name="project-search")

urlpatterns = router.urls
