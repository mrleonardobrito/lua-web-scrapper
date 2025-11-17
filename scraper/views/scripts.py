from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..models import Script, ScriptExecution
from ..serializers import ScriptSerializer, ScriptExecutionSerializer


class ScriptViewSet(viewsets.ModelViewSet):
    serializer_class = ScriptSerializer
    queryset = Script.objects.all()

    def get_queryset(self):
        return Script.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        script = self.get_object()
        executions = script.executions.all()
        serializer = ScriptExecutionSerializer(executions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def latest_execution(self, request, pk=None):
        script = self.get_object()
        latest_execution = script.executions.order_by('-started_at').first()

        if latest_execution:
            serializer = ScriptExecutionSerializer(latest_execution)
            return Response(serializer.data)
        else:
            return Response({'message': 'Nenhuma execução encontrada'}, status=status.HTTP_404_NOT_FOUND)


class ScriptExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScriptExecutionSerializer
    queryset = ScriptExecution.objects.all()
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_queryset(self):
        return ScriptExecution.objects.filter(
            script__user=self.request.user
        ).select_related('script')
