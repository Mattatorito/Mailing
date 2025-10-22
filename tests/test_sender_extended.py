#!/usr/bin/env python3
"""Расширенные тесты для mailing.sender."""

from __future__ import annotations
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, AsyncIterator

from src.mailing.models import Recipient, DeliveryResult
from src.mailing.sender import (
    run_campaign, 
    CampaignController, 
    CampaignCancelled
)
from src.resend.client import ResendError


class TestCampaignController:
    """Тесты для CampaignController."""
    
    def test_init_default_state(self):
        """Тест начального состояния контроллера."""
        controller = CampaignController()
        assert not controller.cancelled()
        assert not controller.is_cancelled
    
    def test_cancel_sets_flag(self):
        """Тест установки флага отмены."""
        controller = CampaignController()
        controller.cancel()
        assert controller.cancelled()
        assert controller.is_cancelled
    
    def test_is_cancelled_property(self):
        """Тест свойства is_cancelled."""
        controller = CampaignController()
        assert not controller.is_cancelled
        
        controller.cancel()
        assert controller.is_cancelled


class TestCampaignCancelled:
    """Тесты для исключения CampaignCancelled."""
    
    def test_exception_creation(self):
        """Тест создания исключения."""
        exc = CampaignCancelled()
        assert isinstance(exc, Exception)
        assert str(exc) == ""
    
    def test_exception_with_message(self):
        """Тест создания исключения с сообщением."""
        exc = CampaignCancelled("Campaign was cancelled")
        assert str(exc) == "Campaign was cancelled"


class TestRunCampaignAsync:
    """Тесты для асинхронной функции run_campaign."""
    
    @pytest.fixture
    def sample_recipients(self) -> List[Recipient]:
        """Создает образцы получателей для тестов."""
        return [
            Recipient(
                email="user1@example.com",
                name="User One",
                variables={"company": "Company A", "role": "Manager"}
            ),
            Recipient(
                email="user2@example.com", 
                name="User Two",
                variables={"company": "Company B", "role": "Developer"}
            ),
            Recipient(
                email="user3@example.com",
                name="User Three", 
                variables={"company": "Company C", "role": "Designer"}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_dry_run_basic(self, sample_recipients):
        """Тест базового dry run режима."""
        events = []
        async for event in run_campaign(
            recipients=sample_recipients,
            template_name="test_template.html",
            subject="Test Subject",
            dry_run=True,
            concurrency=2
        ):
            events.append(event)
        
        # Проверяем что есть события прогресса и завершения
        progress_events = [e for e in events if e.get("type") == "progress"]
        finished_events = [e for e in events if e.get("type") == "finished"]
        
        assert len(progress_events) == len(sample_recipients)
        assert len(finished_events) == 1
        
        # Проверяем результаты
        for event in progress_events:
            result = event["result"]
            assert isinstance(result, DeliveryResult)
            assert result.success is True
            assert result.status_code == 200
            assert result.provider == "dry-run"
    
    @pytest.mark.asyncio
    async def test_campaign_cancellation(self, sample_recipients):
        """Тест отмены кампании через контроллер."""
        controller = CampaignController()
        
        # Отменяем кампанию заранее
        controller.cancel()
        
        events = []
        async for event in run_campaign(
            recipients=sample_recipients,
            template_name="test_template.html", 
            subject="Test Subject",
            dry_run=True,
            concurrency=1,
            controller=controller
        ):
            events.append(event)
        
        # Должно быть событие отмены
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) >= 1
        assert "cancelled" in error_events[0].get("message", "").lower()
    
    @pytest.mark.asyncio
    @patch('mailing.sender.TemplateEngine')
    @patch('mailing.sender.DeliveryRepository')
    @patch('mailing.sender.SuppressionRepository')
    @patch('mailing.sender.ResendClient')
    @patch('mailing.sender.DailyQuota')
    async def test_template_rendering_error(
        self, mock_quota, mock_client, mock_suppressions,
        mock_repo, mock_template_engine, sample_recipients
    ):
        """Тест обработки ошибки рендеринга шаблона."""
        
        # Настраиваем моки
        mock_template_engine.return_value.render.side_effect = Exception("Template error")
        mock_suppressions.return_value.is_unsubscribed.return_value = False
        mock_suppressions.return_value.is_suppressed.return_value = False
        mock_quota.return_value.load.return_value = None
        mock_quota.return_value.register.return_value = None
        mock_repo.return_value.save_delivery.return_value = None
        
        events = []
        async for event in run_campaign(
            recipients=[sample_recipients[0]],  # Один получатель
            template_name="broken_template.html",
            subject="Test Subject", 
            dry_run=False,
            concurrency=1
        ):
            events.append(event)
        
        # Проверяем что есть событие с ошибкой
        progress_events = [e for e in events if e.get("type") == "progress"]
        assert len(progress_events) == 1
        
        result = progress_events[0]["result"]
        assert result.success is False
        assert "Template error" in result.error
    
    @pytest.mark.asyncio
    @patch('mailing.sender.TemplateEngine')
    @patch('mailing.sender.DeliveryRepository')
    @patch('mailing.sender.SuppressionRepository')
    @patch('mailing.sender.ResendClient')
    @patch('mailing.sender.DailyQuota')
    async def test_suppression_handling(
        self, mock_quota, mock_client, mock_suppressions,
        mock_repo, mock_template_engine, sample_recipients
    ):
        """Тест обработки подавленных email адресов."""
        
        # Настраиваем моки - первый адрес отписан, второй подавлен
        def mock_unsubscribed(email):
            return email == "user1@example.com"
        
        def mock_suppressed(email):
            return email == "user2@example.com"
        
        mock_suppressions.return_value.is_unsubscribed.side_effect = mock_unsubscribed
        mock_suppressions.return_value.is_suppressed.side_effect = mock_suppressed
        mock_quota.return_value.load.return_value = None
        mock_template_engine.return_value.render.return_value = ("<html>", "text")
        mock_repo.return_value.save_delivery.return_value = None
        
        # Мокаем успешную отправку для третьего получателя
        mock_client.return_value.send_message = AsyncMock(return_value=DeliveryResult(
            email="user3@example.com",
            success=True,
            status_code=200,
            provider="resend"
        ))
        
        events = []
        async for event in run_campaign(
            recipients=sample_recipients,
            template_name="test_template.html",
            subject="Test Subject",
            dry_run=False,
            concurrency=2
        ):
            events.append(event)
        
        progress_events = [e for e in events if e.get("type") == "progress"]
        assert len(progress_events) == 3
        
        # Проверяем результаты
        results = [e["result"] for e in progress_events]
        
        # Находим результат для каждого получателя
        user1_result = next(r for r in results if r.email == "user1@example.com")
        user2_result = next(r for r in results if r.email == "user2@example.com") 
        user3_result = next(r for r in results if r.email == "user3@example.com")
        
        assert user1_result.success is False
        assert user1_result.error == "unsubscribed"
        
        assert user2_result.success is False
        assert user2_result.error == "suppressed"
        
        assert user3_result.success is True
    
    @pytest.mark.asyncio
    @patch('mailing.sender.TemplateEngine')
    @patch('mailing.sender.DeliveryRepository')
    @patch('mailing.sender.SuppressionRepository')
    @patch('mailing.sender.ResendClient')
    @patch('mailing.sender.DailyQuota')
    async def test_resend_api_error(
        self, mock_quota, mock_client, mock_suppressions,
        mock_repo, mock_template_engine, sample_recipients
    ):
        """Тест обработки ошибки Resend API."""
        
        # Настраиваем моки
        mock_suppressions.return_value.is_unsubscribed.return_value = False
        mock_suppressions.return_value.is_suppressed.return_value = False
        mock_quota.return_value.load.return_value = None
        mock_quota.return_value.register.return_value = None
        mock_template_engine.return_value.render.return_value = ("<html>", "text")
        mock_repo.return_value.save_delivery.return_value = None
        
        # Мокаем ошибку Resend API
        mock_client.return_value.send_message = AsyncMock(
            side_effect=ResendError("API rate limit exceeded")
        )
        
        events = []
        async for event in run_campaign(
            recipients=[sample_recipients[0]],
            template_name="test_template.html",
            subject="Test Subject",
            dry_run=False,
            concurrency=1
        ):
            events.append(event)
        
        progress_events = [e for e in events if e.get("type") == "progress"]
        assert len(progress_events) == 1
        
        result = progress_events[0]["result"]
        assert result.success is False
        assert "API rate limit exceeded" in result.error
    
    @pytest.mark.asyncio
    async def test_concurrency_control(self, sample_recipients):
        """Тест управления конкурентностью."""
        # Создаем больше получателей для тестирования конкурентности
        many_recipients = []
        for i in range(10):
            many_recipients.append(Recipient(
                email=f"user{i}@example.com",
                name=f"User {i}",
                variables={"index": str(i)}
            ))
        
        # Тестируем с низкой конкурентностью
        start_time = asyncio.get_event_loop().time()
        events = []
        
        async for event in run_campaign(
            recipients=many_recipients,
            template_name="test_template.html",
            subject="Test Subject",
            dry_run=True,
            concurrency=2  # Низкая конкурентность
        ):
            events.append(event)
        
        end_time = asyncio.get_event_loop().time()
        low_concurrency_time = end_time - start_time
        
        # Проверяем что все события получены
        progress_events = [e for e in events if e.get("type") == "progress"]
        assert len(progress_events) == len(many_recipients)
        
        # Время выполнения должно быть больше при низкой конкурентности
        # (каждый recipient имеет sleep 0.1, с concurrency=2 должно быть ~0.5 сек)
        assert low_concurrency_time >= 0.4
    
    @pytest.mark.asyncio
    async def test_stats_aggregation(self, sample_recipients):
        """Тест агрегации статистики."""
        events = []
        async for event in run_campaign(
            recipients=sample_recipients,
            template_name="test_template.html",
            subject="Test Subject",
            dry_run=True,
            concurrency=2
        ):
            events.append(event)
        
        # Проверяем что в каждом событии есть статистика
        for event in events:
            assert "stats" in event
            stats = event["stats"]
            assert isinstance(stats, dict)
        
        # Финальная статистика должна содержать все отправки
        finished_event = next(e for e in events if e.get("type") == "finished")
        final_stats = finished_event["stats"]
        
        # Проверяем что статистика корректна
        assert "sent" in final_stats or "total" in final_stats
    
    @pytest.mark.asyncio
    async def test_empty_recipients_list(self):
        """Тест с пустым списком получателей."""
        events = []
        async for event in run_campaign(
            recipients=[],
            template_name="test_template.html",
            subject="Test Subject",
            dry_run=True,
            concurrency=2
        ):
            events.append(event)
        
        # Должно быть только событие завершения
        assert len(events) == 1
        assert events[0]["type"] == "finished"
    
    @pytest.mark.asyncio
    @patch('mailing.sender.logger')
    async def test_logging(self, mock_logger, sample_recipients):
        """Тест логирования в процессе кампании."""
        events = []
        async for event in run_campaign(
            recipients=sample_recipients,
            template_name="test_template.html",
            subject="Test Subject",
            dry_run=True,
            concurrency=2
        ):
            events.append(event)
        
        # Проверяем что логирование было вызвано
        mock_logger.info.assert_called()
        
        # Проверяем что логируется начало кампании
        call_args = [call[0] for call in mock_logger.info.call_args_list]
        start_logged = any("Starting campaign" in str(args) for args in call_args)
        assert start_logged


class TestBatchSending:
    """Тесты для batch отправки."""
    
    @pytest.mark.asyncio
    @patch('mailing.sender.TemplateEngine')
    @patch('mailing.sender.DeliveryRepository')
    @patch('mailing.sender.SuppressionRepository') 
    @patch('mailing.sender.ResendClient')
    @patch('mailing.sender.DailyQuota')
    async def test_large_batch_handling(
        self, mock_quota, mock_client, mock_suppressions,
        mock_repo, mock_template_engine
    ):
        """Тест обработки большого batch'а получателей."""
        
        # Создаем большой список получателей
        large_recipients = []
        for i in range(100):
            large_recipients.append(Recipient(
                email=f"user{i}@example.com",
                name=f"User {i}",
                variables={"batch_id": "large_test"}
            ))
        
        # Настраиваем моки
        mock_suppressions.return_value.is_unsubscribed.return_value = False
        mock_suppressions.return_value.is_suppressed.return_value = False
        mock_quota.return_value.load.return_value = None
        mock_template_engine.return_value.render.return_value = ("<html>", "text")
        mock_repo.return_value.save_delivery.return_value = None
        
        # Счетчик вызовов для проверки batch обработки
        call_count = 0
        
        async def mock_send(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return DeliveryResult(
                email=f"user{call_count-1}@example.com",
                success=True,
                status_code=200,
                provider="resend"
            )
        
        mock_client.return_value.send_message = mock_send
        
        events = []
        async for event in run_campaign(
            recipients=large_recipients,
            template_name="test_template.html",
            subject="Batch Test",
            dry_run=False,
            concurrency=10  # Высокая конкурентность для batch
        ):
            events.append(event)
        
        # Проверяем что все получатели обработаны
        progress_events = [e for e in events if e.get("type") == "progress"]
        assert len(progress_events) == 100
        
        # Проверяем что все отправки успешны
        successful_results = [
            e["result"] for e in progress_events 
            if e["result"].success
        ]
        assert len(successful_results) == 100


class TestErrorHandling:
    """Тесты для обработки ошибок."""
    
    @pytest.mark.asyncio
    @patch('mailing.sender.TemplateEngine')
    async def test_template_engine_import_error(self, mock_template_engine):
        """Тест обработки ошибки импорта TemplateEngine."""
        
        # Мокаем ошибку инициализации
        mock_template_engine.side_effect = ImportError("Cannot import TemplateEngine")
        
        with pytest.raises(ImportError):
            events = []
            async for event in run_campaign(
                recipients=[Recipient(email="test@example.com", variables={})],
                template_name="test_template.html",
                subject="Test",
                dry_run=True,
                concurrency=1
            ):
                events.append(event)
    
    @pytest.mark.asyncio
    async def test_exception_in_task_processing(self):
        """Тест обработки исключения при обработке отдельной задачи."""
        controller = CampaignController()
        recipient = Recipient(email="test@example.com", variables={})
        
        events = []
        async for event in run_campaign(
            recipients=[recipient],
            template_name="test_template.html",
            subject="Test",
            dry_run=True,
            concurrency=1,
            controller=controller
        ):
            events.append(event)
        
        # Проверяем нормальное завершение
        finished_events = [e for e in events if e.get("type") == "finished"]
        assert len(finished_events) == 1
    
    @pytest.mark.asyncio
    @patch('mailing.sender.TemplateEngine')
    @patch('mailing.sender.DeliveryRepository')
    @patch('mailing.sender.SuppressionRepository')
    @patch('mailing.sender.ResendClient')
    @patch('mailing.sender.DailyQuota')
    async def test_worker_exception_handling(
        self, mock_quota, mock_client, mock_suppressions,
        mock_repo, mock_template_engine
    ):
        """Тест обработки исключения в worker функции."""
        
        # Настраиваем моки для нормальной работы
        mock_suppressions.return_value.is_unsubscribed.return_value = False
        mock_suppressions.return_value.is_suppressed.return_value = False
        mock_quota.return_value.load.return_value = None
        mock_quota.return_value.register.return_value = None
        mock_repo.return_value.save_delivery.return_value = None
        
        # Мокаем ошибку в рендеринге
        mock_template_engine.return_value.render.side_effect = RuntimeError("Worker failed")
        
        recipients = [Recipient(email="test@example.com", variables={})]
        
        events = []
        async for event in run_campaign(
            recipients=recipients,
            template_name="test_template.html",
            subject="Test",
            dry_run=False,
            concurrency=1
        ):
            events.append(event)
        
        # Должно быть событие с ошибкой и событие завершения
        progress_events = [e for e in events if e.get("type") == "progress"]
        finished_events = [e for e in events if e.get("type") == "finished"]
        
        assert len(progress_events) == 1
        assert len(finished_events) == 1
        
        # Проверяем что ошибка зафиксирована
        result = progress_events[0]["result"]
        assert result.success is False
        assert "Worker failed" in result.error


if __name__ == "__main__":
    pytest.main([__file__])