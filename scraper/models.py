from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class ScrapingSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='created',
                              choices=[
                                  ('created', 'Criada'),
                                  ('running', 'Executando'),
                                  ('completed', 'Concluída'),
                                  ('error', 'Erro')
                              ])
    urls = models.JSONField(default=list, help_text='URLs para scraping')
    results = models.JSONField(
        default=list, help_text='Resultados do scraping')
    screenshots = models.JSONField(
        default=list, help_text='Caminhos das screenshots')

    class Meta:
        verbose_name = 'Sessão de Scraping'
        verbose_name_plural = 'Sessões de Scraping'
        ordering = ['-created_at']

    def __str__(self):
        return f'Sessão {self.session_id} - {self.status}'


class ScrapingResult(models.Model):
    session = models.ForeignKey(
        ScrapingSession, on_delete=models.CASCADE, related_name='items')
    url = models.URLField()
    title = models.CharField(max_length=500, blank=True)
    screenshot_path = models.CharField(max_length=500, blank=True)
    data = models.JSONField(default=dict)
    scraped_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Resultado de Scraping'
        verbose_name_plural = 'Resultados de Scraping'
        ordering = ['-scraped_at']

    def __str__(self):
        return f'{self.url} - {self.title or "Sem título"}'


class Script(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='scripts')
    name = models.CharField(
        max_length=200, help_text='Nome descritivo do script')
    code = models.TextField(help_text='Código Lua do script')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_executed_at = models.DateTimeField(
        null=True, blank=True, help_text='Última execução do script')

    class Meta:
        verbose_name = 'Script Lua'
        verbose_name_plural = 'Scripts Lua'
        ordering = ['-updated_at']
        unique_together = ['user', 'name']

    def __str__(self):
        return f'{self.user.username}: {self.name}'

    def save(self, *args, **kwargs):
        if self.pk:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class ScriptExecution(models.Model):
    script = models.ForeignKey(
        Script, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, default='pending',
                              choices=[
                                  ('pending', 'Pendente'),
                                  ('running', 'Executando'),
                                  ('success', 'Sucesso'),
                                  ('error', 'Erro')
                              ])
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    request_args = models.JSONField(
        default=dict, help_text='Argumentos da requisição (URL, wait, etc.)')
    response_data = models.JSONField(
        null=True, blank=True, help_text='Dados retornados pela execução')
    logs = models.TextField(blank=True, help_text='Logs da execução')
    screenshot_url = models.URLField(
        blank=True, null=True, help_text='URL da screenshot gerada')

    class Meta:
        verbose_name = 'Execução de Script'
        verbose_name_plural = 'Execuções de Scripts'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.script.name} - {self.status} ({self.started_at})'

    @property
    def duration(self):
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
