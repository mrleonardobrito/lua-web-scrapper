from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import lua_editor, auth, scripts

app_name = 'scraper'

router = DefaultRouter()
router.register(r'scripts', scripts.ScriptViewSet, basename='script')
router.register(r'script-executions',
                scripts.ScriptExecutionViewSet, basename='script-execution')

urlpatterns = [
    path('api/', include(router.urls)),

    # Lua execution
    path('api/lua/execute/', lua_editor.ExecuteLuaScriptAsyncView.as_view(),
         name='execute_lua_script_async'),

    # Authentication
    path('api/auth/csrf-token/', auth.csrf_token, name='csrf_token'),
    path('api/auth/user/', auth.user_info, name='user_info'),
    path('api/auth/completed/', auth.post_login_redirect,
         name='post_login_redirect'),
    path('api/auth/logout/', auth.logout, name='logout'),
]
