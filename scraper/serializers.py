from rest_framework import serializers
from .models import Script, ScriptExecution


class ScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Script
        fields = [
            'id', 'name', 'code', 'created_at', 'updated_at', 'last_executed_at'
        ]
        read_only_fields = ['id', 'created_at',
                            'updated_at', 'last_executed_at']

    def validate_name(self, value):
        user = self.context['request'].user
        queryset = Script.objects.filter(user=user, name=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Você já possui um script com este nome.")

        return value


class ScriptExecutionSerializer(serializers.ModelSerializer):
    script_name = serializers.CharField(source='script.name', read_only=True)

    class Meta:
        model = ScriptExecution
        fields = [
            'id', 'script', 'script_name', 'status', 'started_at', 'finished_at',
            'request_args', 'response_data', 'logs', 'screenshot_url', 'duration'
        ]
        read_only_fields = [
            'id', 'script', 'script_name', 'started_at', 'finished_at', 'duration'
        ]


class SubscribeInputSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['subscribe'], required=True)
    session_id = serializers.CharField(required=False, allow_null=True)


class SubscribedOutputSerializer(serializers.Serializer):
    type = serializers.CharField(default='subscribed')
    session_id = serializers.CharField(required=False, allow_null=True)
    message = serializers.CharField()


class ErrorOutputSerializer(serializers.Serializer):
    type = serializers.CharField(default='error')
    message = serializers.CharField()


class LuaExecutionProgressOutputSerializer(serializers.Serializer):
    type = serializers.CharField(default='lua_execution_progress')
    session_id = serializers.CharField()
    step_index = serializers.IntegerField(required=False, allow_null=True)
    step_title = serializers.CharField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['pending', 'running', 'success', 'error'],
        default='running'
    )
    log = serializers.CharField(required=False, allow_null=True)
    timestamp = serializers.FloatField(required=False, allow_null=True)


class LuaExecutionCompletedOutputSerializer(serializers.Serializer):
    type = serializers.CharField(default='lua_execution_completed')
    session_id = serializers.CharField()
    success = serializers.BooleanField(default=False)
    result = serializers.DictField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    timestamp = serializers.FloatField(required=False, allow_null=True)


class LuaExecutionErrorOutputSerializer(serializers.Serializer):
    type = serializers.CharField(default='lua_execution_error')
    session_id = serializers.CharField()
    error = serializers.CharField(required=False, allow_null=True)
    details = serializers.CharField(required=False, allow_null=True)
    timestamp = serializers.FloatField(required=False, allow_null=True)
